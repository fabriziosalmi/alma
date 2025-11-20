#!/usr/bin/env python3
"""
Quick start script to run the ALMA API server
"""
import sys
from pathlib import Path

import uvicorn

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def main():
    """Run the API server"""
    print("🚀 Starting ALMA Controller API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 ReDoc: http://localhost:8000/redoc")
    print("")

    uvicorn.run("aicdn.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    main()
