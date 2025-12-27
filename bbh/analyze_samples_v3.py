#!/usr/bin/env python3
"""
BBH Benchmark Sample Analyzer (v3 - Comprehensive)

Key improvements:
1. Extracts what model ACTUALLY answered (not just target matching)
2. Categorizes: correct, wrong_answer, no_answer  
3. Better format vs content distinction
4. More extraction patterns
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Optional, Tuple, Dict


def extract_option_from_text(text: str) -> Optional[str]:
    """Extract option letter (a-g) from response text."""
    text = text.lower()
    
    # Priority ordered patterns
    patterns = [
        r'answer is[:\s]+\*?\*?\(?([a-g])\)?',
        r'correct answer is[:\s]+\*?\*?\(?([a-g])\)?',
        r'\\boxed\{\(?([a-g])\)?\}',
        r'\*\*\(?([a-g])\)?\*\*',
        r'option\s+([a-g])\b',
        r':\s*\(?([a-g])\)\s*$',
        r'^\s*([a-g])[:\.\s]',
        r'\(([a-g])\)',
    ]
    
    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(1)
    return None


def extract_boolean_from_text(text: str) -> Optional[str]:
    """Extract boolean answer from response text."""
    text = text.lower()
    
    # Check for plausible/implausible first (sports understanding)
    if 'implausible' in text:
        return 'no'
    if 'plausible' in text:
        return 'yes'
    
    # Priority: more specific patterns first
    bool_patterns = [
        (r'is\s+(true|false|yes|no|valid|invalid)', 1),
        (r'answer is[:\s]+(true|false|yes|no|valid|invalid)', 1),
        (r'\*\*(true|false|yes|no|valid|invalid)\*\*', 1),
        (r'\b(true|false)\b', 1),
        (r'\b(yes|no)\b', 1),
        (r'\b(valid|invalid)\b', 1),
    ]
    
    for p, group in bool_patterns:
        match = re.search(p, text)
        if match:
            return match.group(group)
    return None


def extract_answer(text: str, target: str) -> Dict:
    """
    Extract model's answer and compare with target.
    Returns detailed result dict.
    """
    result = {
        'target': target.lower().strip(),
        'extracted': None,
        'category': 'no_answer',  # correct, wrong_answer, no_answer
        'pattern': None,
    }
    
    target_norm = result['target']
    text_lower = text.lower()
    
    # Determine target type and extract accordingly
    if re.match(r'^\([a-g]\)$', target_norm):
        # Multiple choice
        target_letter = target_norm[1]
        extracted = extract_option_from_text(text_lower)
        
        if extracted:
            result['extracted'] = f"({extracted})"
            result['pattern'] = 'option'
            if extracted == target_letter:
                result['category'] = 'correct'
            else:
                result['category'] = 'wrong_answer'
        else:
            result['category'] = 'no_answer'
    
    elif target_norm in ['true', 'false', 'yes', 'no', 'valid', 'invalid']:
        # Boolean
        extracted = extract_boolean_from_text(text_lower)
        
        if extracted:
            result['extracted'] = extracted
            result['pattern'] = 'boolean'
            if extracted == target_norm:
                result['category'] = 'correct'
            else:
                result['category'] = 'wrong_answer'
        else:
            result['category'] = 'no_answer'
    
    else:
        # Complex answer (word sorting, etc.)
        if target_norm in text_lower:
            result['extracted'] = target_norm
            result['pattern'] = 'direct'
            result['category'] = 'correct'
        else:
            result['category'] = 'no_answer'
    
    return result


def analyze_sample(data: dict, task_name: str = "") -> Dict:
    """Analyze a single sample."""
    target = data.get("target", "")
    resps = data.get("resps", [[]])
    response_text = resps[0][0] if resps and resps[0] else ""
    filtered = data.get("filtered_resps", [])
    official_valid = not (filtered and filtered[0] == "[invalid]")
    official_correct = data.get("exact_match", 0) == 1.0
    
    # Check for think tags
    has_think = '</think>' in response_text.lower()
    
    # Extract final answer text
    if has_think:
        parts = re.split(r'</think>', response_text, flags=re.IGNORECASE)
        final_text = parts[-1].strip() if len(parts) > 1 else response_text
    else:
        final_text = response_text
    
    # Extract and categorize answer
    answer_result = extract_answer(final_text, target)
    
    return {
        "doc_id": data.get("doc_id", ""),
        "target": target,
        "has_think": has_think,
        "official_valid": official_valid,
        "official_correct": official_correct,
        "extracted": answer_result["extracted"],
        "category": answer_result["category"],
        "pattern": answer_result["pattern"],
        "final_text": final_text[:200] if final_text else "",
    }


def analyze_task_file(filepath: str, limit_samples: int = 3) -> Dict:
    """Analyze a single task's samples file."""
    stats = {
        "total": 0,
        "has_think": 0,
        "official_correct": 0,
        "correct": 0,
        "wrong_answer": 0,
        "no_answer": 0,
        "patterns": defaultdict(int),
        "samples": [],
    }
    
    with open(filepath) as f:
        for line in f:
            data = json.loads(line)
            stats["total"] += 1
            
            result = analyze_sample(data, filepath)
            
            if result["has_think"]:
                stats["has_think"] += 1
            if result["official_correct"]:
                stats["official_correct"] += 1
            
            # Categorize
            if result["category"] == "correct":
                stats["correct"] += 1
                if result["pattern"]:
                    stats["patterns"][result["pattern"]] += 1
            elif result["category"] == "wrong_answer":
                stats["wrong_answer"] += 1
            else:
                stats["no_answer"] += 1
            
            # Store samples
            if len(stats["samples"]) < limit_samples:
                if result["category"] != "correct" or not result["official_correct"]:
                    stats["samples"].append(result)
    
    return stats


def print_task_stats(task: str, stats: Dict):
    """Print single task statistics."""
    total = stats["total"]
    if not total:
        return
    
    official = stats["official_correct"] / total * 100
    true_acc = stats["correct"] / total * 100
    wrong = stats["wrong_answer"] / total * 100
    no_ans = stats["no_answer"] / total * 100
    think = stats["has_think"] / total * 100
    
    print(f"\n{'='*60}")
    print(f"Task: {task}")
    print(f"{'-'*60}")
    print(f"  Samples: {total} | Think tags: {stats['has_think']} ({think:.0f}%)")
    print(f"  Official: {stats['official_correct']} ({official:.1f}%)")
    print(f"  True:     {stats['correct']} ({true_acc:.1f}%)")
    print(f"  Wrong:    {stats['wrong_answer']} ({wrong:.1f}%)")
    print(f"  No answer: {stats['no_answer']} ({no_ans:.1f}%)")
    
    if stats["samples"]:
        print(f"\n  Samples:")
        for s in stats["samples"][:2]:
            cat = s["category"].upper()
            print(f"    [{cat}] Doc {s['doc_id']}: target='{s['target']}' got='{s['extracted']}'")


def analyze_config(config_path: str, limit: int = 3) -> Tuple[Dict, Dict]:
    """Analyze all tasks in a config."""
    config_path = Path(config_path)
    sample_files = sorted(config_path.glob("samples_*.jsonl"))
    
    if not sample_files:
        print(f"No sample files in {config_path}")
        return {}, {}
    
    print(f"\nFound {len(sample_files)} task files")
    
    overall = {
        "total": 0, "has_think": 0, "official_correct": 0,
        "correct": 0, "wrong_answer": 0, "no_answer": 0,
        "patterns": defaultdict(int),
    }
    
    task_results = {}
    
    for sf in sample_files:
        task = sf.stem
        task = re.sub(r'_\d{4}-\d{2}-\d{2}T.*', '', task)
        task = task.replace('samples_bbh_cot_fewshot_', '')
        
        stats = analyze_task_file(str(sf), limit)
        task_results[task] = stats
        
        print_task_stats(task, stats)
        
        # Aggregate
        for k in ["total", "has_think", "official_correct", "correct", "wrong_answer", "no_answer"]:
            overall[k] += stats[k]
        for p, c in stats["patterns"].items():
            overall["patterns"][p] += c
    
    return task_results, overall


def print_summary(overall: Dict, config: str):
    """Print overall summary."""
    print("\n" + "=" * 80)
    print(f"SUMMARY: {config}")
    print("=" * 80)
    
    total = overall["total"]
    if not total:
        return
    
    official = overall["official_correct"] / total * 100
    true_acc = overall["correct"] / total * 100
    wrong = overall["wrong_answer"] / total * 100
    no_ans = overall["no_answer"] / total * 100
    think = overall["has_think"] / total * 100
    
    print(f"\nTotal samples: {total}")
    print(f"Think tags: {overall['has_think']} ({think:.1f}%)")
    
    print(f"\n--- ACCURACY ---")
    print(f"Official (benchmark):  {overall['official_correct']:>5} ({official:>5.2f}%)")
    print(f"True (extracted):      {overall['correct']:>5} ({true_acc:>5.2f}%)")
    print(f"Gap:                          +{true_acc - official:.2f}%")
    
    print(f"\n--- ERROR BREAKDOWN ---")
    print(f"Wrong answer (model chose wrong): {overall['wrong_answer']:>5} ({wrong:>5.1f}%)")
    print(f"No answer (couldn't extract):     {overall['no_answer']:>5} ({no_ans:>5.1f}%)")
    
    # Recovery potential
    format_issues = overall["correct"] - overall["official_correct"]
    if format_issues > 0:
        print(f"\n--- FORMAT RECOVERY ---")
        print(f"Correct but unrecognized by benchmark: {format_issues}")
        print(f"Recovery potential: +{format_issues / total * 100:.2f}%")


def main():
    parser = argparse.ArgumentParser(description='BBH Analyzer v3')
    parser.add_argument('--config', '-c', type=str, help='Config to analyze')
    parser.add_argument('--all', '-a', action='store_true', help='Analyze all')
    parser.add_argument('--list', '-l', action='store_true', help='List configs')
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--base-dir', '-b', type=str, default=None)
    
    args = parser.parse_args()
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    
    # Find configs
    configs = {}
    for item in base_dir.iterdir():
        if item.is_dir() and list(item.glob("samples_*.jsonl")):
            configs[item.name] = len(list(item.glob("samples_*.jsonl")))
    
    if args.list:
        print("Configs:")
        for name, count in sorted(configs.items()):
            print(f"  {name} ({count} tasks)")
        return
    
    to_analyze = [args.config] if args.config else list(configs.keys())
    
    all_results = {}
    
    for config in to_analyze:
        config_path = base_dir / config
        if not config_path.exists():
            print(f"Not found: {config}")
            continue
        
        print("\n" + "#" * 80)
        print(f"# {config}")
        print("#" * 80)
        
        tasks, overall = analyze_config(str(config_path), args.limit)
        all_results[config] = {"tasks": tasks, "overall": overall}
        
        print_summary(overall, config)
    
    # Comparison
    if len(all_results) > 1:
        print("\n" + "#" * 80)
        print("# COMPARISON")
        print("#" * 80)
        print(f"\n{'Config':<50} {'Official':>8} {'True':>8} {'Wrong':>8} {'NoAns':>8}")
        print("-" * 82)
        for name, data in sorted(all_results.items()):
            o = data["overall"]
            if o["total"]:
                off = o["official_correct"] / o["total"] * 100
                true = o["correct"] / o["total"] * 100
                wrong = o["wrong_answer"] / o["total"] * 100
                noan = o["no_answer"] / o["total"] * 100
                print(f"{name:<50} {off:>7.1f}% {true:>7.1f}% {wrong:>7.1f}% {noan:>7.1f}%")


if __name__ == "__main__":
    main()
