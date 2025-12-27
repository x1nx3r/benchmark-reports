#!/usr/bin/env python3
"""
Random sampling of missed patterns across all tasks.
Shows what the model outputs for samples we mark as "wrong".
"""
import json
import re
import random
from pathlib import Path
from collections import defaultdict

random.seed(42)  # Reproducible sampling

config = "top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt"

# Our current matching logic (simplified)
def is_matched(target, final):
    target = target.lower().strip()
    final = final.lower()
    
    # Option letter
    if re.match(r'^\([a-g]\)$', target):
        letter = target[1]
        patterns = [
            rf'\({letter}\)', rf'\b{letter}\b\s*[:\.]', rf'option\s+{letter}\b',
            rf'answer\s+is\s+\(?{letter}\)?', rf'\*\*\(?{letter}\)?\*\*',
            rf'\\boxed\{{{letter}\}}', rf'correct\s+answer\s+is[:\s]+\(?{letter}\)?',
        ]
        for p in patterns:
            if re.search(p, final):
                return True
    
    # Boolean
    elif target in ['true', 'false', 'yes', 'no', 'valid', 'invalid']:
        if target in final:
            return True
        # Plausible mapping
        if target == 'yes' and 'plausible' in final and 'implausible' not in final:
            return True
        if target == 'no' and 'implausible' in final:
            return True
    
    # Direct
    elif target in final:
        return True
    
    return False


# Collect all "wrong" samples
all_wrong = []

for task_file in Path(config).glob("samples_*.jsonl"):
    task = task_file.stem.replace('samples_bbh_cot_fewshot_', '').split('_2025')[0]
    
    with open(task_file) as f:
        for line in f:
            s = json.loads(line)
            target = s.get('target', '')
            resp = s.get('resps', [[]])[0][0] if s.get('resps') else ''
            
            if '</think>' in resp.lower():
                final = resp.lower().split('</think>')[-1]
            else:
                final = resp[-500:].lower()
            
            if not is_matched(target, final):
                all_wrong.append({
                    'task': task,
                    'doc': s.get('doc_id'),
                    'target': target.lower().strip(),
                    'final': final[:400]
                })

print(f"Total 'wrong' samples: {len(all_wrong)}\n")

# Random sample
sample = random.sample(all_wrong, min(30, len(all_wrong)))

print("=" * 80)
print("RANDOM SAMPLE OF MISSED PATTERNS")
print("=" * 80)

# Group potential patterns
patterns_found = defaultdict(list)

for s in sample:
    print(f"\n[{s['task']}] Doc {s['doc']} | Target: '{s['target']}'")
    print(f"Final text: {s['final'][:200]}...")
    
    # Look for patterns we might be missing
    found = []
    if '**' in s['final']:
        bold = re.findall(r'\*\*([^*]+)\*\*', s['final'])
        found.append(f"bold: {bold[:2]}")
    if 'answer' in s['final']:
        ans = re.findall(r'answer[:\s]+([^\n.!?]{1,50})', s['final'])
        found.append(f"answer: {ans[:2]}")
    if 'result' in s['final']:
        found.append("has 'result'")
    if 'correct' in s['final']:
        found.append("has 'correct'")
    if 'therefore' in s['final'] or 'thus' in s['final']:
        found.append("has therefore/thus")
    if 'so ' in s['final']:
        found.append("has 'so'")
    
    if found:
        print(f"  Patterns: {found}")
        for f in found:
            patterns_found[f.split(':')[0]].append(s)

print("\n" + "=" * 80)
print("PATTERN SUMMARY")
print("=" * 80)
for pat, samples in sorted(patterns_found.items(), key=lambda x: -len(x[1])):
    print(f"\n{pat}: {len(samples)} samples")
    for s in samples[:2]:
        print(f"  [{s['task']}] target='{s['target']}' -> {s['final'][:80]}...")
