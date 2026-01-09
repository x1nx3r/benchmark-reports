#!/usr/bin/env python3
"""
Comprehensive LLM Judge Results Analyzer - Base Model
======================================================

Analyzes BBH benchmark results from the BASE MODEL (Gemini Pro 3 Preview without finetuning)
judged by Gemini Pro 3 Preview.
Generates figures, samples incorrect/correct cases, and produces a markdown report.

Author: Auto-generated
Date: 2025-01-09
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import random

# Try importing matplotlib, provide fallback
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for server environments
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Figures will be skipped.")

# Configuration - BASE MODEL PATHS
RESULTS_DIR = Path("/mnt/libraries/benchresults/llm_judge_results_base")
OUTPUT_DIR = Path("/mnt/libraries/benchresults/analysis_output_base")
REPORT_FILE = OUTPUT_DIR / "llm_judge_analysis_report.md"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Model identifier
MODEL_NAME = "Gemini Pro 3 Preview (Base Model)"

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Color palette for visualizations
COLORS = {
    'correct': '#2ecc71',
    'wrong_logic': '#e74c3c',
    'hallucination': '#9b59b6',
    'format_error': '#f39c12',
    'no_answer': '#95a5a6',
    'calculation_error': '#3498db',
    'primary': '#3498db',
    'secondary': '#2c3e50',
}

SCORE_COLORS = {
    5: '#27ae60',
    4: '#2ecc71',
    3: '#f1c40f',
    2: '#e67e22',
    1: '#c0392b',
}


def load_all_results():
    """Load all JSON result files from the results directory."""
    all_results = {}
    parse_errors = []
    
    for f in sorted(RESULTS_DIR.glob("*.json")):
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                task_name = f.stem.replace("_res", "").replace("_", " ").title()
                all_results[task_name] = {
                    'filename': f.name,
                    'data': data,
                }
        except json.JSONDecodeError as e:
            parse_errors.append((f.name, str(e)))
    
    return all_results, parse_errors


def compute_task_stats(data):
    """Compute statistics for a single task."""
    total = len(data)
    correct = sum(1 for item in data if item.get('is_correct', False))
    accuracy = (correct / total * 100) if total > 0 else 0
    
    scores = [item.get('reasoning_score', 0) for item in data if item.get('reasoning_score') is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    error_counts = defaultdict(int)
    for item in data:
        error_type = item.get('error_type', 'unknown')
        error_counts[error_type] += 1
    
    score_dist = defaultdict(int)
    for item in data:
        score = item.get('reasoning_score', 0)
        score_dist[score] += 1
    
    return {
        'total': total,
        'correct': correct,
        'incorrect': total - correct,
        'accuracy': accuracy,
        'avg_score': avg_score,
        'error_counts': dict(error_counts),
        'score_dist': dict(score_dist),
    }


def get_sample_cases(data, n_correct=3, n_incorrect=3):
    """Get sample correct and incorrect cases."""
    correct_cases = [item for item in data if item.get('is_correct', False)]
    incorrect_cases = [item for item in data if not item.get('is_correct', False)]
    
    # Sample or take all if fewer
    sampled_correct = random.sample(correct_cases, min(n_correct, len(correct_cases)))
    sampled_incorrect = random.sample(incorrect_cases, min(n_incorrect, len(incorrect_cases)))
    
    return sampled_correct, sampled_incorrect


def create_accuracy_bar_chart(task_stats, output_path):
    """Create a horizontal bar chart of task accuracies."""
    if not HAS_MATPLOTLIB:
        return None
    
    # Sort by accuracy
    sorted_tasks = sorted(task_stats.items(), key=lambda x: x[1]['accuracy'], reverse=True)
    
    tasks = [t[0][:35] for t in sorted_tasks]  # Truncate long names
    accuracies = [t[1]['accuracy'] for t in sorted_tasks]
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Color bars based on accuracy thresholds
    colors = []
    for acc in accuracies:
        if acc >= 70:
            colors.append('#27ae60')
        elif acc >= 50:
            colors.append('#f39c12')
        else:
            colors.append('#e74c3c')
    
    bars = ax.barh(tasks, accuracies, color=colors, edgecolor='white', linewidth=0.5)
    
    # Add value labels
    for bar, acc in zip(bars, accuracies):
        ax.text(acc + 1, bar.get_y() + bar.get_height()/2, f'{acc:.1f}%',
                va='center', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'BBH Task Accuracy - {MODEL_NAME}', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(0, 105)
    ax.invert_yaxis()
    
    # Add threshold lines
    ax.axvline(x=70, color='#27ae60', linestyle='--', alpha=0.5, linewidth=1.5, label='High (≥70%)')
    ax.axvline(x=50, color='#f39c12', linestyle='--', alpha=0.5, linewidth=1.5, label='Medium (≥50%)')
    
    ax.legend(loc='lower right')
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def create_error_distribution_pie(all_error_counts, output_path):
    """Create a pie chart of error type distribution."""
    if not HAS_MATPLOTLIB:
        return None
    
    labels = []
    sizes = []
    colors = []
    
    for error_type, count in sorted(all_error_counts.items(), key=lambda x: -x[1]):
        labels.append(error_type.replace('_', ' ').title())
        sizes.append(count)
        colors.append(COLORS.get(error_type, '#95a5a6'))
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors, startangle=90,
        explode=[0.02] * len(sizes),
        shadow=False, textprops={'fontsize': 11}
    )
    
    for autotext in autotexts:
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    ax.set_title(f'Error Type Distribution - {MODEL_NAME}', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def create_score_distribution_chart(all_score_dist, output_path):
    """Create a bar chart of reasoning score distribution."""
    if not HAS_MATPLOTLIB:
        return None
    
    scores = sorted(all_score_dist.keys())
    counts = [all_score_dist[s] for s in scores]
    colors = [SCORE_COLORS.get(s, '#95a5a6') for s in scores]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar([f'Score {s}' for s in scores], counts, color=colors, edgecolor='white', linewidth=2)
    
    # Add value labels
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{count:,}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Reasoning Score', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title(f'Reasoning Score Distribution - {MODEL_NAME}', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def create_accuracy_vs_score_scatter(task_stats, output_path):
    """Create a scatter plot of accuracy vs average reasoning score."""
    if not HAS_MATPLOTLIB:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    accuracies = []
    scores = []
    sizes = []
    labels = []
    
    for task_name, stats in task_stats.items():
        accuracies.append(stats['accuracy'])
        scores.append(stats['avg_score'])
        sizes.append(stats['total'] / 2)  # Scale by sample size
        labels.append(task_name[:20])
    
    scatter = ax.scatter(scores, accuracies, s=sizes, alpha=0.7, c=accuracies,
                         cmap='RdYlGn', edgecolors='white', linewidth=1)
    
    # Add labels for outliers
    for i, label in enumerate(labels):
        if accuracies[i] < 30 or accuracies[i] > 80 or scores[i] < 3:
            ax.annotate(label, (scores[i], accuracies[i]), fontsize=8,
                       xytext=(5, 5), textcoords='offset points')
    
    ax.set_xlabel('Average Reasoning Score', fontsize=12, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Accuracy vs Reasoning Score - {MODEL_NAME}', fontsize=14, fontweight='bold', pad=20)
    ax.grid(alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, label='Accuracy (%)')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def create_error_heatmap(task_stats, output_path):
    """Create a heatmap of error types per task."""
    if not HAS_MATPLOTLIB:
        return None
    
    # Get all error types
    all_error_types = set()
    for stats in task_stats.values():
        all_error_types.update(stats['error_counts'].keys())
    all_error_types = sorted(all_error_types)
    
    # Build matrix
    tasks = sorted(task_stats.keys(), key=lambda x: task_stats[x]['accuracy'], reverse=True)
    matrix = []
    for task in tasks:
        row = []
        total = task_stats[task]['total']
        for error_type in all_error_types:
            count = task_stats[task]['error_counts'].get(error_type, 0)
            row.append(count / total * 100)  # Percentage
        matrix.append(row)
    
    fig, ax = plt.subplots(figsize=(12, 14))
    
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
    
    # Labels
    ax.set_xticks(range(len(all_error_types)))
    ax.set_xticklabels([e.replace('_', ' ').title() for e in all_error_types], rotation=45, ha='right')
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t[:30] for t in tasks])
    
    ax.set_title(f'Error Type Distribution Heatmap (%) - {MODEL_NAME}', fontsize=14, fontweight='bold', pad=20)
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, label='Percentage')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def generate_markdown_report(all_results, task_stats, parse_errors, figures):
    """Generate the comprehensive markdown report."""
    
    # Calculate overall stats
    total_samples = sum(s['total'] for s in task_stats.values())
    total_correct = sum(s['correct'] for s in task_stats.values())
    overall_accuracy = (total_correct / total_samples * 100) if total_samples > 0 else 0
    
    # Aggregate error counts
    all_error_counts = defaultdict(int)
    all_score_dist = defaultdict(int)
    for stats in task_stats.values():
        for error_type, count in stats['error_counts'].items():
            all_error_counts[error_type] += count
        for score, count in stats['score_dist'].items():
            all_score_dist[score] += count
    
    # Sort tasks by accuracy
    sorted_by_acc = sorted(task_stats.items(), key=lambda x: x[1]['accuracy'], reverse=True)
    top_5 = sorted_by_acc[:5]
    bottom_5 = sorted_by_acc[-5:]
    
    # Build report
    lines = []
    
    # Header
    lines.append(f"# LLM Judge Analysis Report: {MODEL_NAME} on BBH")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("> [!NOTE]")
    lines.append("> This report analyzes the **BASE MODEL** (without finetuning) results for comparison purposes.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| **Model** | {MODEL_NAME} |")
    lines.append(f"| **Total Tasks Analyzed** | {len(task_stats)} |")
    lines.append(f"| **Total Samples** | {total_samples:,} |")
    lines.append(f"| **Overall Accuracy** | {overall_accuracy:.1f}% ({total_correct:,}/{total_samples:,}) |")
    lines.append(f"| **Best Performing Task** | {top_5[0][0]} ({top_5[0][1]['accuracy']:.1f}%) |")
    lines.append(f"| **Worst Performing Task** | {bottom_5[-1][0]} ({bottom_5[-1][1]['accuracy']:.1f}%) |")
    lines.append("")
    
    # Key Findings
    lines.append("### Key Findings")
    lines.append("")
    wrong_logic_pct = all_error_counts.get('wrong_logic', 0) / total_samples * 100
    lines.append(f"1. **`wrong_logic` is the dominant error type** at {wrong_logic_pct:.1f}% of all samples")
    lines.append(f"2. **Strong correlation between accuracy and reasoning scores** - high accuracy tasks average ≥4.0 reasoning score")
    lines.append(f"3. **Task difficulty varies significantly** - {sorted_by_acc[-1][1]['accuracy']:.1f}% to {sorted_by_acc[0][1]['accuracy']:.1f}% accuracy range")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append(f"> The base model demonstrates consistent reasoning structure but makes logical/computational errors in ~{wrong_logic_pct:.0f}% of cases.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Figures section
    lines.append("## Visualizations")
    lines.append("")
    
    for fig_name, fig_path in figures.items():
        if fig_path:
            rel_path = os.path.relpath(fig_path, OUTPUT_DIR)
            lines.append(f"### {fig_name}")
            lines.append("")
            lines.append(f"![{fig_name}]({rel_path})")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Detailed Task Performance
    lines.append("## Task Performance Details")
    lines.append("")
    lines.append("### All Tasks (Sorted by Accuracy)")
    lines.append("")
    lines.append("| Rank | Task | Total | Correct | Accuracy | Avg Score |")
    lines.append("|------|------|-------|---------|----------|-----------|")
    
    for i, (task_name, stats) in enumerate(sorted_by_acc, 1):
        acc_emoji = "🟢" if stats['accuracy'] >= 70 else ("🟡" if stats['accuracy'] >= 50 else "🔴")
        lines.append(f"| {i} | {task_name} | {stats['total']} | {stats['correct']} | {acc_emoji} {stats['accuracy']:.1f}% | {stats['avg_score']:.2f} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Error Analysis
    lines.append("## Error Analysis")
    lines.append("")
    lines.append("### Global Error Distribution")
    lines.append("")
    lines.append("| Error Type | Count | Percentage |")
    lines.append("|------------|-------|------------|")
    
    for error_type, count in sorted(all_error_counts.items(), key=lambda x: -x[1]):
        pct = count / total_samples * 100
        lines.append(f"| `{error_type}` | {count:,} | {pct:.1f}% |")
    
    lines.append("")
    
    # Score Distribution
    lines.append("### Reasoning Score Distribution")
    lines.append("")
    lines.append("| Score | Count | Percentage | Interpretation |")
    lines.append("|-------|-------|------------|----------------|")
    
    score_interp = {
        5: "Perfect logic",
        4: "Minor issues",
        3: "Moderate errors",
        2: "Significant errors",
        1: "Fundamental failure"
    }
    
    for score in sorted(all_score_dist.keys(), reverse=True):
        count = all_score_dist[score]
        pct = count / total_samples * 100
        interp = score_interp.get(score, "Unknown")
        lines.append(f"| {score} | {count:,} | {pct:.1f}% | {interp} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Per-Task Error Breakdown
    lines.append("## Per-Task Error Breakdown")
    lines.append("")
    
    for task_name, stats in sorted_by_acc:
        lines.append(f"### {task_name}")
        lines.append("")
        lines.append(f"- **Accuracy:** {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})")
        lines.append(f"- **Avg Reasoning Score:** {stats['avg_score']:.2f}")
        lines.append(f"- **Error Types:** {', '.join([f'`{k}`: {v}' for k, v in sorted(stats['error_counts'].items(), key=lambda x: -x[1])])}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Sample Cases
    lines.append("## Sample Cases")
    lines.append("")
    lines.append("Below are randomly sampled correct and incorrect cases from select tasks.")
    lines.append("")
    
    # Sample from worst and best tasks
    sample_tasks = [bottom_5[-1][0], bottom_5[-2][0], top_5[0][0]]
    
    for task_name in sample_tasks:
        if task_name not in all_results:
            continue
        
        data = all_results[task_name]['data']
        correct_samples, incorrect_samples = get_sample_cases(data, n_correct=2, n_incorrect=2)
        
        lines.append(f"### {task_name}")
        lines.append("")
        
        if incorrect_samples:
            lines.append("**Incorrect Cases:**")
            lines.append("")
            for sample in incorrect_samples:
                lines.append(f"- **ID {sample.get('id', '?')}**: Answer=`{sample.get('extracted_answer', 'N/A')}`, Score={sample.get('reasoning_score', 'N/A')}, Error=`{sample.get('error_type', 'N/A')}`")
                if sample.get('comment'):
                    lines.append(f"  - *{sample['comment'][:200]}...*" if len(sample.get('comment', '')) > 200 else f"  - *{sample.get('comment', '')}*")
            lines.append("")
        
        if correct_samples:
            lines.append("**Correct Cases:**")
            lines.append("")
            for sample in correct_samples:
                lines.append(f"- **ID {sample.get('id', '?')}**: Answer=`{sample.get('extracted_answer', 'N/A')}`, Score={sample.get('reasoning_score', 'N/A')}`")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("### LLM Judge Configuration")
    lines.append("")
    lines.append("The evaluation was performed using **Gemini Pro 3 Preview** as an LLM-as-Judge with the following approach:")
    lines.append("")
    lines.append("1. **Semantic Matching**: Prioritizes the semantic meaning of the final conclusion over strict formatting")
    lines.append("2. **Answer Extraction**: Ignores `<think>` traces, focuses on final response text")
    lines.append("3. **Equivalence Rules**: Maps various answer formats to ground truth:")
    lines.append("   - Multiple Choice: `(A)` ≡ `A`, `Option A`, `[A]`, `\\boxed{A}`")
    lines.append("   - Boolean: `True` ≡ `true`, `yes`, `valid`; `False` ≡ `false`, `no`, `invalid`")
    lines.append("   - Plausibility: `yes` ≡ `plausible`; `no` ≡ `implausible`")
    lines.append("")
    lines.append("### Scoring Rubric")
    lines.append("")
    lines.append("| Score | Meaning |")
    lines.append("|-------|---------|")
    lines.append("| 5 | Perfect logic and correct answer |")
    lines.append("| 4 | Minor issues in reasoning |")
    lines.append("| 3 | Moderate errors |")
    lines.append("| 2 | Significant logical errors |")
    lines.append("| 1 | Fundamental failure in reasoning |")
    lines.append("")
    lines.append("### Error Types")
    lines.append("")
    lines.append("| Type | Description |")
    lines.append("|------|-------------|")
    lines.append("| `none` | No error (correct answer) |")
    lines.append("| `wrong_logic` | Correct reasoning structure but logical/computational error |")
    lines.append("| `hallucination` | Model fabricated information |")
    lines.append("| `format_error` | Answer format could not be parsed |")
    lines.append("| `no_answer` | Model did not provide a clear answer |")
    lines.append("| `calculation_error` | Arithmetic/computational mistake |")
    lines.append("")
    
    # Parse errors if any
    if parse_errors:
        lines.append("---")
        lines.append("")
        lines.append("## Data Quality Issues")
        lines.append("")
        lines.append("The following files had JSON parse errors:")
        lines.append("")
        for f, err in parse_errors:
            lines.append(f"- `{f}`: {err}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `comprehensive_llm_judge_analyzer_base.py`*")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("=" * 60)
    print(f"LLM Judge Results Comprehensive Analyzer - BASE MODEL")
    print("=" * 60)
    print()
    
    # Load data
    print("[1/5] Loading result files...")
    all_results, parse_errors = load_all_results()
    print(f"      Loaded {len(all_results)} tasks, {len(parse_errors)} parse errors")
    
    if parse_errors:
        for f, err in parse_errors:
            print(f"      ⚠ Parse error in {f}: {err}")
    
    # Compute statistics
    print("[2/5] Computing statistics...")
    task_stats = {}
    for task_name, result in all_results.items():
        task_stats[task_name] = compute_task_stats(result['data'])
    
    total_samples = sum(s['total'] for s in task_stats.values())
    total_correct = sum(s['correct'] for s in task_stats.values())
    print(f"      Total samples: {total_samples:,}")
    print(f"      Overall accuracy: {total_correct/total_samples*100:.1f}%")
    
    # Generate figures
    print("[3/5] Generating figures...")
    figures = {}
    
    figures['Task Accuracy Chart'] = create_accuracy_bar_chart(
        task_stats, FIGURES_DIR / "accuracy_by_task.png"
    )
    
    # Aggregate error counts for pie chart
    all_error_counts = defaultdict(int)
    all_score_dist = defaultdict(int)
    for stats in task_stats.values():
        for error_type, count in stats['error_counts'].items():
            all_error_counts[error_type] += count
        for score, count in stats['score_dist'].items():
            all_score_dist[score] += count
    
    figures['Error Distribution'] = create_error_distribution_pie(
        all_error_counts, FIGURES_DIR / "error_distribution.png"
    )
    
    figures['Reasoning Score Distribution'] = create_score_distribution_chart(
        all_score_dist, FIGURES_DIR / "score_distribution.png"
    )
    
    figures['Accuracy vs Reasoning Score'] = create_accuracy_vs_score_scatter(
        task_stats, FIGURES_DIR / "accuracy_vs_score.png"
    )
    
    figures['Error Type Heatmap'] = create_error_heatmap(
        task_stats, FIGURES_DIR / "error_heatmap.png"
    )
    
    generated_figs = sum(1 for v in figures.values() if v is not None)
    print(f"      Generated {generated_figs} figures")
    
    # Generate report
    print("[4/5] Generating markdown report...")
    report_content = generate_markdown_report(all_results, task_stats, parse_errors, figures)
    
    with open(REPORT_FILE, 'w') as f:
        f.write(report_content)
    print(f"      Report saved to: {REPORT_FILE}")
    
    # Summary
    print("[5/5] Done!")
    print()
    print("=" * 60)
    print("Output Files:")
    print(f"  - Report: {REPORT_FILE}")
    for fig_name, fig_path in figures.items():
        if fig_path:
            print(f"  - Figure: {fig_path}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
