from pathlib import Path
import ast

PATH = Path("scripts/generate_research_summaries_gemini_v0_2.py")
SOURCE = PATH.read_text()

assert "timeout=120_000" in SOURCE

tree = ast.parse(SOURCE)
node = next(
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "is_transient_error"
)

module = ast.Module(body=[node], type_ignores=[])
ns = {}
exec(compile(module, str(PATH), "exec"), ns)

class ReadTimeout(Exception):
    pass

assert ns["is_transient_error"](ReadTimeout("timed out"))
assert ns["is_transient_error"](Exception("503 UNAVAILABLE"))
assert ns["is_transient_error"](Exception("429 RESOURCE_EXHAUSTED"))
assert not ns["is_transient_error"](Exception("invalid JSON schema"))

script = (
    Path(__file__).resolve().parents[1]
    / "scripts/generate_research_summaries_gemini_v0_2.py"
).read_text(encoding="utf-8")

assert "VALID_EVIDENCE_SEGMENT_ID_RANGE" in script
assert "for grounding_attempt in range(1, 4):" in script
assert "GROUNDING RETRY" in script

print("GEMINI GROUNDING RETRY CONTRACT: PASS")
print("GEMINI TIMEOUT CONTRACT: PASS")
