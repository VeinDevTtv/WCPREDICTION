import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowDownUp,
  BarChart3,
  Brackets,
  CheckCircle2,
  Download,
  Info,
  LineChart,
  PanelRightOpen,
  RefreshCcw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Trophy,
  UsersRound,
  X,
} from "lucide-react";
import report from "./data/dashboard.json";
import "./styles.css";

const STAGES = [
  { key: "round_of_32", label: "Round of 32", short: "R32" },
  { key: "quarterfinal", label: "Quarterfinal", short: "QF" },
  { key: "semifinal", label: "Semifinal", short: "SF" },
  { key: "final", label: "Final", short: "Final" },
  { key: "champion", label: "Champion", short: "Win" },
];

const TEAM_FLAGS = {
  Algeria: "dz",
  Argentina: "ar",
  Australia: "au",
  Austria: "at",
  Belgium: "be",
  "Bosnia and Herzegovina": "ba",
  Brazil: "br",
  Canada: "ca",
  "Cape Verde": "cv",
  Colombia: "co",
  Croatia: "hr",
  Curacao: "cw",
  "Czech Republic": "cz",
  "DR Congo": "cd",
  Ecuador: "ec",
  Egypt: "eg",
  England: "gb-eng",
  France: "fr",
  Germany: "de",
  Ghana: "gh",
  Haiti: "ht",
  Iran: "ir",
  Iraq: "iq",
  "Ivory Coast": "ci",
  Japan: "jp",
  Jordan: "jo",
  Mexico: "mx",
  Morocco: "ma",
  Netherlands: "nl",
  "New Zealand": "nz",
  Norway: "no",
  Panama: "pa",
  Paraguay: "py",
  Portugal: "pt",
  Qatar: "qa",
  "Saudi Arabia": "sa",
  Scotland: "gb-sct",
  Senegal: "sn",
  "South Africa": "za",
  "South Korea": "kr",
  Spain: "es",
  Sweden: "se",
  Switzerland: "ch",
  Tunisia: "tn",
  Turkey: "tr",
  "United States": "us",
  Uruguay: "uy",
  Uzbekistan: "uz",
};

const percent = (value, digits = value >= 0.1 ? 1 : 2) => `${((value ?? 0) * 100).toFixed(digits)}%`;
const signed = (value, digits = 1) => `${value > 0 ? "+" : ""}${Number(value ?? 0).toFixed(digits)}`;
const flagUrl = (team, size = 40) => `https://flagcdn.com/w${size}/${TEAM_FLAGS[team] ?? "un"}.png`;

function getStageValue(team, stageKey, mode = "absolute") {
  const raw = report.stageProbabilities?.[stageKey]?.[team] ?? 0;
  if (mode === "absolute" || stageKey === "round_of_32") return raw;
  const index = STAGES.findIndex((stage) => stage.key === stageKey);
  const previous = report.stageProbabilities?.[STAGES[index - 1]?.key]?.[team] ?? 0;
  return previous > 0 ? raw / previous : 0;
}

function buildRows() {
  return report.champions.map((champion, index) => {
    const meta = report.teamMetadata?.[champion.team] ?? {};
    const context = report.teamContext?.[champion.team] ?? {};
    return {
      rank: index + 1,
      team: champion.team,
      group: meta.group ?? "-",
      fifaRank: context.fifaRank ?? meta.fifaRank ?? null,
      fifaPoints: context.fifaPoints ?? meta.fifaPoints ?? null,
      champion: champion.probability,
      round_of_32: getStageValue(champion.team, "round_of_32"),
      quarterfinal: getStageValue(champion.team, "quarterfinal"),
      semifinal: getStageValue(champion.team, "semifinal"),
      final: getStageValue(champion.team, "final"),
      ...context,
    };
  });
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function stageLabel(stage) {
  return {
    group: "Group Stage",
    round_of_32: "Round of 32",
    round_of_16: "Round of 16",
    quarterfinal: "Quarterfinal",
    semifinal: "Semifinal",
    third_place: "Third Place",
    final: "Final",
  }[stage] ?? stage;
}

function scoreText(match) {
  return `${match.homeGoals}-${match.awayGoals}`;
}

function scorerText(match) {
  return (match.scorers ?? []).map((scorer) => `${scorer.minute}' ${scorer.player}`).join(", ");
}

function TeamName({ team, rank }) {
  return (
    <span className="team-name">
      {rank ? <span className="rank-pill">{rank}</span> : null}
      <img src={flagUrl(team)} alt="" loading="lazy" />
      <span>{team}</span>
    </span>
  );
}

function Bar({ value, max = 1, tone = "green" }) {
  const width = Math.max(0, Math.min(100, max > 0 ? (value / max) * 100 : 0));
  return (
    <span className="bar-track" aria-hidden="true">
      <span className={`bar-fill ${tone}`} style={{ "--w": `${width}%` }} />
    </span>
  );
}

function TopCommand({ openDrawer }) {
  return (
    <header className="command">
      <button className="brand-button" type="button" onClick={() => scrollToId("overview")} aria-label="Scroll to overview">
        <span className="brand-glyph">
          <Trophy size={18} />
        </span>
        <span>
          <strong>WCP Forecast Lab</strong>
          <small>2026 analyst workspace</small>
        </span>
      </button>
      <nav aria-label="Workspace navigation">
        <button type="button" onClick={() => scrollToId("compare")}>Compare</button>
        <button type="button" onClick={() => scrollToId("bracket")}>Bracket</button>
        <button type="button" onClick={() => scrollToId("quality")}>Backtest</button>
        <button type="button" onClick={() => scrollToId("teams")}>Teams</button>
      </nav>
      <div className="command-actions">
        <button type="button" className="ghost-button" onClick={() => openDrawer("sources")}>
          <Info size={16} />
          Sources
        </button>
        <button type="button" className="primary-button" onClick={() => openDrawer("simulation")}>
          <PanelRightOpen size={16} />
          Simulation
        </button>
      </div>
    </header>
  );
}

function SourceStrip({ openDrawer }) {
  const deltas = report.backtest.deltas ?? {};
  return (
    <section className="source-strip" id="overview">
      <button type="button" onClick={() => openDrawer("model")}>
        <DatabaseIcon />
        <span>
          <strong>{report.model.rows.toLocaleString()} matches</strong>
          <small>{report.model.firstMatch} to {report.model.lastMatch}</small>
        </span>
      </button>
      <button type="button" onClick={() => openDrawer("sources")}>
        <CheckCircle2 size={18} />
        <span>
          <strong>FIFA ranking {report.sources?.fifaRankingOfficialDate ?? "current"}</strong>
          <small>Rechecked {report.sources?.fifaRankingPulledAt ?? "n/a"}</small>
        </span>
      </button>
      <button type="button" onClick={() => openDrawer("quality")}>
        <ShieldCheck size={18} />
        <span>
          <strong>{signed(deltas.logLoss, 3)} log-loss delta</strong>
          <small>Positive means lower than baseline</small>
        </span>
      </button>
      <button type="button" onClick={() => openDrawer("simulation")}>
        <Activity size={18} />
        <span>
          <strong>{report.simulation.runs.toLocaleString()} runs</strong>
          <small>Seed {report.simulation.seed}</small>
        </span>
      </button>
    </section>
  );
}

function DatabaseIcon() {
  return <BarChart3 size={18} />;
}

function Leaders({ rows, selectTeam }) {
  const max = rows[0]?.champion ?? 1;
  return (
    <section className="panel leaders">
      <div className="panel-heading">
        <div>
          <h2>Champion Board</h2>
          <p>Current title probabilities after public-data context adjustments.</p>
        </div>
        <Trophy size={20} />
      </div>
      <div className="leader-list">
        {rows.slice(0, 8).map((row) => (
          <button type="button" key={row.team} onClick={() => selectTeam(row.team)}>
            <TeamName team={row.team} rank={row.rank} />
            <strong>{percent(row.champion)}</strong>
            <Bar value={row.champion} max={max} tone={row.rank === 1 ? "gold" : "green"} />
          </button>
        ))}
      </div>
    </section>
  );
}

function ComparePanel({ rows, teamA, teamB, setTeamA, setTeamB, mode, setMode, openDrawer }) {
  const a = rows.find((row) => row.team === teamA) ?? rows[0];
  const b = rows.find((row) => row.team === teamB) ?? rows[1];
  const maxStage = Math.max(...STAGES.flatMap((stage) => [getStageValue(a.team, stage.key, mode), getStageValue(b.team, stage.key, mode)]), 0.01);

  return (
    <section className="panel compare-panel" id="compare">
      <div className="panel-heading">
        <div>
          <h2>Team Comparison</h2>
          <p>Compare stage path, public priors, form, and penalty signal.</p>
        </div>
        <button className="icon-action" type="button" onClick={() => openDrawer("model")} aria-label="Open model details">
          <Info size={16} />
        </button>
      </div>
      <div className="compare-controls">
        <label>
          <span>Team A</span>
          <select value={a.team} onChange={(event) => setTeamA(event.target.value)}>
            {rows.map((row) => <option key={row.team} value={row.team}>{row.team}</option>)}
          </select>
        </label>
        <label>
          <span>Team B</span>
          <select value={b.team} onChange={(event) => setTeamB(event.target.value)}>
            {rows.map((row) => <option key={row.team} value={row.team}>{row.team}</option>)}
          </select>
        </label>
        <div className="segmented" aria-label="Probability mode">
          <button type="button" className={mode === "absolute" ? "active" : ""} onClick={() => setMode("absolute")}>Absolute</button>
          <button type="button" className={mode === "conditional" ? "active" : ""} onClick={() => setMode("conditional")}>Conditional</button>
        </div>
        <button className="ghost-button" type="button" onClick={() => { setTeamA(rows[0].team); setTeamB(rows[1].team); }}>
          <RefreshCcw size={15} />
          Clear
        </button>
      </div>
      <div className="compare-grid">
        {[a, b].map((row) => (
          <article className="team-compare" key={row.team}>
            <div className="compare-title">
              <TeamName team={row.team} />
              <strong>{percent(row.champion)}</strong>
            </div>
            <div className="stage-stack">
              {STAGES.map((stage) => {
                const value = getStageValue(row.team, stage.key, mode);
                return (
                  <div key={stage.key} className="stage-row">
                    <span>{stage.short}</span>
                    <Bar value={value} max={maxStage} tone={stage.key === "champion" ? "gold" : "green"} />
                    <strong>{percent(value)}</strong>
                  </div>
                );
              })}
            </div>
            <dl className="context-grid">
              <div><dt>FIFA</dt><dd>{row.fifaRank ? `#${row.fifaRank}` : "-"}</dd></div>
              <div><dt>Elo</dt><dd>{Math.round(row.eloRating ?? 0)}</dd></div>
              <div><dt>Form</dt><dd>{signed(row.recentFormDelta)}</dd></div>
              <div><dt>Penalties</dt><dd>{percent(row.penaltyStrength ?? 0.5)}</dd></div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

function QualityPanel({ openDrawer }) {
  const improved = report.backtest.improved;
  const baseline = report.backtest.baseline;
  const windows = report.backtest.rollingWindows ?? [];
  const maxLoss = Math.max(...windows.map((row) => row.metrics.log_loss), improved.log_loss, 0.01);

  return (
    <section className="panel quality-panel" id="quality">
      <div className="panel-heading">
        <div>
          <h2>Backtest Quality</h2>
          <p>Optimized for log loss and Brier score; accuracy remains secondary.</p>
        </div>
        <button className="icon-action" type="button" onClick={() => openDrawer("quality")} aria-label="Open quality details">
          <Info size={16} />
        </button>
      </div>
      <div className="metric-grid">
        <div><span>Log loss</span><strong>{improved.log_loss.toFixed(3)}</strong><small>Baseline {baseline.log_loss.toFixed(3)}</small></div>
        <div><span>Brier</span><strong>{improved.brier_score.toFixed(3)}</strong><small>Baseline {baseline.brier_score.toFixed(3)}</small></div>
        <div><span>Accuracy</span><strong>{percent(improved.accuracy)}</strong><small>Baseline {percent(baseline.accuracy)}</small></div>
      </div>
      <div className="rolling-list">
        {windows.map((window) => (
          <div className="rolling-row" key={window.cutoff}>
            <span>{window.cutoff}</span>
            <Bar value={window.metrics.log_loss} max={maxLoss} tone="blue" />
            <strong>{window.metrics.log_loss.toFixed(3)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function SmallMatchCard({ match }) {
  const homeWon = match.winner === match.home;
  const awayWon = match.winner === match.away;
  return (
    <article className={`bracket-match ${match.stage === "final" ? "final-card" : ""}`}>
      <div className="match-meta">
        <span>M{match.matchNumber}</span>
        <span>{match.date}</span>
      </div>
      <div className={`score-team ${homeWon ? "winner" : ""}`}>
        <TeamName team={match.home} />
        <strong>{match.homeGoals}</strong>
      </div>
      <div className={`score-team ${awayWon ? "winner" : ""}`}>
        <TeamName team={match.away} />
        <strong>{match.awayGoals}</strong>
      </div>
      <p>{scorerText(match) || "No scorers"}</p>
      {match.decidedBy !== "regulation" ? <small>{match.decidedBy.replaceAll("_", " ")}</small> : null}
    </article>
  );
}

function GroupPicks({ groups }) {
  return (
    <aside className="bracket-rail">
      <div className="rail-heading">
        <strong>Group Picks</strong>
        <span>{groups.length} groups</span>
      </div>
      <div className="group-pick-list">
        {groups.map((group) => (
          <article key={group.group} className="group-pick">
            <div>
              <strong>Group {group.group}</strong>
              <span>{group.winner} / {group.runnerUp}</span>
            </div>
            <ol>
              {group.standings.map((row) => (
                <li key={row.team} className={row.qualified ? "qualified" : ""}>
                  <span>{row.position}</span>
                  <TeamName team={row.team} />
                  <strong>{row.points} pts</strong>
                </li>
              ))}
            </ol>
          </article>
        ))}
      </div>
    </aside>
  );
}

function BestThirds({ bracket }) {
  return (
    <aside className="bracket-rail right">
      <div className="rail-heading">
        <strong>Best Thirds</strong>
        <span>Top 8 advance</span>
      </div>
      <div className="third-list">
        {(bracket.bestThirds ?? []).map((row) => (
          <article key={row.team}>
            <span>{row.thirdRank}</span>
            <TeamName team={row.team} />
            <strong>{row.points} pts</strong>
          </article>
        ))}
      </div>
      <div className="played-box">
        <div className="rail-heading compact">
          <strong>Played Results</strong>
          <span>{bracket.asOfDate}</span>
        </div>
        {(bracket.playedResults ?? []).map((match) => (
          <SmallMatchCard key={match.matchNumber} match={match} />
        ))}
      </div>
      <div className="champion-box">
        <span>Predicted Champion</span>
        <TeamName team={bracket.champion} />
        <strong>{bracket.champion}</strong>
        <small>Final: {bracket.champion} over {bracket.runnerUp}; third place {bracket.thirdPlace}</small>
      </div>
    </aside>
  );
}

function KnockoutBracket({ bracket }) {
  const stageOrder = ["round_of_32", "round_of_16", "quarterfinal", "semifinal", "third_place", "final"];
  return (
    <section className="knockout-board">
      {stageOrder.map((stage) => {
        const matches = bracket.knockoutBracket?.[stage] ?? [];
        if (!matches.length) return null;
        return (
          <div className="knockout-column" key={stage}>
            <div className="stage-heading">
              <strong>{stageLabel(stage)}</strong>
              <span>{matches.length}</span>
            </div>
            {matches.map((match) => <SmallMatchCard key={match.matchNumber} match={match} />)}
          </div>
        );
      })}
    </section>
  );
}

function AllMatchScores({ matches }) {
  return (
    <div className="all-match-scores">
      <div className="rail-heading">
        <strong>All Match Scores</strong>
        <span>{matches.length} matches</span>
      </div>
      <div className="score-grid">
        {matches.map((match) => (
          <article key={match.matchNumber} className={match.status === "played" ? "played" : ""}>
            <div className="match-meta">
              <span>M{match.matchNumber}</span>
              <span>{match.group ? `Group ${match.group}` : stageLabel(match.stage)}</span>
            </div>
            <strong>{match.home} {scoreText(match)} {match.away}</strong>
            <p>{scorerText(match) || "No scorers"}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

function BracketChallenge({ openDrawer }) {
  const bracket = report.bracketChallenge ?? {};
  const matches = bracket.matches ?? [];
  const downloadCsv = () => {
    const header = ["Match", "Stage", "Date", "Venue", "Home", "Away", "Score", "Winner", "Scorers", "Status"];
    const body = matches.map((match) => [
      match.matchNumber,
      stageLabel(match.stage),
      match.date,
      match.venue,
      match.home,
      match.away,
      scoreText(match),
      match.winner ?? "",
      scorerText(match),
      match.status,
    ]);
    const csv = [header, ...body].map((line) => line.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "wcp-bracket-challenge.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (!matches.length) return null;

  return (
    <section className="panel bracket-panel" id="bracket">
      <div className="panel-heading bracket-title">
        <div>
          <h2>Bracket Challenge</h2>
          <p>Most-likely model path as of {bracket.asOfDate}, with played results locked and future scorers assigned from the scorer pool.</p>
        </div>
        <div className="bracket-actions">
          <button className="ghost-button" type="button" onClick={() => openDrawer("bracket")}>
            <Info size={15} />
            Sources
          </button>
          <button className="primary-button" type="button" onClick={downloadCsv}>
            <Download size={15} />
            CSV
          </button>
        </div>
      </div>
      <div className="bracket-layout">
        <GroupPicks groups={bracket.groupPicks ?? []} />
        <div className="bracket-center">
          <div className="bracket-summary">
            <div>
              <Brackets size={18} />
              <span>Mode</span>
              <strong>{bracket.mode?.replaceAll("_", " ")}</strong>
            </div>
            <div>
              <Trophy size={18} />
              <span>Champion</span>
              <strong>{bracket.champion}</strong>
            </div>
            <div>
              <Activity size={18} />
              <span>Matches</span>
              <strong>{matches.length}</strong>
            </div>
          </div>
          <KnockoutBracket bracket={bracket} />
        </div>
        <BestThirds bracket={bracket} />
      </div>
      <AllMatchScores matches={matches} />
    </section>
  );
}

function TeamTable({ rows, mode, setMode, teamA, setTeamA, teamB, setTeamB }) {
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("all");
  const [sort, setSort] = useState({ key: "champion", direction: "desc" });
  const groups = useMemo(() => ["all", ...Array.from(new Set(rows.map((row) => row.group))).sort()], [rows]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const multiplier = sort.direction === "asc" ? 1 : -1;
    return rows
      .filter((row) => (!normalized || row.team.toLowerCase().includes(normalized)) && (group === "all" || row.group === group))
      .sort((a, b) => {
        const av = sort.key in a ? a[sort.key] : getStageValue(a.team, sort.key, mode);
        const bv = sort.key in b ? b[sort.key] : getStageValue(b.team, sort.key, mode);
        if (typeof av === "string" || typeof bv === "string") return String(av).localeCompare(String(bv)) * multiplier;
        return ((av ?? -1) - (bv ?? -1)) * multiplier;
      });
  }, [group, mode, query, rows, sort]);

  const maxByStage = useMemo(() => Object.fromEntries(STAGES.map((stage) => [
    stage.key,
    Math.max(...rows.map((row) => getStageValue(row.team, stage.key, mode)), 0.01),
  ])), [rows, mode]);

  const toggleSort = (key) => setSort((current) => ({
    key,
    direction: current.key === key && current.direction === "desc" ? "asc" : "desc",
  }));

  const reset = () => {
    setQuery("");
    setGroup("all");
    setSort({ key: "champion", direction: "desc" });
  };

  const downloadCsv = () => {
    const header = ["Rank", "Team", "Group", "FIFA Rank", "Elo", "Recent Form", ...STAGES.map((stage) => stage.label)];
    const body = filtered.map((row) => [
      row.rank,
      row.team,
      row.group,
      row.fifaRank ?? "",
      row.eloRating ?? "",
      row.recentFormDelta ?? "",
      ...STAGES.map((stage) => percent(getStageValue(row.team, stage.key, mode))),
    ]);
    const csv = [header, ...body].map((line) => line.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "wcp-forecast-table.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="panel table-panel" id="teams">
      <div className="panel-heading">
        <div>
          <h2>All Teams</h2>
          <p>Sortable stage probabilities with model context and comparison actions.</p>
        </div>
        <span className="row-count">{filtered.length} / {rows.length}</span>
      </div>
      <div className="table-tools">
        <label className="search-box">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search team" />
        </label>
        <label className="select-box">
          <span>Group</span>
          <select value={group} onChange={(event) => setGroup(event.target.value)}>
            {groups.map((item) => <option key={item} value={item}>{item === "all" ? "All groups" : `Group ${item}`}</option>)}
          </select>
        </label>
        <div className="segmented" aria-label="Table probability mode">
          <button type="button" className={mode === "absolute" ? "active" : ""} onClick={() => setMode("absolute")}>Absolute</button>
          <button type="button" className={mode === "conditional" ? "active" : ""} onClick={() => setMode("conditional")}>Conditional</button>
        </div>
        <button type="button" className="ghost-button" onClick={reset}><RefreshCcw size={15} />Reset</button>
        <button type="button" className="primary-button" onClick={downloadCsv}><Download size={15} />CSV</button>
      </div>
      {filtered.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {["rank", "team", "group", "fifaRank"].map((key) => (
                  <th key={key}><button type="button" onClick={() => toggleSort(key)}>{key === "fifaRank" ? "FIFA" : key}<ArrowDownUp size={12} /></button></th>
                ))}
                {STAGES.map((stage) => (
                  <th key={stage.key}><button type="button" onClick={() => toggleSort(stage.key)}>{stage.short}<ArrowDownUp size={12} /></button></th>
                ))}
                <th>Context</th>
                <th>Compare</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.team} className={row.team === teamA || row.team === teamB ? "selected-row" : ""}>
                  <td>{row.rank}</td>
                  <td><TeamName team={row.team} /></td>
                  <td>Group {row.group}</td>
                  <td>{row.fifaRank ? `#${row.fifaRank}` : "-"}</td>
                  {STAGES.map((stage) => {
                    const value = getStageValue(row.team, stage.key, mode);
                    return (
                      <td key={stage.key}>
                        <span className="prob-cell">
                          <strong>{percent(value)}</strong>
                          <Bar value={value} max={maxByStage[stage.key]} tone={stage.key === "champion" ? "gold" : "green"} />
                        </span>
                      </td>
                    );
                  })}
                  <td>
                    <span className="context-line">Elo {Math.round(row.eloRating ?? 0)} · Form {signed(row.recentFormDelta)}</span>
                  </td>
                  <td>
                    <span className="compare-actions">
                      <button type="button" onClick={() => setTeamA(row.team)}>A</button>
                      <button type="button" onClick={() => setTeamB(row.team)}>B</button>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <UsersRound size={28} />
          <strong>No teams match those filters.</strong>
          <button type="button" className="ghost-button" onClick={reset}>Reset filters</button>
        </div>
      )}
    </section>
  );
}

function Drawer({ drawer, close }) {
  if (!drawer) return null;
  const content = {
    sources: {
      title: "Public Sources",
      icon: Info,
      body: [
        `FIFA ranking source: ${report.sources?.fifaRankingSource ?? "not listed"}.`,
        `Ranking official date: ${report.sources?.fifaRankingOfficialDate ?? "not listed"}; pulled/rechecked ${report.sources?.fifaRankingPulledAt ?? "not listed"}.`,
        ...(report.sources?.sourceNotes ?? []),
      ],
    },
    model: {
      title: "Model Details",
      icon: SlidersHorizontal,
      body: [
        `${report.model.featureColumns.length} feature columns: Elo, rolling form, scoring profile, rest, host/neutral context, and attack/defense strength.`,
        `Selected full-model blend weight ${report.model.blendWeight}; regularization C ${report.model.cValue}.`,
        "Rolling features are generated before each match is updated to avoid future-data leakage.",
      ],
    },
    quality: {
      title: "Backtest Details",
      icon: LineChart,
      body: [
        `Cutoff backtest from ${report.backtest.cutoff}: ${report.backtest.testMatches.toLocaleString()} held-out matches.`,
        `Log loss improved by ${signed(report.backtest.deltas.logLoss, 3)} and Brier score improved by ${signed(report.backtest.deltas.brierScore, 3)} versus baseline.`,
        `Accuracy delta is ${signed(report.backtest.deltas.accuracy, 3)}; the model prioritizes calibrated probabilities over raw hit rate.`,
      ],
    },
    simulation: {
      title: "Simulation Details",
      icon: Activity,
      body: [
        `${report.simulation.runs.toLocaleString()} Monte Carlo runs with seed ${report.simulation.seed}.`,
        `Context features: ${Object.entries(report.simulation.contextFeatures ?? {}).filter(([, value]) => Boolean(value)).map(([key]) => key).join(", ")}.`,
        ...(report.simulation.tiebreakNotes ?? []),
      ],
    },
    bracket: {
      title: "Bracket Challenge",
      icon: Brackets,
      body: [
        `As-of date: ${report.bracketChallenge?.asOfDate ?? "not listed"}. Mode: ${report.bracketChallenge?.mode?.replaceAll("_", " ") ?? "not listed"}.`,
        ...(report.bracketChallenge?.sourceNotes ?? []),
        ...(report.bracketChallenge?.scorerModelNotes ?? []),
      ],
    },
  }[drawer];
  const Icon = content.icon;
  return (
    <div className="drawer-backdrop" role="presentation" onClick={close}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title" onClick={(event) => event.stopPropagation()}>
        <div className="drawer-head">
          <span><Icon size={18} /><strong id="drawer-title">{content.title}</strong></span>
          <button type="button" onClick={close} aria-label="Close drawer"><X size={18} /></button>
        </div>
        <div className="drawer-body">
          {content.body.map((item) => <p key={item}>{item}</p>)}
        </div>
      </aside>
    </div>
  );
}

function App() {
  const rows = useMemo(buildRows, []);
  const [drawer, setDrawer] = useState(null);
  const [teamA, setTeamA] = useState(rows[0]?.team ?? "Spain");
  const [teamB, setTeamB] = useState(rows[1]?.team ?? "Argentina");
  const [mode, setMode] = useState("absolute");

  return (
    <main>
      <TopCommand openDrawer={setDrawer} />
      <div className="workspace">
        <SourceStrip openDrawer={setDrawer} />
        <div className="workspace-grid">
          <Leaders rows={rows} selectTeam={setTeamA} />
          <ComparePanel
            rows={rows}
            teamA={teamA}
            teamB={teamB}
            setTeamA={setTeamA}
            setTeamB={setTeamB}
            mode={mode}
            setMode={setMode}
            openDrawer={setDrawer}
          />
          <QualityPanel openDrawer={setDrawer} />
        </div>
        <BracketChallenge openDrawer={setDrawer} />
        <TeamTable
          rows={rows}
          mode={mode}
          setMode={setMode}
          teamA={teamA}
          teamB={teamB}
          setTeamA={setTeamA}
          setTeamB={setTeamB}
        />
      </div>
      <footer>
        <span>Informational model output, not a guarantee of match results.</span>
        <span>World Cup {report.simulation.year} · Seed {report.simulation.seed}</span>
      </footer>
      <Drawer drawer={drawer} close={() => setDrawer(null)} />
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
