#!/usr/bin/env python3
"""
BBH Benchmark Sample Analyzer (v2 - Rigorous)

Provides accurate metrics by:
1. Handling <think></think> tag responses properly
2. Flexible answer matching beyond official regex
3. Distinguishing format errors from content errors
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Optional, Tuple


def normalize_answer(answer: str, task_name: str = "") -> str:
    """Normalize answer for comparison."""
    answer = answer.strip().lower()
    
    # Remove common punctuation at end
    answer = re.sub(r'[.!?,;:]+$', '', answer)
    
    # Handle boolean variations
    bool_map = {
        'true': 'true', 'yes': 'yes', 'valid': 'valid',
        'false': 'false', 'no': 'no', 'invalid': 'invalid',
    }
    if answer in bool_map:
        return bool_map[answer]
    
    # Handle option letter variations: (A), A., A:, Option A -> a
    option_match = re.match(r'^(?:\()?([a-g])(?:\)|\.|\:)?$', answer)
    if option_match:
        return f"({option_match.group(1)})"
    
    return answer


def extract_final_answer(response: str) -> Tuple[str, bool]:
    """
    Extract the final answer from response, handling <think> tags.
    Returns (answer_text, has_think_tags)
    """
    has_think = '</think>' in response.lower()
    
    # If has think tags, extract content after closing tag
    if has_think:
        parts = re.split(r'</think>', response, flags=re.IGNORECASE)
        if len(parts) > 1:
            final_part = parts[-1].strip()
        else:
            final_part = response
    else:
        final_part = response
    
    return final_part, has_think


def match_answer_flexible(response_text: str, target: str, task_name: str = "") -> dict:
    """
    Flexibly match answer in response against target.
    Returns dict with match info.
    """
    result = {
        "official_match": False,  # Would match the official regex
        "content_match": False,   # Target appears in response (correct answer)
        "extracted": None,
        "match_pattern": None,
    }
    
    target_norm = normalize_answer(target, task_name)
    response_lower = response_text.lower()
    
    # 1. Check official format: "the answer is X"
    official_pattern = re.search(
        r'(?:so\s+)?the\s+answer\s+is\s+[:\s]*([^\n.!?]+)', 
        response_lower
    )
    if official_pattern:
        extracted = normalize_answer(official_pattern.group(1), task_name)
        result["extracted"] = extracted
        result["match_pattern"] = "official_the_answer_is"
        if extracted == target_norm or target_norm in extracted:
            result["official_match"] = True
            result["content_match"] = True
            return result
    
    # 2. Check if target appears anywhere in reasonable context
    # For options like (A), (B), etc.
    if re.match(r'^\([a-g]\)$', target_norm):
        letter = target_norm[1]  # Extract just the letter
        # Various option formats
        option_patterns = [
            (rf'\({letter}\)', "option_paren"),           # (A)
            (rf'\b{letter}\b\s*[:\.]', "option_colon"),   # A: or A.
            (rf'option\s+{letter}\b', "option_word"),     # Option A
            (rf'answer\s+is\s+\({letter}\)', "answer_is_paren"), # answer is (A)
            (rf'answer\s+is\s+{letter}\b', "answer_is_letter"),  # answer is A
            (rf'\*\*\({letter}\)\*\*', "bold_option"),    # **(A)**
            (rf'\*\*{letter}\*\*', "bold_letter"),        # **A**
            (rf':\s*\({letter}\)\s*$', "colon_end"),      # ends with : (A)
            (rf'\\boxed\{{{letter}\}}', "boxed"),         # \boxed{A}
            (rf'correct\s+answer\s+is[:\s]+\(?{letter}\)?', "correct_answer"), # correct answer is A
        ]
        for pat, name in option_patterns:
            if re.search(pat, response_lower, re.IGNORECASE):
                result["content_match"] = True
                result["extracted"] = f"({letter})"
                result["match_pattern"] = name
                return result
    
    # 3. For boolean/yes-no answers
    elif target_norm in ['true', 'false', 'yes', 'no', 'valid', 'invalid']:
        # Check various formats
        bool_patterns = [
            (rf'\b{target_norm}\b', "boolean_direct"),
            (rf'is\s+{target_norm}', "is_boolean"),
            (rf'result\s+is\s+{target_norm}', "result_is"),
            (rf':\s*{target_norm}', "colon_boolean"),
            (rf'\*\*{target_norm}\*\*', "bold_boolean"),
        ]
        for pat, name in bool_patterns:
            if re.search(pat, response_lower):
                result["content_match"] = True
                result["extracted"] = target_norm
                result["match_pattern"] = name
                return result
        
        # NEW: plausible/implausible mapping for sports_understanding etc.
        if target_norm == 'yes':
            # "plausible" (but NOT "implausible") means yes
            if re.search(r'\bplausible\b', response_lower) and not re.search(r'\bimplausible\b', response_lower):
                result["content_match"] = True
                result["extracted"] = "yes (plausible)"
                result["match_pattern"] = "plausible_yes"
                return result
        elif target_norm == 'no':
            # "implausible" means no
            if re.search(r'\bimplausible\b', response_lower):
                result["content_match"] = True
                result["extracted"] = "no (implausible)"
                result["match_pattern"] = "implausible_no"
                return result
    
    # 4. Direct target match (for complex answers like word lists)
    elif target_norm in response_lower:
        result["content_match"] = True
        result["extracted"] = target_norm
        result["match_pattern"] = "direct_match"
        return result
    
    # 5. Try various extraction patterns for any answer type
    extraction_patterns = [
        (r'answer\s*:\s*([^\n]+)', "answer_colon"),
        (r'final\s+answer\s*:\s*([^\n]+)', "final_answer"),
        (r'result\s+is\s+([^\n.]+)', "result_is"),
        (r'therefore\s*,?\s+([^\n.]+)', "therefore"),
        (r'thus\s*,?\s+([^\n.]+)', "thus"),
        (r'\\boxed\{([^}]+)\}', "boxed_extract"),
    ]
    
    for pattern, name in extraction_patterns:
        match = re.search(pattern, response_lower)
        if match:
            extracted = normalize_answer(match.group(1), task_name)
            if target_norm in extracted or extracted == target_norm:
                result["content_match"] = True
                result["extracted"] = extracted
                result["match_pattern"] = name
                return result
    
    return result


def analyze_sample(data: dict, task_name: str = "") -> dict:
    """Analyze a single sample."""
    target = data.get("target", "")
    resps = data.get("resps", [[]])
    response_text = resps[0][0] if resps and resps[0] else ""
    filtered = data.get("filtered_resps", [])
    official_valid = not (filtered and filtered[0] == "[invalid]")
    official_correct = data.get("exact_match", 0) == 1.0
    
    # Extract final answer (handling think tags)
    final_answer_text, has_think = extract_final_answer(response_text)
    
    # Flexible matching on final answer
    match_result = match_answer_flexible(final_answer_text, target, task_name)
    
    return {
        "doc_id": data.get("doc_id", ""),
        "target": target,
        "has_think": has_think,
        "official_valid": official_valid,
        "official_correct": official_correct,
        "content_correct": match_result["content_match"],
        "format_correct": official_valid and official_correct,
        "extracted": match_result["extracted"],
        "match_pattern": match_result["match_pattern"],
        "response_len": len(response_text),
        "final_answer_text": final_answer_text[:200] if final_answer_text else "",
    }


def analyze_task_file(filepath: str, limit_samples: int = 3) -> dict:
    """Analyze a single task's samples file."""
    stats = {
        "total": 0,
        "has_think": 0,
        "official_valid": 0,
        "official_correct": 0,
        "content_correct": 0,
        "format_issue": 0,  # content_correct but not official_correct
        "actually_wrong": 0,
        "patterns_used": defaultdict(int),
        "sample_issues": [],
    }
    
    with open(filepath) as f:
        for line in f:
            data = json.loads(line)
            stats["total"] += 1
            
            result = analyze_sample(data, filepath)
            
            if result["has_think"]:
                stats["has_think"] += 1
            if result["official_valid"]:
                stats["official_valid"] += 1
            if result["official_correct"]:
                stats["official_correct"] += 1
            if result["content_correct"]:
                stats["content_correct"] += 1
                if result["match_pattern"]:
                    stats["patterns_used"][result["match_pattern"]] += 1
            
            # Categorize issue
            if result["content_correct"] and not result["official_correct"]:
                stats["format_issue"] += 1
            elif not result["content_correct"]:
                stats["actually_wrong"] += 1
            
            # Store samples for review
            if len(stats["sample_issues"]) < limit_samples:
                if not result["official_correct"]:
                    stats["sample_issues"].append({
                        "doc_id": result["doc_id"],
                        "target": result["target"],
                        "content_correct": result["content_correct"],
                        "extracted": result["extracted"],
                        "pattern": result["match_pattern"],
                        "has_think": result["has_think"],
                        "final_text": result["final_answer_text"][:150],
                    })
    
    return stats


def analyze_config(config_path: str, limit_samples: int = 3) -> Tuple[dict, dict]:
    """Analyze all tasks in a config directory."""
    config_path = Path(config_path)
    sample_files = sorted(config_path.glob("samples_*.jsonl"))
    
    if not sample_files:
        print(f"No sample files found in {config_path}")
        return {}, {}
    
    print(f"\nFound {len(sample_files)} task files")
    
    overall = {
        "total": 0,
        "has_think": 0,
        "official_valid": 0,
        "official_correct": 0,
        "content_correct": 0,
        "format_issue": 0,
        "actually_wrong": 0,
        "patterns_used": defaultdict(int),
    }
    
    task_results = {}
    
    for sample_file in sample_files:
        # Extract task name
        task_name = sample_file.stem
        task_name = re.sub(r'_\d{4}-\d{2}-\d{2}T.*', '', task_name)
        task_name = task_name.replace('samples_bbh_cot_fewshot_', '')
        
        print(f"\n{'='*60}")
        print(f"Task: {task_name}")
        print(f"{'-'*60}")
        
        stats = analyze_task_file(str(sample_file), limit_samples)
        task_results[task_name] = stats
        
        # Calculate metrics
        total = stats["total"]
        official_acc = stats["official_correct"] / total * 100 if total else 0
        true_acc = stats["content_correct"] / total * 100 if total else 0
        think_rate = stats["has_think"] / total * 100 if total else 0
        format_issues = stats["format_issue"] / total * 100 if total else 0
        
        print(f"  Samples: {total}")
        print(f"  Think tags: {stats['has_think']} ({think_rate:.1f}%)")
        print(f"  Official accuracy: {stats['official_correct']}/{total} ({official_acc:.1f}%)")
        print(f"  True accuracy: {stats['content_correct']}/{total} ({true_acc:.1f}%)")
        print(f"  Format issues: {stats['format_issue']} ({format_issues:.1f}%)")
        print(f"  Actually wrong: {stats['actually_wrong']}")
        
        if stats["patterns_used"]:
            print(f"  Match patterns: {dict(stats['patterns_used'])}")
        
        # Show sample issues
        if stats["sample_issues"]:
            print(f"\n  Sample issues:")
            for s in stats["sample_issues"][:2]:
                status = "FORMAT" if s["content_correct"] else "WRONG"
                print(f"    [{status}] Doc {s['doc_id']}: target='{s['target']}' extracted='{s['extracted']}'")
                print(f"           Final: {s['final_text'][:80]}...")
        
        # Aggregate
        for key in ["total", "has_think", "official_valid", "official_correct", 
                    "content_correct", "format_issue", "actually_wrong"]:
            overall[key] += stats[key]
        for pat, count in stats["patterns_used"].items():
            overall["patterns_used"][pat] += count
    
    return task_results, overall


def print_summary(overall: dict, config_name: str):
    """Print overall summary."""
    print("\n" + "=" * 80)
    print(f"SUMMARY: {config_name}")
    print("=" * 80)
    
    total = overall["total"]
    if not total:
        print("No samples analyzed")
        return
    
    official_acc = overall["official_correct"] / total * 100
    true_acc = overall["content_correct"] / total * 100
    think_rate = overall["has_think"] / total * 100
    format_rate = overall["format_issue"] / total * 100
    wrong_rate = overall["actually_wrong"] / total * 100
    parse_rate = overall["official_valid"] / total * 100
    
    print(f"\nTotal samples: {total}")
    print(f"Think tags present: {overall['has_think']} ({think_rate:.1f}%)")
    
    print(f"\n--- ACCURACY METRICS ---")
    print(f"Official accuracy (benchmark): {overall['official_correct']}/{total} ({official_acc:.2f}%)")
    print(f"True accuracy (flexible):      {overall['content_correct']}/{total} ({true_acc:.2f}%)")
    print(f"Accuracy gap:                  +{true_acc - official_acc:.2f}%")
    
    print(f"\n--- ERROR BREAKDOWN ---")
    print(f"Format issues (correct but unrecognized): {overall['format_issue']} ({format_rate:.1f}%)")
    print(f"Actually wrong answers:                   {overall['actually_wrong']} ({wrong_rate:.1f}%)")
    print(f"Official parse rate:                      {overall['official_valid']} ({parse_rate:.1f}%)")
    
    if overall["patterns_used"]:
        print(f"\n--- MATCH PATTERNS ---")
        for pat, count in sorted(overall["patterns_used"].items(), key=lambda x: -x[1]):
            print(f"  {pat}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description='BBH Benchmark Analyzer (Rigorous)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_samples_v2.py --config 3shot-nosysprompt
  python analyze_samples_v2.py --config "top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt"
  python analyze_samples_v2.py --all
  python analyze_samples_v2.py --list
        """
    )
    
    parser.add_argument('--config', '-c', type=str, help='Config directory to analyze')
    parser.add_argument('--all', '-a', action='store_true', help='Analyze all configs')
    parser.add_argument('--list', '-l', action='store_true', help='List available configs')
    parser.add_argument('--limit', type=int, default=3, help='Sample limit per task (default: 3)')
    parser.add_argument('--base-dir', '-b', type=str, default=None, help='Base directory')
    
    args = parser.parse_args()
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    
    # Discover configs
    configs = {}
    for item in base_dir.iterdir():
        if item.is_dir() and list(item.glob("samples_*.jsonl")):
            configs[item.name] = item.name
    
    if args.list:
        print("Available configurations:")
        for name in sorted(configs):
            count = len(list((base_dir / name).glob("samples_*.jsonl")))
            print(f"  {name} ({count} tasks)")
        return
    
    # Determine what to analyze
    if args.config:
        to_analyze = [args.config]
    elif args.all:
        to_analyze = list(configs.keys())
    else:
        to_analyze = list(configs.keys())
    
    all_results = {}
    
    for config_name in to_analyze:
        config_path = base_dir / config_name
        if not config_path.exists():
            print(f"Config not found: {config_name}")
            continue
        
        print("\n" + "#" * 80)
        print(f"# CONFIG: {config_name}")
        print("#" * 80)
        
        task_results, overall = analyze_config(str(config_path), args.limit)
        all_results[config_name] = {"tasks": task_results, "overall": overall}
        
        print_summary(overall, config_name)
    
    # Comparison table if multiple
    if len(all_results) > 1:
        print("\n" + "#" * 80)
        print("# COMPARISON")
        print("#" * 80)
        
        print(f"\n{'Config':<50} {'Official':>10} {'True':>10} {'Gap':>10} {'Think':>8}")
        print("-" * 88)
        
        for name, data in sorted(all_results.items()):
            o = data["overall"]
            if o["total"]:
                off = o["official_correct"] / o["total"] * 100
                true = o["content_correct"] / o["total"] * 100
                gap = true - off
                think = o["has_think"] / o["total"] * 100
                print(f"{name:<50} {off:>9.1f}% {true:>9.1f}% {gap:>+9.1f}% {think:>7.0f}%")


if __name__ == "__main__":
    main()
