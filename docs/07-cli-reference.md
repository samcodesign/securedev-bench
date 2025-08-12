# CLI Reference

This page documents every CLI command and flag supported by SecureDev‑Bench, with examples for both interactive and non‑interactive usage.

## Overview

- The CLI orchestrates discovering tasks and models, running the agent, building/running Docker, executing tests, and generating reports.
- Entry points:
  - Recommended: `python run_benchmark.py`
  - Advanced: `python -m securedev_bench.cli`

## Interactive Mode

Run without non‑interactive flags:

```bash
python run_benchmark.py
```

You will be prompted for:

- Models to test (multi‑select)
- Tasks to run (multi‑select)
- Verbose logging toggle
- Keep temporary directories toggle
- Save artifacts toggle (and output directory if enabled)

Outputs:

- Console summary table
- `benchmark_report.md` and `benchmark_report.json` in the project root
- Optional artifacts (see “Artifacts”)

## Non‑Interactive Mode

Use when automating or scripting runs. You must specify both `--tasks` and `--models`.

```bash
python run_benchmark.py -y \
  --tasks task-001-hardcoded-key task-005-insecure-deserialization \
  --models gemini:gemini-2.5-pro gemini:gemini-2.0-flash-thinking-exp \
  --verbose \
  --artifacts-dir artifacts
```

## Flags and Commands

- **--help, -h**: Show help and exit.
- **--list**: Print available tasks and models and exit.

- **--tasks <list>**: Space‑separated list of task IDs to run. Required with `-y`.
  - Example: `--tasks task-001-hardcoded-key task-005-insecure-deserialization`

- **--models <list>**: Space‑separated list of model specs to test. Required with `-y`.
  - Format: `provider:model_name`
  - Examples: `gemini:gemini-2.5-pro`, `gemini:gemini-2.0-flash-thinking-exp`

- **--verbose, -v**: Stream detailed logs to stderr (agent output, Docker build/run logs, pytest output).

- **--non-interactive, -y**: Run without prompts. Requires `--tasks` and `--models`.

- **--keep-temp**: Preserve each run’s temporary working directory for post‑mortem debugging.
  - Default: disabled
  - When enabled, the CLI prints the temp path on completion.

- **--artifacts-dir <path>**: Directory to save lightweight artifacts (see below).
  - Default: `artifacts`
  - Effective only if artifact saving is enabled.

- **--no-artifacts**: Disable saving artifacts.
  - Default: saving artifacts is enabled in non‑interactive runs
  - In interactive mode, you control this via a prompt.

## Artifacts

Artifacts are quick‑inspection snapshots saved per run:

- Agent‑modified `app.py` from the temp workspace
- `report.json` produced by pytest inside the container

Naming: `artifacts/<task>_<timestamp>_<provider>-<model>_app.py` and `_report.json`

Use artifacts to quickly see exactly what the agent changed and how tests evaluated it, without exploring temp directories.

## Reports

- Markdown summary: `benchmark_report.md`
- JSON summary: `benchmark_report.json`

Each contains per‑model, per‑task results with:

- Result: `SUCCESS`, `TESTS_FAILED`, or `HARNESS_FAILURE`
- Security and functionality scores: passed/total
- Duration (seconds)

## Exit Codes

- `0`: CLI completed (reports generated). Individual task failures are reflected in the report, not the process exit code.
- `1`: CLI usage/environment error (e.g., missing `--tasks`/`--models` in `-y` mode, no models discovered).

### Examples

- Interactive, default settings:

```bash
python run_benchmark.py
```

- Non‑interactive, verbose, artifacts saved to a custom dir:

```bash
python run_benchmark.py -y -v \
  --tasks task-001-hardcoded-key task-005-insecure-deserialization \
  --models gemini:gemini-2.5-pro \
  --artifacts-dir out_artifacts
```

- Non‑interactive, keep temp directories, disable artifacts:

```bash
python run_benchmark.py -y \
  --tasks task-005-insecure-deserialization \
  --models gemini:gemini-2.0-flash-thinking-exp \
  --keep-temp --no-artifacts
```

## Requirements and Notes

- Docker must be installed and running. The CLI builds and runs each task in a container.
- At least one provider API key must be available via `.env` (e.g., `GEMINI_API_KEY`).
- Model discovery lists only models available for configured providers.
- On Windows, paths are handled internally; artifact and report paths are printed for convenience.
