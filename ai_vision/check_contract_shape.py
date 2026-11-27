"""Compare the structure of our result with the contract's sample file.

    python -m ai_vision.check_contract_shape contracts/SAMPLE_FILE.json ml_data/raw_photos/member1/crab_back.png
"""
import json
import sys
from pathlib import Path

from ai_vision.vision_step import run_vision


def shape(x):
    if isinstance(x, dict):
        return {k: shape(v) for k, v in x.items()}
    if isinstance(x, list):
        return [shape(x[0])] if x else []
    if isinstance(x, bool):
        return "bool"
    if isinstance(x, (int, float)):
        return "number"
    return type(x).__name__


def compare(expected, got, path, problems):
    if isinstance(expected, dict):
        if not isinstance(got, dict):
            problems.append("%s: expected an object, got %s" % (path or "result", got))
            return
        for key in expected:
            if key not in got:
                problems.append("%s.%s is MISSING in our result" % (path, key))
            else:
                compare(expected[key], got[key], path + "." + key, problems)
        for key in got:
            if key not in expected:
                problems.append("%s.%s is EXTRA (not in the contract sample)" % (path, key))
    elif isinstance(expected, list):
        if not isinstance(got, list):
            problems.append("%s: expected a list" % path)
        elif expected and got:
            compare(expected[0], got[0], path + "[0]", problems)
    elif expected != got:
        problems.append("%s: contract has type %s, ours is %s" % (path, expected, got))


if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)

sample = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
ours = json.loads(json.dumps(run_vision(sys.argv[2])))

problems = []
compare(shape(sample), shape(ours), "", problems)

if problems:
    print("Differences found:")
    for p in problems:
        print("  -", p)
else:
    print("Our result has the same structure as the contract sample.")
print("Note: an empty list in either file cannot be compared inside.")