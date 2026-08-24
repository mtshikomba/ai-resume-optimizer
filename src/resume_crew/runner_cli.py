import sys
import json
from pathlib import Path
from resume_crew.runner import run_from_inputs


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: python -m resume_crew.runner_cli <path/to/inputs.json> [--timeout SECONDS] [--poll POLL_SECONDS]")
        sys.exit(2)
    inputs_path = Path(argv[0])
    import argparse
    parser = argparse.ArgumentParser(prog="resume_crew.runner_cli")
    parser.add_argument("inputs", help="Path to inputs.json")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds to wait for artifacts (default 300)")
    parser.add_argument("--poll", type=float, default=2.0, help="Polling interval seconds (default 2.0)")
    args = parser.parse_args(argv)

    inputs_path = Path(args.inputs)
    if not inputs_path.exists():
        print(f"Inputs file not found: {inputs_path}")
        sys.exit(1)
    print(f"Starting pipeline for {inputs_path} with timeout={args.timeout}s, poll={args.poll}s...", flush=True)
    result = run_from_inputs(str(inputs_path), timeout_seconds=args.timeout, poll_interval=args.poll)
    print("Result:\n", flush=True)
    print(json.dumps(result, indent=2), flush=True)
    if result.get("status") != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
