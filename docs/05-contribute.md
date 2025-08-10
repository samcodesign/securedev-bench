# Contributing to SecureDev‑Bench

Thank you for your interest in improving SecureDev‑Bench. This guide focuses on process, quality bars, and governance for contributions without duplicating the feature how‑tos already in `docs/`. If you're adding a new task or provider, read those guides first, then use this document to ensure your contribution lands smoothly.

### Contribution Principles
- **Security first**: Prefer minimal, deterministic, offline‑friendly designs. Avoid network calls in tasks; rely on local fixtures.
- **Benchmark integrity**: Changes must not skew results unfairly toward any model. Keep prompts, harness behavior, and scoring neutral.
- **Reproducibility**: Results should be re‑runnable across hosts. Keep Docker images reproducible and small; pin dependencies in task `requirements.txt`.
- **Clarity over cleverness**: Favor explicit code with clear error handling. Benchmarks are read by humans and executed by machines.

### Scope of Contributions
- Improvements to the benchmark harness: CLI, discovery, runner, reporting.
- New or improved tasks and providers (see `docs/` for interfaces). This guide adds process and quality expectations.
- Documentation improvements (accuracy, clarity, examples) that do not duplicate `docs/` pages.

### Status Lifecycle for Issues and PRs
- **Issues**
  - `needs-triage`: Newly opened, awaiting maintainer review.
  - `info-needed`: Awaiting reporter details or reproduction steps.
  - `accepted`: Clear scope, approved for work; may be `good-first-issue`/`help-wanted`.
  - `blocked`: External dependency or unanswered question.
  - `duplicate` / `wontfix` / `invalid`: Closed with rationale.
  - `in-progress`: Assignee actively working (link branch/PR).
  - `ready-for-pr`: Design agreed; implementers welcome.
- **Pull Requests**
  - `awaiting-review`: Ready for review.
  - `changes-requested`: Revisions needed; reviewer left specific items.
  - `awaiting-author`: Author to respond/iterate.
  - `ready-to-merge`: All checks green; maintainer will merge.
  - `blocked`: Waiting on dependency (another PR, external fix).

These labels help track throughput and set expectations. Maintainers may add more granular labels for area ownership (e.g., `area:runner`, `area:reporting`, `area:tasks`, `area:providers`).

### Definition of Done (DoD)
- Code builds and runs locally; no crashes in normal flows.
- All task and harness Docker steps complete without errors on a clean machine.
- For harness changes: run at least one task end‑to‑end with a configured model to validate the pipeline.
- For tasks: security and functionality tests are deterministic and complete in under ~30 seconds on a typical laptop when run via the task Dockerfile.
- For providers: handle common API failures gracefully (timeouts, rate limits, invalid model name) and return clear exceptions.
- Documentation updated where behavior changes.

### Quality Bar by Contribution Type
- **Tasks** (do not duplicate `docs/01-adding-tasks.md`)
  - Keep the vulnerable code realistic and minimal. Prefer single‑file apps.
  - Tests must be precise: the security test should fail on `app.py` and pass on `solution.py`; functionality must pass on both.
  - Ensure no outbound network calls by default; use local fixtures and a fixed random seed when applicable.
  - Keep images lean: avoid heavy base images and unnecessary build layers.
  - Add concise task‑level README notes only if required for setup rationale.
- **Providers** (complement `docs/02-adding-providers.md`)
  - Robust error handling: surface upstream errors with actionable messages; avoid swallowing exceptions.
  - Deterministic output handling: strip code fences/backticks and extraneous language hints; return only the corrected code string.
  - Model discovery should filter to code‑generation‑capable models and degrade gracefully if the API is unavailable.
  - Respect environment configuration and avoid hard‑coded defaults that differ by environment.
- **Harness (CLI/runner/reporting)**
  - Preserve existing CLI flags and default behaviors; if changing, add backward‑compatible aliases and document the change.
  - Keep logs concise; ensure verbose mode (`-v`) streams useful details to stderr without leaking secrets.
  - Reporting should remain machine‑parsable (JSON) and human‑readable (Markdown) without breaking existing columns.

### Local Development Workflow
1. Fork and create a feature branch:
   ```bash
   git checkout -b feat/<area>-<short-description>
   # e.g., feat/runner-timeout-handling or task/005-xxe
   ```
2. Set up the environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. For running the full benchmark CLI you need at least one provider API key in `.env` (e.g., `GEMINI_API_KEY`).
4. Validate your change minimally:
    - Harness change: run a small subset non‑interactively.
     ```bash
     python run_benchmark.py -y \
       --tasks task-001-hardcoded-key \
       --models gemini:gemini-1.5-pro
     ```
    - Task change: build and run the task container directly from its directory.
     ```bash
     docker build -t securedev-bench-task .
     docker run --rm -e API_KEY=DUMMY_KEY_FOR_TESTING securedev-bench-task
     ```
      This should execute tests and produce the report inside the container (the harness uses the same pattern).

### Coding and Review Standards
- Use descriptive names and explicit error handling; keep control‑flow shallow.
- Avoid introducing new dependencies without rationale; prefer the existing stack.
- Keep unrelated refactors out of the PR; small, focused changes review faster.
- Add targeted unit tests when modifying harness logic (e.g., result parsing or error categorization).
- Follow Conventional Commits in messages: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

### Benchmark Result Statuses (for readers of reports)
- `SUCCESS`: Vulnerability fixed and functionality preserved.
- `TESTS_FAILED`: Either security or functionality tests failed.
- `HARNESS_FAILURE`: Infrastructure error (e.g., Docker or provider call).

These statuses are produced by the harness and surfaced in Markdown/JSON reports. Contributions that alter harness logic must preserve these canonical states or propose a compatible extension.

### Security Guidance
- Do not include real secrets in examples or tests. Use obvious placeholders.
- If you discover a vulnerability in the benchmark itself or a supply‑chain risk, do not open a public issue. Contact the maintainers privately (see the email in `CODE_OF_CONDUCT.md`) and/or use a private security advisory channel.
- Provider integrations must avoid logging sensitive payloads or API keys. Scrub or redact when verbose logging is enabled.

### Documentation Changes
- Keep this guide focused on process and quality. Task/provider step‑by‑steps live in `docs/`.
- Update `README.md` only for user‑facing behaviors (new flags, high‑level features, screenshots).
- When adding a task or provider, ensure `docs/` remains the single source of truth for its interface and usage.

### Governance and Decision‑Making
- Small changes: Maintainer approval by one reviewer and green local verification is sufficient.
- Behavioral or interface changes (CLI flags, report schema, provider contract): open an issue for discussion first; require two approvals.
- Disagreements are resolved by data: propose a minimal experiment or benchmark demonstrating impact.

### PR Checklist (copy into your description)
- [ ] Scope is narrow and well‑defined; linked to an issue or rationale provided
- [ ] Harness builds and runs at least one task end‑to‑end locally
- [ ] For tasks: security test fails on `app.py`, passes on `solution.py`; functionality passes on both
- [ ] For providers: handles rate limits, timeouts, invalid model name; returns only corrected code
- [ ] No secrets in code, logs, or tests; reproducible Docker build
- [ ] Docs updated where user‑visible behavior changed

### Getting Help
- Use issues for bugs and feature proposals; tag with the relevant `area:` label.
- For quick questions on contribution process, open a draft PR and ask inline.
- For conduct concerns, see `CODE_OF_CONDUCT.md`.

We appreciate your contributions. Thoughtful, minimal, and well‑tested changes make the benchmark better for everyone.


