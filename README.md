# DevOps Dashboard

A Kubernetes-based monitoring dashboard built with Python and Docker.

## Tech Stack
- Python 3.9
- Flask
- Podman/Docker
- Kubernetes (minikube)
- PostgreSQL
- Redis

## Getting Started

### Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/api/app.py
```

### Docker Build
```bash
podman build -t devops-dashboard:latest .
podman run -p 5000:5000 devops-dashboard:latest
```

### Kubernetes Deploy
```bash
kubectl apply -f k8s/
```
```