# File: backend/run_backend.py
# Description: Launcher script for running the FastAPI backend with Uvicorn

import sys
import os
import uvicorn

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)

