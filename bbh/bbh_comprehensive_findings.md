# BBH Benchmark Comprehensive Findings Report

**Date:** December 27, 2025  
**Benchmark:** BIG-Bench Hard (BBH) with Chain-of-Thought Few-Shot Prompting  
**Total Samples Analyzed:** 19,533 (6,511 per configuration × 3 configurations)

---

## Executive Summary

| Metric | 0-shot (No Sys) | 3-shot (No Sys) | 3-shot (With Sys) |
|--------|-----------------|-----------------|-------------------|
| **Overall Accuracy** | 3.92% | 34.36% | 34.50% |
| **Parsing Success** | 13.72% | 64.41% | 66.56% |
| **Potential Accuracy** | 32.42% | 46.83% | 45.43% |
| **Accuracy Gain (Improved)** | +28.51% | +12.47% | +10.94% |
| **Think Tags** | 0% | 0% | 0% |

> [!IMPORTANT]
> **0-shot shows massive accuracy gap (3.92% vs 34.36%)** - Few-shot examples are critical for this benchmark.
> Improved regex patterns could boost 0-shot accuracy by **+28.51%** (largest gain).

---

## Configuration Comparison

### Accuracy Across Configurations

```
                0-shot    3-shot     3-shot
               (No Sys)  (No Sys)  (With Sys)
Accuracy         3.92%    34.36%     34.50%   
Parsing         13.72%    64.41%     66.56%
Potential       32.42%    46.83%     45.43%
```

### Key Observations

1. **Few-shot prompting is essential**: 0-shot → 3-shot provides ~30% absolute accuracy gain
2. **System prompt has minimal impact**: Only +0.14% difference between 3-shot configs
3. **0-shot has severe parsing issues**: Only 13.72% of responses use standard answer format
4. **Improved patterns help most on 0-shot**: +28.51% potential gain vs +12% for 3-shot

---

## Per-Task Performance (0-shot)

### Tasks with 0% Accuracy
| Task | Valid | Invalid | Potential |
|------|-------|---------|-----------|
| Dyck Languages | 2 | 248 | 0.8% |
| Geometric Shapes | 13 | 237 | 38.8% |
| Logical Deduction 7-obj | 2 | 248 | 21.2% |
| Word Sorting | 0 | 250 | 0.4% |

### Tasks with Highest Potential Recovery (0-shot)
| Task | Current | Potential | Gain |
|------|---------|-----------|------|
| Date Understanding | 8.4% | 55.6% | **+47.2%** |
| Formal Fallacies | 2.4% | 50.8% | **+48.4%** |
| Boolean Expressions | 6.8% | 47.6% | **+40.8%** |
| Geometric Shapes | 0.0% | 38.8% | **+38.8%** |
| Disambiguation QA | 2.0% | 31.6% | **+29.6%** |

---

## Per-Task Performance (3-shot No Sys)

### Top 10 Tasks by Accuracy
| Task | Accuracy | Valid | Potential |
|------|----------|-------|-----------|
| Navigate | 66.4% | 241 | 68.0% |
| Sports Understanding | 62.8% | 222 | 69.2% |
| Causal Judgement | 56.7% | 171 | 61.0% |
| Object Counting | 56.4% | 193 | 61.2% |
| Tracking Shuffled 3-obj | 56.0% | 240 | 57.6% |
| Multistep Arithmetic | 50.0% | 212 | 56.4% |
| Boolean Expressions | 46.0% | 147 | 78.8% |
| Reasoning Colored Objects | 45.6% | 185 | 61.6% |
| Web of Lies | 45.6% | 234 | 49.6% |
| Tracking Shuffled 5-obj | 43.2% | 201 | 49.2% |

### Bottom 5 Tasks by Accuracy
| Task | Accuracy | Invalid Rate | Potential |
|------|----------|--------------|-----------|
| Dyck Languages | 1.6% | 76.0% | 6.8% |
| Word Sorting | 2.8% | 89.2% | 6.8% |
| Logical Deduction 7-obj | 3.6% | 76.8% | 19.2% |
| Logical Deduction 5-obj | 8.8% | 67.6% | 31.6% |
| Formal Fallacies | 17.6% | 64.0% | 40.0% |

---

## System Prompt Impact (3-shot)

### Tasks Improved by System Prompt (>5%)
| Task | No Sys | With Sys | Δ |
|------|--------|----------|---|
| Snarks | 29.8% | **49.4%** | +19.6% |
| Boolean Expressions | 46.0% | **60.8%** | +14.8% |
| Ruin Names | 32.4% | **43.2%** | +10.8% |

### Tasks Degraded by System Prompt (>5%)
| Task | No Sys | With Sys | Δ |
|------|--------|----------|---|
| Causal Judgement | **56.7%** | 43.3% | -13.4% |
| Tracking Shuffled 3-obj | **56.0%** | 42.4% | -13.6% |
| Tracking Shuffled 5-obj | **43.2%** | 33.2% | -10.0% |

---

## Answer Pattern Analysis

### Pattern Distribution by Config

| Pattern | 0-shot | 3-shot (No Sys) | 3-shot (With Sys) |
|---------|--------|-----------------|-------------------|
| `answer:` | 57.4% | 84.9% | 85.1% |
| `the answer is` | 29.5% | 68.3% | 69.6% |
| `so the answer is` | 4.9% | 52.4% | 51.5% |
| `final_answer` | 12.2% | 1.4% | 0.6% |

> [!NOTE]
> 0-shot uses `final_answer` pattern more frequently (12.2%) vs 3-shot (1.4%), suggesting different response structure without few-shot examples.

### Top Recovery Patterns (0-shot)
| Pattern | Count | Description |
|---------|-------|-------------|
| `which_is` | 1,161 | "which is X" |
| `answer_is` | 853 | "answer is X" |
| `final_result` | 356 | "final result is X" |
| `the_answer_is` | 296 | "the answer is X" |
| `argument_is_valid` | 148 | Formal fallacies |

---

## Key Findings

1. **Few-shot examples are critical**: 0-shot accuracy (3.92%) is ~9x lower than 3-shot (34.36%)

2. **Answer formatting degrades without examples**: Only 13.72% parsing success in 0-shot vs 64-66% in 3-shot

3. **Improved patterns help all configs**: But 0-shot benefits most (+28.51% potential gain)

4. **System prompt trade-offs**: Helps some tasks (Snarks +19.6%) but hurts others (Causal Judgement -13.4%)

5. **Task difficulty varies widely**: From 66.4% (Navigate) to 1.6% (Dyck Languages)

---

## Files Generated

| File | Description |
|------|-------------|
| `analysis_output_v4.txt` | Full analysis with all 3 configurations |
| `analyze_samples.py` | Script with 40+ extraction patterns |
| `bbh_comprehensive_findings.md` | This report |
