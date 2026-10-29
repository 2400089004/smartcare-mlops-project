# SmartCare MLOps — Full-stack educational healthcare monitoring prototype

A polished Flask dashboard + API + SQLite demo history + ML training scaffold + Docker + Prometheus + Grafana + Kubernetes starter.

**Safety and privacy:** educational prototype only, not a medical device or diagnostic tool. Do not use outputs for medical decisions. Use synthetic/demo data only; do not enter patient-identifiable or real clinical data. Measurement flags are illustrative and not a complete triage system. For concerning symptoms seek professional care; severe/sudden symptoms warrant emergency services regardless of app output.

## Architecture
- Frontend: responsive HTML/CSS/JavaScript dashboard with live API data and chart
- Backend: Flask REST API, validation, history endpoints, Prometheus metrics
- Storage: SQLite for local demo measurement history (not production-ready for multi-replica use)
- ML: Scikit-learn pipeline + MLflow training scaffold for UCI Heart Disease dataset
- Containers: Docker and Docker Compose
- Observability: Prometheus scrape config and pre-provisioned Grafana dashboard
- Deployment: Kubernetes Deployment and Service starter
- CI: GitHub Actions tests + Docker build

## Run locally
Python 3.11+ and Docker/Compose are recommended.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python app.py
```
Open `http://localhost:3000`.

## Run the complete stack with monitoring
```bash
cp .env.example .env
# Edit .env and set a unique GRAFANA_ADMIN_PASSWORD
docker compose up --build -d
docker compose ps
```
- SmartCare frontend/API: http://localhost:3000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (username `admin`; password from `.env`)
- Metrics: http://localhost:3000/metrics

If deploying on a remote EC2 instance, do not expose Prometheus/Grafana publicly without access controls. Prefer SSH tunnels or private networking and a secured reverse proxy. Security groups should expose only intended ports. For quick SSH tunnels from your local computer:
```bash
ssh -i your-key.pem -L 3000:localhost:3000 -L 3001:localhost:3001 -L 9090:localhost:9090 ubuntu@YOUR_EC2_PUBLIC_IP
```
Then open the localhost URLs locally.

## API endpoints
- `GET /` — dashboard
- `GET /health` — liveness
- `GET /ready` — readiness/model availability
- `GET /metrics` — Prometheus metrics
- `GET /api/v1/measurements?limit=20` — recent demo records
- `POST /api/v1/measurements/check` — validate and save measurements
- `POST /api/v1/models/heart-risk` — trained educational model inference (requires a trained model artifact)

Example:
```bash
curl -X POST http://localhost:3000/api/v1/measurements/check \
  -H 'Content-Type: application/json' \
  -d '{"heart_rate_bpm":72,"spo2_percent":98,"temperature_c":36.8}'
```

## Included dataset and ML training
The project now includes the processed Cleveland subset of the UCI Heart Disease dataset in `data/heart.csv` (303 rows, 13 features, target column `num`). The original `processed.cleveland.data` file and a preparation script are also included.

Source: https://archive.ics.uci.edu/dataset/45/heart+disease

Install dependencies and train from the project root:
```bash
python -m pip install -r requirements.txt
python ml/train_heart_model.py
```
The training script defaults to the included `data/heart.csv`, converts `num` into a binary educational target (0 vs values greater than 0), imputes missing feature values within the training pipeline, evaluates a held-out test split, logs metrics to MLflow, and writes `artifacts/heart_model.joblib` plus `artifacts/heart_metrics.json`.

To regenerate the CSV from the included original data file:
```bash
python data/prepare_heart.py
```
After training, restart the Flask app and use the **Heart disease model experiment** form on the dashboard to test the `/api/v1/models/heart-risk` endpoint with invented/demo values. The form uses the original UCI feature codes.

The dataset is small and older; test-set metrics from it are not evidence of clinical performance. This project is an educational prototype only and must not be used for medical decisions. Do not submit real patient information to the demo. Only add separate diabetes/kidney models after selecting their own appropriate datasets, feature schemas, target definitions, and evaluation methods; one model cannot detect every disease.

## Prometheus and Grafana
Compose starts both services and provisions a Prometheus datasource and a dashboard.
Prometheus scrape config is in `monitoring/prometheus.yml`.
Dashboard JSON is in `monitoring/grafana/dashboards/smartcare-overview.json`.
Metrics include request counts, request latency histograms, and submitted measurement check totals.

## GitHub
```bash
git init
git add .
git commit -m "Build SmartCare full-stack MLOps prototype"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```
Never commit `.env`, credentials, real patient data, or downloaded datasets containing restricted data.

## AWS / ECR / EKS
1. Build and test locally first.
2. Create ECR repository and push a versioned image.
3. Replace the image in `k8s/deployment.yaml` with your ECR image URI.
4. Configure EKS IAM, namespace, secret handling, storage, service discovery and network policies.
5. Apply `kubectl apply -f k8s/deployment.yaml`.
6. SQLite is not appropriate for multi-replica production. Move to managed PostgreSQL/MySQL with backups and migration before scaling replicas.
7. For Kubernetes Prometheus/Grafana, use a supported monitoring chart such as kube-prometheus-stack and configure ServiceMonitor/PodMonitor or scrape annotations consistently. Compose monitoring is for local/single-host learning.
8. Do not deploy real patient data until privacy, security, clinical validation and regulatory requirements have been reviewed.

## Next improvements
- Add authentication and role-based access before any multi-user use
- Replace SQLite with managed relational database for multi-replica deployments
- Add audit trail, CSRF protection, rate limiting, TLS, secret management and backup/restore tests
- Add dataset validation, model cards, calibration and subgroup evaluation
- Add model drift/data quality monitoring and a safe model approval/rollback workflow
