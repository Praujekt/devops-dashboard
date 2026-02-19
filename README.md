# DevOps Dashboard

A Kubernetes-based F1 and system monitoring dashboard demonstrating modern DevOps practices including containerization, orchestration, observability, and air-gapped deployment strategies.

## Features

- **F1 Race Data**: Real-time next race info, latest race results, and driver championship standings
- **System Metrics**: Live CPU, memory, and disk usage monitoring with Prometheus integration
- **Kubernetes Monitoring**: Pod status, health checks, and cluster visibility
- **Multi-Environment Deployment**: Helm charts configured for dev, staging, and production
- **Air-Gapped Deployment**: Bundling strategy for offline/disconnected environments
- **Observability Stack**: Prometheus metrics collection and Grafana visualization
- **CI/CD Pipeline**: Automated testing, linting, and Docker image builds via GitHub Actions

## Tech Stack

**Application:**
- Python 3.9 with Flask
- OpenF1 API for Formula 1 data
- Prometheus client for metrics exposition

**Infrastructure:**
- Podman/Docker for containerization
- Kubernetes (minikube) for orchestration
- Helm for deployment management
- Prometheus for metrics collection
- Grafana for dashboards

## Quick Start

### Prerequisites
- Python 3.9+
- Podman or Docker
- Kubernetes cluster (minikube for local)
- Helm 3.x

### Local Development
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python src/api/app.py

# Access at http://localhost:5000
```

### Docker Build
```bash
# Build image
podman build -t localhost/devops-dashboard:latest .

# Run container
podman run -p 5000:5000 localhost/devops-dashboard:latest
```

### Kubernetes Deployment
```bash
# Start minikube
minikube start

# Load image into minikube
podman save localhost/devops-dashboard:latest -o dashboard.tar
minikube image load dashboard.tar
rm dashboard.tar

# Deploy with Helm (default environment)
helm install dashboard ./helm/dashboard

# Or deploy to specific environment
helm install dashboard ./helm/dashboard -f helm/dashboard/values-dev.yaml
helm install dashboard ./helm/dashboard -f helm/dashboard/values-staging.yaml
helm install dashboard ./helm/dashboard -f helm/dashboard/values-prod.yaml

# Access the dashboard
kubectl port-forward service/devops-dashboard 5000:5000
# Visit http://localhost:5000
```

## Observability Stack

### Deploy Prometheus
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus -f helm/prometheus-values.yaml

# Access Prometheus
kubectl port-forward service/prometheus-server 9090:80
# Visit http://localhost:9090
```

### Deploy Grafana
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install grafana grafana/grafana -f helm/grafana-values.yaml

# Access Grafana
kubectl port-forward service/grafana 3000:80
# Visit http://localhost:3000 (admin/admin)
```

## Air-Gapped Deployment

For deploying to environments without internet access:
```bash
# Create deployment bundle
./scripts/create-airgap-bundle.sh v6

# Transfer airgap-bundle/ directory to target system via USB/physical media

# On air-gapped system, deploy from bundle
cd airgap-bundle
./deploy.sh
```

The bundle includes:
- Container images (pre-pulled and saved as tar)
- Helm charts with all configurations
- Deployment scripts
- Manifest file with checksums

## API Endpoints

- `GET /` - Web dashboard UI
- `GET /health` - Health check endpoint
- `GET /api/metrics` - System metrics (JSON)
- `GET /metrics` - Prometheus metrics endpoint
- `GET /environment` - Current environment info
- `GET /f1/next-race` - Upcoming F1 race details
- `GET /f1/latest-race` - Most recent race results
- `GET /f1/driver-standings` - Current championship standings
- `GET /k8s/pods` - Kubernetes pod details

## Environment Configurations

Three environment profiles are available:

**Development** (`values-dev.yaml`):
- 1 replica
- Lower resource limits (200m CPU, 256Mi memory)
- NodePort on 30080

**Staging** (`values-staging.yaml`):
- 2 replicas
- Medium resources (300m CPU, 384Mi memory)
- NodePort on 30081

**Production** (`values-prod.yaml`):
- 3 replicas
- Higher resources (500m CPU, 512Mi memory)
- LoadBalancer service type

## CI/CD Pipeline

GitHub Actions automatically:
1. Lints Python code and Helm charts
2. Runs tests
3. Builds Docker images
4. Validates container health

Workflow runs on every push to `main` branch.

## Project Structure
```
.
├── src/
│   ├── api/          # Flask application
│   └── web/          # HTML dashboard
├── helm/
│   ├── dashboard/    # Helm chart for app
│   ├── prometheus-values.yaml
│   └── grafana-values.yaml
├── scripts/
│   └── create-airgap-bundle.sh
├── k8s/              # Raw Kubernetes manifests (legacy)
├── Dockerfile
├── requirements.txt
└── README.md
```

## Development Notes

- Uses Podman (Docker-compatible) for rootless containers
- RBAC configured for pod-level Kubernetes API access
- Prometheus metrics exposed on `/metrics` endpoint
- Multi-architecture builds supported (adjust Dockerfile as needed)

## License

MIT