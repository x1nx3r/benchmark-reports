#!/usr/bin/env python3
"""
BBH Benchmark Sample Analyzer

Parses JSONL sample files from BBH benchmark results and checks for:
1. <think></think> tags in model responses
2. Various answer format patterns
3. Invalid/filtered responses
4. Response statistics
"""

import json
import re
import os
import glob
from collections import defaultdict
from pathlib import Path


def extract_answer_improved(response_text: str, target: str = None) -> tuple[str, str]:
    """
    Attempt to extract an answer using improved regex patterns.
    Returns (extracted_answer, pattern_name) or (None, None) if no match.
    """
    # Priority-ordered patterns for answer extraction
    extraction_patterns = [
        # Highest priority: LaTeX boxed answers (common in math-trained models)
        ("boxed_latex", re.compile(
            r"\$?\\\\?\\boxed\{([^}]+)\}\$?", re.IGNORECASE)),
        ("boxed_latex_double", re.compile(
            r"\\\\boxed\{([^}]+)\}", re.IGNORECASE)),
        
        # "Final Answer:" header patterns (often at end of response)
        ("final_answer_header", re.compile(
            r"Final\s+Answer\s*[:\-]?\s*(?:The\s+)?(?:final\s+)?(?:answer\s+is\s+)?[:\-]?\s*\$?\\\\?\\?boxed\{([^}]+)\}\$?", re.IGNORECASE)),
        ("final_answer_is_boxed", re.compile(
            r"(?:the\s+)?final\s+answer\s+is\s+\$?\\\\?\\?boxed\{([^}]+)\}\$?", re.IGNORECASE)),
        ("final_answer_plain", re.compile(
            r"Final\s+Answer\s*[:\-]\s*(?:The\s+)?(?:answer\s+is\s+)?([^\n\.]+?)(?:\.|$)", re.IGNORECASE)),
        
        # "Thus, the result/answer is" patterns
        ("thus_result_is", re.compile(
            r"Thus,?\s+(?:the\s+)?(?:result|answer|final\s+answer)\s+is\s+([^\.\n]+)", re.IGNORECASE)),
        
        # High priority: explicit answer statements
        ("so_the_answer_is", re.compile(
            r"so,?\s+(?:the\s+)?answer\s+is\s+[:\s]*([^\.\n]+)", re.IGNORECASE)),
        ("the_answer_is", re.compile(
            r"(?:^|\s)the\s+answer\s+is\s+[:\s]*([^\.\n]+)", re.IGNORECASE)),
        ("answer_is", re.compile(
            r"answer\s+is\s+[:\s]*([^\.\n]+)", re.IGNORECASE)),
        
        # Therefore/Thus patterns
        ("therefore_answer", re.compile(
            r"therefore,?\s+(?:the\s+)?(?:answer|result|final\s+answer)\s+is\s+[:\s]*([^\.\n]+)", re.IGNORECASE)),
        ("thus_answer", re.compile(
            r"thus,?\s+(?:the\s+)?(?:answer|result)\s+is\s+[:\s]*([^\.\n]+)", re.IGNORECASE)),
        ("hence_answer", re.compile(
            r"hence,?\s+(?:the\s+)?(?:answer|result)\s+is\s+[:\s]*([^\.\n]+)", re.IGNORECASE)),
        
        # Final answer variants
        ("final_answer_colon", re.compile(
            r"final\s+answer\s*[:=]\s*([^\.\n]+)", re.IGNORECASE)),
        ("final_result", re.compile(
            r"final\s+result\s*[:=]?\s*is?\s*([^\.\n]+)", re.IGNORECASE)),
        
        # Conclusion patterns
        ("this_gives_us", re.compile(
            r"this\s+gives\s+us\s+([^\.\n]+)", re.IGNORECASE)),
        ("we_get", re.compile(
            r"(?:we|I)\s+get\s*[:=]?\s*([^\.\n]+)", re.IGNORECASE)),
        ("which_is", re.compile(
            r"which\s+is\s+([^\.\n]+?)(?:\.|$)", re.IGNORECASE)),
        ("result_is", re.compile(
            r"(?:the\s+)?result\s+is\s+([^\.\n]+)", re.IGNORECASE)),
        
        # Option/choice patterns (for multiple choice)
        ("correct_answer", re.compile(
            r"(?:the\s+)?correct\s+(?:answer|option|choice)\s+is\s+([^\.\n]+)", re.IGNORECASE)),
        ("answer_should_be", re.compile(
            r"(?:the\s+)?answer\s+should\s+be\s+([^\.\n]+)", re.IGNORECASE)),
        ("answer_would_be", re.compile(
            r"(?:the\s+)?answer\s+would\s+be\s+([^\.\n]+)", re.IGNORECASE)),
        
        # Boolean/Yes-No at end of response
        ("ends_with_boolean", re.compile(
            r"(?:^|\n)\s*(True|False|Yes|No)\s*\.?\s*$", re.IGNORECASE | re.MULTILINE)),
        
        # Parenthetical answer at end
        ("ends_with_option", re.compile(
            r"(?:^|\n)\s*\(?([A-K])\)?\s*\.?\s*$", re.IGNORECASE | re.MULTILINE)),
        
        # "So X" at very end (common conclusion)
        ("so_conclusion", re.compile(
            r"[Ss]o,?\s+(True|False|Yes|No|valid|invalid|\([A-K]\))\s*\.?\s*$")),
        
        # Answer: X format
        ("answer_colon_eol", re.compile(
            r"[Aa]nswer\s*:\s*([^\n]+?)(?:\n|$)")),
        
        # Bracket/parenthesis answers
        ("bracketed_answer", re.compile(
            r"(?:is|=)\s*\[([^\]]+)\]", re.IGNORECASE)),
        
        # ========== NEW PATTERNS FROM SAMPLE ANALYSIS ==========
        
        # Task-specific: Formal Fallacies (valid/invalid conclusions)
        ("answer_valid_invalid", re.compile(
            r"[Aa]nswer\s*:\s*(valid|invalid)\s*\.?\s*$", re.IGNORECASE | re.MULTILINE)),
        ("argument_is_valid", re.compile(
            r"(?:the\s+)?argument\s+is\s+(valid|invalid|sound)", re.IGNORECASE)),
        ("so_it_is_valid", re.compile(
            r"[Ss]o,?\s+(?:it\s+)?(?:is\s+)?(valid|invalid)\s*\.?\s*$")),
        ("conclusion_valid", re.compile(
            r"(?:the\s+)?(?:conclusion|argument)\s+(?:is\s+)?(valid|invalid)", re.IGNORECASE)),
        
        # Task-specific: Snarks (sarcastic option identification)
        ("sarcastic_option_is", re.compile(
            r"(?:the\s+)?sarcastic\s+(?:option|statement|one)\s+is\s+\(?([A-K])\)?", re.IGNORECASE)),
        ("so_sarcastic_is", re.compile(
            r"[Ss]o,?\s+(?:the\s+)?sarcastic\s+(?:option|statement)?\s*(?:is\s+)?\(?([A-K])\)?", re.IGNORECASE)),
        
        # Task-specific: Movie recommendation, logical deduction
        ("so_option_is", re.compile(
            r"[Ss]o\s+(?:the\s+)?(?:correct\s+)?option\s+(?:is\s+)?\(?([A-K])\)?", re.IGNORECASE)),
        ("option_x_is_correct", re.compile(
            r"(?:option|choice)\s+\(?([A-K])\)?\s+is\s+(?:the\s+)?(?:correct|right|best)", re.IGNORECASE)),
        ("which_is_option", re.compile(
            r"which\s+(?:is\s+|corresponds\s+to\s+)?option\s+\(?([A-K])\)?", re.IGNORECASE)),
        
        # Conclusion with option letter at end
        ("therefore_option", re.compile(
            r"[Tt]herefore,?\s+(?:the\s+)?(?:correct\s+)?(?:answer|option)\s+is\s+\(?([A-K])\)?", re.IGNORECASE)),
        ("thus_option", re.compile(
            r"[Tt]hus,?\s+(?:the\s+)?(?:correct\s+)?(?:answer|option)\s+is\s+\(?([A-K])\)?", re.IGNORECASE)),
        
        # "So the correct answer is option X"
        ("so_correct_answer_option", re.compile(
            r"[Ss]o,?\s+(?:the\s+)?correct\s+answer\s+(?:is\s+)?(?:option\s+)?\(?([A-K])\)?", re.IGNORECASE)),
        
        # Ends with option reference in various forms
        ("ends_option_letter", re.compile(
            r"(?:is\s+|be\s+)\(?([A-K])\)?\s*[.!]?\s*$", re.IGNORECASE)),
        ("answer_becomes", re.compile(
            r"(?:the\s+)?(?:final\s+)?answer\s+(?:becomes|turns out to be)\s+\(?([A-K])\)?", re.IGNORECASE)),
        
        # Boolean conclusions in various forms
        ("verdict_is", re.compile(
            r"(?:the\s+)?(?:final\s+)?verdict\s+is\s+(True|False|Yes|No|valid|invalid)", re.IGNORECASE)),
        ("final_verdict", re.compile(
            r"[Ff]inal\s+[Vv]erdict\s*:\s*(True|False|Yes|No|valid|invalid)", re.IGNORECASE)),
        ("so_final_answer", re.compile(
            r"[Ss]o,?\s+(?:the\s+)?final\s+answer\s+is\s+(True|False|Yes|No|valid|invalid|\([A-K]\))", re.IGNORECASE)),
        
        # Extract option from "The X is the Y" patterns common in logical deduction
        ("the_x_is_option", re.compile(
            r"(?:The\s+)(?:correct\s+)?(?:answer|choice|option)\s+is\s+\(?([A-K])\)?(?:\s|\.|\)|$)", re.IGNORECASE)),
        
        # Dyck languages - look for bracket-only answers at end
        ("dyck_brackets_end", re.compile(
            r"(?:^|\n)\s*([}\]>\)]+)\s*$", re.MULTILINE)),
        
        # Word sorting - numbered list final item (very last numbered item)
        ("numbered_list_last", re.compile(
            r"\d+\.\s+(\w+)\s*$", re.MULTILINE)),
    ]
    
    for pattern_name, pattern in extraction_patterns:
        match = pattern.search(response_text)
        if match:
            answer = match.group(1).strip()
            # Clean up the answer
            answer = answer.rstrip('.,;:')
            if answer:
                return answer, pattern_name
    
    return None, None


def analyze_sample_file(filepath: str) -> dict:
    """Analyze a single JSONL sample file."""
    stats = {
        "total_samples": 0,
        "think_tags": 0,
        "valid_answers": 0,
        "invalid_answers": 0,
        "exact_match_correct": 0,
        "exact_match_incorrect": 0,
        "answer_patterns": defaultdict(int),
        "think_tag_samples": [],
        "invalid_samples": [],
        # New stats for improved extraction
        "improved_extractions": 0,
        "improved_matches": 0,
        "extraction_patterns_used": defaultdict(int),
    }
    
    # Regex patterns to check (original benchmark patterns)
    patterns = {
        "think_open": re.compile(r"<think>", re.IGNORECASE),
        "think_close": re.compile(r"</think>", re.IGNORECASE),
        "think_block": re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL),
        "answer_is": re.compile(r"the answer is\s+(.+?)[\.\s\n]", re.IGNORECASE),
        "so_answer_is": re.compile(r"so the answer is\s+(.+?)[\.\s\n]", re.IGNORECASE),
        "therefore": re.compile(r"therefore,?\s+(?:the\s+)?(?:answer|result)\s+is\s+(.+?)[\.\s\n]", re.IGNORECASE),
        "final_answer": re.compile(r"final\s+answer[:\s]+(.+?)[\.\s\n]", re.IGNORECASE),
        "answer_colon": re.compile(r"answer[:\s]+(.+?)[\.\s\n]", re.IGNORECASE),
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                stats["total_samples"] += 1
                
                # Get the model response
                resps = data.get("resps", [[]])
                response_text = resps[0][0] if resps and resps[0] else ""
                
                # Check for think tags
                has_think_open = bool(patterns["think_open"].search(response_text))
                has_think_close = bool(patterns["think_close"].search(response_text))
                has_think_block = bool(patterns["think_block"].search(response_text))
                
                if has_think_open or has_think_close or has_think_block:
                    stats["think_tags"] += 1
                    stats["think_tag_samples"].append({
                        "doc_id": data.get("doc_id"),
                        "has_open": has_think_open,
                        "has_close": has_think_close,
                        "has_block": has_think_block,
                        "preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
                    })
                
                # Check answer patterns
                for pattern_name, pattern in patterns.items():
                    if pattern_name.startswith("think"):
                        continue
                    if pattern.search(response_text):
                        stats["answer_patterns"][pattern_name] += 1
                
                # Check filtered response
                filtered_resp = data.get("filtered_resps", [])
                target = data.get("target", "")
                is_invalid = filtered_resp and filtered_resp[0] == "[invalid]"
                
                if is_invalid:
                    stats["invalid_answers"] += 1
                    
                    # Try improved extraction on invalid responses
                    extracted, pattern_used = extract_answer_improved(response_text, target)
                    if extracted:
                        stats["improved_extractions"] += 1
                        stats["extraction_patterns_used"][pattern_used] += 1
                        
                        # Check if extracted answer matches target
                        extracted_clean = extracted.strip().lower()
                        target_clean = target.strip().lower()
                        
                        # Flexible matching
                        is_match = (
                            extracted_clean == target_clean or
                            extracted_clean in target_clean or
                            target_clean in extracted_clean or
                            # Handle option format: (A) vs A
                            extracted_clean.strip('()') == target_clean.strip('()') or
                            # Handle "true"/"false" variations
                            (extracted_clean in ['true', 'yes'] and target_clean in ['true', 'yes']) or
                            (extracted_clean in ['false', 'no'] and target_clean in ['false', 'no'])
                        )
                        
                        if is_match:
                            stats["improved_matches"] += 1
                    
                    stats["invalid_samples"].append({
                        "doc_id": data.get("doc_id"),
                        "target": target,
                        "preview": response_text[:300] + "..." if len(response_text) > 300 else response_text,
                        "improved_extraction": extracted,
                        "extraction_pattern": pattern_used,
                    })
                else:
                    stats["valid_answers"] += 1
                
                # Check exact match
                exact_match = data.get("exact_match", 0)
                if exact_match == 1.0:
                    stats["exact_match_correct"] += 1
                else:
                    stats["exact_match_incorrect"] += 1
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num} in {filepath}: {e}")
    
    return stats


def analyze_directory(directory: str, limit_invalid_samples: int = 5) -> dict:
    """Analyze all JSONL files in a directory."""
    results = {}
    
    # Find all sample JSONL files
    pattern = os.path.join(directory, "samples_*.jsonl")
    files = glob.glob(pattern)
    
    print(f"\nFound {len(files)} sample files in {directory}")
    print("=" * 80)
    
    overall_stats = {
        "total_samples": 0,
        "think_tags": 0,
        "valid_answers": 0,
        "invalid_answers": 0,
        "exact_match_correct": 0,
        "exact_match_incorrect": 0,
        "answer_patterns": defaultdict(int),
        "files_with_think_tags": [],
        # Improved extraction stats
        "improved_extractions": 0,
        "improved_matches": 0,
        "extraction_patterns_used": defaultdict(int),
    }
    
    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        # Extract task name from filename
        task_name = filename.replace("samples_", "").split("_2025-")[0]
        
        print(f"\nAnalyzing: {task_name}")
        print("-" * 60)
        
        stats = analyze_sample_file(filepath)
        results[task_name] = stats
        
        # Print summary for this file
        print(f"  Total samples: {stats['total_samples']}")
        print(f"  Think tags found: {stats['think_tags']}")
        print(f"  Valid answers: {stats['valid_answers']}")
        print(f"  Invalid answers: {stats['invalid_answers']}")
        print(f"  Exact match correct: {stats['exact_match_correct']}")
        print(f"  Exact match incorrect: {stats['exact_match_incorrect']}")
        
        accuracy = stats['exact_match_correct'] / stats['total_samples'] * 100 if stats['total_samples'] > 0 else 0
        print(f"  Accuracy: {accuracy:.1f}%")
        
        # Print improved extraction stats
        if stats['invalid_answers'] > 0:
            recovery_pct = stats['improved_extractions'] / stats['invalid_answers'] * 100
            print(f"  Improved extraction: {stats['improved_extractions']}/{stats['invalid_answers']} ({recovery_pct:.1f}% of invalid)")
            if stats['improved_matches'] > 0:
                print(f"  Potential recovered matches: {stats['improved_matches']} (would boost accuracy to {((stats['exact_match_correct'] + stats['improved_matches']) / stats['total_samples'] * 100):.1f}%)")
        
        # Print answer patterns
        if stats['answer_patterns']:
            print(f"  Answer patterns found:")
            for pattern, count in sorted(stats['answer_patterns'].items(), key=lambda x: -x[1]):
                print(f"    - {pattern}: {count}")
        
        # Print invalid sample previews (limited)
        if stats['invalid_samples'] and limit_invalid_samples > 0:
            print(f"\n  Sample invalid responses (showing up to {limit_invalid_samples}):")
            for sample in stats['invalid_samples'][:limit_invalid_samples]:
                print(f"    Doc ID {sample['doc_id']} (target: {sample['target']}):")
                preview_lines = sample['preview'].split('\n')[:3]
                for line in preview_lines:
                    print(f"      {line[:80]}{'...' if len(line) > 80 else ''}")
        
        # Aggregate stats
        overall_stats["total_samples"] += stats["total_samples"]
        overall_stats["think_tags"] += stats["think_tags"]
        overall_stats["valid_answers"] += stats["valid_answers"]
        overall_stats["invalid_answers"] += stats["invalid_answers"]
        overall_stats["exact_match_correct"] += stats["exact_match_correct"]
        overall_stats["exact_match_incorrect"] += stats["exact_match_incorrect"]
        
        for pattern, count in stats["answer_patterns"].items():
            overall_stats["answer_patterns"][pattern] += count
        
        if stats["think_tags"] > 0:
            overall_stats["files_with_think_tags"].append(task_name)
        
        # Aggregate improved extraction stats
        overall_stats["improved_extractions"] += stats.get("improved_extractions", 0)
        overall_stats["improved_matches"] += stats.get("improved_matches", 0)
        for pattern, count in stats.get("extraction_patterns_used", {}).items():
            overall_stats["extraction_patterns_used"][pattern] += count
    
    return results, overall_stats


def print_overall_summary(stats: dict, config_name: str):
    """Print overall summary statistics."""
    print("\n" + "=" * 80)
    print(f"OVERALL SUMMARY: {config_name}")
    print("=" * 80)
    
    print(f"\nTotal samples analyzed: {stats['total_samples']}")
    print(f"Samples with <think> tags: {stats['think_tags']}")
    print(f"Valid answers (parsed successfully): {stats['valid_answers']}")
    print(f"Invalid answers (parsing failed): {stats['invalid_answers']}")
    print(f"Exact match correct: {stats['exact_match_correct']}")
    print(f"Exact match incorrect: {stats['exact_match_incorrect']}")
    
    if stats['total_samples'] > 0:
        accuracy = stats['exact_match_correct'] / stats['total_samples'] * 100
        valid_rate = stats['valid_answers'] / stats['total_samples'] * 100
        think_rate = stats['think_tags'] / stats['total_samples'] * 100
        
        print(f"\nOverall accuracy: {accuracy:.2f}%")
        print(f"Answer parsing success rate: {valid_rate:.2f}%")
        print(f"Think tag occurrence rate: {think_rate:.2f}%")
        
        # Improved extraction summary
        if stats['invalid_answers'] > 0:
            recovery_rate = stats['improved_extractions'] / stats['invalid_answers'] * 100
            potential_accuracy = (stats['exact_match_correct'] + stats['improved_matches']) / stats['total_samples'] * 100
            print(f"\n--- IMPROVED EXTRACTION ANALYSIS ---")
            print(f"Invalid answers that could be re-parsed: {stats['improved_extractions']}/{stats['invalid_answers']} ({recovery_rate:.1f}%)")
            print(f"Answers that match target after improved extraction: {stats['improved_matches']}")
            print(f"Potential accuracy with improved regex: {potential_accuracy:.2f}% (vs {accuracy:.2f}% original)")
            print(f"Potential accuracy gain: +{potential_accuracy - accuracy:.2f}%")
            
            if stats['extraction_patterns_used']:
                print(f"\nPatterns that recovered answers:")
                for pattern, count in sorted(stats['extraction_patterns_used'].items(), key=lambda x: -x[1])[:10]:
                    print(f"  - {pattern}: {count}")
    
    print(f"\nAnswer patterns across all samples:")
    for pattern, count in sorted(stats['answer_patterns'].items(), key=lambda x: -x[1]):
        pct = count / stats['total_samples'] * 100 if stats['total_samples'] > 0 else 0
        print(f"  - {pattern}: {count} ({pct:.1f}%)")
    
    if stats['files_with_think_tags']:
        print(f"\nTasks with <think> tags: {len(stats['files_with_think_tags'])}")
        for task in stats['files_with_think_tags']:
            print(f"  - {task}")
    else:
        print("\nNo <think> tags found in any samples.")


def main():
    """Main entry point with CLI argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze BBH benchmark sample files for answer patterns and accuracy.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_samples.py --config 3shot-nosysprompt
  python analyze_samples.py --config "top_p0.95,rep_penalty_1.05-zeroshot-sysprompt" --limit 5
  python analyze_samples.py --all
  python analyze_samples.py --list
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Specific config directory to analyze (e.g., "3shot-nosysprompt")'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Analyze all known configurations'
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
        help='Limit number of invalid samples to show per task (default: 3)'
    )
    parser.add_argument(
        '--base-dir', '-b',
        type=str,
        default=None,
        help='Base directory containing config folders (default: script directory)'
    )
    
    args = parser.parse_args()
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    
    # Known configurations
    known_configs = {
        "0shot-nosysprompt": "0-shot without system prompt",
        "3shot-nosysprompt": "3-shot without system prompt",
        "3shot-withsysprompt": "3-shot with system prompt",
        "top_p0.95,rep_penalty_1.05-zeroshot-sysprompt": "0-shot with sys (top_p=0.95, rep_penalty=1.05)",
    }
    
    # Auto-discover additional configs
    for item in base_dir.iterdir():
        if item.is_dir() and item.name not in known_configs:
            # Check if it looks like a config dir (has samples_*.jsonl files)
            if list(item.glob("samples_*.jsonl")):
                known_configs[item.name] = item.name
    
    if args.list:
        print("Available configurations:")
        for config_dir, config_name in sorted(known_configs.items()):
            full_path = base_dir / config_dir
            status = "✓" if full_path.exists() else "✗"
            print(f"  {status} {config_dir}")
            if full_path.exists():
                sample_count = len(list(full_path.glob("samples_*.jsonl")))
                print(f"      ({sample_count} task files)")
        return
    
    # Determine which configs to analyze
    if args.config:
        configs_to_analyze = [(args.config, known_configs.get(args.config, args.config))]
    elif args.all:
        configs_to_analyze = list(known_configs.items())
    else:
        # Default: analyze all known configs
        configs_to_analyze = list(known_configs.items())
    
    all_results = {}
    
    for config_dir, config_name in configs_to_analyze:
        full_path = base_dir / config_dir
        if full_path.exists():
            print("\n" + "#" * 80)
            print(f"# ANALYZING: {config_name}")
            print("#" * 80)
            
            results, overall_stats = analyze_directory(str(full_path), limit_invalid_samples=args.limit)
            all_results[config_dir] = {
                "results": results,
                "overall": overall_stats
            }
            print_overall_summary(overall_stats, config_name)
        else:
            print(f"Directory not found: {full_path}")
    
    # Compare configs if we have specific pairs
    if "3shot-nosysprompt" in all_results and "3shot-withsysprompt" in all_results:
        print("\n" + "#" * 80)
        print("# COMPARISON: 3-shot With vs Without System Prompt")
        print("#" * 80)
        
        for key in ["think_tags", "valid_answers", "invalid_answers", "exact_match_correct"]:
            val1 = all_results["3shot-nosysprompt"]["overall"][key]
            val2 = all_results["3shot-withsysprompt"]["overall"][key]
            diff = val2 - val1
            print(f"{key}: No SysPrompt={val1}, With SysPrompt={val2}, Diff={diff:+d}")


if __name__ == "__main__":
    main()
