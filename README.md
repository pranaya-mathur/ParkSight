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
- edge/
- cloud/
- langgraph/
- infra/helm/
- docker/
