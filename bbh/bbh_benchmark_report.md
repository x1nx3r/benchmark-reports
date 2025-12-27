# BBH Benchmark Analysis Report

**Date:** December 27, 2025  
**Benchmark:** BIG-Bench Hard (BBH) with Chain-of-Thought Few-Shot Prompting  
**Configurations:** 3-shot with/without system prompt

---

## Executive Summary

This report analyzes the BBH benchmark results from two configurations, examining both the official accuracy scores and the underlying response patterns to identify model behavior characteristics.

| Metric | Without System Prompt | With System Prompt |
|--------|----------------------|-------------------|
| **Overall Accuracy** | 34.36% | 34.50% |
| **Answer Parsing Success** | 64.41% | 66.56% |
| **Think Tags Present** | 0% | 0% |
| **Total Samples** | 6,511 | 6,511 |

**Key Finding:** No `<think></think>` reasoning tags were found in any of the 13,022 total samples analyzed.

---

## Detailed Performance Analysis

### Top Performing Tasks (>50% Accuracy)

| Task | No SysPrompt | With SysPrompt | Best Config |
|------|-------------|----------------|-------------|
| Navigate | **66.4%** | 62.4% | No SysPrompt |
| Sports Understanding | **62.8%** | 58.4% | No SysPrompt |
| Boolean Expressions | 46.0% | **60.8%** | With SysPrompt |
| Causal Judgement | **56.7%** | 43.3% | No SysPrompt |
| Object Counting | **56.4%** | 51.6% | No SysPrompt |
| Tracking Shuffled (3 obj) | **56.0%** | 42.4% | No SysPrompt |
| Multistep Arithmetic | **50.0%** | 46.4% | No SysPrompt |

### Worst Performing Tasks (<20% Accuracy)

| Task | No SysPrompt | With SysPrompt | Issue |
|------|-------------|----------------|-------|
| Dyck Languages | 1.6% | 0.8% | 75%+ parsing failures |
| Word Sorting | 2.8% | 5.6% | 89%+ parsing failures |
| Logical Deduction (7 obj) | 3.6% | 6.0% | 77%+ parsing failures |
| Logical Deduction (5 obj) | 8.8% | 9.2% | 64%+ parsing failures |
| Formal Fallacies | 17.6% | 22.4% | 60%+ parsing failures |
| Tracking Shuffled (7 obj) | 18.0% | 14.0% | 49%+ parsing failures |

---

## Answer Parsing Analysis

The benchmark uses regex extraction (`the answer is (.*)`) to parse model responses. High parsing failure rates directly impact measured accuracy.

### Parsing Success Rate by Task Category

```
High Success (>90%):
├── Navigate: 96.4% (241/250)
├── Salient Translation: 95.2% (238/250)
├── Tracking Shuffled 3-obj: 96.0% (240/250)
└── Web of Lies: 93.6% (234/250)

Medium Success (70-90%):
├── Causal Judgement: 91.4% (171/187)
├── Sports Understanding: 88.8% (222/250)
└── Multistep Arithmetic: 84.8% (212/250)

Low Success (<50%):
├── Word Sorting: 10.8% (27/250)
├── Logical Deduction 7-obj: 23.2% (58/250)
├── Dyck Languages: 24.0% (60/250)
└── Logical Deduction 5-obj: 32.4% (81/250)
```

### Answer Pattern Distribution

| Pattern | Occurrence Rate | Description |
|---------|-----------------|-------------|
| `answer:` | 85% | Contains "answer" followed by colon |
| `the answer is` | 69% | Standard answer format |
| `so the answer is` | 52% | Chain-of-thought conclusion |
| `therefore` | 8-10% | Alternative conclusion format |
| `final_answer` | 0.6-1.4% | Explicit final answer label |

---

## Configuration Comparison

### System Prompt Impact

| Metric | Difference (With - Without) |
|--------|----------------------------|
| Overall Accuracy | +0.14% (negligible) |
| Valid Answers | +140 samples (+2.15%) |
| Invalid Answers | -140 samples (-2.15%) |

### Tasks Where System Prompt Helps Significantly (>5% improvement)

1. **Boolean Expressions:** +14.8% (46.0% → 60.8%)
2. **Snarks:** +19.6% (29.8% → 49.4%)
3. **Ruin Names:** +10.8% (32.4% → 43.2%)
4. **Disambiguation QA:** +6.8% (26.0% → 32.8%)

### Tasks Where No System Prompt is Better (>5% decline with sysprompt)

1. **Causal Judgement:** -13.4% (56.7% → 43.3%)
2. **Tracking Shuffled 3-obj:** -13.6% (56.0% → 42.4%)
3. **Tracking Shuffled 5-obj:** -10.0% (43.2% → 33.2%)
4. **Object Counting:** -4.8% (56.4% → 51.6%)

---

## Root Cause Analysis

### High Parsing Failure Causes

1. **Non-standard answer formats:**
   - Model says "Answer: True" instead of "So the answer is True"
   - Model uses bullet points or structured output
   - Model trails off without explicit conclusion

2. **Complex multi-step reasoning:**
   - Model gets lost in lengthy explanations
   - Answer buried in verbose reasoning
   - Multiple candidate answers mentioned

3. **Task-specific formatting issues:**
   - **Dyck Languages:** Outputs bracket sequences without "the answer is" prefix
   - **Word Sorting:** Produces sorted lists without standard answer format
   - **Logical Deduction:** Complex constraint solving without clear conclusion

### Sample Invalid Response Patterns

```
Pattern 1: Trailing explanation without answer marker
"Therefore, the final result is True."  ← Missing "the answer is"

Pattern 2: Alternative phrasings
"This gives us (B)."  ← Not captured by regex

Pattern 3: Incomplete reasoning
"Let's analyze:
- Step 1...
- Step 2..."  ← Never reaches conclusion
```

---

## Recommendations

### For Benchmark Improvement

1. **Expand regex patterns** to capture:
   - `therefore,? the (?:final )?(?:answer|result) is`
   - `this gives us`
   - `the correct (?:answer|option) is`

2. **Add fallback extraction** for tasks with structured outputs (Dyck, Word Sorting)

### For Model Improvement

1. **Reinforce answer format** in fine-tuning data
2. **Add explicit conclusion markers** in training examples
3. **Reduce reasoning verbosity** for simple tasks

---

## Appendix: Per-Task Breakdown

### Configuration: 3-shot Without System Prompt

| Task | Samples | Valid | Invalid | Correct | Accuracy |
|------|---------|-------|---------|---------|----------|
| Boolean Expressions | 250 | 147 | 103 | 115 | 46.0% |
| Causal Judgement | 187 | 171 | 16 | 106 | 56.7% |
| Date Understanding | 250 | 128 | 122 | 81 | 32.4% |
| Disambiguation QA | 250 | 184 | 66 | 65 | 26.0% |
| Dyck Languages | 250 | 60 | 190 | 4 | 1.6% |
| Formal Fallacies | 250 | 90 | 160 | 44 | 17.6% |
| Geometric Shapes | 250 | 169 | 81 | 52 | 20.8% |
| Hyperbaton | 250 | 171 | 79 | 103 | 41.2% |
| Logical Deduction 5-obj | 250 | 81 | 169 | 22 | 8.8% |
| Logical Deduction 7-obj | 250 | 58 | 192 | 9 | 3.6% |
| Logical Deduction 3-obj | 250 | 134 | 116 | 71 | 28.4% |
| Movie Recommendation | 250 | 136 | 114 | 72 | 28.8% |
| Multistep Arithmetic | 250 | 212 | 38 | 125 | 50.0% |
| Navigate | 250 | 241 | 9 | 166 | 66.4% |
| Object Counting | 250 | 193 | 57 | 141 | 56.4% |
| Penguins in Table | 146 | 81 | 65 | 44 | 30.1% |
| Reasoning Colored Obj | 250 | 185 | 65 | 114 | 45.6% |
| Ruin Names | 250 | 160 | 90 | 81 | 32.4% |
| Salient Translation | 250 | 238 | 12 | 96 | 38.4% |
| Snarks | 178 | 87 | 91 | 53 | 29.8% |
| Sports Understanding | 250 | 222 | 28 | 157 | 62.8% |
| Temporal Sequences | 250 | 217 | 33 | 102 | 40.8% |
| Tracking Shuffled 5-obj | 250 | 201 | 49 | 108 | 43.2% |
| Tracking Shuffled 7-obj | 250 | 127 | 123 | 45 | 18.0% |
| Tracking Shuffled 3-obj | 250 | 240 | 10 | 140 | 56.0% |
| Web of Lies | 250 | 234 | 16 | 114 | 45.6% |
| Word Sorting | 250 | 27 | 223 | 7 | 2.8% |

**Totals:** 6,511 samples | 4,194 valid | 2,317 invalid | 2,237 correct | **34.36% accuracy**
