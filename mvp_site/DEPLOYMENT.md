# WorldArchitect.AI Deployment Guide

This document covers production deployment configuration for WorldArchitect.AI, focusing on concurrency optimization and performance tuning.

## Table of Contents

- [Gunicorn Concurrency Configuration](#gunicorn-concurrency-configuration)
- [Environment Variables](#environment-variables)
- [Performance Tuning](#performance-tuning)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Gunicorn Concurrency Configuration

### Overview

WorldArchitect.AI uses **Gunicorn with gthread workers** for production deployment. This configuration is optimized for I/O-bound workloads (MCP server, Firestore, Gemini API calls).

**Performance Characteristics:**
- **Default**: 1 worker (sync) = 1 concurrent request
- **Production**: (2×CPU+1) workers × 4 threads = 12+ concurrent requests on 1 CPU

### Configuration File

All Gunicorn settings are defined in `gunicorn.conf.py`:

```python
# Worker configuration
workers = (2 * CPU_count) + 1
worker_class = "gthread"
threads = 4

# Calculated concurrency
max_concurrent_requests = workers × threads
# Example: 3 workers × 4 threads = 12 concurrent requests
```

### Worker Formula Explained

**Formula:** `workers = (2 × CPU_cores) + 1`

**Rationale:**
- One worker handles I/O while others process
- +1 ensures continuous request handling during worker restarts
- Optimal for I/O-bound applications (API calls, database queries)

**Examples:**
- **1 CPU**: 3 workers × 4 threads = **12 concurrent requests**
- **2 CPU**: 5 workers × 4 threads = **20 concurrent requests**
- **4 CPU**: 9 workers × 4 threads = **36 concurrent requests**

## Environment Variables

### Core Configuration

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `GUNICORN_WORKERS` | `(2*CPU)+1` | Number of worker processes | `3` |
| `GUNICORN_THREADS` | `4` | Threads per worker | `4` |
| `GUNICORN_RELOAD` | `False` | Auto-reload on code changes (dev only) | `True` |

### Setting Environment Variables

#### Docker / Docker Compose

```yaml
# docker-compose.yml
services:
  worldarchitect:
    environment:
      - GUNICORN_WORKERS=5
      - GUNICORN_THREADS=4
```

#### Kubernetes

```yaml
# deployment.yaml
spec:
  containers:
  - name: worldarchitect
    env:
    - name: GUNICORN_WORKERS
      value: "5"
    - name: GUNICORN_THREADS
      value: "4"
```

#### Google Cloud Run

```bash
gcloud run deploy worldarchitect-ai \
  --set-env-vars GUNICORN_WORKERS=5,GUNICORN_THREADS=4
```

#### Render

1. Go to service settings
2. Navigate to "Environment" tab
3. Add variables:
   - `GUNICORN_WORKERS` = `5`
   - `GUNICORN_THREADS` = `4`

## Performance Tuning

### Determining Optimal Worker Count

**Step 1: Start with Formula**
```bash
GUNICORN_WORKERS=$((2 * $(nproc) + 1))
```

**Step 2: Load Test**
Use tools like `ab`, `wrk`, or `locust` to simulate traffic:

```bash
# Apache Bench example
ab -n 1000 -c 50 https://your-domain.com/api/campaigns

# Monitor metrics:
# - Response time P95/P99
# - Throughput (requests/second)
# - Error rate
```

**Step 3: Monitor Resources**
```bash
# Check CPU usage per worker
ps aux | grep gunicorn

# Check memory usage
docker stats  # For containers
```

**Step 4: Adjust Based on Results**

| Symptom | Action |
|---------|--------|
| High CPU usage (>80%) | Reduce workers or add CPU |
| Low CPU usage (<50%) | Increase workers |
| High memory usage | Reduce workers or add RAM |
| Request queue building up | Increase workers/threads |
| Timeout errors | Check timeout setting (300s default) |

### Thread Count Tuning

**Guidelines:**
- **Light I/O workload**: 2-4 threads per worker
- **Heavy I/O workload**: 4-8 threads per worker
- **Very high concurrency**: Consider gevent workers instead

**Warning:** Too many threads increases context switching overhead.

### Memory Considerations

**Formula for Memory Planning:**
```
Total Memory = Base Memory + (Workers × Worker Memory)

Where:
- Base Memory: ~200MB (Flask app + libraries)
- Worker Memory: ~150-250MB per worker (varies with workload)

Example (3 workers):
Total = 200MB + (3 × 200MB) = 800MB
Recommendation: Allocate 1GB+ for safety margin
```

### Timeout Configuration

Current setting: **300 seconds (5 minutes)**

**Adjust if:**
- Gemini API calls consistently timeout → Increase timeout
- Workers killed during long operations → Increase timeout
- Slow clients abuse resources → Decrease timeout

```python
# In gunicorn.conf.py
timeout = 300  # Adjust as needed
graceful_timeout = 30  # Time for graceful shutdown
```

## Monitoring

### Health Check Endpoint

Monitor service health at `/health`:

```bash
curl https://your-domain.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "worldarchitect-ai",
  "timestamp": "2025-11-17T12:34:56.789Z",
  "concurrency": {
    "workers": 5,
    "threads": 4,
    "max_concurrent_requests": 20
  },
  "mcp_client": {
    "configured": true,
    "base_url": "http://localhost:8000",
    "skip_http": false
  }
}
```

### Key Metrics to Track

1. **Request Queue Length** - Should stay near 0
2. **Worker Busy %** - Should be <80% on average
3. **Response Time** - Track P50, P95, P99
4. **Memory per Worker** - Watch for memory leaks
5. **Worker Restart Rate** - Should be gradual, not sudden

### Logging

Gunicorn access logs include request duration:

```
192.168.1.1 - - [17/Nov/2025:12:34:56] "POST /api/campaigns HTTP/1.1" 200 1234 "-" "Mozilla/5.0" 2500000
                                                                                              ^^^^^^^
                                                                                           Duration (μs)
                                                                                           2.5 seconds
```

**Convert microseconds to seconds:** `duration_μs / 1,000,000`

## Troubleshooting

### Common Issues

#### Workers Timing Out

**Symptom:** Workers killed with `SIGTERM` or `SIGKILL`

**Solutions:**
1. Increase timeout: `timeout = 600` in `gunicorn.conf.py`
2. Check for infinite loops in code
3. Optimize slow database queries
4. Add caching for expensive operations

#### Out of Memory

**Symptom:** Workers crash with OOM errors

**Solutions:**
1. Reduce worker count
2. Add memory limits per worker
3. Check for memory leaks (use memory profiler)
4. Implement worker restart policy:
   ```python
   max_requests = 1000  # Restart after 1000 requests
   max_requests_jitter = 50
   ```

#### Poor Concurrency

**Symptom:** Requests queuing up, slow response times

**Solutions:**
1. Increase workers: `GUNICORN_WORKERS=7`
2. Increase threads: `GUNICORN_THREADS=6`
3. Check MCP server capacity
4. Consider switching to gevent workers for extreme concurrency

#### Connection Pool Exhausted

**Symptom:** `requests.exceptions.ConnectionError`

**Solution:** Connection pooling is configured in `mcp_client.py`:
```python
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,  # Increase if needed
    pool_maxsize=20,      # Increase if needed
    max_retries=3,
    pool_block=False
)
```

### Testing Configuration Changes

**Local Testing:**

```bash
# Build Docker image
docker build -t worldarchitect-test ./mvp_site

# Run with custom config
docker run -p 8080:8080 \
  -e GUNICORN_WORKERS=5 \
  -e GUNICORN_THREADS=4 \
  worldarchitect-test

# Load test
ab -n 1000 -c 20 http://localhost:8080/health
```

**Staging Testing:**

1. Deploy to staging with new configuration
2. Run production-like load tests
3. Monitor for 24-48 hours
4. Check error rates and response times
5. Gradual rollout to production

## Advanced: Alternative Worker Types

### Option 2: Gevent Workers (High Concurrency)

For applications requiring >100 concurrent connections:

**Requirements:**
```txt
# Add to requirements.txt
gevent>=24.2.1
```

**Configuration:**
```python
# In gunicorn.conf.py
worker_class = "gevent"
worker_connections = 1000  # Each worker handles 1000 connections

def post_fork(server, worker):
    from gevent import monkey
    monkey.patch_all()
```

**Performance:**
- 3 workers × 1000 connections = **3,000 concurrent requests**
- Best for I/O-bound workloads
- Requires careful testing with Firebase/Firestore SDK

**Trade-offs:**
- ✅ Massive concurrency improvement
- ✅ Low memory overhead
- ⚠️ Requires monkey patching (potential compatibility issues)
- ⚠️ More complex debugging

### Option 3: ASGI + Uvicorn (Modern Async)

For native async/await support:

**Requirements:**
```txt
uvicorn[standard]>=0.27.0
asgiref>=3.7.0
```

**Trade-offs:**
- ✅ Modern async architecture
- ✅ Better async integration
- ⚠️ Requires WSGI→ASGI wrapper
- ⚠️ More code changes for full benefit

**Note:** Current gthread configuration is recommended for most use cases.

## Production Checklist

Before deploying:

- [ ] Set `GUNICORN_WORKERS` based on CPU count
- [ ] Set `GUNICORN_THREADS` to 4 (or tuned value)
- [ ] Verify timeout is sufficient (300s default)
- [ ] Test with production-like load
- [ ] Monitor `/health` endpoint
- [ ] Set up logging aggregation
- [ ] Configure alerts for high error rates
- [ ] Document rollback procedure
- [ ] Perform gradual rollout

## References

- [Gunicorn Design Documentation](https://docs.gunicorn.org/en/stable/design.html)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/stable/deploying/)
- [WorldArchitect.AI README](./README.md)
