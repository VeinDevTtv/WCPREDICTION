import React from "react";
import { createRoot } from "react-dom/client";
import { Activity, BarChart3, Brackets, Database, Github, ShieldCheck, Trophy } from "lucide-react";
import report from "./data/dashboard.json";
import "./styles.css";

const percent = (value) => `${(value * 100).toFixed(value >= 0.1 ? 1 : 2)}%`;
const context = report.simulation.contextFeatures ?? {};

function MetricTile({ label, improved, baseline, lowerIsBetter = true }) {
  const delta = lowerIsBetter ? baseline - improved : improved - baseline;
  return (
    <div className="metric-tile">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{improved.toFixed(3)}</div>
      <div className={delta >= 0 ? "metric-delta positive" : "metric-delta"}>
        baseline {baseline.toFixed(3)} · {delta >= 0 ? "better" : "behind"} by {Math.abs(delta).toFixed(3)}
      </div>
    </div>
  );
}

function ChampionBoard() {
  const teams = report.champions;
  const max = teams[0]?.probability ?? 1;
  return (
    <section className="panel leaderboard" aria-labelledby="champion-title">
      <div className="section-heading">
        <Trophy size={18} />
        <div>
          <h2 id="champion-title">All Country Champion Probabilities</h2>
          <p>{teams.length} teams · {report.simulation.runs.toLocaleString()} deterministic-seed simulations</p>
        </div>
      </div>
      <div className="leader-list">
        {teams.map((team, index) => (
          <div className="leader-row" key={team.team}>
            <div className="rank">{String(index + 1).padStart(2, "0")}</div>
            <div className="team-name">{team.team}</div>
            <div className="bar-track" aria-hidden="true">
              <div className="bar-fill" style={{ width: `${(team.probability / max) * 100}%` }} />
            </div>
            <div className="probability">{percent(team.probability)}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function StagePath() {
  const teams = report.champions.slice(0, 6);
  const stages = [
    ["R32", "round_of_32"],
    ["QF", "quarterfinal"],
    ["SF", "semifinal"],
    ["Final", "final"],
    ["Win", "champion"],
  ];
  return (
    <section className="panel path-panel" aria-labelledby="path-title">
      <div className="section-heading">
        <Brackets size={18} />
        <div>
          <h2 id="path-title">Probability Path</h2>
          <p>How top teams survive each tournament phase</p>
        </div>
      </div>
      <div className="stage-grid">
        <div className="stage-label team-label">Team</div>
        {stages.map(([label]) => (
          <div className="stage-label" key={label}>{label}</div>
        ))}
        {teams.map((team) => (
          <React.Fragment key={team.team}>
            <div className="stage-team">{team.team}</div>
            {stages.map(([label, key]) => {
              const value = report.stageProbabilities[key][team.team] ?? 0;
              return (
                <div className="stage-cell" key={`${team.team}-${label}`}>
                  <span style={{ height: `${Math.max(value * 100, 4)}%` }} />
                  <b>{percent(value)}</b>
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </section>
  );
}

function CalibrationChart() {
  const bins = report.backtest.improved.calibration;
  return (
    <div className="calibration">
      {bins.map((bin) => (
        <div className="cal-bin" key={bin.low}>
          <div className="cal-bars">
            <span className="confidence" style={{ height: `${bin.mean_confidence * 100}%` }} />
            <span className="empirical" style={{ height: `${bin.empirical_accuracy * 100}%` }} />
          </div>
          <small>{Math.round(bin.low * 100)}-{Math.round(bin.high * 100)}</small>
        </div>
      ))}
    </div>
  );
}

function QualityPanel() {
  return (
    <section className="panel quality-panel" aria-labelledby="quality-title">
      <div className="section-heading">
        <ShieldCheck size={18} />
        <div>
          <h2 id="quality-title">Model Quality</h2>
          <p>Chronological holdout since {report.backtest.cutoff}</p>
        </div>
      </div>
      <div className="metrics">
        <MetricTile label="Log loss" improved={report.backtest.improved.log_loss} baseline={report.backtest.baseline.log_loss} />
        <MetricTile label="Brier score" improved={report.backtest.improved.brier_score} baseline={report.backtest.baseline.brier_score} />
        <MetricTile label="Accuracy" improved={report.backtest.improved.accuracy} baseline={report.backtest.baseline.accuracy} lowerIsBetter={false} />
      </div>
      <div className="chart-card">
        <div>
          <h3>Calibration</h3>
          <p>Blue is confidence, green is realized accuracy.</p>
        </div>
        <CalibrationChart />
      </div>
    </section>
  );
}

function MethodStrip() {
  const items = [
    ["Open data", "49k+ international matches through public CSVs", Database],
    ["Dynamic Elo", "Margin, venue, and tournament-importance adjusted ratings", Activity],
    ["FIFA prior", `${context.fifa_prior_teams ?? 0} team ranking rows blended into tournament strength`, BarChart3],
    ["Context scores", "Fixture, travel, rest, climate, and squad availability modifiers", Trophy],
  ];
  return (
    <section className="method-strip" aria-label="Model methodology">
      {items.map(([title, body, Icon]) => (
        <article className="method-item" key={title}>
          <Icon size={19} />
          <div>
            <h3>{title}</h3>
            <p>{body}</p>
          </div>
        </article>
      ))}
    </section>
  );
}

function ModelInputs() {
  const used = [
    "49,400 public international match results",
    "Match date, teams, scoreline, tournament, host country, neutral flag",
    "Derived dynamic Elo, margin, venue-neutrality, and competition-weight features",
    `${context.fifa_prior_teams ?? 0} official FIFA ranking priors`,
    `${context.fixture_count ?? 0} exact group fixtures with kickoff times and stadiums`,
    `${context.venue_count ?? 0} venues with coordinates, altitude, roof, and historical June climate`,
    "Travel distance, rest-day, and configurable squad availability adjustments",
  ];
  const next = ["Live matchday weather forecasts", "Confirmed injuries, suspensions, lineups, and recent player minutes feeds"];
  return (
    <section className="input-panel" aria-labelledby="input-title">
      <div>
        <h2 id="input-title">Model inputs</h2>
        <p>
          This version keeps the open historical model, then applies tournament-context modifiers from the
          2026 schedule, venues, rankings, travel, rest, climate, and availability fields.
        </p>
      </div>
      <div className="input-columns">
        <div>
          <h3>Used now</h3>
          <ul>
            {used.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div>
          <h3>Live feeds next</h3>
          <ul>
            {next.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </div>
    </section>
  );
}

function App() {
  return (
    <main>
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">W</span>
          <div>
            <strong>WCP Forecast Lab</strong>
            <small>Open-data World Cup model</small>
          </div>
        </div>
        <nav aria-label="Dashboard sections">
          <a href="#backtest">Backtest</a>
          <a href="#simulation">Simulation</a>
          <a href="https://github.com/VeinDevTtv/WCPREDICTION" target="_blank" rel="noreferrer">
            <Github size={16} /> GitHub
          </a>
        </nav>
      </header>

      <section className="intro">
        <div>
          <h1>World Cup 2026 probabilities, tested before they are trusted.</h1>
          <p>
            A reproducible forecast built from public international results, chronological validation,
            and tournament simulations that expose uncertainty instead of hiding it.
          </p>
        </div>
        <div className="run-card">
          <span>latest trained data</span>
          <strong>{report.model.lastMatch}</strong>
          <small>{report.model.rows.toLocaleString()} matches · seed {report.simulation.seed}</small>
        </div>
      </section>

      <section className="dashboard-grid" id="simulation">
        <ChampionBoard />
        <StagePath />
        <div id="backtest">
          <QualityPanel />
        </div>
      </section>

      <MethodStrip />
      <ModelInputs />
    </main>
  );
}

export default App;

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
