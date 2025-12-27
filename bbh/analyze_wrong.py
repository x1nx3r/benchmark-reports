#!/usr/bin/env python3
"""
Detailed analysis of what's extractable vs genuinely wrong.
"""
import json
import re
from pathlib import Path
from collections import defaultdict

config = "top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt"

# Categories
categories = {
    'wrong_answer': 0,      # Model gives answer but it's wrong
    'no_answer': 0,         # Model doesn't give clear answer
    'format_issue': 0,      # Correct answer in weird format
    'partial': 0,           # Partial match or reasoning correct
}

task_breakdown = defaultdict(lambda: defaultdict(int))

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
                final = resp[-500:].lower()
            
            # Check if we can extract ANY answer
            extracted_option = None
            
            # Look for option letters
            if re.match(r'^\([a-g]\)$', target):
                target_letter = target[1]
                
                # Find what option the model chose
                patterns = [
                    r'answer is[:\s]+\*?\*?\(?([a-g])\)?',
                    r'correct answer is[:\s]+\*?\*?\(?([a-g])\)?',
                    r'\*\*\(?([a-g])\)?\*\*',
                    r'\\boxed\{?\(?([a-g])\)?\}?',
                    r'^\s*\(?([a-g])\)?[:\.\s]',
                ]
                
                for p in patterns:
                    match = re.search(p, final)
                    if match:
                        extracted_option = match.group(1)
                        break
                
                if extracted_option:
                    if extracted_option == target_letter:
                        categories['format_issue'] += 1
                        task_breakdown[task]['format'] += 1
                    else:
                        categories['wrong_answer'] += 1
                        task_breakdown[task]['wrong'] += 1
                else:
                    categories['no_answer'] += 1
                    task_breakdown[task]['no_answer'] += 1
            
            # Boolean/yes-no
            elif target in ['true', 'false', 'yes', 'no', 'valid', 'invalid']:
                # Check for any boolean in response
                bools_found = []
                for b in ['true', 'false', 'yes', 'no', 'valid', 'invalid', 'plausible', 'implausible']:
                    if b in final:
                        bools_found.append(b)
                
                # Map plausible
                if 'plausible' in bools_found and 'implausible' not in bools_found:
                    bools_found = ['yes']
                elif 'implausible' in bools_found:
                    bools_found = ['no']
                
                if target in bools_found:
                    categories['format_issue'] += 1
                    task_breakdown[task]['format'] += 1
                elif any(b in ['true', 'false', 'yes', 'no', 'valid', 'invalid'] for b in bools_found):
                    categories['wrong_answer'] += 1
                    task_breakdown[task]['wrong'] += 1
                else:
                    categories['no_answer'] += 1
                    task_breakdown[task]['no_answer'] += 1
            
            else:
                # Complex answers
                if target in final:
                    categories['format_issue'] += 1
                    task_breakdown[task]['format'] += 1
                else:
                    categories['no_answer'] += 1
                    task_breakdown[task]['no_answer'] += 1

print("=" * 60)
print("BREAKDOWN OF 'ACTUALLY WRONG' SAMPLES")
print("=" * 60)
print(f"\nTotal analyzed: {sum(categories.values())}")
print(f"  Wrong answer (model chose different option):  {categories['wrong_answer']}")
print(f"  No clear answer found:                        {categories['no_answer']}")
print(f"  Format issue (should have been caught):       {categories['format_issue']}")

print("\n" + "=" * 60)
print("BY TASK")
print("=" * 60)
for task, stats in sorted(task_breakdown.items(), key=lambda x: -sum(x[1].values())):
    total = sum(stats.values())
    print(f"\n{task}: {total} total")
    for cat, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
