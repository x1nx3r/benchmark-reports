# BBH Benchmark Analysis Report

**Config:** `top_p0.95,rep_penalty1.05-zeroshot-bruteforcesysprompt`  
**Date:** December 27, 2025  
**Samples:** 6,511 across 27 tasks

---

## Executive Summary

| Metric       | Official | True (Extracted) |
| ------------ | -------- | ---------------- |
| **Accuracy** | 0.09%    | **43.83%**       |
| **Correct**  | 6        | 2,854            |
| **Gap**      | —        | **+43.74%**      |

> [!IMPORTANT]
> The model achieves **43.83% accuracy** (not 0.09%). The entire gap is due to answer format mismatch, not reasoning capability.

---

## Key Findings

### 1. `<think>` Tags Present (89.7%)
All 27 tasks contain responses with `<think></think>` reasoning tags. The model reasons inside the tags and outputs answers afterward.

### 2. Format vs Content Errors

| Category                                        | Count | %     |
| ----------------------------------------------- | ----- | ----- |
| **Correct** (extractable + matches target)      | 2,854 | 43.8% |
| **Wrong Answer** (model chose different option) | 2,454 | 37.7% |
| **No Answer** (couldn't extract)                | 1,203 | 18.5% |

### 3. Why Official Score is 0.09%
The benchmark expects: `"the answer is (A)"`  
Model outputs: `"The result is False."` or `**(A)**` or `Answer: A`

---

## Per-Task Breakdown

### Top 10 by True Accuracy

| Task                   | True      | Wrong | No Ans |
| ---------------------- | --------- | ----- | ------ |
| boolean_expressions    | **79.6%** | 18.0% | 2.4%   |
| navigate               | **61.6%** | 29.2% | 9.2%   |
| multistep_arithmetic   | **60.8%** | 0.0%  | 39.2%  |
| sports_understanding   | **60.8%** | 37.2% | 2.0%   |
| snarks                 | **59.0%** | 38.8% | 2.2%   |
| logical_deduction_3obj | **58.8%** | 38.0% | 3.2%   |
| dyck_languages         | **58.4%** | 0.0%  | 41.6%  |
| object_counting        | **57.2%** | 0.0%  | 42.8%  |
| hyperbaton             | **54.8%** | 42.0% | 3.2%   |
| penguins_in_table      | **54.1%** | 39.7% | 6.2%   |

### Bottom 5 by True Accuracy

| Task                   | True  | Wrong | No Ans |
| ---------------------- | ----- | ----- | ------ |
| word_sorting           | 0.8%  | 0.0%  | 99.2%  |
| web_of_lies            | 12.0% | 75.2% | 12.8%  |
| formal_fallacies       | 26.0% | 73.6% | 0.4%   |
| salient_translation    | 26.8% | 63.2% | 10.0%  |
| logical_deduction_7obj | 26.0% | 42.8% | 31.2%  |

---

## Answer Extraction Patterns

Patterns used to extract correct answers:

| Pattern                 | Description                  |
| ----------------------- | ---------------------------- |
| `(a)` to `(g)`          | Option letter in parentheses |
| `answer is X`           | Standard answer format       |
| `**X**`                 | Markdown bold                |
| `\boxed{X}`             | LaTeX boxed                  |
| `plausible/implausible` | Maps to yes/no               |
| Direct match            | Target string in response    |

---

## Sample Responses

### Correct (Format Issue)
```
Target: False
Response: <think>...reasoning...</think>
          The result of the Boolean expression is False.
Status: Correct answer, but benchmark marks [invalid]
```

### Wrong Answer
```
Target: (A)
Response: <think>...reasoning...</think>
          The correct answer is **(B)**.
Status: Model chose B, target was A
```

### No Answer
```
Target: barn damp delmarva...
Response: <think>...reasoning...</think>
          Let me sort these words...
Status: Never outputs final sorted list
```

---

## Recommendations

1. **For Evaluation:** Use flexible answer extraction patterns
2. **For Model Training:** Reinforce `"the answer is X"` format
3. **For Prompting:** Add explicit output format instructions

---

## Files Generated

| File                         | Description                                |
| ---------------------------- | ------------------------------------------ |
| `analyze_samples_v3.py`      | Comprehensive analyzer with categorization |
| `analysis_v3_bruteforce.txt` | Full per-task report                       |
| `random_samples_report.txt`  | Random samples from all tasks              |
