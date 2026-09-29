"""Python-only submission entry point for public M1-2 deployment checks.

Run from the repository root:
    python python_submission/run_public_check.py

This entry point runs the full public verification implemented in
``backend/scripts/verify_deployment.py``. It only sends read-only requests:
Vercel, Render health/warmup/docs, public data summary, and CORS.
"""

from __future__ import annotations

import runpy
from pathlib import Path


VERIFIER = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "verify_deployment.py"


def main() -> None:
    """Run the maintained public-deployment verifier as a standalone Python file."""

    runpy.run_path(str(VERIFIER), run_name="__main__")


if __name__ == "__main__":
    main()
