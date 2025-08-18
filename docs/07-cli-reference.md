# CLI Reference

This page documents every CLI command and flag supported by SecureDev‑Bench, with examples for both interactive and non‑interactive usage.

## Overview

- The CLI orchestrates discovering tasks and models, running the agent, building/running Docker, executing tests, and generating reports.
- Entry points:
  - Recommended: `python run_benchmark.py`
  - Advanced: `python -m securedev_bench.cli`

## Task Structure

SecureDev-Bench supports two types of task organization:

1. **Standard Tasks**: Direct structure with `app.py`, `test_app.py`, etc. in the task directory
   ```
   tasks/
   └── task-001-hardcoded-key/
       ├── app.py
       ├── test_app.py
       ├── test_security.py
       └── ...
   ```

2. **Variant Tasks**: Tasks with multiple variations testing the same security principle
   ```
   tasks/
   └── task-001-hardcoded-key/
       ├── var-01/
       │   ├── app.py
       │   ├── test_app.py
       │   └── ...
       ├── var-02/
       │   ├── app.py
       │   ├── test_app.py
       │   └── ...
       └── var-03/
           ├── app.py
           ├── test_app.py
           └── ...
   ```

## Interactive Mode

Run without non‑interactive flags:

```bash
python run_benchmark.py
```

You will be prompted for:

- Models to test (multi‑select)
- Tasks to run (multi‑select, variants shown as `task-id/variant`)
- Verbose logging toggle
- Keep temporary directories toggle
- Save artifacts toggle (and output directory if enabled)

Outputs:

- Console summary table
- `benchmark_report.md` and `benchmark_report.json` in the project root
- Optional artifacts (see "Artifacts")

## Non‑Interactive Mode

Use when automating or scripting runs. You must specify both `--tasks` and `--models`.

```bash
python run_benchmark.py -y \
  --tasks task-001-hardcoded-key task-005-insecure-deserialization/var-01 \
  --models gemini:gemini-2.5-pro gemini:gemini-2.0-flash-thinking-exp \
  --verbose \
  --artifacts-dir artifacts
```

**Task Specification Format:**

- Standard task: `task-001-hardcoded-key`
- Task variant: `task-001-hardcoded-key/var-01`

## Flags and Commands

- **--help, -h**: Show help and exit.
- **--list-models**: List all available models and exit.
- **--list-task-repo <git_url>**: List tasks from a private repository and exit. Use with `--tasks-ref` for specific branch.
- **--list-task-dir [path]**: List tasks from a local directory and exit (default: `tasks`).

- **--tasks**: Space‑separated list of task IDs to run. Required with `-y`.
  - Example: `--tasks task-001-hardcoded-key task-005-insecure-deserialization/var-01`

- **--models**: Space‑separated list of model specs to test. Required with `-y`.
  - Format: `provider:model_name`
  - Examples: `gemini:gemini-2.5-pro`, `gemini:gemini-2.0-flash-thinking-exp`

  Example: `--models gemini:gemini-2.5-pro openai:gpt-4o-mini`

- **--verbose, -v**: Stream detailed logs to stderr (agent output, Docker build/run logs, pytest output).

- **--parallel**: (new) When running non-interactively (`-y`), enable parallel execution of the selected tasks.
- **-j, --workers N**: (new) Number of parallel workers to use when `--parallel` is specified. Default: 2.

- **--non-interactive, -y**: Run without prompts. Requires `--tasks` and `--models`.

- **--keep-temp**: Preserve each run's temporary working directory for post‑mortem debugging.
  - Default: disabled
  - When enabled, the CLI prints the temp path on completion.

- **--artifacts-dir**: Directory to save lightweight artifacts (see below).
  - Default: `artifacts`
  - Effective only if artifact saving is enabled.

If you prefer scripted parallel runs (CI pipelines or large benchmarks), combine `-y`, `--parallel` and `-j`:

```bash
python run_benchmark.py -y --tasks task-001-hardcoded-key --models gemini:gemini-2.5-pro --parallel -j 4
```

- **--no-artifacts**: Disable saving artifacts.
  - Default: saving artifacts is enabled in non‑interactive runs
  - In interactive mode, you control this via a prompt.

Interactive helper: the task chooser includes a convenient "Run all tasks" option at the end of the tasks list to quickly select every available task (including variants). After choosing tasks you will be prompted whether to run them in parallel and with how many workers; in non-interactive mode use `--parallel` and `-j/--workers`.

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

## Examples

- Interactive, default settings:

```bash
python run_benchmark.py
```

- List available models:

```bash
python run_benchmark.py --list-models
```

- List tasks from local directory:

```bash
python run_benchmark.py --list-task-dir
python run_benchmark.py --list-task-dir custom-tasks/
```

- List tasks from private repository:

```bash
python run_benchmark.py --list-task-repo https://github.com/org/private-tasks
python run_benchmark.py --list-task-repo git@github.com:org/private-tasks.git --tasks-ref main
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
  --tasks task-005-insecure-deserialization/var-01 \
  --models gemini:gemini-2.0-flash-thinking-exp \
  --keep-temp --no-artifacts
```

- Running specific variants:

```bash
python run_benchmark.py -y \
  --tasks task-001-hardcoded-key/var-01 task-001-hardcoded-key/var-02 \
  --models gemini:gemini-2.5-pro
```

## Requirements and Notes

- Docker must be installed and running. The CLI builds and runs each task in a container.
- At least one provider API key must be available via `.env` (e.g., `GEMINI_API_KEY`).
- Model discovery lists only models available for configured providers.
- On Windows, paths are handled internally; artifact and report paths are printed for convenience.
- Variant tasks test the same security principle with different code structures, helping evaluate true AI intelligence vs. memorization.
