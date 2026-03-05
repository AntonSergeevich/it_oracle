# diagnostics.py
import os
from questions_bank import QUESTIONS, SCALE_SHORT

base_dirs = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "images"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_images", "images"),
]

def list_files(d):
    try:
        return os.listdir(d)
    except Exception:
        return []

for d in base_dirs:
    print("DIR:", d)
    for f in list_files(d):
        print("  ", f)
print("\nExpected names per question (examples):")
for q in QUESTIONS:
    qid = q["id"]
    scale = q.get("scale","").strip()
    short = SCALE_SHORT.get(scale, scale.lower() if scale else "")
    print(f"id={qid:2} scale={scale:12} -> q_{qid}_{short}.png  or q_{str(qid).zfill(2)}_{short}.png or q_{qid}.png")

import os
from questions_bank import QUESTIONS, find_image_for_question

missing = []
for q in QUESTIONS:
    p = find_image_for_question(q)
    if not p:
        missing.append(q["id"])
    else:
        print(f"FOUND id={q['id']} -> {p}")
print("MISSING ids:", missing)