#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) args.set(process.argv[i], process.argv[i + 1]);
const snapshot = path.resolve(args.get("--snapshot") || "");
const output = path.resolve(args.get("--output") || "");
const summaryOutput = path.resolve(args.get("--summary") || "");
const nativeCatalog = path.resolve(args.get("--native-catalog") || "");
const includePatchHistory = args.get("--include-patch-history") === "true";
if (!snapshot || !output || !summaryOutput) throw new Error("Required: --snapshot --output --summary");

const require = createRequire(import.meta.url);
const typescriptPath = path.join(snapshot, "preact", "node_modules", "typescript");
const ts = require(typescriptPath);

const DISPLAY_PROPS = new Set([
  "label", "title", "description", "text", "message", "tooltip", "placeholder",
  "caption", "header", "emptytext", "confirmtext", "canceltext", "displayname",
  "reason", "subtitle", "hint",
]);
const PATCH_DISPLAY_PROPS = new Set([
  "before", "after", "value", "name", "tag", "date",
  "size", "win", "loss", "situation",
]);
const JSX_ATTRIBUTES = new Set([
  "aria-label", "title", "placeholder", "alt", "label", "text", "message",
  "description", "caption", "header", "tooltip",
]);
const MESSAGE_CALL = /^(?:setError|setMessage|showError|showToast|addToast|notify|alert|confirm)$/i;

function walkFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  const result = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) result.push(...walkFiles(full));
    else if (/\.(?:ts|tsx|js|jsx)$/i.test(entry.name)) result.push(full);
  }
  return result;
}

function layerFor(relative) {
  const normalized = relative.replaceAll("\\", "/");
  const match = normalized.match(/\/layers\/([^/]+)\//);
  if (match) return match[1];
  if (normalized.startsWith("preact-remote/")) return "motd_remote";
  if (normalized.includes("/components/")) return "shared_component";
  if (normalized.includes("/apis/") || normalized.includes("/services/")) return "api";
  if (normalized.includes("/config/")) return "config";
  return "app_shell";
}

function normalize(value) {
  return value.replace(/\s+/g, " ").trim();
}

function visible(value, context) {
  value = normalize(value);
  if (value.length < 1 || value.length > 1000 || !/\p{L}/u.test(value)) return false;
  if (/^(?:https?:|\/|\.\/|\.\.\/|@\/|data:)/i.test(value)) return false;
  if (/\.(?:png|webp|jpg|svg|css|ts|tsx|js|json|wav|ogg)$/i.test(value)) return false;
  if (/^(?:M\d|rgba?\(|hsla?\()/i.test(value)) return false;
  if (/^\d+(?:px|rem|em|%)(?:\s+\d+(?:px|rem|em|%))*$/i.test(value)) return false;
  if (context !== "jsx_text" && /^[a-z0-9_.:/@-]+$/.test(value)) return false;
  return true;
}

const canonicalTerms = [];
if (nativeCatalog && fs.existsSync(nativeCatalog)) {
  for (const line of fs.readFileSync(nativeCatalog, "utf8").split(/\r?\n/)) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (!["hero_name", "ability_name", "item_name", "announcer_event"].includes(row.category)) continue;
    const term = normalize(row.english.replace(/\^(?:[0-9]{3}|[A-Za-z]|\*)/g, ""));
    if (term.length < 3) continue;
    if (["hero_name", "announcer_event"].includes(row.category) || term.includes(" ") || term.length >= 8) {
      canonicalTerms.push(term);
    }
  }
  canonicalTerms.sort((a, b) => b.length - a.length || a.localeCompare(b));
}

function protectedTerms(value) {
  const found = [];
  const occupied = [];
  for (const term of canonicalTerms) {
    let index = value.indexOf(term);
    while (index >= 0) {
      const end = index + term.length;
      const left = index === 0 ? "" : value[index - 1];
      const right = end === value.length ? "" : value[end];
      const boundary = !/[A-Za-z0-9]/.test(left) && !/[A-Za-z0-9]/.test(right);
      const overlap = occupied.some(([a, b]) => !(end <= a || index >= b));
      if (boundary && !overlap) {
        occupied.push([index, end]);
        found.push(term);
      }
      index = value.indexOf(term, index + 1);
    }
  }
  return [...new Set(found)];
}

const rows = [];
const seen = new Map();
let excludedPatchHistoryFiles = 0;
let scannedFiles = 0;

function addCandidate(sourceFile, node, value, kind, status = "TRANSLATE", context = "") {
  value = normalize(value);
  if (!visible(value, kind)) return;
  const relative = path.relative(snapshot, sourceFile.fileName).replaceAll("\\", "/");
  const pos = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
  const base = `${relative}\0${kind}\0${value}`;
  const occurrence = (seen.get(base) || 0) + 1;
  seen.set(base, occurrence);
  const hash = crypto.createHash("sha256").update(value).digest("hex");
  rows.push({
    id: `preact:${relative}:${kind}:${hash.slice(0, 12)}:${occurrence}`,
    english: value,
    source_file: relative,
    source_line: pos.line + 1,
    source_column: pos.character + 1,
    kind,
    layer: layerFor(relative),
    context,
    status,
    runtime_role: "DISPLAY_TEXT",
    protected_terms: protectedTerms(value),
    russian: "",
    english_hash: hash,
  });
}

function literalValue(node) {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  return null;
}

function collectLiteralDescendants(node, result = []) {
  const value = literalValue(node);
  if (value !== null) result.push([node, value]);
  else ts.forEachChild(node, child => collectLiteralDescendants(child, result));
  return result;
}

const roots = [path.join(snapshot, "preact", "src"), path.join(snapshot, "preact-remote", "src")];
for (const fileName of roots.flatMap(walkFiles).sort()) {
  const normalizedFile = fileName.replaceAll("\\", "/");
  if (!includePatchHistory && /\/patch-notes-v2\/patches\//i.test(normalizedFile)) {
    excludedPatchHistoryFiles++;
    continue;
  }
  if (/\/(?:mock|mockdata)\.(?:ts|tsx|js|jsx)$/i.test(normalizedFile) || /\/components\/icons\//i.test(normalizedFile)) continue;
  scannedFiles++;
  const sourceText = fs.readFileSync(fileName, "utf8");
  const scriptKind = /\.tsx$/i.test(fileName) ? ts.ScriptKind.TSX : /\.jsx$/i.test(fileName) ? ts.ScriptKind.JSX : ts.ScriptKind.TS;
  const sourceFile = ts.createSourceFile(fileName, sourceText, ts.ScriptTarget.Latest, true, scriptKind);

  function visit(node, countryMap = false) {
    let inCountryMap = countryMap;
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === "COUNTRY_MAP") inCountryMap = true;

    if (ts.isJsxText(node)) {
      addCandidate(sourceFile, node, node.getText(sourceFile), "jsx_text", "TRANSLATE", "Rendered JSXText");
    } else if (ts.isJsxAttribute(node)) {
      const name = node.name.getText(sourceFile).toLowerCase();
      if (JSX_ATTRIBUTES.has(name) && node.initializer) {
        if (ts.isStringLiteral(node.initializer)) {
          addCandidate(sourceFile, node.initializer, node.initializer.text, "jsx_attribute", name === "alt" ? "REVIEW" : "TRANSLATE", `JSX ${name}`);
        } else if (ts.isJsxExpression(node.initializer) && node.initializer.expression) {
          const expression = node.initializer.expression;
          const value = literalValue(expression);
          if (value !== null) addCandidate(sourceFile, expression, value, "jsx_attribute", name === "alt" ? "REVIEW" : "TRANSLATE", `JSX ${name}`);
          else if (ts.isTemplateExpression(expression)) addCandidate(sourceFile, expression, expression.getText(sourceFile).slice(1, -1), "jsx_template_attribute", "REVIEW", `Dynamic JSX ${name}`);
        }
      }
    } else if (ts.isJsxExpression(node) && node.expression && (includePatchHistory || ts.isConditionalExpression(node.expression))) {
      const branches = ts.isConditionalExpression(node.expression)
        ? [node.expression.whenTrue, node.expression.whenFalse]
        : [node.expression];
      for (const branch of branches) {
        const value = literalValue(branch);
        if (value !== null) {
          addCandidate(sourceFile, branch, value, "jsx_expression_literal", "TRANSLATE", "Rendered JSX conditional literal");
        }
      }
    } else if (ts.isPropertyAssignment(node)) {
      const property = node.name.getText(sourceFile).replace(/^['"]|['"]$/g, "").toLowerCase();
      const value = literalValue(node.initializer);
      if (value !== null && (DISPLAY_PROPS.has(property) || inCountryMap || (includePatchHistory && PATCH_DISPLAY_PROPS.has(property)))) {
        addCandidate(sourceFile, node.initializer, value, inCountryMap ? "display_map_value" : "display_config_value", "TRANSLATE", inCountryMap ? "COUNTRY_MAP display name" : `Display property ${property}`);
      } else if (includePatchHistory && property === "lines") {
        for (const [literalNode, literal] of collectLiteralDescendants(node.initializer)) {
          addCandidate(sourceFile, literalNode, literal, "display_config_value", "TRANSLATE", "Patch editorial line");
        }
      }
    } else if (ts.isCallExpression(node)) {
      const expressionName = node.expression.getText(sourceFile).split(".").at(-1);
      if (MESSAGE_CALL.test(expressionName)) {
        for (const argument of node.arguments) {
          for (const [literalNode, value] of collectLiteralDescendants(argument)) {
            addCandidate(sourceFile, literalNode, value, "user_message", "REVIEW", `User-message call ${expressionName}`);
          }
        }
      }
    }

    ts.forEachChild(node, child => visit(child, inCountryMap));
  }
  visit(sourceFile, false);
}

rows.sort((a, b) => a.source_file.localeCompare(b.source_file) || a.source_line - b.source_line || a.source_column - b.source_column || a.id.localeCompare(b.id));
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, rows.map(row => JSON.stringify(row)).join("\n") + "\n", "utf8");

const countBy = key => Object.fromEntries([...rows.reduce((map, row) => map.set(row[key], (map.get(row[key]) || 0) + 1), new Map())].sort());
const summary = {
  parser: `TypeScript Compiler API ${ts.version}`,
  scanned_files: scannedFiles,
  excluded_patch_history_files: excludedPatchHistoryFiles,
  candidate_count: rows.length,
  by_layer: countBy("layer"),
  by_kind: countBy("kind"),
  by_status: countBy("status"),
  protected_term_rows: rows.filter(row => row.protected_terms.length > 0).length,
  exclusions: ["CSS", "SVG path data", "class names", "route IDs", "API URLs", "resource paths", "technical enums", "mock data", ...(includePatchHistory ? [] : ["patch-notes-v2/patches history"])],
};
fs.writeFileSync(summaryOutput, JSON.stringify(summary, null, 2) + "\n", "utf8");
process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
