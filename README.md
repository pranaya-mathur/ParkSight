# ParkSight AI: Enterprise Parking Monetization & Cognitive Guidance

![ParkSight AI Dashboard Mockup](assets/hero_dashboard.png)

[![Status](https://img.shields.io/badge/Status-Production--oriented-emerald.svg)]()
[![Vision](https://img.shields.io/badge/Vision-YOLO11%20%2B%20ONNX-blue.svg)]()
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20LangGraph%20%7C%20React-slate.svg)]()

ParkSight AI is an edge-first intelligent parking platform: **computer vision** on the edge, **orchestration and revenue logic** in the cloud, and a **React** operations dashboard. The system combines YOLO-based detection, optional **ONNX** vehicle re-identification and license-plate recognition, **LangGraph** reasoning over **Groq**, and **PostgreSQL** (or SQLite locally) for persistence.

---

## Enterprise analytics gallery

High-level module visuals (marketing assets in `assets/`).

### Revenue & monetization

Occupancy-aware pricing, trend views, and localized earnings presentation.

![Revenue Analytics](assets/revenue_analytics.png)

### Enforcement & policy

Policy-driven violations, challans, and settlement-oriented workflows.

![Violation Hub](assets/violation_hub.png)

---

## System architecture

### Topology

```mermaid
graph TD
    subgraph Edge ["Edge node"]
        Cam[Camera / MOCK] --> SB[Scene builder]
        SB --> IE[Identity: Re-ID + ALPR]
        SB --> SE[Slot engine]
        IE & SE --> SB
    end

    subgraph Cloud ["Cloud core"]
        SB --> API[FastAPI]
        API --> RS[Revenue & pricing]
        API --> BR[Brain: LangGraph]
        API --> BI[Billing & AR]
        RS & BR & BI --> DB[(Postgres / SQLite)]
    end

    subgraph UI ["Operations UI"]
        API --> Dash[React + Vite]
    end
```

### Revenue & enforcement (conceptual)

```mermaid
sequenceDiagram
    participant E as Edge
    participant C as Cloud API
    participant R as Revenue
    participant T as Enforcement / tickets

    E->>C: Scene telemetry (identity, dwell, slots)
    C->>R: Pricing inputs
    R-->>C: Rates & surge factors
    alt Policy violation
        C->>T: Ticket / challan record
        T-->>C: Persisted outcome
    end
    C-->>E: Guidance & state sync
```

---

## Repository layout

| Path | Role |
|------|------|
| `cloud/api/` | FastAPI application: scenes, telemetry, analytics, revenue, reservations, **billing** |
| `cloud/api/billing_service.py` | Invoices, payments, parking sessions, AR-style summaries |
| `brain/` | LangGraph + Groq (`build_graph`) |
| `edge/` | Scene loop, YOLO detection, slot geometry, **identity** (ONNX or simulated / torch) |
| `edge/onnx_identity.py` | ONNX Runtime: OSNet Re-ID + LPRNet |
| `edge/plate_pipeline.py` | MNet plate detector + perspective warp (production-style ALPR chip) |
| `edge/models/` | Downloaded weights (YOLO / ONNX); **not** committed by default |
| `ui/` | Vite + React dashboard (`npm run dev` / `npm run build`) |
| `docker/` | `Dockerfile.api`, `Dockerfile.edge`, `Dockerfile.ui`, `nginx-ui.conf` (proxies `/api` to the API) |
| `download_models.py` | YOLO weights + ONNX bundles (Re-ID, LPRNet, MNet) into `edge/` and `edge/models/` |
| `infra/helm/` | Kubernetes Helm chart |
| `tests/` | Pytest: API, billing, brain, edge slot/scene, stack contract, optional live Groq smoke |

**Dependency entry points:** root **`requirements.txt`** (full stack including edge CV). **`cloud/api/requirements.txt`** targets the API Docker image. **`pyproject.toml`** names the `parksight-ai` package (`cloud*`, `edge*`, `brain*`) for editable installs.

---

## Capabilities (current)

### Revenue, enforcement, and billing

- **Dynamic pricing**: Occupancy-linked multipliers and policy hooks used by `/system/process` and revenue endpoints.
- **Enforcement**: Violation and ticketing flows surfaced in analytics and UI.
- **Billing & accounts receivable**: REST routes under `/billing/*` (invoices, payments, sessions, summaries) backed by SQLAlchemy models in the API layer; UI section for Billing & AR.

### Spatial & guidance

- Slot polygons (Shapely), scene construction from detections, pathfinding and broadcast-style messaging in API responses.

### Identity & ALPR

| Mode | When | Notes |
|------|------|--------|
| **ONNX (recommended)** | `PARKSIGHT_IDENTITY_MODE=auto` and `edge/models/vehicle_reid_osnet.onnx` present | OSNet-style **512-D** embeddings; **MNet** (`mnet_plate.onnx`) for detect + warp when available, then **LPRNet** (`lprnet.onnx`); ROI resize fallback if no plate chip. |
| **Torch** | `PARKSIGHT_IDENTITY_MODE=torch` | ResNet18 embeddings; optional **EasyOCR** via `ALPR_EASYOCR=1`. |
| **Simulated** | No ONNX weights, or explicit `simulated` | Deterministic demo vectors for development. |

Weights: run **`python download_models.py`** from the repo root (YOLO + ONNX files into `edge/` and `edge/models/`). In Docker Compose, mount **`parksight-models`** to `/app/edge/models` so ONNX files survive container rebuilds.

---

## Technology stack

- **Vision**: Ultralytics YOLO11 (and optional YOLOv8 fallback weights), OpenCV headless, Shapely.
- **ONNX inference**: `onnxruntime` for Re-ID and LPR (CPU execution provider by default in code paths).
- **Brain**: LangGraph + **langchain-groq** (default model family: Llama 3.3 on Groq). Without `GROQ_API_KEY`, the API uses deterministic fallbacks where implemented.
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.x, `uvicorn`.
- **Data**: SQLite via `DATABASE_URL` for local dev; **PostgreSQL 15** in Compose for the `api` service.
- **UI**: React 18, Vite 4, Framer Motion, Lucide; dev server proxies `/api` → `http://localhost:8000`; production UI image uses **nginx** per `docker/nginx-ui.conf`.

---

## Prerequisites

- **Python** 3.9+ (3.10+ recommended; Dockerfiles use 3.10)
- **Node.js** 18+ for the UI
- **Docker** + Docker Compose (optional, for full stack)

---

## Environment variables

Create a **`.env`** at the repository root (Compose reads it for substitution) or export variables in your shell.

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Enables Groq-backed LangGraph paths on `POST /system/process`. Omit for offline operation; one pytest case calls the live API when this key **and** network are available. |
| `DATABASE_URL` | SQLAlchemy URL. Example: `sqlite:///./parksight.db` locally; Compose sets Postgres for `api`. |
| `API_URL` | Edge ingest URL (default `http://localhost:8000/system/process`). In Compose: `http://api:8000/system/process`. |
| `CAMERA_SOURCE` | Edge input: `MOCK` (default), or a video file path (e.g. `.mp4`). Optional `edge/configs/kaggle_config.json` for slot geometry. |
| `PARKSIGHT_IDENTITY_MODE` | `auto` (default), `onnx`, `torch`, or `simulated`. See identity table above. |
| `PARKSIGHT_IDENTITY_IMAGENET` | `1` to use pretrained ImageNet weights for ResNet18 (torch path only). |
| `ALPR_EASYOCR` | `1` to attempt EasyOCR on the torch path (extra dependency). |

---

## Quick start (local)

### 1. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .   # optional: editable package install
```

Run Python modules from the **repository root** so `cloud`, `edge`, and `brain` resolve.

### 2. Models (optional but recommended for real CV)

```bash
python download_models.py
```

### 3. `.env` (minimal local)

```env
GROQ_API_KEY=your_key_here   # optional
DATABASE_URL=sqlite:///./parksight.db
```

### 4. Run processes

```bash
# Terminal 1: API
python3 -m cloud.api.main

# Terminal 2: Edge (posts scenes to the API)
python3 -m edge.main

# Terminal 3: UI — http://localhost:5173 (Vite proxies /api → :8000)
cd ui && npm install && npm run dev
```

- **API**: `http://localhost:8000` — `GET /health`, `POST /system/process`, plus analytics, revenue, and **`/billing/*`** routes.
- **UI**: `http://localhost:5173`

`POST /system/process` returns structured JSON including guidance, revenue context, and violations, depending on configuration and data.

---

## Docker Compose

Full stack: **Postgres**, **API**, **edge worker**, **UI** (nginx on host **3000** → app on **80** inside the container).

```bash
export GROQ_API_KEY=your_key_here   # optional
docker compose up --build
```

| Service | Host ports | Notes |
|---------|------------|--------|
| `db` | 5432 | Postgres; user/password/database `parksight` / `parksight` / `parksight_db` |
| `api` | 8000 | FastAPI |
| `ui` | 3000 | Static build + **`/api` → API** via `docker/nginx-ui.conf` |
| `edge` | — | `python -m edge.main`; image installs the full edge stack (**first build can be lengthy** due to PyTorch / Ultralytics). |

**Volumes:** `parksight-telemetry` (API telemetry dir), **`parksight-models`** → `/app/edge/models` (persist ONNX weights across rebuilds). Populate models inside the volume or copy from a host run of `download_models.py`.

```bash
CAMERA_SOURCE=MOCK docker compose up
```

Kubernetes assets: **`infra/helm/`**.

---

## Development and verification

```bash
# Python (from repo root, venv active)
pytest tests/ -q

# UI production bundle
cd ui && npm ci && npm run build
```

**Compose file validation:** `docker compose config -q`

**Notes:**

- Prefer running tests with **network enabled** if `GROQ_API_KEY` is set, so the optional live Groq smoke test can reach the API.
- Some tests are **skipped** when optional ONNX files are absent; CI or local runs with `edge/models/` populated exercise the full identity path.

---

## API surface (non-exhaustive)

| Area | Examples |
|------|-----------|
| Core | `GET /health`, `POST /system/process` |
| Telemetry & analytics | `GET /telemetry/summary`, heatmap, violations, forecast |
| Revenue | `GET /revenue/summary`, `GET /revenue/tickets` |
| Reservations | `POST /reserve`, `GET /reservations/active` |
| Billing | `GET /billing/summary`, `GET/POST /billing/invoices`, payments, sessions |

Refer to `cloud/api/main.py` for the authoritative route list and request bodies.

---

## Roadmap

- [x] Identity: ALPR (LPRNet + optional MNet warp) and cross-camera Re-ID (ONNX OSNet path).
- [x] Spatial: overlays, guidance, and facility messaging in API/UI.
- [x] Predictive & reservations: forecasting and reservation endpoints.
- [x] Monetization: dynamic pricing and enforcement ticketing.
- [x] Billing & AR: invoices, payments, parking sessions, dashboard hooks.
- [ ] Multi-site clustering, mobile payments, and deeper payment-provider integrations (V5+).

---

## License and third-party weights

ONNX sample weights are downloaded from public GitHub repositories (see URLs in `download_models.py`). Verify license terms for your deployment before redistributing weights or derived models.
