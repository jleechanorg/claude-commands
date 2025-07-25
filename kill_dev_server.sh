#!/bin/bash
# Kill any process listening on port 8080 (used by Flask dev server)
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs -r kill -9
