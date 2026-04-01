# ParkSight AI (Production Repo)

## What we are building
An enterprise-grade, edge-first intelligent parking guidance system:
- CV (YOLO) for perception on edge devices
- Deterministic slot engine for decisions (authoritative)
- LangGraph-powered LLM for explanations (advisory only)
- Cloud control plane for orchestration, policy, telemetry
- CI/CD + Docker + Helm for production deployment

## Architecture
Edge:
- camera-service
- cv-inference (YOLO/TensorRT)
- slot-engine (polygon overlap)
- scene-builder (structured JSON)

Cloud:
- FastAPI APIs
- LangGraph orchestrator (LLM)
- policy-engine (rules/guardrails)
- telemetry

## Key Principles
- Deterministic > ML > LLM
- LLM cannot decide safety or slot state
- Edge-first latency, cloud for orchestration

## Run (local dev)
```bash
docker compose up --build
```

## Deploy (Kubernetes)
```bash
helm install parksight ./infra/helm
```

## CI/CD
GitHub → CodeBuild → ECR → EKS (+ Edge OTA)

## Folders
- docker/
---

## Roadmap

### Immediate (Priority 1)
- **Real CV Integration**: Replace mock perception with Ultralytics YOLO26-N + TensorRT export.
- **Advanced Slot Logic**: Upgrade `slot_engine` to true polygons (Shapely) with homography calibration.
- **Hardware Support**: Add RTSP/CSI camera stream support.
- **Smart Orchestration**: Expand LangGraph with conditional routing for urgent alerts.
- **Persistence**: Add Docker volumes and persistent telemetry logging.

### Medium-Term (Priority 2)
- **Scalability**: Multi-camera support and cross-camera tracking.
- **UI/UX**: AR guidance overlay and complex real-time occupancy heatmaps.
- **Observability**: Integration with Prometheus/Grafana for enterprise telemetry.
- **Quality**: Automated CI/CD pipelines via GitHub Actions.

### Advanced (Long-Term)
- **Re-ID**: Vehicle re-identification and license-plate linking.
- **Dynamic Mapping**: Learning slot locations automatically from historical patterns.
- **Resilience**: Edge-only fallback mode for cloud outages.
