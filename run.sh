#!/bin/bash

# Navigate to directory
cd ~/veiled-vector-core

# Activate Python Environment
source venv/bin/activate

# Run the Worker loop
# output logs to worker.log
echo "Starting Kaji Worker..."
nohup python3 src/orchestrator.py > worker.log 2>&1 &

echo "Worker is running in background. Tail logs with: tail -f worker.log"
