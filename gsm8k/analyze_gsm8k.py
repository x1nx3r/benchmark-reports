#!/usr/bin/env python3
"""
GSM8K Benchmark Sample Analyzer

Analyzes GSM8K benchmark results to understand:
- Answer extraction patterns
- Accuracy metrics
- Response quality issues (repetition, format)
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict


def extract_answer_improved(response_text: str, target: str = None) -> tuple[str, str]:
    """
    Attempt to extract a numeric answer using improved regex patterns.
    Returns (extracted_answer, pattern_name) or (None, None) if no match.
    """
    extraction_patterns = [
        # Standard GSM8K format: #### N
        ("hash_answer", re.compile(r"####\s*(\$?[\d,]+(?:\.\d+)?)", re.MULTILINE)),
        
        # "The answer is N" variants
        ("the_answer_is", re.compile(
            r"(?:the|so the|thus the|therefore the)\s+answer\s+is\s+\$?([\d,]+(?:\.\d+)?)", 
            re.IGNORECASE)),
        
        # "Answer: N" format
        ("answer_colon", re.compile(
            r"answer\s*:\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE)),
        
        # "= N" at end of calculation
        ("equals_answer", re.compile(
            r"=\s*\$?([\d,]+(?:\.\d+)?)\s*(?:dollars?|per day|per week|loaves?|eggs?|hours?)?\.?\s*$", 
            re.IGNORECASE | re.MULTILINE)),
        
        # "best answer is N"
        ("best_answer", re.compile(
            r"(?:the\s+)?best\s+answer\s+is\s+\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE)),
        
        # "final answer is N"
        ("final_answer", re.compile(
            r"(?:the\s+)?final\s+answer\s+is\s+\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE)),
        
        # "result is N"
        ("result_is", re.compile(
            r"(?:the\s+)?(?:final\s+)?result\s+is\s+\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE)),
        
        # "total is N"
        ("total_is", re.compile(
            r"(?:the\s+)?total\s+(?:is|=|equals)\s+\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE)),
        
        # "N dollars/hours/etc" at sentence end
        ("amount_unit", re.compile(
            r"\$?([\d,]+(?:\.\d+)?)\s*(?:dollars?|hours?|loaves?|eggs?|days?|weeks?|people|items?)\.?\s*$", 
            re.IGNORECASE | re.MULTILINE)),
        
        # Boxed answer: \boxed{N}
        ("boxed", re.compile(r"\\boxed\{([\d,]+(?:\.\d+)?)\}")),
        
        # Last number in response (fallback)
        ("last_number", re.compile(r"([\d,]+(?:\.\d+)?)\s*[.!]?\s*$")),
    ]
    
    for pattern_name, pattern in extraction_patterns:
        match = pattern.search(response_text)
        if match:
            answer = match.group(1).replace(",", "")
            return answer, pattern_name
    
    return None, None


def detect_repetition(response_text: str) -> dict:
    """Detect repetition patterns in response."""
    lines = response_text.split('\n')
    
    # Check for repeated sentences
    sentences = re.split(r'[.!?]+', response_text)
    sentence_counts = defaultdict(int)
    for s in sentences:
        s = s.strip()
        if len(s) > 20:
            sentence_counts[s] += 1
    
    repeated_sentences = {s: c for s, c in sentence_counts.items() if c > 2}
    
    # Check for "The answer is X" repetition
    answer_pattern = re.compile(r"the answer is \d+", re.IGNORECASE)
    answer_matches = answer_pattern.findall(response_text)
    
    return {
        "has_repetition": len(repeated_sentences) > 0 or len(answer_matches) > 3,
        "repeated_sentences": len(repeated_sentences),
        "answer_repetitions": len(answer_matches),
    }


def parse_target(target: str) -> str:
    """Extract the numeric answer from GSM8K target format."""
    # GSM8K format: "explanation... #### N"
    match = re.search(r"####\s*(\d+)", target)
    if match:
        return match.group(1)
    return target


def analyze_sample_file(filepath: str, limit_samples: int = 3) -> dict:
    """Analyze a single GSM8K samples JSONL file."""
    stats = {
        "total_samples": 0,
        "valid_answers": 0,
        "invalid_answers": 0,
        "exact_match_correct": 0,
        "exact_match_incorrect": 0,
        "has_repetition": 0,
        "improved_extractions": 0,
        "improved_matches": 0,
        "extraction_patterns_used": defaultdict(int),
        "invalid_samples": [],
        "answer_patterns": defaultdict(int),
    }
    
    with open(filepath, 'r') as f:
        for line in f:
            data = json.loads(line)
            stats["total_samples"] += 1
            
            doc_id = data.get("doc_id", "unknown")
            target = data.get("target", "")
            target_num = parse_target(target)
            filtered_resps = data.get("filtered_resps", [])
            resps = data.get("resps", [[]])
            response_text = resps[0][0] if resps and resps[0] else ""
            exact_match = data.get("exact_match", 0)
            
            # Check answer patterns
            if "####" in response_text:
                stats["answer_patterns"]["hash_answer"] += 1
            if re.search(r"the answer is", response_text, re.IGNORECASE):
                stats["answer_patterns"]["the_answer_is"] += 1
            if re.search(r"answer\s*:", response_text, re.IGNORECASE):
                stats["answer_patterns"]["answer_colon"] += 1
            
            # Check for repetition
            rep_info = detect_repetition(response_text)
            if rep_info["has_repetition"]:
                stats["has_repetition"] += 1
            
            # Check validity
            is_invalid = filtered_resps and filtered_resps[0] == "[invalid]"
            
            if is_invalid:
                stats["invalid_answers"] += 1
                
                # Try improved extraction
                extracted, pattern = extract_answer_improved(response_text, target_num)
                if extracted:
                    stats["improved_extractions"] += 1
                    stats["extraction_patterns_used"][pattern] += 1
                    
                    # Check if extracted matches target
                    if extracted == target_num:
                        stats["improved_matches"] += 1
                
                # Store sample for review
                if len(stats["invalid_samples"]) < limit_samples:
                    stats["invalid_samples"].append({
                        "doc_id": doc_id,
                        "target": target_num,
                        "response_preview": response_text[:300] + "..." if len(response_text) > 300 else response_text,
                        "response_end": "..." + response_text[-300:] if len(response_text) > 300 else "",
                        "repetition": rep_info,
                        "extracted": extracted,
                        "pattern": pattern,
                    })
            else:
                stats["valid_answers"] += 1
            
            # Track exact match
            if exact_match == 1.0:
                stats["exact_match_correct"] += 1
            else:
                stats["exact_match_incorrect"] += 1
    
    return stats


def analyze_config(config_path: str, limit_samples: int = 3) -> tuple[dict, dict]:
    """Analyze all sample files in a config directory."""
    config_path = Path(config_path)
    sample_files = list(config_path.rglob("samples_*.jsonl"))
    
    if not sample_files:
        print(f"No sample files found in {config_path}")
        return {}, {}
    
    print(f"\nFound {len(sample_files)} sample files in {config_path}")
    
    overall_stats = {
        "total_samples": 0,
        "valid_answers": 0,
        "invalid_answers": 0,
        "exact_match_correct": 0,
        "exact_match_incorrect": 0,
        "has_repetition": 0,
        "improved_extractions": 0,
        "improved_matches": 0,
        "extraction_patterns_used": defaultdict(int),
        "answer_patterns": defaultdict(int),
    }
    
    all_results = {}
    
    for sample_file in sample_files:
        # Extract task name from filename
        task_name = sample_file.stem.split("_")[1] if "_" in sample_file.stem else sample_file.stem
        
        print("=" * 60)
        print(f"Analyzing: {task_name}")
        print("-" * 60)
        
        stats = analyze_sample_file(str(sample_file), limit_samples)
        all_results[task_name] = stats
        
        # Print task stats
        print(f"  Total samples: {stats['total_samples']}")
        print(f"  Valid answers: {stats['valid_answers']}")
        print(f"  Invalid answers: {stats['invalid_answers']}")
        print(f"  Exact match correct: {stats['exact_match_correct']}")
        print(f"  Has repetition issues: {stats['has_repetition']}")
        
        if stats['total_samples'] > 0:
            accuracy = stats['exact_match_correct'] / stats['total_samples'] * 100
            print(f"  Accuracy: {accuracy:.1f}%")
            
            if stats['invalid_answers'] > 0:
                recovery_rate = stats['improved_extractions'] / stats['invalid_answers'] * 100
                potential_matches = stats['improved_matches']
                print(f"  Improved extraction: {stats['improved_extractions']}/{stats['invalid_answers']} ({recovery_rate:.1f}% of invalid)")
                potential_acc = (stats['exact_match_correct'] + potential_matches) / stats['total_samples'] * 100
                print(f"  Potential recovered matches: {potential_matches} (would boost accuracy to {potential_acc:.1f}%)")
        
        # Print answer patterns
        if stats['answer_patterns']:
            print(f"\n  Answer patterns found:")
            for pattern, count in sorted(stats['answer_patterns'].items(), key=lambda x: -x[1]):
                print(f"    - {pattern}: {count}")
        
        # Print sample invalid responses
        if stats['invalid_samples']:
            print(f"\n  Sample invalid responses (showing up to {limit_samples}):")
            for sample in stats['invalid_samples']:
                print(f"    Doc ID {sample['doc_id']} (target: {sample['target']}):")
                print(f"      Extracted: {sample['extracted']} (pattern: {sample['pattern']})")
                print(f"      Repetition issues: {sample['repetition']}")
                if sample['response_end']:
                    print(f"      Response end: {sample['response_end'][:150]}...")
        
        # Aggregate overall stats
        for key in ["total_samples", "valid_answers", "invalid_answers", 
                    "exact_match_correct", "exact_match_incorrect", "has_repetition",
                    "improved_extractions", "improved_matches"]:
            overall_stats[key] += stats[key]
        
        for pattern, count in stats["extraction_patterns_used"].items():
            overall_stats["extraction_patterns_used"][pattern] += count
        
        for pattern, count in stats["answer_patterns"].items():
            overall_stats["answer_patterns"][pattern] += count
    
    return all_results, overall_stats


def print_overall_summary(stats: dict, config_name: str):
    """Print overall summary statistics."""
    print("\n" + "=" * 80)
    print(f"OVERALL SUMMARY: {config_name}")
    print("=" * 80)
    
    print(f"\nTotal samples analyzed: {stats['total_samples']}")
    print(f"Valid answers (parsed successfully): {stats['valid_answers']}")
    print(f"Invalid answers (parsing failed): {stats['invalid_answers']}")
    print(f"Samples with repetition issues: {stats['has_repetition']}")
    print(f"Exact match correct: {stats['exact_match_correct']}")
    print(f"Exact match incorrect: {stats['exact_match_incorrect']}")
    
    if stats['total_samples'] > 0:
        accuracy = stats['exact_match_correct'] / stats['total_samples'] * 100
        valid_rate = stats['valid_answers'] / stats['total_samples'] * 100
        rep_rate = stats['has_repetition'] / stats['total_samples'] * 100
        
        print(f"\nOverall accuracy: {accuracy:.2f}%")
        print(f"Answer parsing success rate: {valid_rate:.2f}%")
        print(f"Repetition issue rate: {rep_rate:.2f}%")
        
        # Improved extraction summary
        if stats['invalid_answers'] > 0:
            recovery_rate = stats['improved_extractions'] / stats['invalid_answers'] * 100
            potential_accuracy = (stats['exact_match_correct'] + stats['improved_matches']) / stats['total_samples'] * 100
            print(f"\n--- IMPROVED EXTRACTION ANALYSIS ---")
            print(f"Invalid answers that could be re-parsed: {stats['improved_extractions']}/{stats['invalid_answers']} ({recovery_rate:.1f}%)")
            print(f"Answers that match target after improved extraction: {stats['improved_matches']}")
            print(f"Potential accuracy with improved regex: {potential_accuracy:.2f}% (vs {accuracy:.2f}% original)")
            print(f"Potential accuracy gain: +{potential_accuracy - accuracy:.2f}%")
    
    # Pattern usage
    if stats['extraction_patterns_used']:
        print(f"\nPatterns that recovered answers:")
        for pattern, count in sorted(stats['extraction_patterns_used'].items(), key=lambda x: -x[1]):
            print(f"  - {pattern}: {count}")
    
    # Answer patterns
    if stats['answer_patterns']:
        print(f"\nAnswer patterns across all samples:")
        for pattern, count in sorted(stats['answer_patterns'].items(), key=lambda x: -x[1]):
            pct = count / stats['total_samples'] * 100
            print(f"  - {pattern}: {count} ({pct:.1f}%)")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Analyze GSM8K benchmark sample files for answer patterns and accuracy.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_gsm8k.py --config testrun-complete-0-shot
  python analyze_gsm8k.py --config testrun-complete-8-shot --limit 5
  python analyze_gsm8k.py --all
  python analyze_gsm8k.py --list
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Specific config directory to analyze'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Analyze all configurations'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available configurations'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=3,
        help='Limit number of invalid samples to show (default: 3)'
    )
    parser.add_argument(
        '--base-dir', '-b',
        type=str,
        default=None,
        help='Base directory containing config folders (default: script directory)'
    )
    
    args = parser.parse_args()
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    
    # Discover configurations
    configs = {}
    for item in base_dir.iterdir():
        if item.is_dir():
            # Check if it has sample files (recursively)
            if list(item.rglob("samples_*.jsonl")):
                configs[item.name] = item.name
    
    if args.list:
        print("Available configurations:")
        for config_name in sorted(configs.keys()):
            config_path = base_dir / config_name
            sample_count = len(list(config_path.rglob("samples_*.jsonl")))
            print(f"  ✓ {config_name} ({sample_count} sample files)")
        return
    
    # Determine which configs to analyze
    if args.config:
        configs_to_analyze = [args.config]
    elif args.all:
        configs_to_analyze = list(configs.keys())
    else:
        configs_to_analyze = list(configs.keys())
    
    all_results = {}
    
    for config_name in configs_to_analyze:
        config_path = base_dir / config_name
        if config_path.exists():
            print("\n" + "#" * 80)
            print(f"# ANALYZING: {config_name}")
            print("#" * 80)
            
            results, overall_stats = analyze_config(str(config_path), limit_samples=args.limit)
            all_results[config_name] = {
                "results": results,
                "overall": overall_stats
            }
            print_overall_summary(overall_stats, config_name)
        else:
            print(f"Directory not found: {config_path}")
    
    # Comparison if we have multiple
    if len(all_results) > 1:
        print("\n" + "#" * 80)
        print("# COMPARISON ACROSS CONFIGS")
        print("#" * 80)
        
        print(f"\n{'Config':<40} {'Accuracy':>10} {'Parse Rate':>12} {'Repetition':>12}")
        print("-" * 74)
        for config_name, data in sorted(all_results.items()):
            stats = data['overall']
            if stats['total_samples'] > 0:
                acc = stats['exact_match_correct'] / stats['total_samples'] * 100
                parse = stats['valid_answers'] / stats['total_samples'] * 100
                rep = stats['has_repetition'] / stats['total_samples'] * 100
                print(f"{config_name:<40} {acc:>9.1f}% {parse:>11.1f}% {rep:>11.1f}%")


if __name__ == "__main__":
    main()
