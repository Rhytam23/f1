<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
<h3 align="center">TrackShift 2026</h3>

  <p align="center">
    We don't predict tyres. We predict decisions.
    <br />
    <a href="https://github.com/Rhytam23/f1"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Rhytam23/f1/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/Rhytam23/f1/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

> We don't predict tyres. We predict decisions.

An end-to-end, simulator-independent race intelligence platform built for **TrackShift 2026**.

The repository integrates two core layers:
1. **DegradIQ (`degradiq/`)**: The dedicated **Tyre Degradation Isolation Subsystem** solving the core TrackShift 2026 challenge. Isolates true physical tyre wear from noisy practice telemetry (de-fueling, de-trafficking, track evolution cleaning), fits a piecewise-linear Hinge degradation model, validates against race pace with low MAE (e.g., 0.38s at Monza Hard), and visualizes results via an interactive Streamlit dashboard.
2. **Race Intelligence Engine (`backend/`, `frontend/`, `simulator/`, `radio/`, `evaluation/`)**: Real-time pit wall decision engine turning telemetry into explainable strategic recommendations (`PIT`, `STAY_OUT`, `UNDERCUT`, `OVERCUT`, `DEFEND`, `ATTACK`) with confidence ratings, driver radio conflict detection, Monte Carlo position prediction, and interactive web dashboards.

Full documentation index and architecture guides: [doc/INDEX.md](doc/INDEX.md).

### Repository Layout


```
degradiq/    Tyre Degradation Isolation Subsystem (Streamlit dashboard, hinge models, validation)
frontend/    Pit Wall & Strategic HQ dashboards, 14-corner SVG track viz, telemetry inspector
backend/     Ingestion → 10-stage normalization → state estimation → pace/tyre/opponent estimators →
             event detection → strategy decision engine → Monte Carlo prediction → WebSocket
simulator/   Telemetry generator, seeded scenario engine (12 scenarios), pit stop simulation, replay
radio/       Async audio transcription & human/AI conflict detection (5 disagreement rules)
evaluation/  Backtesting engine, latency benchmarking (<2s targets), stress testing
data/        Cached FastF1 telemetry & race session pickles
doc/         Comprehensive 10-part technical documentation suite
tests/       Unit, interface, scenario, and integration test suite (256/256 passing)
```

---

### Engineering Principles


- **Physics-Informed Models First**: Physical degradation models (piecewise-linear hinge wear curve, fuel burn weight correction) take precedence; ML models validate and refine.
- **Explainable Strategy**: The strategy engine decides (`PIT` / `STAY_OUT` / `UNDERCUT`); driver radio intelligence detects human-AI divergence; every recommendation carries an audit reason and confidence score.
- **Zero Hallucinated Numbers**: Every confidence, degradation slope, and delta traces back to real FastF1 session telemetry or physics-calibrated simulation.
- **Strict Subsystem Isolation**: DegradIQ operates as a self-contained analysis module while seamlessly providing calibrated tyre degradation parameters to the broader pit wall decision pipeline.

---

### 📖 Project Understanding (Future Reference)


Built for the TrackShift 2026 competition. Two integrated layers: DegradIQ isolates true tyre
wear from noisy practice telemetry (de-fueling, de-trafficking, track evolution) using a
piecewise-linear "Hinge" degradation model validated against real race pace (e.g. 0.38s MAE at
Monza); the Race Intelligence Engine turns live telemetry into explainable pit-wall
recommendations (PIT/STAY_OUT/UNDERCUT/OVERCUT/DEFEND/ATTACK) with Monte Carlo position
prediction and driver-radio conflict detection. 256/256 tests passing per its own docs.

**Stack:** Python (FastAPI, pandas, scikit-learn, xgboost) backend + Streamlit dashboard +
frontend dashboards; simulator and backtesting/evaluation harness included.
**Status:** competition submission for TrackShift 2026 — the most technically deep repo in your
account, with a real test suite and documentation index (`doc/INDEX.md`).

### 🎯 Where This Can Be Used


- Motorsport/sports-analytics portfolio piece — the tyre-degradation isolation work in
  particular is genuinely novel methodology, worth highlighting on its own.
- Reference architecture for any "noisy real-time telemetry → explainable decision engine"
  problem outside racing (e.g. any domain with sensor noise + high-stakes real-time calls).
- **Hackathons:** built for one, and reusable for the next — the backtesting/evaluation harness
  and simulator are a strong base for any future real-time-decision-engine hackathon track.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With

* [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
* [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
* [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
* [![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
* [![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
* [![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
* [![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

### Quick Start


#### 1. DegradIQ Streamlit Dashboard (Tyre Wear Isolation)
To view the interactive tyre degradation curves, noise attribution (fuel vs. track vs. wear), validation MAE, and pit-window recommendations:

```bash
# Using the DegradIQ environment:
degradiq\.venv\Scripts\python.exe -m streamlit run degradiq/dashboard.py
```

#### 2. Race Intelligence Engine (Live Pit Wall Demo)
To launch the end-to-end race decision engine with live scenario playback, embedded REST API, and web pit wall dashboard:

```bash
# Using the main environment:
.venv\Scripts\activate
python demo.py --scenario tyre_cliff --speed 2.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser to view the live Pit Wall & HQ dashboard.

#### 3. Running Tests
```bash
.venv\Scripts\activate
pytest
```
*All 256 unit, scenario, and integration tests passing.*

---

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/Rhytam23/f1/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

No license file has been added to this repository yet.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Rhytam Biswas - [@Rhytam23](https://github.com/Rhytam23)

Project Link: [https://github.com/Rhytam23/f1](https://github.com/Rhytam23/f1)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/Rhytam23/f1.svg?style=for-the-badge
[contributors-url]: https://github.com/Rhytam23/f1/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Rhytam23/f1.svg?style=for-the-badge
[forks-url]: https://github.com/Rhytam23/f1/network/members
[stars-shield]: https://img.shields.io/github/stars/Rhytam23/f1.svg?style=for-the-badge
[stars-url]: https://github.com/Rhytam23/f1/stargazers
[issues-shield]: https://img.shields.io/github/issues/Rhytam23/f1.svg?style=for-the-badge
[issues-url]: https://github.com/Rhytam23/f1/issues
