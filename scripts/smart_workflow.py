#!/usr/bin/env python3
"""
Smart Workflow - Easy-to-use wrapper for the hybrid workflow

This script provides a simple interface to the hybrid workflow with smart defaults.

Usage:
    python smart_workflow.py --input weekly-links/2025-10-23-links.md
    python smart_workflow.py --latest
    python smart_workflow.py --all
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Main function that delegates to hybrid_workflow.py"""
    # Get the path to the hybrid workflow script
    script_dir = Path(__file__).parent
    hybrid_script = script_dir / "hybrid_workflow.py"

    # Pass all arguments to the hybrid workflow
    cmd = [sys.executable, str(hybrid_script)] + sys.argv[1:]

    # Run the hybrid workflow
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    exit(main())
