# Grafana Cloud Setup for Claude Mistake Detection

## Step 1: Create Grafana Cloud Account

1. Go to [Grafana Cloud](https://grafana.com/products/cloud/)
2. Sign up for a free account
3. Create a new stack (choose region closest to you)
4. Note your Grafana URL (e.g., `https://yourname.grafana.net`)

## Step 2: Configure GCP Cloud Monitoring Data Source

1. In your Grafana Cloud dashboard, go to **Configuration > Data Sources**
2. Click **Add data source**
3. Select **Google Cloud Monitoring**
4. Configure the data source:
   - **Name**: `GCP Cloud Monitoring`
   - **Authentication Type**: `Google JWT File`
   - **Default Project**: Your GCP project ID
   - **Upload JWT File**: Upload your service account key file:
     ```
     ~/.config/gcp/mistake-detection-service-account.json
     ```

## Step 3: Import Dashboard

1. Go to **+ > Import** in your Grafana Cloud instance
2. Upload the dashboard JSON file:
   ```
   grafana/dashboards/claude-mistake-detection.json
   ```
3. Select your GCP data source when prompted
4. Click **Import**

## Step 4: Configure Alerts (Optional)

1. In the dashboard, click on any panel
2. Select **Edit**
3. Go to **Alert** tab
4. Configure alert rules for:
   - High mistake detection rate (> 5 per hour)
   - Auto-learn failures
   - High correlation scores (> 85%)

## Step 5: Verify Data Flow

1. Generate a mistake detection event by using sycophantic phrases
2. Check your dashboard after 1-2 minutes
3. Verify metrics appear in your panels

## Cost Monitoring

Your free tier includes:
- 10,000 series
- 3 users
- 14-day retention
- Basic alerting

Monitor usage at: Configuration > Usage Insights

## Troubleshooting

### No Data Appearing
1. Check GCP service account permissions
2. Verify project ID in data source configuration
3. Check GCP Cloud Monitoring API is enabled
4. Ensure metrics are being sent (check logs)

### Authentication Issues
1. Verify service account key file is valid
2. Check file permissions (should be 600)
3. Ensure service account has `monitoring.metricWriter` role

### Dashboard Issues
1. Re-import dashboard if panels are broken
2. Check data source UID matches dashboard configuration
3. Verify time range settings

## Support

For issues:
1. Check logs at `~/tmp/mistake-detection/mistake-detection.log`
2. Test GCP connection with the setup script
3. Verify dashboard queries in Grafana's Explore section
