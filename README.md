# ParkSight AI: Enterprise Parking Guidance & Analytics

[![Production Ready](https://img.shields.io/badge/Status-Production--Ready-green.svg)]()
[![AI Powered](https://img.shields.io/badge/AI-YOLO11%20%2B%20LangGraph-blue.svg)]()

ParkSight AI is an enterprise-grade, edge-first intelligent parking guidance system designed to rival professional solutions like Parquery. It combines high-performance Computer Vision (CV) with LLM-based explainability and robust cloud analytics.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Edge ["Edge (Camera / Jetson)"]
        Cam[Camera Service] --> CV[CV Inference (YOLO11)]
        CV --> SE[Slot Engine (Shapely)]
        SE --> SB[Scene Builder]
        GE[Guidance Engine] -.-> SB
    end

    subgraph Cloud ["Cloud Control Plane"]
        SB --> API[Telemetry / API]
        API --> DB[(In-Memory History)]
        DB --> AS[Analytics Service]
        DB --> RG[Report Generator]
        API --> LG[LangGraph Orchestrator]
    end

    subgraph Frontend ["User Interface"]
        LG --> UI[React Dashboard]
        RG --> UI
    end
```

---

## 🚀 Core Functionalities (Current State)

### 1. Real-time Occupancy Detection (Functional)
- **Engine**: Uses **Shapely** polygons for high-precision slot detection.
- **Perspective Correction**: Integrated **3x3 Homography Matrix** for top-down coordinate mapping.
- **Overstay Tracking**: Tracks `occupancy_duration` for every vehicle in real-time.

### 2. Anomaly & Hazard Detection (Functional)
- **Safety Hazards**: Detects pedestrians and bicycles in car-only zones.
- **Policy Violations**: Automated alerts for **Overstay Violations** and **Blocked Infrastructure** (e.g., Fire Hydrants).
- **Rule-based Engine**: Moves beyond simulation to deterministic violation detection.

### 3. Automated Parking Guidance (Functional)
- **Deterministic Steering**: Calculates distances and angles using top-down geometry.
- **LLM Advisory**: **LangGraph** provides context-aware instructions (e.g., "Slot 3 is free, watch out for the pedestrian nearby").

### 4. Smart Parking Management (Functional)
- **Peak Hour Analysis**: Identifies usage frequency by the hour to optimize lot operations.
- **Usage Trends**: Historical tracking of average occupancy and overcrowding.
- **Violation Reporting**: Categorized alerts for management (Safety vs. Policy).

---

## 🛠️ Tech Stack
- **Edge**: Python, Ultralytics YOLOv11, OpenCV, Shapely.
- **Cloud**: FastAPI, LangGraph, LangChain, Groq (Llama 3).
- **Orchestration**: Docker, Docker Compose.

---

## 🚦 Getting Started

### Local Development (Docker)
```bash
docker compose up --build
```

### Environment Setup
Create a `.env` file from `.env.example`:
```bash
GROQ_API_KEY=your_key_here
CAMERA_SOURCE=MOCK # Use RTSP/CSI URL for real hardware
```

---

## 🗺️ Roadmap

### ✅ Completed (V1.0)
- [x] **Real CV Integration**: Robust YOLOv11 filtering for safety objects.
- [x] **Advanced Slot Logic**: Shapely Integration with Homography calibration.
- [x] **Smart Orchestration**: LangGraph conditional routing for URGENT alerts.
- [x] **Analytics Module**: Peak hour and violation reporting logic.

### 🟡 In-Progress (V1.1)
- [ ] **Database Persistence**: Move telemetry tracking to SQLite/PostgreSQL.
- [ ] **Multi-Camera Support**: Orchestrating multiple edge devices in one dashboard.
- [ ] **AR Guidance**: UI overlay for mobile-first parking guidance.

### 📈 Future (V2.0)
- [ ] **ALPR**: Automatic License Plate Recognition.
- [ ] **Re-ID**: Tracking specific vehicles across multiple camera perspectives.
- [ ] **Edge Fallback**: Offline mode for edge-only operations during cloud outages.
