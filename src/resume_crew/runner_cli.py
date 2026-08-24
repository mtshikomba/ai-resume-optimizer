import sys
import json
from pathlib import Path
from resume_crew.runner import run_from_inputs


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: python -m resume_crew.runner_cli <path/to/inputs.json>")
        sys.exit(2)
    inputs_path = Path(argv[0])
    if not inputs_path.exists():
        print(f"Inputs file not found: {inputs_path}")
        sys.exit(1)
    print(f"Starting pipeline for {inputs_path}...", flush=True)
    result = run_from_inputs(str(inputs_path))
    print("Result:\n", flush=True)
    print(json.dumps(result, indent=2), flush=True)
    if result.get("status") != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
