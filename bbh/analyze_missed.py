#!/usr/bin/env python3
"""Comprehensive missed patterns analysis across all tasks."""
import json
import re
from pathlib import Path
from collections import defaultdict

config = "top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt"

# Additional patterns to check
new_patterns = {
    'plausible_yes': (r'\bplausible\b(?!.*implausible)', 'yes'),
    'implausible_no': (r'\bimplausible\b', 'no'),
    'bold_option': (r'\*\*\(?([a-g])\)?\*\*', None),  # **A** or **(A)**
    'boxed': (r'\\?boxed\{([^}]+)\}', None),
    'correct_answer_is': (r'correct answer is[:\s]+\(?([a-g])\)?', None),
    'answer_equals': (r'answer\s*=\s*\(?([a-g])\)?', None),
}

task_stats = defaultdict(lambda: {'missed': 0, 'recovered': defaultdict(int)})

for task_file in Path(config).glob("samples_*.jsonl"):
    task = task_file.stem.replace('samples_bbh_cot_fewshot_', '').split('_2025')[0]
    
    with open(task_file) as f:
        for line in f:
            s = json.loads(line)
            target = s.get('target', '').lower().strip()
            resp = s.get('resps', [[]])[0][0] if s.get('resps') else ''
            
            if '</think>' in resp.lower():
                final = resp.lower().split('</think>')[-1]
            else:
                final = resp[-400:].lower()
            
            # Check current patterns
            current_match = False
            target_norm = target
            if re.match(r'^\([a-g]\)$', target):
                letter = target[1]
                if re.search(rf'\({letter}\)|{letter}[:\.]|\boption\s+{letter}\b', final):
                    current_match = True
            elif target in ['true', 'false', 'yes', 'no', 'valid', 'invalid']:
                if target in final:
                    current_match = True
            elif target in final:
                current_match = True
            
            if not current_match:
                task_stats[task]['missed'] += 1
                
                # Check new patterns
                for pat_name, (pattern, equiv) in new_patterns.items():
                    match = re.search(pattern, final, re.IGNORECASE)
                    if match:
                        # Check if this would match target
                        if equiv and equiv == target:
                            task_stats[task]['recovered'][pat_name] += 1
                        elif match.groups():
                            extracted = match.group(1).lower()
                            if re.match(r'^\([a-g]\)$', target):
                                if extracted == target[1]:
                                    task_stats[task]['recovered'][pat_name] += 1
                            elif extracted == target:
                                task_stats[task]['recovered'][pat_name] += 1

print("=== Recovery Potential by Task ===\n")
total_missed = 0
total_recovered = 0
for task, stats in sorted(task_stats.items(), key=lambda x: -x[1]['missed']):
    recovered = sum(stats['recovered'].values())
    total_missed += stats['missed']
    total_recovered += recovered
    if recovered > 0:
        print(f"{task}:")
        print(f"  Missed: {stats['missed']}, Recoverable: {recovered}")
        print(f"  Patterns: {dict(stats['recovered'])}")
        print()

print(f"\n=== SUMMARY ===")
print(f"Total missed: {total_missed}")
print(f"Additional recoverable: {total_recovered}")
print(f"Potential improvement: +{total_recovered} answers")
