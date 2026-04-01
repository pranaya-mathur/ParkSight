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

## Functionalities & Use Cases

- **Real-time Occupancy Detection**: Monitoring live CCTV streams to display free vs. occupied parking spaces.
- **Obstacle & Hazard Detection**: Identifying pedestrians, vehicles, or road cones to assist in safety.
- **Automated Parking Guidance**: Providing intelligent navigation, interpreting camera data to assist with parallel or perpendicular parking.
- **Smart Parking Management**: Generating reports on parking lot utilization, peak hours, and identifying overcrowding.
- **Anomaly Detection**: Detecting unusual behavior or safety hazards and sending real-time alerts.

### Example Implementations
- **SmartPark-V11**: Utilizes YOLO11 and OpenCV for real-time tracking of parking occupancy.
- **LLM-Assisted Navigation**: AI system that translates scene descriptions into safe navigation paths.
- **Chatbot Parking Finder**: Integrates YOLO objects with a chatbot to guide users to available spots.

## Advantages Over Conventional Systems
- **Cost-Effective**: Replaces thousands of individual hardware sensors with fewer camera installations.
- **High Accuracy**: Deep learning techniques reaching 95% accuracy in daylight and 90% in low-light.
- **Contextual Understanding**: LLMs provide superior semantic understanding compared to traditional vision-only systems.

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
