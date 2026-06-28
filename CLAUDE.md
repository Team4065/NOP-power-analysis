# Claude Code Context — NOP Power Analysis

## Always read these docs first

Before writing any code in this repo, pin and read these six files:

1. [docs/SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md) — what the tool must do
2. [docs/telemetry_schema.md](docs/telemetry_schema.md) — real AKit signal paths and subsystem groups
3. [docs/architecture.md](docs/architecture.md) — data flow and module responsibilities
4. [docs/TESTING.md](docs/TESTING.md) — test strategy and invariants
5. [docs/GLOSSARY.md](docs/GLOSSARY.md) — FRC/AKit term definitions
6. Active feature doc in [docs/features/](docs/features/) — current session state

## Critical data facts

- **Real logs live outside this repo**: `../championship_logs/` (sibling directory, ~1.8 GB, git-ignored — back up separately when changing machines; see [docs/STARTUP.md](docs/STARTUP.md))
- **Format**: AdvantageKit sparse CSV — values only appear in rows where they changed; `null` elsewhere; always forward-fill
- **PDH data is always zero**: old PDH hardware has no CAN bus — `/PowerDistribution/*` signals are useless
- **12V voltage source**: `/SystemStats/BatteryVoltage` (real data, 12.8V idle → ~11V under load)
- **Total current**: sum of all motor current signals (no PDH total available)
- **Brownout threshold**: **6.0V** (read from `/SystemStats/BrownoutVoltage`) — not 6.8V
- **Brownout detection**: use `/SystemStats/BrownedOut` boolean signal directly

## Cross-platform rules

- Use `pathlib.Path` for all file paths — no string `/` or `\\` concatenation
- No hardcoded data paths — user supplies `--log-dir` at runtime
- Matplotlib: auto-detect headless Linux and switch to `Agg` backend only then

## Plot annotation rule

Every plot must include four vertical lines:
1. Match start (auto begins)
2. Teleop start (auto → teleop transition)
3. Endgame start (MatchTime ≤ 30s during teleop)
4. Match end (robot disabled, MatchTime = 0)

## AI workflow

Follow the six-stage pipeline in [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md):
Requirements → SRD → Test plan → Tests (red) → Implementation (green) → Refactor

For each new feature: copy [docs/features/FEATURE_TEMPLATE.md](docs/features/FEATURE_TEMPLATE.md), fill in Section 0 (session state) at the start and end of every session.
