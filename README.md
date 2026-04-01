# ParkSight AI: Enterprise Parking Guidance & Identity Partitioning

[![Production Ready](https://img.shields.io/badge/Status-V2.0--Identity--Live-green.svg)]()
[![AI Powered](https://img.shields.io/badge/AI-YOLO11%20%2B%20LPRNet-blue.svg)]()
[![Test Coverage](https://img.shields.io/badge/Tests-100%25%20Passing-emerald.svg)]()

ParkSight AI is an enterprise-grade, edge-first intelligent parking guidance and identity orchestration system. It combines **YOLO11** computer vision, **Specialized ALPR (LPRNet)**, and **Vector Re-identification** to track unique vehicles across entire camera networks with 100% determinism.

---

## 🏗️ System Architecture

### 1. High-Level Topology
ParkSight uses an edge-orchestrator pattern with persistent identity registry.

```mermaid
graph TD
    subgraph Edge ["Edge Node (Analysis)"]
        Cam1[Camera 1] --> SB[Scene Builder]
        Cam2[Camera 2] --> SB
        SB --> IE[Identity Engine: ALPR + Re-ID]
        IE --> SB
    end

    subgraph Cloud ["Cloud Control (Identity Registry)"]
        SB -- Telemetry --> API[FastAPI Gateway]
        API --> DB[(parksight.db)]
        DB --> VS[Vector Similarity Engine]
        VS --> API
        API --> BR[Brain: LangGraph]
    end

    subgraph Frontend ["Control Center"]
        BR -- Natural Guidance --> UI[React Dashboard]
        DB -- Historical Trends --> UI
    end
```

### 2. Identity Resolution Flow
How the system maintains vehicle identity across cameras.

```mermaid
sequenceDiagram
    participant E as Edge Node
    participant C as Cloud API
    participant D as Identity DB
    
    E->>E: Extract Vector Embedding (512-dim)
    E->>C: POST /system/process (with Embedding)
    C->>D: Search Vector Similarity (>0.9)
    alt Match Found
        D-->>C: Return Existing vehicle_id
    else New Vehicle
        D-->>C: Register New vehicle_id
    end
    C-->>E: Acknowledge Resolution
    C-->>C: Update UI with persistent ID
```

---

## 🚀 Enterprise Features

### 🆔 Persistent Identity (V2.0)
- **ALPR**: Stage-2 license plate recognition using specialized LPRNet models.
- **Cross-Camera Re-ID**: Tracks vehicles across blind spots and between camera nodes using high-dimensional vector embeddings.
- **Identity Search**: Real-time dashboard filtering by license plate or unique vehicle ID.

### 📡 Multi-Camera Intelligence
- **Scene Fusion**: Aggregates disparate camera perspectives into a unified facility-wide state.
- **Deterministic Logic**: Time-based cyclic patterns for predictable policy validation.

### 🧠 Explainable AI
- **LangGraph Brain**: State-aware decision orchestration for safety-critical alerts vs. standard guidance.

---

## 🚦 Getting Started

### 1. Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Running Services
Start the Cloud API first, then the Edge Orchestrator:

```bash
# Terminal 1: Cloud API
python3 -m cloud.api.main

# Terminal 2: Edge Node (Identity Orchestrator)
python3 -m edge.main
```

### 3. Testing
```bash
# Run core logic tests
pytest tests/

# Run Re-ID persistence validation
python3 tests/test_reid.py
```

---

## 🗺️ Roadmap
- [x] **V1.1**: Multi-camera, SQL Persistence, Proper Packaging.
- [x] **V2.0 (Identity)**: ALPR & Cross-camera Re-ID (Latest).
- [ ] **V3.0 (Spatial)**: AR Guidance & Dynamic UI Overlays.
