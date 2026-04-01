# ParkSight AI: Enterprise Parking Guidance & Analytics

[![Production Ready](https://img.shields.io/badge/Status-Production--Ready-green.svg)]()
[![AI Powered](https://img.shields.io/badge/AI-YOLO11%20%2B%20Brain-blue.svg)]()
[![Test Coverage](https://img.shields.io/badge/Tests-100%25%20Passing-emerald.svg)]()

ParkSight AI is an enterprise-grade, edge-first intelligent parking guidance system designed for high-scale environments. It combines **YOLO11** computer vision, **Shapely** geometry for precision slot detection, and a **LangGraph-based Brain** for explainable, safety-critical decision orchestration.

---

## 🏗️ System Architecture

### 1. High-Level Topology
ParkSight uses an edge-orchestrator pattern to minimize latency and maximize privacy.

```mermaid
graph TD
    subgraph Edge ["Edge Layer (Computer Vision)"]
        Cam1[Camera 01] --> SB[Scene Builder]
        Cam2[Camera 02] --> SB
        SB --> CV[CV Inference: YOLO11]
        CV --> SE[Slot Engine: Shapely]
        SE --> SB
    end

    subgraph Cloud ["Cloud Layer (Orchestration & Analytics)"]
        SB -- Telemetry Stream --> API[FastAPI Gateway]
        API --> DB[(Postgres / SQLite)]
        DB --> AS[Analytics Service]
        API --> BR[Brain: LangGraph]
    end

    subgraph Frontend ["User Layer"]
        BR -- Natural Guidance --> UI[React Dashboard]
        DB -- Historical Trends --> UI
    end
```

### 2. AI Decision Flow (Orchestration)
The system differentiates between **STANDARD** guidance and **URGENT** safety alerts using a state-aware decision tree.

```mermaid
stateDiagram-v2
    [*] --> Classify
    Classify --> Standard : No Hazards Detected
    Classify --> Urgent : Hazard/Policy Violation
    
    state Standard {
        [*] --> GenerateGuidance
        GenerateGuidance --> AdviseBestSlot
    }
    
    state Urgent {
        [*] --> TriggerAlert
        TriggerAlert --> BroadcastNotification
    }
    
    Standard --> [*]
    Urgent --> [*]
```

### 3. Telemetry Sequence
How a raw frame becomes a management insight.

```mermaid
sequenceDiagram
    participant E as Edge Node
    participant C as Cloud API
    participant D as Database
    participant U as UI
    
    E->>E: Capture Frame & Run YOLO11
    E->>E: Calculate Slot Occupancy (Shapely)
    E->>C: POST /system/process (Scene JSON)
    C->>D: Save Telemetry Event
    C->>C: Invoke LangGraph (Decision)
    C-->>E: Return Guidance Advice
    U->>C: GET /analytics/heatmap
    C->>D: Query Historical Data
    D-->>C: Result Set
    C-->>U: Heatmap JSON
```

---

## 🚀 Enterprise Features

### 📡 Multi-Camera Intelligence
- **Scene Fusion**: Supports multiple cameras per edge node with shared inference resources.
- **Deterministic Simulation**: V1.1 includes a time-based cyclic pattern for testing overstays and safety hazards without randomness.

### 🧠 Explainable AI
- **LangGraph Brain**: Uses a conditional state graph to route "URGENT" alerts (e.g., Pedestrian in Zone) separately from "STANDARD" guidance.
- **Natural Language Steering**: Provides high-quality instructions based on top-down Euclidean distance mapping.

### 📊 Persistent Analytics
- **SQL Backend**: Full **SQLAlchemy** integration for reliable, persistent historical data.
- **Heatmaps & Trends**: High-performance calculations for slot utilization and peak hour analysis.

---

## 🚦 Getting Started

### 1. Installation
The project is properly packaged. From the root directory:

```bash
# Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Running Services
Start the Cloud API first (requires `GROQ_API_KEY` for AI features):

```bash
# Cloud API
python3 -m cloud.api.main

# Edge Node (Simulated Multi-Camera)
python3 -m edge.scene_builder
```

### 3. Testing
Our enterprise-grade test suite ensures 100% logic validation.

```bash
pytest tests/
```

---

## 🗺️ Roadmap
- [x] **V1.1 (Production Ready)**: Multi-camera, SQL Persistence, Proper Packaging.
- [ ] **V1.2 (Spatial Awareness)**: Dynamic UI overlay for mobile-first parking navigation.
- [ ] **V2.0 (Identity)**: ALPR (License Plate Recognition) & Re-ID across camera nodes.
