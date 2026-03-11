#!/usr/bin/env python3
"""
============================================================
  Skylink Delta AI Support — START SCRIPT
  Run this to launch the full website
============================================================
"""
import os, sys, subprocess, webbrowser, time

PORT = 8000
BASE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(BASE, "backend", "main.py")

print("""
╔══════════════════════════════════════════════╗
║   SKYLINK DELTA AI SUPPORT WEBSITE           ║
╠══════════════════════════════════════════════╣
║  Starting full-stack server...               ║
╚══════════════════════════════════════════════╝
""")

# Check Python version
if sys.version_info < (3, 8):
    print("❌ Python 3.8+ required. Download from python.org")
    sys.exit(1)

print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
print(f"✅ Starting server on http://localhost:{PORT}\n")

# Open browser after small delay
def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")

import threading
threading.Thread(target=open_browser, daemon=True).start()

# Run backend
os.chdir(BASE)
os.execv(sys.executable, [sys.executable, MAIN, str(PORT)])
