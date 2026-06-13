import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowDownUp,
  BarChart3,
  Brackets,
  CheckCircle2,
  Download,
  FlaskConical,
  Info,
  LineChart,
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

function scorerChipText(scorer) {
  const lastName = scorer.player.split(" ").at(-1) ?? scorer.player;
  return `${lastName} ${scorer.minute}'`;
}

function stageDateRange(stage, matches = []) {
  if (stage === "round_of_32") return "Jun 28 - Jul 3";
  if (stage === "round_of_16") return "Jul 4 - Jul 7";
  if (stage === "quarterfinal") return "Jul 9 - Jul 11";
  if (stage === "semifinal") return "Jul 14 - Jul 15";
  if (stage === "final") return "Jul 19";
  if (stage === "third_place") return "Jul 18";
  const dates = Array.from(new Set(matches.map((match) => match.date))).filter(Boolean);
  return dates.length ? dates.join(" / ") : "";
}

function useRevealMotion() {
  useEffect(() => {
    const nodes = Array.from(document.querySelectorAll(".motion-reveal"));
    if (!nodes.length) return undefined;
    if (!("IntersectionObserver" in window)) {
      nodes.forEach((node) => node.classList.add("is-visible"));
      return undefined;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("is-visible");
        });
      },
      { threshold: 0.16 },
    );
    nodes.forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, []);
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
  const dataLabel = `v${report.bracketChallenge?.asOfDate ?? "current"}`;
  const navItems = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "compare", label: "Compare", icon: ArrowDownUp },
    { id: "bracket", label: "Bracket", icon: Brackets },
    { id: "quality", label: "Backtest", icon: LineChart },
    { id: "teams", label: "Teams", icon: UsersRound },
  ];
  return (
    <header className="command">
      <button className="brand-button" type="button" onClick={() => scrollToId("overview")} aria-label="Scroll to overview">
        <span className="brand-glyph">
          <FlaskConical size={22} />
        </span>
        <span className="brand-copy">
          <strong>WCP Forecast Lab</strong>
        </span>
      </button>
      <nav aria-label="Workspace navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              className={item.id === "bracket" ? "active" : ""}
              type="button"
              key={item.id}
              onClick={() => scrollToId(item.id)}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>
      <div className="command-actions">
        <button type="button" className="data-button" onClick={() => openDrawer("bracket")}>
          <DatabaseIcon />
          Data: {dataLabel}
          <span aria-hidden="true">⌄</span>
        </button>
        <button type="button" className="command-icon" onClick={() => openDrawer("sources")} aria-label="Open sources">
          <Info size={20} />
        </button>
        <button type="button" className="command-icon" onClick={() => openDrawer("simulation")} aria-label="Open simulation settings">
          <SlidersHorizontal size={20} />
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

function SmallMatchCard({ match, connector = false, compact = false }) {
  const homeWon = match.winner === match.home;
  const awayWon = match.winner === match.away;
  const scorers = match.scorers ?? [];
  return (
    <article
      className={[
        "bracket-match",
        match.stage === "final" ? "final-card" : "",
        connector ? "with-connector" : "",
        compact ? "compact" : "",
      ].filter(Boolean).join(" ")}
    >
      <div className="match-meta">
        <span>M{match.matchNumber}</span>
        <span>{match.date}</span>
      </div>
      <div className={`score-team ${homeWon ? "winner" : ""}`}>
        <TeamName team={match.home} />
        <strong>{match.homeGoals}</strong>
        {homeWon ? <CheckCircle2 size={14} /> : null}
      </div>
      <div className={`score-team ${awayWon ? "winner" : ""}`}>
        <TeamName team={match.away} />
        <strong>{match.awayGoals}</strong>
        {awayWon ? <CheckCircle2 size={14} /> : null}
      </div>
      {scorers.length ? (
        <div className="scorer-chips">
          {scorers.slice(0, 3).map((scorer, index) => (
            <span key={`${match.matchNumber}-${scorer.player}-${index}`}>{scorerChipText(scorer)}</span>
          ))}
        </div>
      ) : null}
      {match.decidedBy !== "regulation" ? <small>{match.decidedBy.replaceAll("_", " ")}</small> : null}
    </article>
  );
}

function GroupPicks({ groups }) {
  return (
    <aside className="challenge-card group-rail motion-reveal">
      <div className="challenge-card-head">
        <h2>Group Picks</h2>
        <Info size={16} />
      </div>
      <div className="group-table-head">
        <span>Group</span>
        <span>Top 2</span>
        <span>3rd Place</span>
      </div>
      <div className="group-pick-list">
        {groups.map((group) => (
          <article key={group.group} className="group-pick">
            <strong className="group-letter">{group.group}</strong>
            <div className="top-two-box">
              {group.standings.slice(0, 2).map((row) => (
                <div key={row.team}>
                  <span>{row.position}</span>
                  <TeamName team={row.team} />
                </div>
              ))}
            </div>
            <div className={`third-place-pick ${group.standings[2]?.qualified ? "qualified" : ""}`}>
              <span>3</span>
              <TeamName team={group.standings[2]?.team} />
            </div>
          </article>
        ))}
      </div>
      <div className="group-legend">
        <span><i className="dot qualified" />Qualified (Top 2)</span>
        <span><i className="dot third" />Third Place</span>
      </div>
      <button className="edit-picks" type="button">
        <SlidersHorizontal size={15} />
        Edit Group Picks
      </button>
    </aside>
  );
}

function BestThirds({ bracket }) {
  return (
    <aside className="right-rail">
      <section className="challenge-card motion-reveal">
        <div className="challenge-card-head">
          <h2>Best Thirds</h2>
          <Info size={16} />
        </div>
        <div className="third-table">
          <div className="third-table-head">
            <span>Rank</span>
            <span>Team</span>
            <span>Score</span>
          </div>
          {(bracket.bestThirds ?? []).map((row) => (
            <article key={row.team}>
              <span>{row.thirdRank}</span>
              <TeamName team={row.team} />
              <strong>{Number(row.score ?? 0).toFixed(1)}</strong>
            </article>
          ))}
        </div>
        <button className="rail-link" type="button">
          View full table
          <span aria-hidden="true">›</span>
        </button>
      </section>
      <section className="challenge-card motion-reveal">
        <div className="challenge-card-head">
          <h2>Played Results</h2>
          <Info size={16} />
        </div>
        <div className="played-box">
          {(bracket.playedResults ?? []).map((match) => (
            <article className="played-result" key={match.matchNumber}>
              <div className="played-teams">
                <div>
                  <TeamName team={match.home} />
                  <strong>{match.homeGoals}</strong>
                </div>
                <div>
                  <TeamName team={match.away} />
                  <strong>{match.awayGoals}</strong>
                </div>
              </div>
              <div className="played-foot">
                <span>{match.date} · Group {match.group}</span>
                <strong>FT</strong>
              </div>
            </article>
          ))}
        </div>
        <button className="rail-link" type="button">
          View all results
          <span aria-hidden="true">›</span>
        </button>
      </section>
      <section className="champion-callout motion-reveal">
        <Trophy size={24} />
        <span>Champion</span>
        <TeamName team={bracket.champion} />
        <strong>{bracket.champion}</strong>
        <small>Final over {bracket.runnerUp}; third place {bracket.thirdPlace}</small>
      </section>
    </aside>
  );
}

function BracketColumn({ stage, matches, isLast }) {
  const displayMatches = stage === "final"
    ? [...(matches.final ?? []), ...(matches.third_place ?? [])]
    : matches[stage] ?? [];
  const heading = stage === "final" ? "Final" : stageLabel(stage);
  const dates = stage === "final"
    ? stageDateRange("final", displayMatches)
    : stageDateRange(stage, displayMatches);

  return (
    <div className={`knockout-column stage-${stage}`}>
      <div className="stage-heading">
        <strong>{heading}</strong>
        <span>{dates}</span>
      </div>
      <div className="stage-stack">
        {displayMatches.map((match) => (
          <SmallMatchCard key={match.matchNumber} match={match} connector={!isLast && stage !== "final"} />
        ))}
      </div>
    </div>
  );
}

function KnockoutBracket({ bracket }) {
  const stageOrder = ["round_of_32", "round_of_16", "quarterfinal", "semifinal", "final"];
  return (
    <section className="knockout-board">
      {stageOrder.map((stage, index) => (
        <BracketColumn
          key={stage}
          stage={stage}
          matches={bracket.knockoutBracket ?? {}}
          isLast={index === stageOrder.length - 1}
        />
      ))}
    </section>
  );
}

function BracketChallenge({ openDrawer }) {
  const bracket = report.bracketChallenge ?? {};
  const matches = bracket.matches ?? [];
  useRevealMotion();
  const downloadCsv = () => {
    const header = ["Match", "Stage", "Date", "Venue", "Home", "Away", "Score", "Winner", "Scorers", "Status", "Source Status"];
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
      match.status === "played" ? "verified result" : "model prediction",
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
    <section className="bracket-workspace" id="bracket">
      <div className="bracket-layout">
        <GroupPicks groups={bracket.groupPicks ?? []} />
        <section className="challenge-card bracket-center motion-reveal">
          <div className="bracket-toolbar">
            <label>
              <span>Mode</span>
              <select value="most_likely_path" aria-label="Bracket mode" readOnly>
                <option value="most_likely_path">Most likely path</option>
              </select>
            </label>
            <div className="bracket-actions">
              <button className="ghost-button" type="button" onClick={downloadCsv}>
                <Download size={15} />
                Download CSV
              </button>
              <button className="ghost-button" type="button" onClick={() => openDrawer("bracket")}>
                <Info size={15} />
                Sources
              </button>
            </div>
          </div>
          <div className="bracket-canvas">
            <KnockoutBracket bracket={bracket} />
            <div className="canvas-champion">
              <Trophy size={25} />
              <span>Champion</span>
            </div>
          </div>
          <footer className="bracket-footnote">
            <span><Info size={15} /> Bracket reflects the most likely path from the current model forecast.</span>
            <span>All times in local time</span>
          </footer>
        </section>
        <BestThirds bracket={bracket} />
      </div>
      <div className="bracket-data-note">
        <span>{bracket.dataVersion}</span>
        <span>Snapshot {bracket.snapshotTimestampUtc}</span>
        <span>{bracket.squadSource?.teamCount ?? 0} official squads</span>
      </div>
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
        `As-of date: ${report.bracketChallenge?.asOfDate ?? "not listed"}. Snapshot: ${report.bracketChallenge?.snapshotTimestampUtc ?? "not listed"}.`,
        `Squads: ${report.bracketChallenge?.squadSource?.teamCount ?? "n/a"} teams from ${report.bracketChallenge?.squadSource?.version ?? "unknown version"} published ${report.bracketChallenge?.squadSource?.publishedAtUtc ?? "unknown time"}.`,
        ...(report.bracketChallenge?.resultSources ?? []).map((source) => `M${source.matchNumber}: ${source.source} (${source.url})`),
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
        <BracketChallenge openDrawer={setDrawer} />
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
