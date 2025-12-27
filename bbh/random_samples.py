#!/usr/bin/env python3
"""Generate random samples report from all tasks."""
import json
import re
import random
from pathlib import Path

random.seed(42)

config = "top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt"

print("=" * 80)
print("RANDOM SAMPLES REPORT")
print(f"Config: {config}")
print("=" * 80)

for task_file in sorted(Path(config).glob("samples_*.jsonl")):
    task = task_file.stem
    task = re.sub(r'_\d{4}-\d{2}-\d{2}T.*', '', task)
    task = task.replace('samples_bbh_cot_fewshot_', '')
    
    samples = []
    with open(task_file) as f:
        for line in f:
            samples.append(json.loads(line))
    
    # Pick 2 random samples
    picked = random.sample(samples, min(2, len(samples)))
    
    print(f"\n{'#'*80}")
    print(f"# TASK: {task}")
    print(f"{'#'*80}")
    
    for s in picked:
        target = s.get('target', '')
        resp = s.get('resps', [[]])[0][0] if s.get('resps') else ''
        exact = s.get('exact_match', 0)
        doc = s.get('doc_id', '')
        
        # Extract final part after </think>
        if '</think>' in resp.lower():
            final = resp.split('</think>')[-1].strip()
        else:
            final = resp[-500:]
        
        # Check for think tag
        has_think = '<think>' in resp.lower()
        
        print(f"\n--- Doc {doc} ---")
        print(f"Target: {target}")
        print(f"Think tags: {has_think}")
        print(f"Official exact_match: {exact}")
        print(f"\nFinal output (after </think>):")
        print(final[:600])
        if len(final) > 600:
            print("...")
