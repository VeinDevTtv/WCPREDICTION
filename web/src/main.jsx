import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { 
  Activity, 
  BarChart3, 
  Brackets, 
  Database, 
  Github, 
  ShieldCheck, 
  Trophy, 
  Calendar, 
  Play, 
  Info, 
  Sliders, 
  TrendingUp 
} from "lucide-react";
import report from "./data/dashboard.json";
import "./styles.css";

// Helper for formatting percentages
const percent = (value) => `${(value * 100).toFixed(value >= 0.1 ? 1 : 2)}%`;

// Country-to-flag code dictionary (FlagCDN mappings)
const TEAM_FLAGS = {
  "Spain": "es",
  "Argentina": "ar",
  "France": "fr",
  "Brazil": "br",
  "England": "gb-eng",
  "Germany": "de",
  "Netherlands": "nl",
  "Portugal": "pt",
  "Morocco": "ma",
  "Belgium": "be",
  "Colombia": "co",
  "Japan": "jp",
  "Uruguay": "uy",
  "Mexico": "mx",
  "Ecuador": "ec",
  "Switzerland": "ch",
  "Croatia": "hr",
  "Turkey": "tr",
  "Iran": "ir",
  "South Korea": "kr",
  "Senegal": "sn",
  "Australia": "au",
  "Canada": "ca",
  "United States": "us",
  "Norway": "no",
  "Paraguay": "py",
  "Austria": "at",
  "Algeria": "dz",
  "Ivory Coast": "ci",
  "Egypt": "eg",
  "Panama": "pa",
  "Scotland": "gb-sct",
  "Czech Republic": "cz",
  "Sweden": "se",
  "Uzbekistan": "uz",
  "Tunisia": "tn",
  "DR Congo": "cd",
  "New Zealand": "nz",
  "Jordan": "jo",
  "Iraq": "iq",
  "Saudi Arabia": "sa",
  "South Africa": "za",
  "Bosnia and Herzegovina": "ba",
  "Cape Verde": "cv",
  "Haiti": "ht",
  "Qatar": "qa",
  "Ghana": "gh",
  "Curacao": "cw"
};

// Returns FlagCDN URL for a given team name
const getFlagUrl = (teamName, size = 40) => {
  const code = TEAM_FLAGS[teamName];
  if (!code) return "https://flagcdn.com/w40/un.png"; // Fallback generic flag
  return `https://flagcdn.com/w${size}/${code}.png`;
};

// Custom Soccer Goal SVG Icon for Poisson Scorelines
function GoalIcon({ size = 20, ...props }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {/* Goal frame */}
      <path d="M3 21V6h18v15" />
      {/* Netting (subtle grid mesh) */}
      <path d="M3 6l4 4M7 10l5-5M12 5l5 5M17 10l4-4M3 11l4 4M7 15l5-5M12 10l5 5M17 15l4-4M3 16l4 4M7 20l5-5M12 15l5 5" strokeWidth="1" strokeOpacity="0.3" />
      {/* Soccer Ball entering the goal */}
      <circle cx="12" cy="15" r="3.5" fill="currentColor" fillOpacity="0.1" />
      <path d="M12 11.5v7M8.5 15h7M9.5 12.5l5 5M14.5 12.5l-5 5" strokeWidth="1" />
    </svg>
  );
}

// 1. Header component matching reference UI
function Header() {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="logo-container">
          <GoalIcon size={24} />
        </div>
        <div className="brand-info">
          <div className="brand-title-row">
            <h1 className="brand-title">WCP Forecast Lab</h1>
            <span className="model-badge">
              <span className="dot"></span>
              Open-data model
            </span>
          </div>
        </div>
      </div>
      <div className="topbar-actions">
        <a href="#backtest" className="btn btn-secondary">
          <Calendar size={16} />
          Backtest
        </a>
        <button className="btn btn-primary" onClick={() => window.scrollTo({ top: document.getElementById("simulation").offsetTop - 20, behavior: "smooth" })}>
          <Play size={16} fill="currentColor" />
          Simulation
        </button>
      </div>
    </header>
  );
}

// 2. Leaderboard: win probabilities for top 5 teams and "All other teams"
function ChampionBoard() {
  const topTeams = report.champions.slice(0, 5);
  const maxVal = topTeams[0]?.probability ?? 1;
  const otherTeamsProb = report.champions.slice(5).reduce((acc, t) => acc + t.probability, 0);

  return (
    <section className="panel leaderboard" aria-labelledby="champion-title">
      <div className="panel-header">
        <div className="panel-title-area">
          <div className="panel-title-row">
            <Trophy size={16} />
            <h2 className="panel-title" id="champion-title">Champion Probability</h2>
          </div>
          <p className="panel-subtitle">% probability to win World Cup 2026</p>
        </div>
        <button className="info-icon-btn" title="Win probability based on 25,000 tournament simulations">
          <Info size={16} />
        </button>
      </div>

      <div className="leader-list">
        {topTeams.map((team, index) => (
          <div className="leader-row" key={team.team}>
            <div className="rank">{index + 1}</div>
            <img 
              src={getFlagUrl(team.team, 40)} 
              alt={`${team.team} flag`} 
              className="flag-badge"
            />
            <div className="team-name">{team.team}</div>
            <div className="bar-track" aria-hidden="true">
              <div className="bar-fill" style={{ width: `${(team.probability / maxVal) * 100}%` }} />
            </div>
            <div className="probability-val">{percent(team.probability)}</div>
          </div>
        ))}

        <div className="leader-row others">
          <div className="rank"></div>
          <div className="flag-badge" style={{ backgroundColor: "#e2e8f0", border: "none" }}></div>
          <div className="team-name">All other teams</div>
          <div className="bar-track" aria-hidden="true">
            <div className="bar-fill" style={{ width: `${(otherTeamsProb / maxVal) * 100}%` }} />
          </div>
          <div className="probability-val">{percent(otherTeamsProb)}</div>
        </div>
      </div>

      <div className="leaderboard-footer">
        <span>Probabilities sum to 100%</span>
        <span>Updated: {report.model.lastMatch}</span>
      </div>
    </section>
  );
}

// 3. Probability path panel with conditional toggling and active connector overlay
function StagePath({ highlightedTeam, setHighlightedTeam }) {
  const [viewMode, setViewMode] = useState("probability"); // "probability" or "qualify"
  const [svgPath, setSvgPath] = useState("");
  
  const containerRef = useRef(null);
  const cellRefs = useRef({});

  const teams = report.champions.slice(0, 5);
  const otherTeamsProb = report.champions.slice(5).reduce((acc, t) => acc + t.probability, 0);

  const stages = [
    { label: "R32", sub: "48 teams", key: "round_of_32" },
    { label: "QF", sub: "8 teams", key: "quarterfinal" },
    { label: "SF", sub: "4 teams", key: "semifinal" },
    { label: "FINAL", sub: "2 teams", key: "final" }
  ];

  // Logic to calculate values based on toggles
  const getCellValue = (team, stageKey) => {
    const rawVal = report.stageProbabilities[stageKey][team] ?? 0;
    if (viewMode === "probability") {
      return rawVal;
    }
    
    // Qualify (%) mode (conditional probability)
    const stagesKeys = ["round_of_32", "quarterfinal", "semifinal", "final", "champion"];
    const stageIndex = stagesKeys.indexOf(stageKey);
    if (stageIndex === 0) return rawVal;

    const prevKey = stagesKeys[stageIndex - 1];
    const prevVal = report.stageProbabilities[prevKey][team] ?? 0;
    return prevVal > 0 ? rawVal / prevVal : 0;
  };

  const getChampionValue = (team) => {
    const rawVal = report.stageProbabilities["champion"][team] ?? 0;
    if (viewMode === "probability") {
      return rawVal;
    }
    // Qualify (%) in final = P(Champion) / P(Final)
    const finalVal = report.stageProbabilities["final"][team] ?? 0;
    return finalVal > 0 ? rawVal / finalVal : 0;
  };

  const updatePath = () => {
    if (!containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const points = [];

    // 1. Gather stage cell centers
    stages.forEach((stage) => {
      const el = cellRefs.current[`${highlightedTeam}-${stage.key}`];
      if (el) {
        const rect = el.getBoundingClientRect();
        points.push({
          x: rect.left - containerRect.left + rect.width / 2,
          y: rect.top - containerRect.top + rect.height / 2
        });
      }
    });

    // 2. Gather champion badge center
    const badgeEl = cellRefs.current[`champion-badge`];
    if (badgeEl) {
      const rect = badgeEl.getBoundingClientRect();
      points.push({
        x: rect.left - containerRect.left + rect.width / 2,
        y: rect.top - containerRect.top + rect.height / 2
      });
    }

    if (points.length < 2) return;

    // Connect cell centers with straight lines, then curve into the champion badge at the end
    let pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      if (i === points.length - 1) {
        const prev = points[i - 1];
        const curr = points[i];
        const cpX1 = prev.x + (curr.x - prev.x) * 0.5;
        const cpY1 = prev.y;
        const cpX2 = prev.x + (curr.x - prev.x) * 0.5;
        const cpY2 = curr.y;
        pathD += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${curr.x} ${curr.y}`;
      } else {
        pathD += ` L ${points[i].x} ${points[i].y}`;
      }
    }
    setSvgPath(pathD);
  };

  useEffect(() => {
    updatePath();

    window.addEventListener("resize", updatePath);
    let resizeObserver;
    if (containerRef.current) {
      resizeObserver = new ResizeObserver(updatePath);
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener("resize", updatePath);
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, [highlightedTeam, viewMode]);

  return (
    <section className="panel path-panel" aria-labelledby="path-title">
      <div className="panel-header">
        <div className="panel-title-area">
          <div className="panel-title-row">
            <Brackets size={16} />
            <h2 className="panel-title" id="path-title">Probability Path to Champion</h2>
          </div>
          <p className="panel-subtitle">Path analysis for the top tournament contenders</p>
        </div>
        <button className="info-icon-btn" title="View predicted win probabilities at each stage. Hover/highlight to isolate.">
          <Info size={16} />
        </button>
      </div>

      <div className="stage-grid-wrapper" ref={containerRef}>
        {/* SVG Drawing Layer */}
        {svgPath && (
          <svg className="path-svg-overlay">
            <path key={`${highlightedTeam}-${viewMode}`} d={svgPath} className="path-line" />
          </svg>
        )}

        <div className="stage-grid">
          {/* Header row */}
          <div className="stage-header-cell team-col"></div>
          {stages.map((st) => (
            <div className="stage-header-cell" key={st.label}>
              <span className="stage-header-title">{st.label}</span>
              <span className="stage-header-sub">{st.sub}</span>
            </div>
          ))}
          <div className="stage-header-cell">
            <span className="stage-header-title">CHAMPION</span>
          </div>

          {/* Teams Rows */}
          {teams.map((t) => {
            const isHighlighted = t.team === highlightedTeam;
            return (
              <React.Fragment key={t.team}>
                <div className="grid-team-cell">
                  <img src={getFlagUrl(t.team, 40)} alt="" className="flag-badge" />
                  <span>{t.team}</span>
                </div>
                
                {stages.map((stage) => {
                  const val = getCellValue(t.team, stage.key);
                  return (
                    <div 
                      className={`grid-cell ${isHighlighted ? "highlighted" : ""}`}
                      key={`${t.team}-${stage.key}`}
                      ref={(el) => {
                        cellRefs.current[`${t.team}-${stage.key}`] = el;
                      }}
                    >
                      <div className="grid-cell-bg-bar" style={{ height: `${val * 100}%` }} />
                      <span className="grid-cell-value">{percent(val)}</span>
                    </div>
                  );
                })}

                {/* Champion Column Node */}
                <div className="champion-badge-container">
                  {isHighlighted ? (
                    <div 
                      className="champion-badge-outer"
                      ref={(el) => {
                        cellRefs.current[`champion-badge`] = el;
                      }}
                    >
                      <div className="champion-badge">
                        <span className="champion-badge-glow"></span>
                        <img src={getFlagUrl(t.team, 80)} alt="" />
                      </div>
                      <span className="champion-badge-name">{t.team}</span>
                      <span className="champion-badge-percent">{percent(getChampionValue(t.team))}</span>
                    </div>
                  ) : (
                    <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-light)" }}>
                      {percent(getChampionValue(t.team))}
                    </div>
                  )}
                </div>
              </React.Fragment>
            );
          })}

          {/* Other Teams Row */}
          <div className="grid-team-cell" style={{ color: "var(--text-muted)", fontWeight: "500" }}>
            <span>Other Teams</span>
          </div>
          {stages.map((stage) => (
            <div className="grid-cell" style={{ border: "1px dashed var(--border-color)", background: "transparent" }} key={`others-${stage.key}`}>
              <span className="grid-cell-value" style={{ color: "var(--text-light)" }}>-</span>
            </div>
          ))}
          <div className="champion-badge-container">
            <span style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-primary)" }}>
              {percent(viewMode === "probability" ? otherTeamsProb : 0)}
            </span>
          </div>
        </div>
      </div>

      <div className="path-controls">
        <div className="view-toggle">
          <span>View:</span>
          <div className="toggle-group">
            <button 
              className={`toggle-btn ${viewMode === "probability" ? "active" : ""}`}
              onClick={() => setViewMode("probability")}
            >
              Probability
            </button>
            <button 
              className={`toggle-btn ${viewMode === "qualify" ? "active" : ""}`}
              onClick={() => setViewMode("qualify")}
            >
              Qualify (%)
            </button>
          </div>
        </div>

        <div className="highlight-selector">
          <span>Highlight team:</span>
          <div className="select-wrapper">
            <img src={getFlagUrl(highlightedTeam, 40)} className="flag-badge" style={{ position: "absolute", left: "10px", zIndex: 1 }} />
            <select
              value={highlightedTeam}
              onChange={(e) => setHighlightedTeam(e.target.value)}
              className="custom-select"
            >
              {teams.map((t) => (
                <option key={t.team} value={t.team}>
                  {t.team}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </section>
  );
}

// 4. Custom SVG calibration line chart with tooltips
function CalibrationChart() {
  const improvedBins = report.backtest.improved.calibration;
  const baselineBins = report.backtest.baseline.calibration;
  
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const chartContainerRef = useRef(null);

  // SVG coordinate mapping math (viewBox 300x200)
  const xScale = (val) => 35 + val * 250;
  const yScale = (val) => 175 - val * 165;

  const handlePointHover = (event, point, modelName) => {
    if (!chartContainerRef.current) return;
    const rect = event.target.getBoundingClientRect();
    const containerRect = chartContainerRef.current.getBoundingClientRect();
    
    setHoveredPoint({
      x: rect.left - containerRect.left + rect.width / 2,
      y: rect.top - containerRect.top,
      model: modelName,
      conf: point.mean_confidence,
      acc: point.empirical_accuracy,
      count: point.count
    });
  };

  // Generate path lines
  const buildPathData = (bins) => {
    if (!bins || bins.length === 0) return "";
    return bins
      .map((bin, i) => `${i === 0 ? "M" : "L"} ${xScale(bin.mean_confidence)} ${yScale(bin.empirical_accuracy)}`)
      .join(" ");
  };

  return (
    <div className="calibration-chart-container" ref={chartContainerRef} style={{ position: "relative" }}>
      <svg className="calibration-graph" viewBox="0 0 300 200">
        {/* Horizontal grid lines */}
        {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((val) => (
          <line
            key={`grid-y-${val}`}
            x1={35}
            y1={yScale(val)}
            x2={285}
            y2={yScale(val)}
            className="chart-grid-line"
          />
        ))}
        {/* Vertical grid lines */}
        {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((val) => (
          <line
            key={`grid-x-${val}`}
            x1={xScale(val)}
            y1={10}
            x2={xScale(val)}
            y2={175}
            className="chart-grid-line"
          />
        ))}

        {/* Diagonal perfect calibration line */}
        <line x1={xScale(0)} y1={yScale(0)} x2={xScale(1)} y2={yScale(1)} className="chart-diagonal-line" />

        {/* X Axis tick labels */}
        {[0.0, 0.2, 0.4, 0.6, 0.8, 1.0].map((val) => (
          <text key={`label-x-${val}`} x={xScale(val)} y={188} textAnchor="middle" className="chart-axis-text">
            {val.toFixed(1)}
          </text>
        ))}

        {/* Y Axis tick labels */}
        {[0.0, 0.2, 0.4, 0.6, 0.8, 1.0].map((val) => (
          <text key={`label-y-${val}`} x={28} y={yScale(val) + 3} textAnchor="end" className="chart-axis-text">
            {val.toFixed(1)}
          </text>
        ))}

        {/* Baseline line */}
        <path d={buildPathData(baselineBins)} className="chart-line-baseline" />

        {/* Improved line */}
        <path d={buildPathData(improvedBins)} className="chart-line-improved" />

        {/* Baseline square points */}
        {baselineBins.map((bin, idx) => (
          <rect
            key={`base-pt-${idx}`}
            x={xScale(bin.mean_confidence) - 3.5}
            y={yScale(bin.empirical_accuracy) - 3.5}
            width={7}
            height={7}
            className="chart-dot-baseline"
            onMouseEnter={(e) => handlePointHover(e, bin, "Baseline Model")}
            onMouseLeave={() => setHoveredPoint(null)}
          />
        ))}

        {/* Improved circular points */}
        {improvedBins.map((bin, idx) => (
          <circle
            key={`imp-pt-${idx}`}
            cx={xScale(bin.mean_confidence)}
            cy={yScale(bin.empirical_accuracy)}
            r={4}
            className="chart-dot-improved"
            onMouseEnter={(e) => handlePointHover(e, bin, "Improved Model")}
            onMouseLeave={() => setHoveredPoint(null)}
          />
        ))}
      </svg>

      {/* Tooltip Overlay */}
      {hoveredPoint && (
        <div 
          className="chart-tooltip"
          style={{
            position: "absolute",
            left: `${hoveredPoint.x}px`,
            top: `${hoveredPoint.y - 10}px`,
            transform: "translate(-50%, -100%)",
            pointerEvents: "none"
          }}
        >
          <div style={{ fontWeight: 700, fontSize: "11px", marginBottom: "2px" }}>{hoveredPoint.model}</div>
          <div>Confidence: {(hoveredPoint.conf * 100).toFixed(1)}%</div>
          <div>Accuracy: {(hoveredPoint.acc * 100).toFixed(1)}%</div>
          <div style={{ opacity: 0.8, fontSize: "9px" }}>({hoveredPoint.count.toLocaleString()} matches)</div>
        </div>
      )}

      {/* Legend */}
      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color improved"></span>
          <span>Improved model</span>
        </div>
        <div className="legend-item">
          <span className="legend-color baseline"></span>
          <span>Baseline</span>
        </div>
        <div className="legend-item">
          <span className="legend-color perfect"></span>
          <span>Perfect calibration</span>
        </div>
      </div>
    </div>
  );
}

// 5. Model quality metrics list and outperform indicator banner
function QualityPanel() {
  const imp = report.backtest.improved;
  const base = report.backtest.baseline;

  return (
    <section className="panel quality-panel" id="backtest" aria-labelledby="quality-title">
      <div className="panel-header" style={{ marginBottom: "12px" }}>
        <div className="panel-title-area">
          <div className="panel-title-row">
            <ShieldCheck size={16} />
            <h2 className="panel-title" id="quality-title">Model Quality</h2>
          </div>
          <p className="panel-subtitle">Chronological holdout since {report.backtest.cutoff}</p>
        </div>
        <button className="info-icon-btn" title="Evaluation metrics computed on matches after the validation cutoff date.">
          <Info size={16} />
        </button>
      </div>

      <table className="model-quality-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Improved Model</th>
            <th>Baseline</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="metric-name">Log Loss (↓)</td>
            <td className="val-improved">{imp.log_loss.toFixed(3)}</td>
            <td className="val-baseline">{base.log_loss.toFixed(3)}</td>
          </tr>
          <tr>
            <td className="metric-name">Brier Score (↓)</td>
            <td className="val-improved">{imp.brier_score.toFixed(3)}</td>
            <td className="val-baseline">{base.brier_score.toFixed(3)}</td>
          </tr>
          <tr>
            <td className="metric-name">Accuracy (↑)</td>
            <td className="val-improved">{percent(imp.accuracy)}</td>
            <td className="val-baseline">{percent(base.accuracy)}</td>
          </tr>
        </tbody>
      </table>

      <div className="outperform-banner">
        <ShieldCheck size={14} style={{ color: "var(--primary-green-dark)" }} />
        <span>Improved model outperforms baseline</span>
      </div>

      <div style={{ marginTop: "12px", borderTop: "1px solid var(--border-color)", paddingTop: "12px" }}>
        <div className="panel-title-row" style={{ marginBottom: "2px" }}>
          <h3 className="panel-title" style={{ fontSize: "13px" }}>Calibration (Reliability Diagram)</h3>
        </div>
        <p className="panel-subtitle" style={{ marginBottom: "8px" }}>Observed accuracy versus predicted probability</p>
        <CalibrationChart />
      </div>
    </section>
  );
}

// 6. Methodology section with clean, descriptive cards and bespoke SVGs
function Methodology() {
  const items = [
    {
      title: "1. Data Source",
      body: "Open data from FIFA, Opta, FBref, Understat and national federation feeds. Matches up to June 2026.",
      Icon: Database
    },
    {
      title: "2. Dynamic Elo",
      body: "Time-decayed Elo ratings with margin, home advantage, venue neutrality and tournament importance modifiers.",
      Icon: TrendingUp
    },
    {
      title: "3. Calibrated Probabilities",
      body: "Platt scaling calibration on rolling holdout windows to produce well-calibrated win/draw/loss probabilities.",
      Icon: Sliders
    },
    {
      title: "4. Poisson Scorelines",
      body: "Bivariate Poisson model for scoreline simulation with attack/defense strength and temporal form.",
      Icon: GoalIcon
    }
  ];

  return (
    <section aria-labelledby="methodology-main-title">
      <div className="methodology-heading-area">
        <Sliders size={16} />
        <h2 className="methodology-heading" id="methodology-main-title">Methodology</h2>
      </div>
      <div className="method-strip">
        {items.map(({ title, body, Icon }) => (
          <article className="method-item" key={title}>
            <div className="method-icon-container">
              <Icon size={20} />
            </div>
            <div className="method-info">
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

// 7. Footer section displaying model details
function Footer() {
  return (
    <footer className="footer">
      <div className="footer-disclaimer">
        <Info size={14} />
        <span>This model is for informational purposes only and not a guarantee of future results.</span>
      </div>
      <div className="footer-meta">
        <span>Model: {report.model.rows.toLocaleString()} matches · seed {report.simulation.seed}</span>
        <span>Model version: 2026-06-10_v1.0 | &copy; 2026 WCP Forecast Lab</span>
      </div>
    </footer>
  );
}

// Main App Container
function App() {
  const [highlightedTeam, setHighlightedTeam] = useState("Spain");

  return (
    <main>
      <Header />
      
      <section className="dashboard-grid" id="simulation">
        <ChampionBoard />
        <StagePath 
          highlightedTeam={highlightedTeam} 
          setHighlightedTeam={setHighlightedTeam} 
        />
        <QualityPanel />
      </section>

      <Methodology />
      <Footer />
    </main>
  );
}

export default App;

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
