from datetime import date
from pathlib import Path
import ast

PATH = Path("scripts/prepare_manual_source_override_v0_1.py")
SOURCE = PATH.read_text()
TREE = ast.parse(SOURCE)

nodes = [
    node for node in TREE.body
    if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))
]

ns = {}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(PATH), "exec"), ns)

assert ns["extract_video_id"](
    "https://www.youtube.com/watch?v=uHp4tvxEQJI"
) == "uHp4tvxEQJI"

assert ns["extract_video_id"](
    "https://youtu.be/uHp4tvxEQJI"
) == "uHp4tvxEQJI"

try:
    ns["extract_video_id"](
        "https://example.com/watch?v=uHp4tvxEQJI"
    )
except ValueError:
    pass
else:
    raise AssertionError("non-YouTube URL must fail")

source = ns["build_source"](
    "2026-09-23",
    "https://www.youtube.com/watch?v=uHp4tvxEQJI",
)

assert source["video_id"] == "uHp4tvxEQJI"
assert source["video_date"] == "2026-09-23"
assert source["broadcast_date_basis"] == "manual_verified_url"

print("MANUAL SOURCE OVERRIDE CONTRACT: PASS")
