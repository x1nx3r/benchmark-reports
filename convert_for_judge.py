#!/usr/bin/env python3
"""
Convert BBH benchmark samples to JSONL format for LLM-as-judge evaluation.

Creates one JSONL file per task with:
- QUESTION: The prompt/question given to the model
- MODEL_RESPONSE: The model's complete response
- GROUND_TRUTH: The expected correct answer
"""

import json
import argparse
import re
from pathlib import Path


def extract_question(doc: dict) -> str:
    """Extract the question from the document."""
    # The question is typically in 'doc' -> 'input' or 'question'
    doc_content = doc.get('doc', {})
    
    if isinstance(doc_content, dict):
        # Try common field names
        for field in ['input', 'question', 'text', 'prompt']:
            if field in doc_content:
                return doc_content[field]
        # Return the whole doc if no specific field found
        return str(doc_content)
    
    return str(doc_content)


def process_sample_file(input_file: Path, output_file: Path) -> int:
    """Process a single sample file and write to output JSONL."""
    count = 0
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for idx, line in enumerate(f_in, start=1):
            data = json.loads(line)
            
            # Extract fields
            question = extract_question(data)
            
            # Model response is in resps[0][0]
            resps = data.get('resps', [[]])
            model_response = resps[0][0] if resps and resps[0] else ""
            
            # Ground truth is in target
            ground_truth = data.get('target', '')
            
            # Create output entry with ID
            entry = {
                'ID': idx,
                'QUESTION': question,
                'MODEL_RESPONSE': model_response,
                'GROUND_TRUTH': ground_truth,
                'doc_id': data.get('doc_id', ''),
                'exact_match': data.get('exact_match', None),
            }
            
            f_out.write(json.dumps(entry, ensure_ascii=False) + '\n')
            count += 1
    
    return count


def main():
    parser = argparse.ArgumentParser(
        description='Convert BBH samples to JSONL for LLM-as-judge evaluation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python convert_for_judge.py --config bbh/top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt --output llm_judge_data
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        required=True,
        help='Path to config directory containing sample JSONL files'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='llm_judge_data',
        help='Output directory for converted JSONL files (default: llm_judge_data)'
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    output_path = Path(args.output)
    
    if not config_path.exists():
        print(f"Error: Config directory not found: {config_path}")
        return
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all sample files
    sample_files = sorted(config_path.glob("samples_*.jsonl"))
    
    if not sample_files:
        print(f"No sample files found in {config_path}")
        return
    
    print(f"Found {len(sample_files)} task files")
    print(f"Output directory: {output_path}\n")
    
    total_samples = 0
    
    for sample_file in sample_files:
        # Extract task name
        task_name = sample_file.stem
        task_name = re.sub(r'_\d{4}-\d{2}-\d{2}T.*', '', task_name)
        task_name = task_name.replace('samples_bbh_cot_fewshot_', '')
        
        # Output file
        output_file = output_path / f"{task_name}.jsonl"
        
        # Process
        count = process_sample_file(sample_file, output_file)
        total_samples += count
        
        print(f"  {task_name}: {count} samples -> {output_file.name}")
    
    print(f"\nTotal: {total_samples} samples across {len(sample_files)} tasks")
    print(f"Output: {output_path}/")


if __name__ == "__main__":
    main()
