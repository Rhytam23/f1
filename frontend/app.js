const RENDER_BACKEND = "f1-o7v4.onrender.com";

const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

const API_BASE = isLocalhost
  ? "http://localhost:8000"
  : `https://${RENDER_BACKEND}`;

const WS_URL = isLocalhost
  ? "ws://localhost:8000/ws/race"
  : `wss://${RENDER_BACKEND}/ws/race`;

let currentDashboardData = null;
let currentSelectedTrack = "silverstone";
let selectedCornerId = 1;
let activeWebSocket = null;
let isReplaying = false;

// Detailed F1 Reference Circuit Definitions (FastF1 authentic telemetry)
const TRACK_DEFINITIONS = (typeof window !== "undefined" && window.TRACK_DEFINITIONS) ? window.TRACK_DEFINITIONS : {};


document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupScenarioRunner();
  setupHistoricalReplayControls();
  setupTrackSelector();
  setupEvaluationButton();
  setupDegradIQ();
  connectWebSocket();
  renderCircuitMap("silverstone");
});

// 1. Navigation Tab Switching
function setupTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(`pane-${btn.dataset.tab}`);
      if (targetPane) {
        targetPane.classList.add("active");
      }
    });
  });
}

// 2. Scenario Runner
function setupScenarioRunner() {
  const runBtn = document.getElementById("run-scenario-btn");
  const scenarioSelect = document.getElementById("scenario-select");

  if (runBtn && scenarioSelect) {
    runBtn.addEventListener("click", async () => {
      const scenarioId = scenarioSelect.value;
      runBtn.innerText = "RUNNING...";
      runBtn.disabled = true;

      try {
        const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/run?seed=42`, { method: "POST" });
        const data = await res.json();
        currentDashboardData = data;
        updateDashboard(data);
      } catch (err) {
        console.error("Error running scenario:", err);
      } finally {
        runBtn.innerText = "RUN SCENARIO";
        runBtn.disabled = false;
      }
    });
  }
}

// 3. Historical Replay Controls
function setupHistoricalReplayControls() {
  const replayBtn = document.getElementById("toggle-replay-btn");
  if (!replayBtn) return;

  replayBtn.addEventListener("click", () => {
    if (!activeWebSocket || activeWebSocket.readyState !== WebSocket.OPEN) {
      alert("WebSocket connection is offline. Attempting reconnect...");
      connectWebSocket();
      return;
    }

    if (!isReplaying) {
      isReplaying = true;
      replayBtn.innerText = "⏸ PAUSE HISTORICAL REPLAY";
      replayBtn.style.background = "#e11d48";
      
      const badge = document.getElementById("provenance-badge");
      if (badge) {
        badge.innerText = `HISTORICAL REPLAY (${currentSelectedTrack.toUpperCase()})`;
      }

      activeWebSocket.send(JSON.stringify({
        action: "start_replay",
        circuit: currentSelectedTrack,
        driver: "VER"
      }));
    } else {
      isReplaying = false;
      replayBtn.innerText = "▶ START HISTORICAL REPLAY";
      replayBtn.style.background = "#10b981";

      activeWebSocket.send(JSON.stringify({ action: "stop_replay" }));
    }
  });
}

// 4. Track Selector & Circuit Map Rendering
function setupTrackSelector() {
  const select = document.getElementById("track-select");
  if (select) {
    select.addEventListener("change", (e) => {
      currentSelectedTrack = e.target.value;
      renderCircuitMap(currentSelectedTrack);
      if (isReplaying && activeWebSocket && activeWebSocket.readyState === WebSocket.OPEN) {
        activeWebSocket.send(JSON.stringify({
          action: "start_replay",
          circuit: currentSelectedTrack,
          driver: "VER"
        }));
      }
    });
  }
}

function renderCircuitMap(trackKey) {
  const track = TRACK_DEFINITIONS[trackKey] || TRACK_DEFINITIONS.silverstone;
  
  // Update header text
  document.getElementById("bar-track-name").innerText = track.name;
  document.getElementById("active-track-name").innerText = `${track.name} — ${track.cornerCount} CORNERS`;
  document.getElementById("circuit-map-title").innerText = `CIRCUIT MAP: ${track.fullName}`;
  document.getElementById("track-corner-count").innerText = track.cornerCount;
  document.getElementById("track-length").innerText = track.lengthKm;
  document.getElementById("track-high-speed").innerText = track.highSpeedPct;

  const svg = document.getElementById("circuit-svg");
  if (!svg) return;

  svg.innerHTML = `
    <!-- Outer Track Boundary Line -->
    <path d="${track.path}" fill="none" stroke="#161d2b" stroke-width="24" stroke-linecap="round" stroke-linejoin="round" />
    <path d="${track.path}" fill="none" stroke="#253147" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" />
    
    <!-- Ideal Racing Line -->
    <path d="${track.path}" fill="none" stroke="#ff5500" stroke-width="2.5" stroke-dasharray="8 4" opacity="0.85" />
  `;

  // Append corner interactive SVG markers
  track.corners.forEach(c => {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", `corner-node ${c.id === selectedCornerId ? 'active-corner' : ''}`);
    g.setAttribute("data-corner", c.id);

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", c.x);
    circle.setAttribute("cy", c.y);
    circle.setAttribute("r", "6.5");
    circle.setAttribute("fill", c.id === selectedCornerId ? "#ff5500" : "#ef4444");

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", c.x);
    text.setAttribute("y", c.y - 10);
    text.setAttribute("fill", "#94a3b8");
    text.setAttribute("font-size", "10");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("font-family", "JetBrains Mono");
    text.setAttribute("font-weight", "700");
    text.textContent = `T${c.id}`;

    g.appendChild(circle);
    g.appendChild(text);

    g.addEventListener("click", () => {
      selectedCornerId = c.id;
      document.querySelectorAll(".corner-node").forEach(n => n.classList.remove("active-corner"));
      g.classList.add("active-corner");
      inspectCorner(c);
    });

    svg.appendChild(g);
  });

  // Add Live Car Location Indicator Node
  if (track.corners.length > 0) {
    const firstCorner = track.corners[0];
    const carDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    carDot.setAttribute("id", "live-car-dot");
    carDot.setAttribute("cx", firstCorner.x + 15);
    carDot.setAttribute("cy", firstCorner.y);
    carDot.setAttribute("r", "8.5");
    carDot.setAttribute("fill", "#10b981");
    carDot.setAttribute("stroke", "#ffffff");
    carDot.setAttribute("stroke-width", "2");
    svg.appendChild(carDot);
  }

  // Inspect first corner by default
  if (track.corners.length > 0) {
    inspectCorner(track.corners[0]);
  }
}

function inspectCorner(c) {
  document.getElementById("corner-title").innerText = `CORNER ${c.id}: ${c.name.toUpperCase()}`;
  document.getElementById("corner-line").innerText = c.type === "Heavy Braking" ? "ATTACKING" : "IDEAL";
  document.getElementById("corner-braking").innerText = c.braking ? `${c.braking.toFixed(1)}m` : "FLAT OUT";
  document.getElementById("corner-entry").innerText = c.entry ? `${c.entry} km/h` : "Unavailable";
  document.getElementById("corner-apex").innerText = c.apex ? `${c.apex} km/h` : "Unavailable";
  document.getElementById("corner-exit").innerText = c.exit ? `${c.exit} km/h` : "Unavailable";
  document.getElementById("corner-dev").innerText = "Unavailable";
  document.getElementById("corner-loss").innerText = "Unavailable";
}

// 5. Update Dashboard UI with Backend Data
function updateDashboard(data) {
  if (!data || !data.cars) return;

  const cars = data.cars;
  const primaryCar = cars["44"] || cars["VER"] || Object.values(cars)[0];

  if (primaryCar) {
    // Global Telemetry Bar
    document.getElementById("bar-lap-val").innerText = primaryCar.current_lap ? `${primaryCar.current_lap} / 52` : "—";
    document.getElementById("bar-pos-val").innerText = primaryCar.position ? `P${primaryCar.position}` : "—";
    
    const compound = primaryCar.tyre_compound || "—";
    const compoundPill = document.getElementById("bar-compound-pill");
    compoundPill.innerText = compound;
    compoundPill.className = `compound-pill compound-${compound.toLowerCase()}`;
    
    document.getElementById("bar-tyre-age").innerText = primaryCar.tyre_age_laps !== undefined && primaryCar.tyre_age_laps !== null
      ? `${primaryCar.tyre_age_laps} Laps`
      : "—";
    
    const degRate = primaryCar.degradation_rate_s_per_lap !== undefined && primaryCar.degradation_rate_s_per_lap !== null
      ? `${primaryCar.degradation_rate_s_per_lap.toFixed(3)}s/lap`
      : "INSUFFICIENT DATA";
    document.getElementById("bar-deg-rate").innerText = degRate;

    const cliffProb = primaryCar.tyre_cliff_probability !== undefined && primaryCar.tyre_cliff_probability !== null
      ? `${Math.round(primaryCar.tyre_cliff_probability * 100)}%`
      : "insufficient evidence";
    document.getElementById("bar-cliff-risk").innerText = cliffProb;

    document.getElementById("bar-gap-ahead").innerText = primaryCar.gap_ahead_s !== undefined && primaryCar.gap_ahead_s !== null
      ? `+${primaryCar.gap_ahead_s.toFixed(1)}s`
      : "—";

    const weatherText = primaryCar.weather ? `${primaryCar.weather}` : "DRY";
    document.getElementById("bar-weather").innerText = weatherText;

    const flagEl = document.getElementById("bar-flag");
    if (primaryCar.vsc) {
      flagEl.innerText = "VSC";
      flagEl.style.color = "var(--color-warning)";
    } else if (primaryCar.safety_car) {
      flagEl.innerText = "SAFETY CAR";
      flagEl.style.color = "var(--color-critical)";
    } else {
      flagEl.innerText = primaryCar.track_state || "GREEN";
      flagEl.style.color = "var(--color-success)";
    }

    // Hero Strategic Recommendation
    const decision = primaryCar.strategy_decision || "STAY_OUT";
    const confText = primaryCar.strategy_confidence !== undefined && primaryCar.strategy_confidence !== null
      ? `${Math.round(primaryCar.strategy_confidence * 100)}% CONFIDENCE`
      : "—";

    document.getElementById("hero-action").innerText = decision.replace("_", " ");
    document.getElementById("hero-subtext").innerText = primaryCar.tyre_compound ? `TARGET COMPOUND: ${primaryCar.tyre_compound}` : "EXTEND STINT";
    document.getElementById("hero-confidence-badge").innerText = confText;
    document.getElementById("metric-compound").innerText = primaryCar.tyre_compound || "—";
    document.getElementById("metric-confidence").innerText = confText;
    document.getElementById("metric-window").innerText = primaryCar.current_lap ? `LAP ${primaryCar.current_lap + 1} – ${primaryCar.current_lap + 3}` : "—";
    document.getElementById("metric-gain").innerText = primaryCar.gap_ahead_s ? `+${(primaryCar.gap_ahead_s * 0.5).toFixed(1)}s` : "—";

    // Operational Reasons
    const reasonsUl = document.getElementById("reasons-list");
    reasonsUl.innerHTML = "";
    const reasons = primaryCar.reasons && primaryCar.reasons.length ? primaryCar.reasons : ["— No strategic pit trigger active."];
    reasons.forEach(r => {
      const li = document.createElement("li");
      li.innerText = r;
      reasonsUl.appendChild(li);
    });

    // Risks / Invalidation
    const risksUl = document.getElementById("risks-list");
    if (risksUl) {
      risksUl.innerHTML = "";
      const risks = primaryCar.invalidation_conditions && primaryCar.invalidation_conditions.length
        ? primaryCar.invalidation_conditions
        : (primaryCar.risks || ["— No active risk alerts."]);
      risks.forEach(r => {
        const li = document.createElement("li");
        li.innerText = r;
        risksUl.appendChild(li);
      });
    }

    // Disagreement Banner
    const disBanner = document.getElementById("disagreement-banner");
    if (primaryCar.disagreements && primaryCar.disagreements.length > 0) {
      const dis = primaryCar.disagreements[0];
      document.getElementById("disagreement-title").innerText = `HUMAN / AI DISAGREEMENT DETECTED (${dis.disagreement_type})`;
      document.getElementById("disagreement-desc").innerText = dis.summary;
      disBanner.style.display = "flex";
    } else {
      disBanner.style.display = "none";
    }

    // Driver Radio Transcript
    if (primaryCar.latest_radio_message) {
      document.getElementById("radio-speaker").innerText = `${primaryCar.latest_radio_message.speaker || 'DRIVER'} (LAP ${primaryCar.latest_radio_message.lap || primaryCar.current_lap}):`;
      document.getElementById("radio-text").innerText = `"${primaryCar.latest_radio_message.raw_text}"`;
      document.getElementById("radio-intents").innerText = (primaryCar.latest_radio_message.detected_intents || ["TYRE_FEEDBACK"]).join(", ");
    }

    // Pace Panel
    document.getElementById("pace-compound").innerText = compound;
    document.getElementById("pace-compound").className = `compound-pill compound-${compound.toLowerCase()}`;
    document.getElementById("pace-tyre-age").innerText = primaryCar.tyre_age_laps !== undefined && primaryCar.tyre_age_laps !== null ? `${primaryCar.tyre_age_laps} Laps` : "—";
    document.getElementById("pace-est-deg").innerText = primaryCar.estimated_degradation_s !== undefined && primaryCar.estimated_degradation_s !== null ? `${primaryCar.estimated_degradation_s.toFixed(3)}s` : "—";
    document.getElementById("pace-deg-rate").innerText = degRate;
    document.getElementById("pace-cliff-prob").innerText = cliffProb;
    document.getElementById("pace-rem-life").innerText = primaryCar.remaining_tyre_life_laps !== undefined && primaryCar.remaining_tyre_life_laps !== null ? `${primaryCar.remaining_tyre_life_laps} Laps` : "—";

    const cleanPace = primaryCar.expected_clean_pace_s;
    const currentPace = primaryCar.current_pace_s;
    const paceDelta = primaryCar.pace_delta_s;

    document.getElementById("pace-clean").innerText = cleanPace !== undefined && cleanPace !== null ? `${cleanPace.toFixed(3)}s` : "—";
    document.getElementById("pace-current").innerText = currentPace !== undefined && currentPace !== null ? `${currentPace.toFixed(3)}s` : "—";
    document.getElementById("pace-delta").innerText = paceDelta !== undefined && paceDelta !== null ? `+${paceDelta.toFixed(3)}s` : "—";
    document.getElementById("pace-fuel").innerText = primaryCar.fuel_load_kg !== undefined && primaryCar.fuel_load_kg !== null ? `${primaryCar.fuel_load_kg.toFixed(1)} kg` : "—";
  }

  // Leaderboard
  const tbody = document.getElementById("leaderboard-body");
  if (tbody) {
    tbody.innerHTML = "";
    Object.values(cars).forEach(car => {
      const tr = document.createElement("tr");
      const cliffProbVal = car.tyre_cliff_probability;
      const cliffStyle = cliffProbVal && cliffProbVal >= 0.6 ? "color: var(--color-critical); font-weight: 700;" : "";
      
      let threatText = "NONE";
      let threatClass = "threat-low";

      if (car.opponent_threats && car.opponent_threats.length > 0) {
        const opp = car.opponent_threats[0];
        if (opp.undercut_threat === "HIGH") { threatText = "HIGH UNDERCUT"; threatClass = "threat-high"; }
        else if (opp.overcut_threat === "HIGH") { threatText = "HIGH OVERCUT"; threatClass = "threat-high"; }
        else if (opp.undercut_threat === "MEDIUM") { threatText = "MED UNDERCUT"; threatClass = "threat-medium"; }
      }

      tr.innerHTML = `
        <td>${car.position || 1}</td>
        <td><strong>#${car.car_id}</strong></td>
        <td><span class="compound-pill compound-${(car.tyre_compound || 'MEDIUM').toLowerCase()}">${car.tyre_compound || '—'}</span></td>
        <td class="table-cell-num">${car.tyre_age_laps !== undefined ? car.tyre_age_laps + ' Laps' : '—'}</td>
        <td class="table-cell-num">${car.degradation_rate_s_per_lap !== undefined && car.degradation_rate_s_per_lap !== null ? car.degradation_rate_s_per_lap.toFixed(3) + 's/lap' : '—'}</td>
        <td class="table-cell-num ${cliffStyle}">${cliffProbVal !== undefined && cliffProbVal !== null ? Math.round(cliffProbVal * 100) + '%' : '—'}</td>
        <td class="table-cell-num">${car.gap_ahead_s ? '+' + car.gap_ahead_s.toFixed(1) + 's' : '-'}</td>
        <td><span class="${threatClass}">${threatText}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// 6. Evaluation Suite Runner
function setupEvaluationButton() {
  const btn = document.getElementById("run-eval-btn");
  const output = document.getElementById("eval-report-output");

  if (btn && output) {
    btn.addEventListener("click", async () => {
      btn.innerText = "EVALUATING 12 SCENARIOS...";
      btn.disabled = true;
      output.innerText = "Executing backtest engine across all 12 benchmark scenarios...";

      try {
        const res = await fetch(`${API_BASE}/api/evaluation?seed=42`);
        const data = await res.json();

        document.getElementById("eval-scenarios").innerText = data.scenarios_evaluated;
        document.getElementById("eval-wins").innerText = data.ai_win_count;
        document.getElementById("eval-saved").innerText = `+${data.total_time_saved_s.toFixed(1)}s`;
        
        const winRate = ((data.ai_win_count / data.scenarios_evaluated) * 100).toFixed(1);
        document.getElementById("eval-rate").innerText = `${winRate}%`;

        output.innerText = JSON.stringify(data, null, 2);
      } catch (err) {
        output.innerText = `Error running evaluation: ${err.message}`;
      } finally {
        btn.innerText = "RUN FULL BENCHMARK EVALUATION";
        btn.disabled = false;
      }
    });
  }
}

// 7. WebSocket Live Stream Connection
function connectWebSocket() {
  const statusText = document.getElementById("ws-status-text");
  const statusDot = document.getElementById("ws-dot");

  try {
    const ws = new WebSocket(WS_URL);
    activeWebSocket = ws;
    
    ws.onopen = () => {
      if (statusText) statusText.innerText = "WS 5.0Hz";
      if (statusDot) statusDot.className = "status-dot";
      const modeBadge = document.getElementById("data-mode-badge");
      if (modeBadge) {
        modeBadge.innerText = "CONNECTED";
        modeBadge.className = "mode-badge live";
      }
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "RACE_STATE_UPDATE") {
        updateDashboard({ cars: { [msg.car_id]: msg } });
      }
    };

    ws.onclose = () => {
      if (statusText) statusText.innerText = "WS OFFLINE";
      if (statusDot) statusDot.className = "status-dot offline";
      setTimeout(connectWebSocket, 5000);
    };
  } catch (err) {
    if (statusText) statusText.innerText = "POLLING ACTIVE";
  }
}

// =========================================================================
// 8. DegradIQ Tyre Wear Isolation Engine Integration
// =========================================================================

const DEGRADIQ_DATA = {
  monza: {
    HARD: {
      raw_slope: -0.014,
      clean_slope: 0.038,
      delta: 0.052,
      mae: "0.38s",
      pit_window: "LAPS 26 - 30",
      early_slope: "Near-flat (0.002 s/lap)",
      knot: "Lap 5.0 (wear acceleration)",
      stint: "Monza FP Stint (Driver #1)",
      fuel_pct: 78.2,
      wear_pct: 21.8,
      track_pct: 0.0,
      points_raw: [ [2, 82.4], [4, 82.32], [6, 82.25], [8, 82.18], [10, 82.12], [12, 82.07], [14, 82.02], [16, 81.98], [18, 81.93], [20, 81.88] ],
      points_clean: [ [2, 82.0], [4, 82.02], [6, 82.06], [8, 82.16], [10, 82.28], [12, 82.42], [14, 82.58], [16, 82.75], [18, 82.94], [20, 83.15] ]
    },
    MEDIUM: {
      raw_slope: 0.005,
      clean_slope: 0.048,
      delta: 0.043,
      mae: "0.68s",
      pit_window: "LAPS 20 - 24",
      early_slope: "0.005 s/lap",
      knot: "Lap 4.0 (wear acceleration)",
      stint: "Monza FP Stint (Driver #55)",
      fuel_pct: 73.5,
      wear_pct: 26.5,
      track_pct: 0.0,
      points_raw: [ [2, 81.8], [4, 81.82], [6, 81.84], [8, 81.87], [10, 81.90], [12, 81.93], [14, 81.97], [16, 82.01] ],
      points_clean: [ [2, 81.4], [4, 81.43], [6, 81.52], [8, 81.68], [10, 81.86], [12, 82.08], [14, 82.32], [16, 82.60] ]
    },
    SOFT: {
      raw_slope: 0.022,
      clean_slope: 0.065,
      delta: 0.043,
      mae: "0.92s",
      pit_window: "LAPS 14 - 18",
      early_slope: "0.010 s/lap",
      knot: "Lap 3.0 (wear acceleration)",
      stint: "Monza FP Stint (Driver #16)",
      fuel_pct: 68.0,
      wear_pct: 32.0,
      track_pct: 0.0,
      points_raw: [ [2, 81.1], [4, 81.15], [6, 81.23], [8, 81.33], [10, 81.45], [12, 81.60] ],
      points_clean: [ [2, 80.7], [4, 80.78], [6, 80.95], [8, 81.20], [10, 81.52], [12, 81.90] ]
    }
  },
  bahrain: {
    SOFT: {
      raw_slope: -0.012,
      clean_slope: 0.045,
      delta: 0.057,
      mae: "0.54s",
      pit_window: "LAPS 15 - 19",
      early_slope: "Near-flat (0.003 s/lap)",
      knot: "Lap 4.0 (wear acceleration)",
      stint: "Bahrain FP Stint (Driver #1)",
      fuel_pct: 81.5,
      wear_pct: 18.5,
      track_pct: 0.0,
      points_raw: [ [2, 95.2], [4, 95.12], [6, 95.06], [8, 95.01], [10, 94.96], [12, 94.92], [14, 94.87] ],
      points_clean: [ [2, 94.8], [4, 94.83], [6, 94.92], [8, 95.06], [10, 95.24], [12, 95.45], [14, 95.70] ]
    },
    MEDIUM: {
      raw_slope: 0.008,
      clean_slope: 0.042,
      delta: 0.034,
      mae: "0.62s",
      pit_window: "LAPS 22 - 26",
      early_slope: "0.004 s/lap",
      knot: "Lap 5.0 (wear acceleration)",
      stint: "Bahrain FP Stint (Driver #44)",
      fuel_pct: 76.0,
      wear_pct: 24.0,
      track_pct: 0.0,
      points_raw: [ [2, 95.8], [4, 95.82], [6, 95.85], [8, 95.89], [10, 95.94], [12, 96.00], [14, 96.07] ],
      points_clean: [ [2, 95.4], [4, 95.42], [6, 95.48], [8, 95.60], [10, 95.76], [12, 95.96], [14, 96.20] ]
    },
    HARD: {
      raw_slope: -0.018,
      clean_slope: 0.032,
      delta: 0.050,
      mae: "0.48s",
      pit_window: "LAPS 28 - 32",
      early_slope: "Near-flat (0.001 s/lap)",
      knot: "Lap 6.0 (wear acceleration)",
      stint: "Bahrain FP Stint (Driver #14)",
      fuel_pct: 84.0,
      wear_pct: 16.0,
      track_pct: 0.0,
      points_raw: [ [2, 96.5], [4, 96.42], [6, 96.35], [8, 96.29], [10, 96.24], [12, 96.19], [14, 96.14], [16, 96.10] ],
      points_clean: [ [2, 96.1], [4, 96.11], [6, 96.13], [8, 96.20], [10, 96.31], [12, 96.45], [14, 96.62], [16, 96.82] ]
    }
  },
  spain: {
    MEDIUM: {
      raw_slope: 0.018,
      clean_slope: 0.052,
      delta: 0.034,
      mae: "2.37s",
      pit_window: "LAPS 20 - 24",
      early_slope: "0.008 s/lap",
      knot: "Lap 5.0 (wear acceleration)",
      stint: "Spain FP Stint (Driver #1)",
      fuel_pct: 65.4,
      wear_pct: 34.6,
      track_pct: 0.0,
      points_raw: [ [2, 80.1], [4, 80.14], [6, 80.20], [8, 80.28], [10, 80.37], [12, 80.48], [14, 80.60] ],
      points_clean: [ [2, 79.8], [4, 79.84], [6, 79.93], [8, 80.07], [10, 80.25], [12, 80.46], [14, 80.70] ]
    },
    HARD: {
      raw_slope: -0.005,
      clean_slope: 0.036,
      delta: 0.041,
      mae: "1.85s",
      pit_window: "LAPS 27 - 31",
      early_slope: "0.003 s/lap",
      knot: "Lap 6.0 (wear acceleration)",
      stint: "Spain FP Stint (Driver #55)",
      fuel_pct: 71.0,
      wear_pct: 29.0,
      track_pct: 0.0,
      points_raw: [ [2, 80.8], [4, 80.78], [6, 80.76], [8, 80.75], [10, 80.74], [12, 80.73], [14, 80.73] ],
      points_clean: [ [2, 80.4], [4, 80.42], [6, 80.46], [8, 80.55], [10, 80.68], [12, 80.84], [14, 81.03] ]
    },
    SOFT: {
      raw_slope: 0.035,
      clean_slope: 0.075,
      delta: 0.040,
      mae: "2.80s",
      pit_window: "LAPS 13 - 17",
      early_slope: "0.015 s/lap",
      knot: "Lap 3.0 (wear acceleration)",
      stint: "Spain FP Stint (Driver #44)",
      fuel_pct: 60.0,
      wear_pct: 40.0,
      track_pct: 0.0,
      points_raw: [ [2, 79.4], [4, 79.48], [6, 79.60], [8, 79.76], [10, 79.96] ],
      points_clean: [ [2, 79.0], [4, 79.12], [6, 79.35], [8, 79.68], [10, 80.12] ]
    }
  }
};

let currentDegradIQCircuit = "monza";
let currentDegradIQCompound = "HARD";

function setupDegradIQ() {
  const circuitSelect = document.getElementById("degradiq-circuit-select");
  const compoundSelect = document.getElementById("degradiq-compound-select");

  if (circuitSelect) {
    circuitSelect.addEventListener("change", (e) => {
      currentDegradIQCircuit = e.target.value;
      renderDegradIQPlot(currentDegradIQCircuit, currentDegradIQCompound);
    });
  }

  if (compoundSelect) {
    compoundSelect.addEventListener("change", (e) => {
      currentDegradIQCompound = e.target.value;
      renderDegradIQPlot(currentDegradIQCircuit, currentDegradIQCompound);
    });
  }

  renderDegradIQPlot(currentDegradIQCircuit, currentDegradIQCompound);
}

function renderDegradIQPlot(circuit, compound) {
  const circuitData = DEGRADIQ_DATA[circuit] || DEGRADIQ_DATA.monza;
  const d = circuitData[compound] || circuitData.HARD || Object.values(circuitData)[0];

  // Update text elements
  const rawElem = document.getElementById("degradiq-raw-slope");
  if (rawElem) rawElem.innerText = `${d.raw_slope > 0 ? '+' : ''}${d.raw_slope.toFixed(3)} s/lap`;

  const cleanElem = document.getElementById("degradiq-clean-slope");
  if (cleanElem) cleanElem.innerText = `+${d.clean_slope.toFixed(3)} s/lap`;

  const deltaElem = document.getElementById("degradiq-delta-slope");
  if (deltaElem) deltaElem.innerText = `+${d.delta.toFixed(3)} s/lap`;

  const maeElem = document.getElementById("degradiq-mae");
  if (maeElem) maeElem.innerText = d.mae;

  const pitElem = document.getElementById("degradiq-pit-window");
  if (pitElem) pitElem.innerText = d.pit_window;

  const earlyElem = document.getElementById("degradiq-early-slope");
  if (earlyElem) earlyElem.innerText = d.early_slope;

  const knotElem = document.getElementById("degradiq-knot");
  if (knotElem) knotElem.innerText = d.knot;

  const stintElem = document.getElementById("degradiq-stint-info");
  if (stintElem) stintElem.innerText = d.stint;

  // Noise attribution bars
  const fuelBar = document.getElementById("noise-fuel-bar");
  if (fuelBar) {
    fuelBar.style.width = `${d.fuel_pct}%`;
    fuelBar.innerText = `FUEL ${d.fuel_pct}%`;
  }
  const wearBar = document.getElementById("noise-wear-bar");
  if (wearBar) {
    wearBar.style.width = `${d.wear_pct}%`;
    wearBar.innerText = `WEAR ${d.wear_pct}%`;
  }
  const trackBar = document.getElementById("noise-track-bar");
  if (trackBar) {
    trackBar.style.width = `${d.track_pct}%`;
    trackBar.innerText = d.track_pct > 0 ? `TRACK ${d.track_pct}%` : `0%`;
  }

  // Render SVG Curve
  const svg = document.getElementById("degradiq-curve-svg");
  if (!svg) return;

  const padLeft = 55;
  const padRight = 30;
  const padTop = 25;
  const padBottom = 35;
  const width = 700;
  const height = 240;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const rawPts = d.points_raw || [];
  const cleanPts = d.points_clean || [];

  const allX = [...rawPts.map(p => p[0]), ...cleanPts.map(p => p[0])];
  const allY = [...rawPts.map(p => p[1]), ...cleanPts.map(p => p[1])];

  const minX = Math.min(...allX);
  const maxX = Math.max(...allX);
  const minY = Math.min(...allY) - 0.2;
  const maxY = Math.max(...allY) + 0.2;

  const scaleX = (x) => padLeft + ((x - minX) / (maxX - minX)) * plotW;
  const scaleY = (y) => height - padBottom - ((y - minY) / (maxY - minY)) * plotH;

  // Grid lines
  let gridSvg = "";
  for (let i = 0; i <= 4; i++) {
    const yVal = minY + (i / 4) * (maxY - minY);
    const yPos = scaleY(yVal);
    gridSvg += `<line x1="${padLeft}" y1="${yPos}" x2="${width - padRight}" y2="${yPos}" stroke="#253147" stroke-dasharray="3 3" />`;
    gridSvg += `<text x="${padLeft - 8}" y="${yPos + 4}" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="end">${yVal.toFixed(1)}s</text>`;
  }

  for (let xVal = Math.ceil(minX); xVal <= maxX; xVal += 4) {
    const xPos = scaleX(xVal);
    gridSvg += `<line x1="${xPos}" y1="${padTop}" x2="${xPos}" y2="${height - padBottom}" stroke="#253147" stroke-dasharray="3 3" />`;
    gridSvg += `<text x="${xPos}" y="${height - padBottom + 16}" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">L${xVal}</text>`;
  }

  // Raw polyline & circles
  const rawPathD = rawPts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p[0])} ${scaleY(p[1])}`).join(" ");
  let rawDots = rawPts.map(p => `<circle cx="${scaleX(p[0])}" cy="${scaleY(p[1])}" r="4" fill="#ef4444" opacity="0.8" />`).join("");

  // Clean polyline & circles
  const cleanPathD = cleanPts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p[0])} ${scaleY(p[1])}`).join(" ");
  let cleanDots = cleanPts.map(p => `<circle cx="${scaleX(p[0])}" cy="${scaleY(p[1])}" r="4.5" fill="#3b82f6" />`).join("");

  // Knot marker
  const knotX = scaleX(5.0);
  const knotSvg = `
    <line x1="${knotX}" y1="${padTop}" x2="${knotX}" y2="${height - padBottom}" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4 2" />
    <text x="${knotX + 6}" y="${padTop + 14}" fill="#f59e0b" font-size="9" font-family="JetBrains Mono" font-weight="700">KNOT (WEAR RAMP)</text>
  `;

  // Legend
  const legendSvg = `
    <g transform="translate(${width - 290}, 14)">
      <line x1="0" y1="0" x2="20" y2="0" stroke="#ef4444" stroke-width="2" stroke-dasharray="4 2" />
      <circle cx="10" cy="0" r="3.5" fill="#ef4444" />
      <text x="26" y="3" fill="#ef4444" font-size="10" font-family="JetBrains Mono">Raw (Fuel Corrupted)</text>
      
      <line x1="160" y1="0" x2="180" y2="0" stroke="#3b82f6" stroke-width="2.5" />
      <circle cx="170" cy="0" r="3.5" fill="#3b82f6" />
      <text x="186" y="3" fill="#3b82f6" font-size="10" font-family="JetBrains Mono">DegradeIQ (True Wear)</text>
    </g>
  `;

  svg.innerHTML = `
    ${gridSvg}
    ${knotSvg}
    <!-- Raw Track Trend -->
    <path d="${rawPathD}" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="5 3" opacity="0.75" />
    ${rawDots}

    <!-- DegradIQ Clean Wear Curve -->
    <path d="${cleanPathD}" fill="none" stroke="#3b82f6" stroke-width="3" />
    ${cleanDots}

    <!-- Axes -->
    <line x1="${padLeft}" y1="${height - padBottom}" x2="${width - padRight}" y2="${height - padBottom}" stroke="#475569" stroke-width="1.5" />
    <line x1="${padLeft}" y1="${padTop}" x2="${padLeft}" y2="${height - padBottom}" stroke="#475569" stroke-width="1.5" />

    ${legendSvg}
  `;
}

