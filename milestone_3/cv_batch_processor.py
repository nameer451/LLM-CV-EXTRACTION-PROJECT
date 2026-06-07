"""
Milestone 3 CV batch processor.

The mature parser lives in Milestone 2, so this wrapper reuses it instead of
forking another extraction implementation. It keeps the Milestone 3 folder
self-runnable by adding the project root to sys.path.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from milestone_2.cv_batch_processor import (  # noqa: E402,F401
    CVBatchProcessor,
    parse_cv_text_to_structured,
)


if __name__ == "__main__":
    processor = CVBatchProcessor("uploads", "outputs")
    processor.process_folder()
    processor.save_results()
    processor.generate_report()
