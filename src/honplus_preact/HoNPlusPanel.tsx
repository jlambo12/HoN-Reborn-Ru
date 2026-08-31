import { useEffect, useMemo, useState } from "preact/hooks";
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
      <div className="honplus-score-name">{axis.name}</div>
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

  const player = report?.players[selectedPlayer] ?? null;
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
        {report.players.map((item, index) => (
          <button className={index === selectedPlayer ? "active" : ""} onClick={() => { setSelectedPlayer(index); setSelectedMinute(null); }}>
            <strong>{item.username}</strong><span>герой {item.heroId} · роль {item.roleIndex}</span>
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
