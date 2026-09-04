// Isolated runtime test: no network, no game, no installation.
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

const file = "build/phase2a-preact-workspace/preact-remote/src/components/motd.tsx";
const source = readFileSync(file, "utf8");
const start = source.indexOf("const RU_TEXT");
const end = source.indexOf("function tagText", start);
assert(start >= 0 && end > start);
const js = new Bun.Transpiler({ loader: "ts" }).transformSync(source.slice(start, end));
const localize = new Function(js + "; return localize;")();
assert.equal(localize("HOTFIX PATCH"), "ИСПРАВЛЕНИЯ");
assert.equal(localize("Patch 0.12.6.1 Hotfix"), "Исправления патча 0.12.6.1");
assert.match(localize("Warforged Chipper is a brand new concept, and it is here because you asked for it. New effects, voice and model."), /по просьбам игроков/);
assert.match(localize("Succubus joins the roster. Smitten is area denial now, not a single-target hold, and Headmistress lands with her."), /снижает урон врагов/);
assert.equal(localize("PATCH NOTES"), "ОПИСАНИЕ ПАТЧА");
assert.equal(localize("Unknown future announcement"), "Unknown future announcement");
console.log("PASS: 6 MOTD lookup and fallback cases");
