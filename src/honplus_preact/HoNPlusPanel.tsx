import { useEffect, useMemo, useState } from "preact/hooks";
import { useMatchStats } from "@/apis/match-stats/useMatchStats";
import type { PlayerSnapshot } from "@/apis/match-stats/types";
import "./honplus.css";

type Axis = { id: string; name: string; score: number | null };
type Profile = { minute: number; sampleCount: number; reliability: string; axes: Axis[] };
type Player = {
  accountId: string;
  username: string;
  heroId: number;
  roleIndex: number;
  team?: string;
  slotIndex?: number;
  timeline: Profile[];
};
type MatchReport = { modelVersion: string; matchId: number; players: Player[] };

const API_ROOT = "http://127.0.0.1:17821";
const HERO_ICON = (heroId: number) => heroId > 0
  ? `https://gamestorage.juvio.com/heroes/${heroId}/icon.webp`
  : "/assets/hero-placeholder.png";
const ROLE_NAMES: Record<number, string> = {
  1: "Керри", 2: "Мид", 3: "Оффлейн", 4: "Саппорт 4",
  5: "Саппорт 5", 6: "Соло-оффлейн", 7: "Лес",
};
const AXIS_NAMES: Record<string, string> = {
  economy: "ЭКОНОМИКА",
  combat: "ИМПАКТ",
  "team-impact": "КОМАНДА",
};
const RELIABILITY: Record<string, string> = {
  VERY_LOW: "очень мало данных",
  LOW: "мало данных",
  MEDIUM: "средняя выборка",
  GOOD: "хорошая выборка",
  HIGH: "высокая надёжность",
};

function ScoreCard({ axis }: { axis: Axis }) {
  const score = axis.score == null ? null : Math.round(axis.score);
  return (
    <div className={`honplus-score honplus-score-${axis.id}`}>
      <div className="honplus-score-name">{AXIS_NAMES[axis.id] ?? axis.name}</div>
      <div className="honplus-score-value">{score == null ? "—" : score}</div>
      <div className="honplus-score-track">
        <div className="honplus-score-fill" style={{ width: `${score ?? 0}%` }} />
      </div>
      <div className="honplus-score-caption">процентиль среди этого героя и роли</div>
    </div>
  );
}

export default function HoNPlusPanel({ matchId }: { matchId: string }) {
  const [requestedMatchId, setRequestedMatchId] = useState(matchId);
  const [report, setReport] = useState<MatchReport | null>(null);
  const [error, setError] = useState("");
  const [selectedPlayer, setSelectedPlayer] = useState(0);
  const [selectedMinute, setSelectedMinute] = useState<number | null>(null);
  const { data: nativeMatchStats } = useMatchStats(requestedMatchId);

  useEffect(() => {
    let active = true;
    setReport(null);
    setError("");
    fetch(`${API_ROOT}/api/v1/matches/${encodeURIComponent(requestedMatchId)}/triangle`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error(response.status === 404 ? "Матч ещё не собран HoN Plus." : `Ошибка API: ${response.status}`);
        return (await response.json()) as MatchReport;
      })
      .then((value) => active && setReport(value))
      .catch((reason) => active && setError(reason instanceof Error ? reason.message : "Не удалось подключиться к HoN Plus."));
    return () => { active = false; };
  }, [requestedMatchId]);

  const nativePlayers = useMemo(() => {
    const byAccount = new Map<string, PlayerSnapshot>();
    const bySlot = new Map<string, PlayerSnapshot>();
    const first = nativeMatchStats?.snapshots?.[0];
    for (const team of first?.teams ?? []) {
      for (const nativePlayer of team.players) {
        if (nativePlayer.accountId) byAccount.set(nativePlayer.accountId, nativePlayer);
        if (nativePlayer.slotIndex != null) bySlot.set(`${team.team}:${nativePlayer.slotIndex}`, nativePlayer);
      }
    }
    return { byAccount, bySlot };
  }, [nativeMatchStats]);

  const rankedPlayers = useMemo(() => (report?.players ?? []).map((item) => {
    const detail = nativePlayers.byAccount.get(item.accountId)
      ?? nativePlayers.bySlot.get(`${item.team}:${item.slotIndex}`);
    const lastProfile = item.timeline[item.timeline.length - 1];
    const impact = lastProfile?.axes.find((axis) => axis.id === "combat")?.score ?? -1;
    const heroId = detail?.heroId || item.heroId;
    const heroName = detail?.heroName || `Герой ${heroId}`;
    const rawName = detail?.name || item.username;
    const displayName = /^[0-9a-f]{8}-[0-9a-f-]{27}$/i.test(rawName) ? heroName : rawName;
    return { ...item, heroId, heroName, displayName, impact };
  }).sort((left, right) => right.impact - left.impact), [report, nativePlayers]);

  const player = rankedPlayers[selectedPlayer] ?? null;
  const profile = useMemo(() => {
    if (!player?.timeline.length) return null;
    return player.timeline.find((item) => item.minute === selectedMinute) ?? player.timeline[player.timeline.length - 1];
  }, [player, selectedMinute]);

  if (error) return (
    <div className="honplus-state honplus-error">
      <strong>HoN Plus недоступен</strong>
      <span>{error}</span>
      <span>Запустите локальный сервис HoN Plus. Для проверки интерфейса доступен собранный тестовый матч.</span>
      <button className="honplus-demo" onClick={() => setRequestedMatchId("869842")}>Открыть тестовый матч 869842</button>
    </div>
  );
  if (!report) return <div className="honplus-state">HoN Plus рассчитывает показатели матча…</div>;
  if (!player || !profile) return <div className="honplus-state">В матче нет доступных контрольных точек.</div>;

  return (
    <div className="honplus-panel">
      <header className="honplus-header">
        <div><h2>HoN Plus</h2><span>Матч {report.matchId} · модель {report.modelVersion}</span></div>
        <div className={`honplus-reliability honplus-${profile.reliability.toLowerCase()}`}>
          {RELIABILITY[profile.reliability] ?? profile.reliability} · n={profile.sampleCount}
        </div>
      </header>

      <div className="honplus-player-list">
        {rankedPlayers.map((item, index) => (
          <button className={index === selectedPlayer ? "active" : ""} onClick={() => { setSelectedPlayer(index); setSelectedMinute(null); }}>
            <img src={HERO_ICON(item.heroId)} alt={item.heroName} />
            <span className="honplus-player-copy">
              <strong>{item.displayName}</strong>
              <span>{item.heroName} · {ROLE_NAMES[item.roleIndex] ?? `Роль ${item.roleIndex}`}</span>
            </span>
            <span className="honplus-player-rank">#{index + 1}<b>{item.impact < 0 ? "—" : Math.round(item.impact)}</b><small>ИМПАКТ</small></span>
          </button>
        ))}
      </div>

      <div className="honplus-minutes">
        {player.timeline.map((item) => (
          <button className={item.minute === profile.minute ? "active" : ""} onClick={() => setSelectedMinute(item.minute)}>{item.minute} мин</button>
        ))}
      </div>

      <div className="honplus-scores">{profile.axes.map((axis) => <ScoreCard axis={axis} />)}</div>
      <p className="honplus-note">100 — лучше почти всех сопоставимых игроков, 50 — середина выборки. Сравнение выполняется с тем же героем, числовой ролью и минутой матча; сам игрок исключён из эталона.</p>
    </div>
  );
}
