# Local Grafana Setup

## Start Grafana
```bash
cd grafana/
docker-compose up -d
```

## Access Grafana
- URL: http://localhost:3000
- Username: admin
- Password: admin123

## Stop Grafana
```bash
docker-compose down
```

## Setup Data Source
1. Go to Configuration > Data Sources
2. Add Google Cloud Monitoring data source
3. Upload service account key file
4. Set default project ID

The dashboards will be automatically loaded from the provisioning configuration.
