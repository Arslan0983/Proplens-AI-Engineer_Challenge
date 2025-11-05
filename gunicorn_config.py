"""Gunicorn configuration for production deployment."""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 2  # Keep it low for free tier
worker_class = "sync"

# Timeout - increased for heavy initialization
timeout = 120  # 2 minutes for first request (loading models)
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "proplens-ai-agent"

# Preload app (disabled to avoid timeout during startup)
preload_app = False
