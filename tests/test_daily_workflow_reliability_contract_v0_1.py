from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (
    ROOT / ".github/workflows/daily-surveillance.yml"
).read_text(encoding="utf-8")

# Three automatic attempts in the Korea-morning publication window.
assert 'cron: "30 22 * * 0-4"' in workflow
assert 'cron: "30 0 * * 1-5"' in workflow
assert 'cron: "30 2 * * 1-5"' in workflow

# Discovery must expose an explicit readiness state.
assert "id: inventory" in workflow
assert 'echo "source_ready=true" >> "$GITHUB_OUTPUT"' in workflow
assert 'echo "source_ready=false" >> "$GITHUB_OUTPUT"' in workflow
assert '"$rc" -eq 20' in workflow

# SOURCE_NOT_READY must not publish stale/wrong-date research.
gate = (
    "${{ inputs.source_url != '' || "
    "steps.inventory.outputs.source_ready == 'true' }}"
)

required_gated_steps = (
    "Build, validate, and atomically publish latest surveillance",
    "Validate public surface",
    "Verify latest TV report",
    "Commit generated research artifacts",
    "Build public Research Desk site",
    "Configure GitHub Pages",
    "Upload Research Desk Pages artifact",
    "Deploy Research Desk to GitHub Pages",
)

for step in required_gated_steps:
    block = f"- name: {step}"
    assert block in workflow

assert workflow.count(gate) >= len(required_gated_steps)

# Manual recovery remains a first-class production path.
assert "report_date:" in workflow
assert "source_url:" in workflow
assert "Prepare manual source override" in workflow
assert "ALLOW_HISTORICAL_BACKFILL=1" in workflow

print("DAILY RETRY WINDOW: PASS")
print("SOURCE_NOT_READY WORKFLOW CONTRACT: PASS")
print("MANUAL RECOVERY PATH: PASS")
