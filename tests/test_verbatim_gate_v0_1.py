from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.processing.verbatim_gate import exposure_failures

source = [
    "The labor market is cooling faster than expected and the Federal Reserve "
    "may need to consider a different path for interest rates this year."
]
assert exposure_failures([
    "The labor market is cooling faster than expected and the Federal Reserve may need to consider policy."
], source)
assert not exposure_failures([
    "Weaker employment conditions could alter the policy-rate debate."
], source)
print("VERBATIM EXPOSURE: 0")
