import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowDown,
  BarChart3,
  Brackets,
  Calendar,
  CheckCircle2,
  ChevronDown,
  Database,
  Download,
  Goal,
  Info,
  LineChart,
  Play,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Trophy,
  UsersRound,
} from "lucide-react";
import report from "./data/dashboard.json";
import forecastStadium from "./assets/forecast-stadium.png";
import simulationCallout from "./assets/simulation-callout.png";
import "./styles.css";

const STAGES = [
  { key: "round_of_32", label: "Round of 32", short: "R32", sub: "Advance" },
  { key: "quarterfinal", label: "Quarterfinal", short: "QF", sub: "Reach" },
  { key: "semifinal", label: "Semifinal", short: "SF", sub: "Reach" },
  { key: "final", label: "Final", short: "Final", sub: "Reach" },
  { key: "champion", label: "Champion", short: "Win", sub: "Win" },
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

const percent = (value, digits = value >= 0.1 ? 1 : 2) => `${(value * 100).toFixed(digits)}%`;

const getFlagUrl = (team, size = 40) => {
  const code = TEAM_FLAGS[team];
  return code ? `https://flagcdn.com/w${size}/${code}.png` : `https://flagcdn.com/w${size}/un.png`;
};

const getStageValue = (team, stageKey, mode = "absolute") => {
  const raw = report.stageProbabilities?.[stageKey]?.[team] ?? 0;
  if (mode === "absolute" || stageKey === "round_of_32") {
    return raw;
  }

  const stageIndex = STAGES.findIndex((stage) => stage.key === stageKey);
  const previousKey = STAGES[stageIndex - 1]?.key;
  const previous = report.stageProbabilities?.[previousKey]?.[team] ?? 0;
  return previous > 0 ? raw / previous : 0;
};

const buildTeamRows = () =>
  report.champions.map((team, index) => {
    const meta = report.teamMetadata?.[team.team] ?? {};

    return {
      rank: index + 1,
      team: team.team,
      group: meta.group ?? "-",
      fifaRank: meta.fifaRank ?? null,
      fifaPoints: meta.fifaPoints ?? null,
      groupAdvance: report.groupAdvancementProbabilities?.[team.team] ?? 0,
      champion: team.probability,
      round_of_32: getStageValue(team.team, "round_of_32"),
      quarterfinal: getStageValue(team.team, "quarterfinal"),
      semifinal: getStageValue(team.team, "semifinal"),
      final: getStageValue(team.team, "final"),
    };
  });

function useRevealOnScroll() {
  useEffect(() => {
    const elements = Array.from(document.querySelectorAll("[data-reveal]"));
    if (!elements.length) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -8% 0px" },
    );

    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);
}

function scrollToId(id) {
  const element = document.getElementById(id);
  if (element) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
      <Goal size={18} />
    </div>
  );
}

function Header() {
  return (
    <header className="topbar">
      <a className="brand" href="#top" aria-label="WCP Forecast Lab home">
        <BrandMark />
        <div>
          <div className="brand-name">WCP Forecast Lab</div>
          <div className="brand-caption">
            <span className="status-dot" />
            Open-data model
          </div>
        </div>
      </a>

      <nav className="nav-links" aria-label="Primary navigation">
        <a href="#dashboard">Dashboard</a>
        <a href="#atlas">Teams</a>
        <a href="#methodology">Methodology</a>
      </nav>

      <div className="topbar-actions">
        <button className="btn btn-secondary" type="button" onClick={() => scrollToId("backtest")}>
          <Calendar size={16} />
          Backtest
        </button>
        <button className="btn btn-primary" type="button" onClick={() => scrollToId("dashboard")}>
          <Play size={16} fill="currentColor" />
          Simulation
          <ChevronDown size={14} />
        </button>
      </div>
    </header>
  );
}

function HeroIntro() {
  const startDate = "Jun 11";
  const endDate = "Jul 19";

  return (
    <section className="hero-copy" data-reveal>
      <p className="hero-label">World Cup 2026</p>
      <h1>Predict. Simulate. Understand.</h1>
      <p className="hero-description">
        {report.simulation.runs.toLocaleString()} Monte Carlo simulations using dynamic Elo, calibrated match
        probabilities, and tournament-context features.
      </p>

      <div className="hero-stats" aria-label="Simulation summary">
        <div>
          <Trophy size={18} />
          <strong>{report.champions.length}</strong>
          <span>Teams</span>
        </div>
        <div>
          <Activity size={18} />
          <strong>{report.simulation.contextFeatures.fixture_count ?? 72}</strong>
          <span>Matches</span>
        </div>
        <div>
          <Calendar size={18} />
          <strong>
            {startDate} - {endDate}
          </strong>
          <span>Tournament window</span>
        </div>
      </div>
    </section>
  );
}

function PanelHeader({ icon: Icon, title, subtitle, id }) {
  return (
    <div className="panel-header">
      <div>
        <div className="panel-title-row">
          <Icon size={16} />
          <h2 id={id}>{title}</h2>
        </div>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      <button className="icon-button" type="button" title={`${title} details`} aria-label={`${title} details`}>
        <Info size={15} />
      </button>
    </div>
  );
}

function ProbabilityBar({ value, max = 1, tone = "green", label, compact = false }) {
  const width = Math.max(0, Math.min(100, max > 0 ? (value / max) * 100 : 0));

  return (
    <div className={`probability-bar ${compact ? "compact" : ""}`} aria-label={label ?? percent(value)}>
      <span className="probability-track" aria-hidden="true">
        <span className={`probability-fill ${tone}`} style={{ "--bar-width": `${width}%` }} />
      </span>
    </div>
  );
}

function TeamIdentity({ team, rank, showRank = false }) {
  return (
    <div className="team-identity">
      {showRank ? <span className="team-rank">{rank}</span> : null}
      <img src={getFlagUrl(team, 40)} alt="" className="flag-badge" loading="lazy" />
      <span>{team}</span>
    </div>
  );
}

function ChampionCard({ setHighlightedTeam }) {
  const leaders = report.champions.slice(0, 5);
  const top = leaders[0];
  const max = top?.probability ?? 1;

  return (
    <section className="panel champion-card hero-card" aria-labelledby="champion-title" data-reveal>
      <PanelHeader
        icon={Trophy}
        id="champion-title"
        title="Champion Probability"
        subtitle="% probability to win World Cup 2026"
      />

      <div className="champion-feature">
        <div>
          <TeamIdentity team={top.team} />
          <strong>{percent(top.probability)}</strong>
        </div>
        <div className="trophy-orbit" aria-hidden="true">
          <Trophy size={58} />
        </div>
      </div>

      <div className="leader-list">
        {leaders.slice(1).map((team, index) => (
          <button
            className="leader-row"
            key={team.team}
            type="button"
            onClick={() => setHighlightedTeam(team.team)}
            style={{ "--reveal-delay": `${index * 60}ms` }}
          >
            <TeamIdentity team={team.team} rank={index + 2} showRank />
            <span className="leader-prob">{percent(team.probability)}</span>
            <ProbabilityBar value={team.probability} max={max} compact />
          </button>
        ))}
      </div>

      <button className="wide-link" type="button" onClick={() => scrollToId("atlas")}>
        View all 48 teams
        <ArrowDown size={14} />
      </button>
    </section>
  );
}

function StagePath({ highlightedTeam, setHighlightedTeam }) {
  const [viewMode, setViewMode] = useState("absolute");
  const teams = report.champions.slice(0, 5);
  const highlighted = teams.some((team) => team.team === highlightedTeam) ? highlightedTeam : teams[0].team;

  return (
    <section className="panel path-card hero-card" id="dashboard" aria-labelledby="path-title" data-reveal>
      <PanelHeader
        icon={Brackets}
        id="path-title"
        title="Probability Path"
        subtitle={`${highlighted}'s chance to reach each stage`}
      />

      <div className="path-toolbar">
        <div className="segmented-control" aria-label="Path probability mode">
          <button
            type="button"
            className={viewMode === "absolute" ? "active" : ""}
            onClick={() => setViewMode("absolute")}
          >
            Probability
          </button>
          <button
            type="button"
            className={viewMode === "conditional" ? "active" : ""}
            onClick={() => setViewMode("conditional")}
          >
            Percent
          </button>
        </div>
        <label className="mini-select">
          <img src={getFlagUrl(highlighted, 40)} alt="" className="flag-badge" />
          <select value={highlighted} onChange={(event) => setHighlightedTeam(event.target.value)}>
            {teams.map((team) => (
              <option key={team.team} value={team.team}>
                {team.team}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="path-visual" aria-label={`${highlighted} probability path`}>
        <svg className="path-grid-lines" viewBox="0 0 100 48" preserveAspectRatio="none" aria-hidden="true">
          {[12, 31, 50, 69, 88].map((x) => (
            <line key={x} x1={x} y1="4" x2={x} y2="44" />
          ))}
          <polyline points="12,11 31,16 50,27 69,33 88,37" />
        </svg>

        <div className="path-stages">
          {STAGES.map((stage, index) => {
            const value = getStageValue(highlighted, stage.key, viewMode);
            return (
              <div className="path-stage" key={stage.key} style={{ "--stage-index": index }}>
                <span>{stage.short}</span>
                <strong>{percent(value)}</strong>
                <small>{stage.sub}</small>
              </div>
            );
          })}
        </div>

        <div className="path-champion">
          <img src={getFlagUrl(highlighted, 80)} alt="" />
          <span>{highlighted}</span>
          <strong>{percent(getStageValue(highlighted, "champion", viewMode))}</strong>
        </div>
      </div>
    </section>
  );
}

function CalibrationChart() {
  const improved = report.backtest.improved.calibration;
  const baseline = report.backtest.baseline.calibration;
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const xScale = (value) => 35 + value * 250;
  const yScale = (value) => 175 - value * 165;
  const buildPath = (bins) =>
    bins
      .map((bin, index) => `${index === 0 ? "M" : "L"} ${xScale(bin.mean_confidence)} ${yScale(bin.empirical_accuracy)}`)
      .join(" ");

  return (
    <div className="calibration-chart">
      <svg viewBox="0 0 300 200" role="img" aria-label="Reliability diagram">
        {[0, 0.25, 0.5, 0.75, 1].map((value) => (
          <React.Fragment key={value}>
            <line x1={35} x2={285} y1={yScale(value)} y2={yScale(value)} className="chart-grid" />
            <line x1={xScale(value)} x2={xScale(value)} y1={10} y2={175} className="chart-grid" />
            <text x={xScale(value)} y={190} textAnchor="middle" className="chart-label">
              {value.toFixed(value === 0 || value === 1 ? 0 : 2)}
            </text>
            <text x={28} y={yScale(value) + 3} textAnchor="end" className="chart-label">
              {value.toFixed(value === 0 || value === 1 ? 0 : 2)}
            </text>
          </React.Fragment>
        ))}
        <line x1={35} x2={285} y1={175} y2={10} className="chart-perfect" />
        <path d={buildPath(baseline)} className="chart-line baseline" />
        <path d={buildPath(improved)} className="chart-line improved" />
        {baseline.map((bin) => (
          <rect
            key={`baseline-${bin.mean_confidence}`}
            x={xScale(bin.mean_confidence) - 3}
            y={yScale(bin.empirical_accuracy) - 3}
            width="6"
            height="6"
            className="chart-dot baseline"
            onMouseEnter={() => setHoveredPoint({ model: "Baseline", ...bin })}
            onMouseLeave={() => setHoveredPoint(null)}
          />
        ))}
        {improved.map((bin) => (
          <circle
            key={`improved-${bin.mean_confidence}`}
            cx={xScale(bin.mean_confidence)}
            cy={yScale(bin.empirical_accuracy)}
            r="4"
            className="chart-dot improved"
            onMouseEnter={() => setHoveredPoint({ model: "Improved model", ...bin })}
            onMouseLeave={() => setHoveredPoint(null)}
          />
        ))}
      </svg>
      {hoveredPoint ? (
        <div className="chart-tooltip">
          <strong>{hoveredPoint.model}</strong>
          <span>Confidence {percent(hoveredPoint.mean_confidence)}</span>
          <span>Observed {percent(hoveredPoint.empirical_accuracy)}</span>
        </div>
      ) : null}
      <div className="chart-legend">
        <span>
          <i className="legend-dot improved" />
          Improved model
        </span>
        <span>
          <i className="legend-dot baseline" />
          Baseline
        </span>
        <span>
          <i className="legend-line" />
          Perfect calibration
        </span>
      </div>
    </div>
  );
}

function QualityPanel() {
  const improved = report.backtest.improved;
  const baseline = report.backtest.baseline;

  return (
    <section className="panel quality-card hero-card" id="backtest" aria-labelledby="quality-title" data-reveal>
      <PanelHeader
        icon={ShieldCheck}
        id="quality-title"
        title="Model Quality"
        subtitle={`Out-of-sample backtest since ${report.backtest.cutoff}`}
      />

      <table className="quality-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Improved Model</th>
            <th>Baseline</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Log Loss</td>
            <td>{improved.log_loss.toFixed(3)}</td>
            <td>{baseline.log_loss.toFixed(3)}</td>
          </tr>
          <tr>
            <td>Brier Score</td>
            <td>{improved.brier_score.toFixed(3)}</td>
            <td>{baseline.brier_score.toFixed(3)}</td>
          </tr>
          <tr>
            <td>Accuracy</td>
            <td>{percent(improved.accuracy)}</td>
            <td>{percent(baseline.accuracy)}</td>
          </tr>
        </tbody>
      </table>

      <div className="quality-callout">
        <CheckCircle2 size={15} />
        <span>Lower loss and Brier score than baseline</span>
      </div>

      <CalibrationChart />
    </section>
  );
}

function HeroDashboard() {
  const [highlightedTeam, setHighlightedTeam] = useState(report.champions[0]?.team ?? "Spain");

  return (
    <section className="hero-stage" id="top">
      <img className="hero-image" src={forecastStadium} alt="" aria-hidden="true" />
      <div className="hero-image-fade" aria-hidden="true" />
      <Header />

      <div className="hero-layout">
        <HeroIntro />
        <div className="hero-dashboard">
          <ChampionCard setHighlightedTeam={setHighlightedTeam} />
          <StagePath highlightedTeam={highlightedTeam} setHighlightedTeam={setHighlightedTeam} />
          <QualityPanel />
        </div>
      </div>
    </section>
  );
}

function AtlasStageCell({ team, stageKey, mode, max }) {
  const value = getStageValue(team, stageKey, mode);
  const tone = stageKey === "champion" ? "gold" : "green";

  return (
    <div className="atlas-stage-cell">
      <span>{percent(value)}</span>
      <ProbabilityBar value={value} max={max} tone={tone} compact />
    </div>
  );
}

function CountryAtlas() {
  const allRows = useMemo(buildTeamRows, []);
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("all");
  const [mode, setMode] = useState("absolute");
  const [sort, setSort] = useState({ key: "champion", direction: "desc" });

  const groups = useMemo(
    () => ["all", ...Array.from(new Set(allRows.map((row) => row.group).filter(Boolean))).sort()],
    [allRows],
  );

  const maxByStage = useMemo(() => {
    const result = {};
    STAGES.forEach((stage) => {
      result[stage.key] = Math.max(...allRows.map((row) => getStageValue(row.team, stage.key, mode)), 0.01);
    });
    return result;
  }, [allRows, mode]);

  const filteredRows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const rows = allRows.filter((row) => {
      const matchesQuery = !normalizedQuery || row.team.toLowerCase().includes(normalizedQuery);
      const matchesGroup = group === "all" || row.group === group;
      return matchesQuery && matchesGroup;
    });

    const multiplier = sort.direction === "asc" ? 1 : -1;
    return rows.sort((a, b) => {
      const aValue = sort.key in a ? a[sort.key] : getStageValue(a.team, sort.key, mode);
      const bValue = sort.key in b ? b[sort.key] : getStageValue(b.team, sort.key, mode);
      if (typeof aValue === "string" || typeof bValue === "string") {
        return String(aValue).localeCompare(String(bValue)) * multiplier;
      }
      return ((aValue ?? -1) - (bValue ?? -1)) * multiplier;
    });
  }, [allRows, group, mode, query, sort]);

  const toggleSort = (key) => {
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === "desc" ? "asc" : "desc",
    }));
  };

  const downloadCsv = () => {
    const header = ["Rank", "Team", "Group", "FIFA Rank", ...STAGES.map((stage) => stage.label)];
    const rows = filteredRows.map((row) => [
      row.rank,
      row.team,
      row.group,
      row.fifaRank ?? "",
      ...STAGES.map((stage) => percent(getStageValue(row.team, stage.key, mode))),
    ]);
    const csv = [header, ...rows].map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "wcp-country-probabilities.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="atlas-section" id="atlas">
      <div className="section-heading">
        <div className="section-icon">
          <UsersRound size={24} />
        </div>
        <div>
          <h2>All Countries Probability Atlas</h2>
          <p>Explore probabilities for all 48 teams across key tournament stages.</p>
        </div>
      </div>

      <div className="atlas-controls" aria-label="Atlas controls">
        <label className="search-control">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search team..." />
        </label>

        <label className="select-control">
          <span>Group</span>
          <select value={group} onChange={(event) => setGroup(event.target.value)}>
            {groups.map((item) => (
              <option key={item} value={item}>
                {item === "all" ? "All Groups" : `Group ${item}`}
              </option>
            ))}
          </select>
        </label>

        <div className="segmented-control atlas-mode" aria-label="Atlas probability mode">
          <button className={mode === "absolute" ? "active" : ""} type="button" onClick={() => setMode("absolute")}>
            Probability
          </button>
          <button className={mode === "conditional" ? "active" : ""} type="button" onClick={() => setMode("conditional")}>
            Percent
          </button>
        </div>

        <button className="btn btn-secondary download-button" type="button" onClick={downloadCsv}>
          <Download size={15} />
          Download CSV
        </button>
      </div>

      <div className="atlas-table-wrap">
        <table className="atlas-table">
          <thead>
            <tr>
              <th>
                <button type="button" onClick={() => toggleSort("rank")}>
                  #
                </button>
              </th>
              <th>
                <button type="button" onClick={() => toggleSort("team")}>
                  Team
                </button>
              </th>
              <th>
                <button type="button" onClick={() => toggleSort("group")}>
                  Group
                </button>
              </th>
              <th>
                <button type="button" onClick={() => toggleSort("fifaRank")}>
                  FIFA
                </button>
              </th>
              {STAGES.map((stage) => (
                <th key={stage.key}>
                  <button type="button" onClick={() => toggleSort(stage.key)}>
                    <span>{stage.label}</span>
                    <small>{stage.sub}</small>
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={row.team}>
                <td>{row.rank}</td>
                <td>
                  <TeamIdentity team={row.team} />
                </td>
                <td>Group {row.group}</td>
                <td>{row.fifaRank ? `#${row.fifaRank}` : "-"}</td>
                {STAGES.map((stage) => (
                  <td key={stage.key}>
                    <AtlasStageCell team={row.team} stageKey={stage.key} mode={mode} max={maxByStage[stage.key]} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="atlas-mobile-list">
        {filteredRows.map((row, index) => (
          <article className="atlas-card" key={row.team} data-reveal style={{ "--reveal-delay": `${Math.min(index, 10) * 45}ms` }}>
            <div className="atlas-card-header">
              <TeamIdentity team={row.team} rank={row.rank} showRank />
              <span>Group {row.group}</span>
            </div>
            <div className="atlas-card-grid">
              {STAGES.map((stage) => (
                <div key={stage.key}>
                  <small>{stage.short}</small>
                  <strong>{percent(getStageValue(row.team, stage.key, mode))}</strong>
                  <ProbabilityBar
                    value={getStageValue(row.team, stage.key, mode)}
                    max={maxByStage[stage.key]}
                    tone={stage.key === "champion" ? "gold" : "green"}
                    compact
                  />
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="atlas-footer">
        <span>
          Showing {filteredRows.length} of {allRows.length} teams
        </span>
        <span>{mode === "absolute" ? "Absolute tournament probability" : "Conditional stage-to-stage percent"}</span>
      </div>
    </section>
  );
}

function Methodology() {
  const items = [
    {
      icon: Database,
      title: "1. Data Sources",
      body: "Open international match data, FIFA ranking priors, venues, fixtures, travel, rest, and climate features.",
    },
    {
      icon: LineChart,
      title: "2. Dynamic Elo",
      body: "Time-decayed ratings with home advantage, margin adjustment, tournament importance, and lineup context.",
    },
    {
      icon: SlidersHorizontal,
      title: "3. Calibrated Probabilities",
      body: "Rolling holdout calibration produces well-behaved win, draw, loss, and stage probabilities.",
    },
    {
      icon: Sparkles,
      title: "4. Tournament Simulation",
      body: `${report.simulation.runs.toLocaleString()} Monte Carlo runs translate match probabilities into every stage path.`,
    },
  ];

  return (
    <section className="methodology-section" id="methodology" data-reveal>
      <div className="section-heading">
        <div className="section-icon">
          <BarChart3 size={24} />
        </div>
        <div>
          <h2>Methodology at a Glance</h2>
          <p>Transparent ingredients behind the forecast.</p>
        </div>
      </div>

      <div className="methodology-layout">
        <div className="method-grid">
          {items.map(({ icon: Icon, title, body }, index) => (
            <article className="method-card" key={title} data-reveal style={{ "--reveal-delay": `${index * 90}ms` }}>
              <div className="method-icon">
                <Icon size={24} />
              </div>
              <div>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
            </article>
          ))}
        </div>

        <div className="simulation-card" data-reveal>
          <img src={simulationCallout} alt="" />
          <button type="button" aria-label="Simulation overview">
            <Play size={22} fill="currentColor" />
          </button>
          <div>
            <span>Simulation layer</span>
            <strong>See how every path is sampled</strong>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div>
        <Info size={14} />
        <span>This model is for informational purposes only and not a guarantee of future results.</span>
      </div>
      <div>
        <span>Model: {report.model.rows.toLocaleString()} matches</span>
        <span>Seed {report.simulation.seed}</span>
        <span>&copy; 2026 WCP Forecast Lab</span>
      </div>
    </footer>
  );
}

function App() {
  useRevealOnScroll();

  return (
    <main>
      <HeroDashboard />
      <CountryAtlas />
      <Methodology />
      <Footer />
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
