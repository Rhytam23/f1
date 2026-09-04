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

// Detailed F1 Reference Circuit Definitions (Silverstone & Suzuka)
const TRACK_DEFINITIONS = {
  silverstone: {
    name: "SILVERSTONE (BRITISH GP)",
    fullName: "Silverstone Circuit — British Grand Prix",
    lengthKm: "5.891 km",
    cornerCount: 18,
    highSpeedPct: "78%",
    bankingAngle: "1.5°",
    path: "M 100 300 L 120 180 C 140 120, 220 80, 320 80 C 420 80, 520 140, 620 100 C 720 60, 840 100, 900 180 C 950 250, 850 350, 700 340 C 550 330, 400 380, 250 380 C 150 380, 100 340, 100 300 Z",
    corners: [
      { id: 1, name: "Turn 1 (Abbey)", x: 120, y: 220, type: "High Speed", braking: 0, entry: 290, apex: 250, exit: 285 },
      { id: 2, name: "Turn 2 (Farm)", x: 150, y: 160, type: "Flat Out", braking: 0, entry: 295, apex: 290, exit: 300 },
      { id: 3, name: "Turn 3 (Village)", x: 220, y: 100, type: "Heavy Braking", braking: 110, entry: 290, apex: 110, exit: 175 },
      { id: 4, name: "Turn 4 (The Loop)", x: 280, y: 80, type: "Hairpin Traction", braking: 90, entry: 175, apex: 85, exit: 160 },
      { id: 5, name: "Turn 5 (Aintree)", x: 340, y: 80, type: "Acceleration", braking: 0, entry: 160, apex: 210, exit: 260 },
      { id: 6, name: "Turn 6 (Brooklands)", x: 440, y: 100, type: "Medium Speed", braking: 145, entry: 305, apex: 145, exit: 215 },
      { id: 7, name: "Turn 7 (Luffield)", x: 500, y: 125, type: "Long Sweeper", braking: 105, entry: 215, apex: 105, exit: 240 },
      { id: 8, name: "Turn 8 (Woodcote)", x: 560, y: 130, type: "High Speed Exit", braking: 0, entry: 240, apex: 260, exit: 295 },
      { id: 9, name: "Turn 9 (Copse)", x: 670, y: 80, type: "High Speed Sweeper", braking: 180, entry: 315, apex: 265, exit: 290 },
      { id: 10, name: "Turn 10 (Maggotts)", x: 760, y: 80, type: "High Speed S", braking: 0, entry: 300, apex: 285, exit: 275 },
      { id: 11, name: "Turn 11 (Becketts 1)", x: 820, y: 110, type: "High Speed S", braking: 190, entry: 275, apex: 235, exit: 220 },
      { id: 12, name: "Turn 12 (Becketts 2)", x: 870, y: 150, type: "Medium Speed", braking: 160, entry: 220, apex: 195, exit: 210 },
      { id: 13, name: "Turn 13 (Chapel)", x: 895, y: 200, type: "High Exit", braking: 0, entry: 210, apex: 240, exit: 285 },
      { id: 14, name: "Turn 14 (Stowe)", x: 810, y: 310, type: "Heavy Braking", braking: 135, entry: 320, apex: 185, exit: 255 },
      { id: 15, name: "Turn 15 (Vale)", x: 650, y: 340, type: "Chicane Entry", braking: 95, entry: 255, apex: 95, exit: 120 },
      { id: 16, name: "Turn 16 (Club 1)", x: 550, y: 345, type: "Chicane Apex", braking: 105, entry: 120, apex: 105, exit: 140 },
      { id: 17, name: "Turn 17 (Club 2)", x: 420, y: 375, type: "Traction Exit", braking: 0, entry: 140, apex: 160, exit: 210 },
      { id: 18, name: "Turn 18 (Club Exit)", x: 260, y: 375, type: "Flat Out Straight", braking: 0, entry: 210, apex: 230, exit: 290 }
    ]
  },
  suzuka: {
    name: "SUZUKA (JAPANESE GP)",
    fullName: "Suzuka Circuit — Japanese Grand Prix",
    lengthKm: "5.807 km",
    cornerCount: 18,
    highSpeedPct: "80%",
    bankingAngle: "2.5°",
    path: "M 120 320 C 120 180, 250 80, 420 80 C 580 80, 720 120, 850 160 C 950 200, 920 320, 780 340 C 620 360, 450 280, 300 360 C 180 400, 120 380, 120 320 Z",
    corners: [
      { id: 1, name: "Turn 1 (First Corner)", x: 180, y: 220, type: "High Speed", braking: 170, entry: 315, apex: 240, exit: 210 },
      { id: 2, name: "Turn 2", x: 240, y: 150, type: "Medium Speed", braking: 140, entry: 210, apex: 155, exit: 200 },
      { id: 3, name: "Turn 3 (S Curve 1)", x: 300, y: 100, type: "High Speed S", braking: 0, entry: 245, apex: 215, exit: 230 },
      { id: 4, name: "Turn 4 (S Curve 2)", x: 360, y: 85, type: "High Speed S", braking: 0, entry: 230, apex: 205, exit: 220 },
      { id: 5, name: "Turn 5 (S Curve 3)", x: 420, y: 80, type: "High Speed S", braking: 0, entry: 220, apex: 190, exit: 210 },
      { id: 6, name: "Turn 6 (S Curve 4)", x: 480, y: 85, type: "High Speed S", braking: 0, entry: 210, apex: 175, exit: 230 },
      { id: 7, name: "Turn 7 (Dunlop Curve)", x: 560, y: 95, type: "Uphill Sweeper", braking: 0, entry: 230, apex: 220, exit: 260 },
      { id: 8, name: "Turn 8 (Degner 1)", x: 650, y: 110, type: "Right Kink", braking: 180, entry: 275, apex: 195, exit: 180 },
      { id: 9, name: "Turn 9 (Degner 2)", x: 720, y: 130, type: "Tight Right", braking: 120, entry: 180, apex: 135, exit: 190 },
      { id: 10, name: "Turn 10 (Underpass)", x: 780, y: 150, type: "Straight", braking: 0, entry: 190, apex: 240, exit: 275 },
      { id: 11, name: "Turn 11 (Hairpin)", x: 880, y: 180, type: "Heavy Braking Hairpin", braking: 70, entry: 280, apex: 75, exit: 145 },
      { id: 12, name: "Turn 12 (200R)", x: 910, y: 250, type: "Flat Out", braking: 0, entry: 270, apex: 270, exit: 290 },
      { id: 13, name: "Turn 13 (Spoon 1)", x: 860, y: 320, type: "Double Apex Left", braking: 165, entry: 290, apex: 175, exit: 185 },
      { id: 14, name: "Turn 14 (Spoon 2)", x: 750, y: 345, type: "Apex Exit", braking: 140, entry: 185, apex: 150, exit: 240 },
      { id: 15, name: "Turn 15 (130R)", x: 500, y: 300, type: "Ultra High Speed", braking: 0, entry: 310, apex: 290, exit: 315 },
      { id: 16, name: "Turn 16 (Casio 1)", x: 380, y: 330, type: "Chicane Entry", braking: 85, entry: 315, apex: 85, exit: 110 },
      { id: 17, name: "Turn 17 (Casio 2)", x: 300, y: 360, type: "Chicane Exit", braking: 0, entry: 110, apex: 110, exit: 170 },
      { id: 18, name: "Turn 18 (Final Corner)", x: 180, y: 360, type: "Traction Straight", braking: 0, entry: 170, apex: 220, exit: 285 }
    ]
  }
};

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupScenarioRunner();
  setupHistoricalReplayControls();
  setupTrackSelector();
  setupEvaluationButton();
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
