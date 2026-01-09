# Benchmark Reports Repository

Comprehensive benchmark evaluation results for llama 3.2 3B-thinking on multiple reasoning benchmarks, with LLM-as-Judge evaluation using semantic matching.

---

## 📊 Quick Stats

| Metric                   | Value                 |
| ------------------------ | --------------------- |
| **Model Tested**         | llama 3.2 3B thinking |
| **Benchmarks**           | BBH (27 tasks), GSM8K |
| **Total BBH Samples**    | 6,510                 |
| **Overall BBH Accuracy** | 60.1%                 |
| **LLM Judge**            | Gemini Pro 3 Preview  |

---

## 📁 Repository Structure

```
benchresults/
├── analysis_output/           # Generated analysis reports
│   ├── llm_judge_analysis_report.md    # Full markdown report
│   ├── llm_judge_analysis_report.pdf   # PDF version
│   └── figures/                        # Visualization charts
│       ├── accuracy_by_task.png
│       ├── error_distribution.png
│       ├── score_distribution.png
│       ├── accuracy_vs_score.png
│       └── error_heatmap.png
│
├── bbh/                       # BIG-Bench Hard benchmark results
│   ├── 0shot-nosysprompt/     # Zero-shot, no system prompt
│   ├── 3shot-nosysprompt/     # 3-shot, no system prompt
│   ├── 3shot-withsysprompt/   # 3-shot with system prompt
│   ├── top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt/
│   └── *.py / *.txt / *.md    # Analysis scripts and reports
│
├── gsm8k/                     # GSM8K math benchmark results
│   ├── testrun-complete-0-shot/   # Zero-shot results
│   ├── testrun-complete-8-shot/   # 8-shot chain-of-thought
│   └── analyze_gsm8k.py          # Analysis script
│
├── llm_judge_data/            # Prepared data for LLM judging
│   └── *.jsonl                # 27 task files
│
├── llm_judge_results/         # LLM Judge evaluation results
│   └── *_res.json             # 27 result files
│
├── llm_judge_prompt.md        # LLM-as-Judge system prompt
├── comprehensive_llm_judge_analyzer.py  # Analysis script
└── convert_for_judge.py       # Data preparation script
```

---

## 🎯 BBH Task Performance

### All 27 Tasks (Sorted by Accuracy)

| Rank | Task                                | Samples | Correct | Accuracy  | Avg Score |
| ---- | ----------------------------------- | ------- | ------- | --------- | --------- |
| 1    | Boolean Expressions                 | 250     | 214     | **85.6%** | 4.57      |
| 2    | Movie Recommendation                | 250     | 202     | **80.8%** | 4.44      |
| 3    | Penguin In A Table                  | 146     | 110     | **75.3%** | 4.13      |
| 4    | Object Counting                     | 250     | 188     | **75.2%** | 4.28      |
| 5    | Navigate                            | 250     | 185     | **74.0%** | 4.18      |
| 6    | Date Understanding                  | 250     | 180     | **72.0%** | 4.00      |
| 7    | Sports Understanding                | 250     | 178     | **71.2%** | 4.21      |
| 8    | Reasoning About Colored Objects     | 250     | 175     | **70.0%** | 4.16      |
| 9    | Logical Deduction (3 Objects)       | 250     | 174     | 69.6%     | 4.19      |
| 10   | Logical Deduction (7 Objects)       | 250     | 163     | 65.2%     | 3.96      |
| 11   | Web Of Lies                         | 250     | 163     | 65.2%     | 3.72      |
| 12   | Word Sorting                        | 250     | 162     | 64.8%     | 3.72      |
| 13   | Snarks                              | 178     | 112     | 62.9%     | 3.72      |
| 14   | Formal Fallacies                    | 250     | 155     | 62.0%     | 3.48      |
| 15   | Multistep Arithmetic Two            | 250     | 154     | 61.6%     | 4.42      |
| 16   | Hyperbaton                          | 250     | 144     | 57.6%     | 3.31      |
| 17   | Logical Deduction (5 Objects)       | 250     | 143     | 57.2%     | 3.71      |
| 18   | Ruin Names                          | 250     | 143     | 57.2%     | 3.32      |
| 19   | Tracking Shuffled Objects (3)       | 250     | 143     | 57.2%     | 3.60      |
| 20   | Causal Judgement                    | 187     | 104     | 55.6%     | 3.62      |
| 21   | Tracking Shuffled Objects (5)       | 250     | 136     | 54.4%     | 3.18      |
| 22   | Tracking Shuffled Objects (7)       | 250     | 134     | 53.6%     | 3.10      |
| 23   | Temporal Sequence                   | 250     | 124     | 49.6%     | 2.98      |
| 24   | Geometric Shapes                    | 250     | 103     | 41.2%     | 2.65      |
| 25   | Disambiguation QA                   | 250     | 99      | 39.6%     | 3.22      |
| 26   | Salient Translation Error Detection | 250     | 83      | 33.2%     | 3.03      |
| 27   | Dyck Languages                      | 249     | 40      | **16.1%** | 2.41      |

---

## 📈 Error Analysis

### Error Type Distribution

| Error Type          | Count | Percentage | Description                      |
| ------------------- | ----- | ---------- | -------------------------------- |
| `none`              | 3,869 | 59.4%      | Correct answer                   |
| `wrong_logic`       | 2,529 | **38.8%**  | Correct structure, logical error |
| `hallucination`     | 71    | 1.1%       | Fabricated information           |
| `no_answer`         | 27    | 0.4%       | No clear answer provided         |
| `format_error`      | 13    | 0.2%       | Unparseable format               |
| `calculation_error` | 1     | 0.0%       | Arithmetic mistake               |

### Reasoning Score Distribution

| Score | Count | Percentage | Meaning             |
| ----- | ----- | ---------- | ------------------- |
| 5     | 3,774 | 58.0%      | Perfect logic       |
| 4     | 168   | 2.6%       | Minor issues        |
| 3     | 224   | 3.4%       | Moderate errors     |
| 2     | 1,339 | 20.6%      | Significant errors  |
| 1     | 1,005 | 15.4%      | Fundamental failure |

---

## 🔍 Key Findings

1. **`wrong_logic` dominates errors (38.8%)** - The model follows correct reasoning structure but makes logical/computational mistakes

2. **Strong accuracy-score correlation** - High accuracy tasks (>70%) have avg reasoning scores ≥4.0

3. **Task complexity matters** - Tracking shuffled objects degrades with more objects (57.2% → 54.4% → 53.6%)

4. **Symbolic reasoning is weakest** - Dyck Languages (bracket matching) at 16.1% accuracy

5. **Arithmetic reasoning is moderate** - Multistep Arithmetic at 61.6% despite 4.42 avg score (good methodology, calculation slips)

---

## 📂 Available Data Files

### BBH Configurations

| Directory                                                 | Description                       | Tasks |
| --------------------------------------------------------- | --------------------------------- | ----- |
| `0shot-nosysprompt/`                                      | Zero-shot, no system prompt       | 27    |
| `3shot-nosysprompt/`                                      | 3-shot few-shot, no system prompt | 27    |
| `3shot-withsysprompt/`                                    | 3-shot with system prompt         | 27    |
| `top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt/` | Tuned parameters                  | 27    |

### GSM8K Results

| Directory                  | Description              |
| -------------------------- | ------------------------ |
| `testrun-complete-0-shot/` | Zero-shot math reasoning |
| `testrun-complete-8-shot/` | 8-shot chain-of-thought  |

### LLM Judge Results

Each file in `llm_judge_results/` contains:
```json
{
  "id": 1,
  "is_correct": true,
  "extracted_answer": "False",
  "reasoning_score": 5,
  "error_type": "none",
  "comment": "Correctly evaluated boolean operations."
}
```

---

## 🛠️ Analysis Scripts

| Script                                | Purpose                               |
| ------------------------------------- | ------------------------------------- |
| `comprehensive_llm_judge_analyzer.py` | Full analysis with figures and report |
| `analyze_llm_judge.py`                | Quick summary statistics              |
| `convert_for_judge.py`                | Prepare BBH data for LLM judging      |
| `bbh/analyze_samples.py`              | Detailed sample analysis              |
| `gsm8k/analyze_gsm8k.py`              | GSM8K-specific analysis               |

### Running the Analysis

```bash
# Generate full report with figures
python3 comprehensive_llm_judge_analyzer.py

# Quick stats
python3 analyze_llm_judge.py
```

---

## 📋 LLM Judge Methodology

The evaluation uses **semantic matching** with equivalence rules:

| Ground Truth | Accepted Equivalents                  |
| ------------ | ------------------------------------- |
| `(A)`        | `A`, `Option A`, `[A]`, `\boxed{A}`   |
| `True`       | `true`, `yes`, `valid`, `correct`     |
| `False`      | `false`, `no`, `invalid`, `incorrect` |
| `yes`        | `plausible`, `likely`                 |
| `no`         | `implausible`, `unlikely`             |

See [`llm_judge_prompt.md`](llm_judge_prompt.md) for the full system prompt.

---

## 📄 Reports

- **Full Analysis Report:** [`analysis_output/llm_judge_analysis_report.md`](analysis_output/llm_judge_analysis_report.md)
- **PDF Version:** [`analysis_output/llm_judge_analysis_report.pdf`](analysis_output/llm_judge_analysis_report.pdf)
- **BBH Findings:** [`bbh/bbh_analysis_findings.md`](bbh/bbh_analysis_findings.md)

---

## 📊 Visualizations

| Chart                                                     | Description                 |
| --------------------------------------------------------- | --------------------------- |
| ![Accuracy](analysis_output/figures/accuracy_by_task.png) | Task accuracy ranking       |
| ![Errors](analysis_output/figures/error_distribution.png) | Error type pie chart        |
| ![Scores](analysis_output/figures/score_distribution.png) | Reasoning score histogram   |
| ![Scatter](analysis_output/figures/accuracy_vs_score.png) | Accuracy vs reasoning score |
| ![Heatmap](analysis_output/figures/error_heatmap.png)     | Per-task error breakdown    |

---

## 📝 License

This repository contains benchmark evaluation results for research purposes.

---

*Generated: 2025-12-27*
