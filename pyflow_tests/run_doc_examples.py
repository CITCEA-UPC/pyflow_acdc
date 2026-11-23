"""Run all Python files in a doc_examples subfolder."""

from __future__ import annotations

import runpy
from pathlib import Path

DOC_EXAMPLES_DIR = Path(__file__).parent / "doc_examples"


def run_doc_examples(
    folder: str,
    *,
    skip_on_import_error: bool = False,
    skip_on_missing_data: bool = False,
) -> None:
    folder_path = DOC_EXAMPLES_DIR / folder
    if not folder_path.is_dir():
        raise FileNotFoundError(f"Missing doc_examples folder: {folder_path}")

    examples = sorted(folder_path.glob("*.py"))
    if not examples:
        raise FileNotFoundError(f"No examples in {folder_path}")

    for example in examples:
        try:
            runpy.run_path(str(example), run_name="__main__")
        except SystemExit as exc:
            if exc.code not in (0, None):
                raise
        except ImportError as exc:
            if not skip_on_import_error:
                raise
            print(f"  ~ Skipped {example.name}: {exc}")
        except FileNotFoundError as exc:
            if not skip_on_missing_data:
                raise
            print(f"  ~ Skipped {example.name}: {exc}")
