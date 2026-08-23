from __future__ import annotations

from pathlib import Path


RAW_ROOT = Path("data/raw/surveillance")
TEST_DATE = "2099-01-01"

canonical = RAW_ROOT / TEST_DATE
temporary = RAW_ROOT / f".{TEST_DATE}.tmp"

simulated_failure_detected = False


def cleanup() -> None:
    if temporary.exists():
        for path in temporary.iterdir():
            if path.is_file():
                path.unlink()

        temporary.rmdir()


# Ensure the test starts clean.
if canonical.exists():
    raise SystemExit(
        f"ABORT — canonical test directory exists: {canonical}"
    )

cleanup()

RAW_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)

try:
    temporary.mkdir()

    # Simulate the first half of an acquisition.
    transcript = temporary / "transcript.json"
    transcript.write_bytes(
        b'{"simulated":"raw transcript"}'
    )

    print(
        "TEMP TRANSCRIPT WRITTEN:",
        transcript.exists(),
    )

    # Simulate failure before metadata is written
    # and before canonical publication.
    raise RuntimeError(
        "SIMULATED FAILURE BETWEEN RAW AND METADATA WRITE"
    )

except RuntimeError as exc:
    simulated_failure_detected = True
    print("EXPECTED FAILURE:", exc)

finally:
    cleanup()


checks = {
    "failure_detected": simulated_failure_detected,
    "canonical_absent": not canonical.exists(),
    "temp_removed": not temporary.exists(),
}

print()

for name, passed in checks.items():
    print(f"{name}: {passed}")

print()

if all(checks.values()):
    print("ATOMIC FAILURE CLEANUP CHECK: PASS")
else:
    raise SystemExit(
        "ATOMIC FAILURE CLEANUP CHECK: FAIL"
    )
