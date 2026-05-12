# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app, run_startup_checks  # noqa: E402


if __name__ == "__main__":
    run_startup_checks()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
