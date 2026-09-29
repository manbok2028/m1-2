"""Python-only submission entry point for the M1-2 live Firestore CRUD proof.

Run from the repository root:
    python python_submission/run_firestore_crud_check.py

The maintained verifier creates one clearly labelled temporary public record,
checks create/read/update/delete against the deployed Firestore API, and
deletes that temporary record in a ``finally`` block.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


VERIFIER = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "verify_deployment.py"


def main() -> None:
    """Run the maintained verifier with its explicit temporary-CRUD option."""

    if "--verify-crud" not in sys.argv:
        sys.argv.insert(1, "--verify-crud")
    runpy.run_path(str(VERIFIER), run_name="__main__")


if __name__ == "__main__":
    main()
