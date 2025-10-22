#!/usr/bin/env python3
"""
Report Generation for A/B Evaluation

Generates JSON and Markdown comparison reports from structural scores.
Includes summary tables, indicator heatmaps, per-problem breakdowns,
and auto-generated observations.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from problems import PROBLEMS
from scoring import StructuralScore


# ---------------------------------------------------------------------------
# Condition display names
# ---------------------------------------------------------------------------

CONDITION_LABELS = {
    "bare": "A: Bare",
    "extended_thinking": "B: Extended Thinking",
    "skill_injected": "C: Skill-Injected",
    "sequential_thinking_mcp": "D: Sequential Thinking MCP",
}

INDICATOR_NAMES = [
    "numbered_thoughts",
    "explicit_revision",
    "branching_alternatives",
    "scope_adjustment",
    "hypothesis_testing",
    "explicit_filtering",
    "structural_complexity",
    "distinct_approaches",
    "assumption_tracking",
    "tradeoff_analysis",
    "confidence_calibration",
    "quantified_tradeoffs",
    "failure_mode_analysis",
]


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------

def generate_json_report(scores: List[StructuralScore]) -> dict:
    """
    Generate a structured JSON report from scores.

    Args:
        scores: List of StructuralScore objects across all conditions/problems

    Returns:
        Dict suitable for JSON serialization
    """
    by_condition: Dict[str, List[StructuralScore]] = {}
    by_problem: Dict[str, List[StructuralScore]] = {}

    for s in scores:
        by_condition.setdefault(s.condition, []).append(s)
        by_problem.setdefault(s.problem_id, []).append(s)

    # Per-condition aggregates
    condition_summaries = {}
    for condition, cond_scores in sorted(by_condition.items()):
        totals = [s.total_score for s in cond_scores]
        word_counts = [s.word_count for s in cond_scores]
        avg_score = sum(totals) / len(totals) if totals else 0
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        efficiency = round(avg_score / avg_words * 1000, 3) if avg_words > 0 else 0
        condition_summaries[condition] = {
            "label": CONDITION_LABELS.get(condition, condition),
            "num_problems": len(cond_scores),
            "avg_total_score": round(avg_score, 2),
            "max_total_score": round(max(totals), 2) if totals else 0,
            "min_total_score": round(min(totals), 2) if totals else 0,
            "avg_word_count": round(avg_words) if word_counts else 0,
            "score_efficiency": efficiency,
            "per_indicator_avg": _per_indicator_avg(cond_scores),
        }

    # Per-problem breakdown
    problem_breakdowns = {}
    for problem_id, prob_scores in sorted(by_problem.items()):
        problem_breakdowns[problem_id] = {
            s.condition: {
                "total_score": round(s.total_score, 2),
                "word_count": s.word_count,
                "indicators": {
                    ind.name: {"score": ind.score, "count": ind.count}
                    for ind in s.indicators
                },
            }
            for s in prob_scores
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "num_scores": len(scores),
        "max_possible_score": float(len(INDICATOR_NAMES)),
        "conditions": condition_summaries,
        "problems": problem_breakdowns,
        "expected_indicator_analysis": _expected_indicator_analysis(scores),
        "category_aggregation": _category_aggregation(scores),
        "observations": auto_observations(scores),
    }


def _per_indicator_avg(scores: List[StructuralScore]) -> Dict[str, float]:
    """Compute average score per indicator across a set of scores."""
    if not scores:
        return {}
    sums: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for s in scores:
        for ind in s.indicators:
            sums[ind.name] = sums.get(ind.name, 0.0) + ind.score
            counts[ind.name] = counts.get(ind.name, 0) + 1
    return {name: round(sums[name] / counts[name], 3) for name in INDICATOR_NAMES if name in sums}


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def generate_markdown_report(scores: List[StructuralScore]) -> str:
    """
    Generate a Markdown comparison report.

    Args:
        scores: List of StructuralScore objects

    Returns:
        Markdown string with summary table, heatmap, and per-problem breakdown
    """
    lines: List[str] = []
    lines.append("# A/B Evaluation Report: awesome-thinking Skill vs Opus 4.6 Native Reasoning")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Group data
    by_condition: Dict[str, List[StructuralScore]] = {}
    by_problem: Dict[str, List[StructuralScore]] = {}
    for s in scores:
        by_condition.setdefault(s.condition, []).append(s)
        by_problem.setdefault(s.problem_id, []).append(s)

    conditions = sorted(by_condition.keys())

    # --- Summary table ---
    lines.append("## Summary")
    lines.append("")
    header = "| Metric |"
    separator = "|--------|"
    for c in conditions:
        label = CONDITION_LABELS.get(c, c)
        header += f" {label} |"
        separator += "---------|"
    lines.append(header)
    lines.append(separator)

    max_score = float(len(INDICATOR_NAMES))

    # Avg total score with percentage
    row = "| Avg Total Score |"
    for c in conditions:
        totals = [s.total_score for s in by_condition[c]]
        avg = sum(totals) / len(totals) if totals else 0
        pct = avg / max_score * 100 if max_score > 0 else 0
        row += f" {avg:.2f} / {max_score:.1f} ({pct:.0f}%) |"
    lines.append(row)

    # Avg word count
    row = "| Avg Word Count |"
    for c in conditions:
        wc = [s.word_count for s in by_condition[c]]
        avg = sum(wc) / len(wc) if wc else 0
        row += f" {avg:.0f} |"
    lines.append(row)

    # Score efficiency (pts/kword)
    row = "| Score Efficiency (pts/kword) |"
    for c in conditions:
        totals = [s.total_score for s in by_condition[c]]
        wc = [s.word_count for s in by_condition[c]]
        avg_score = sum(totals) / len(totals) if totals else 0
        avg_words = sum(wc) / len(wc) if wc else 0
        eff = avg_score / avg_words * 1000 if avg_words > 0 else 0
        row += f" {eff:.2f} |"
    lines.append(row)

    # Problems evaluated
    row = "| Problems Evaluated |"
    for c in conditions:
        row += f" {len(by_condition[c])} |"
    lines.append(row)

    lines.append("")

    # --- Indicator heatmap ---
    lines.append("## Indicator Heatmap (avg score per condition)")
    lines.append("")
    header = "| Indicator |"
    separator = "|-----------|"
    for c in conditions:
        label = CONDITION_LABELS.get(c, c)
        header += f" {label} |"
        separator += "---------|"
    lines.append(header)
    lines.append(separator)

    for ind_name in INDICATOR_NAMES:
        row = f"| {ind_name} |"
        for c in conditions:
            avg = _indicator_avg(by_condition[c], ind_name)
            bar = _score_bar(avg)
            row += f" {avg:.2f} {bar} |"
        lines.append(row)

    lines.append("")

    # --- Per-problem breakdown ---
    lines.append("## Per-Problem Breakdown")
    lines.append("")

    for problem_id in sorted(by_problem.keys()):
        prob_scores = by_problem[problem_id]
        lines.append(f"### {problem_id}")
        lines.append("")

        header = "| Indicator |"
        separator = "|-----------|"
        for c in conditions:
            if any(s.condition == c for s in prob_scores):
                label = CONDITION_LABELS.get(c, c)
                header += f" {label} |"
                separator += "---------|"
        lines.append(header)
        lines.append(separator)

        for ind_name in INDICATOR_NAMES:
            row = f"| {ind_name} |"
            for c in conditions:
                match = next((s for s in prob_scores if s.condition == c), None)
                if match:
                    ind = next((i for i in match.indicators if i.name == ind_name), None)
                    val = ind.score if ind else 0.0
                    row += f" {val:.2f} |"
            lines.append(row)

        # Total row
        row = "| **TOTAL** |"
        for c in conditions:
            match = next((s for s in prob_scores if s.condition == c), None)
            if match:
                row += f" **{match.total_score:.2f}** |"
        lines.append(row)

        # Word count row
        row = "| *word count* |"
        for c in conditions:
            match = next((s for s in prob_scores if s.condition == c), None)
            if match:
                row += f" *{match.word_count}* |"
        lines.append(row)

        lines.append("")

    # --- Expected Indicator Hit Rate ---
    ei_analysis = _expected_indicator_analysis(scores)
    if ei_analysis.get("summary"):
        lines.append("## Expected Indicator Hit Rate")
        lines.append("")
        header = "| Problem | Expected |"
        separator = "|---------|----------|"
        for c in conditions:
            label = CONDITION_LABELS.get(c, c)
            header += f" {label} |"
            separator += "---------|"
        lines.append(header)
        lines.append(separator)

        for entry in ei_analysis["summary"]:
            row = f"| {entry['problem_id']} | {entry['expected_count']} |"
            for c in conditions:
                rate = entry.get("conditions", {}).get(c)
                if rate is not None:
                    row += f" {rate:.0f}% |"
                else:
                    row += " — |"
            lines.append(row)
        lines.append("")

        if ei_analysis.get("misses"):
            lines.append("### Missed Expected Indicators")
            lines.append("")
            for miss in ei_analysis["misses"]:
                lines.append(f"- **{miss['problem_id']}** / {miss['condition']}: {', '.join(miss['missed'])}")
            lines.append("")

    # --- Category / Difficulty Aggregation ---
    cat_agg = _category_aggregation(scores)
    if cat_agg.get("by_category"):
        lines.append("## Score by Category")
        lines.append("")
        cat_header = "| Category |"
        cat_sep = "|----------|"
        for c in conditions:
            label = CONDITION_LABELS.get(c, c)
            cat_header += f" {label} |"
            cat_sep += "---------|"
        lines.append(cat_header)
        lines.append(cat_sep)
        for cat, cond_avgs in sorted(cat_agg["by_category"].items()):
            row = f"| {cat} |"
            for c in conditions:
                val = cond_avgs.get(c)
                if val is not None:
                    row += f" {val:.2f} |"
                else:
                    row += " — |"
            lines.append(row)
        lines.append("")

    if cat_agg.get("by_difficulty"):
        lines.append("## Score by Difficulty")
        lines.append("")
        diff_header = "| Difficulty |"
        diff_sep = "|------------|"
        for c in conditions:
            label = CONDITION_LABELS.get(c, c)
            diff_header += f" {label} |"
            diff_sep += "---------|"
        lines.append(diff_header)
        lines.append(diff_sep)
        for diff in ["easy", "medium", "hard"]:
            if diff in cat_agg["by_difficulty"]:
                cond_avgs = cat_agg["by_difficulty"][diff]
                row = f"| {diff} |"
                for c in conditions:
                    val = cond_avgs.get(c)
                    if val is not None:
                        row += f" {val:.2f} |"
                    else:
                        row += " — |"
                lines.append(row)
        lines.append("")

    # --- Observations ---
    observations = auto_observations(scores)
    if observations:
        lines.append("## Auto-Generated Observations")
        lines.append("")
        for obs in observations:
            lines.append(f"- {obs}")
        lines.append("")

    return "\n".join(lines)


def _indicator_avg(scores: List[StructuralScore], ind_name: str) -> float:
    """Average score for a specific indicator across scores."""
    values = []
    for s in scores:
        for ind in s.indicators:
            if ind.name == ind_name:
                values.append(ind.score)
    return sum(values) / len(values) if values else 0.0


def _score_bar(score: float) -> str:
    """Visual bar for a 0-1 score."""
    filled = round(score * 5)
    return "\u2588" * filled + "\u2591" * (5 - filled)


# ---------------------------------------------------------------------------
# Expected indicator analysis
# ---------------------------------------------------------------------------

def _expected_indicator_analysis(scores: List[StructuralScore]) -> dict:
    """
    Compute per problem x condition: which expected indicators hit (>=0.5)
    and which missed (scored 0.0).
    """
    # Build problem lookup
    problem_map = {p.id: p for p in PROBLEMS}

    by_problem: Dict[str, List[StructuralScore]] = {}
    for s in scores:
        by_problem.setdefault(s.problem_id, []).append(s)

    summary = []
    misses = []

    for problem_id in sorted(by_problem.keys()):
        problem = problem_map.get(problem_id)
        if not problem or not problem.expected_indicators:
            continue

        expected = problem.expected_indicators
        entry = {
            "problem_id": problem_id,
            "expected_count": len(expected),
            "conditions": {},
        }

        for s in by_problem[problem_id]:
            # Build indicator score lookup for this score
            ind_scores = {ind.name: ind.score for ind in s.indicators}

            hits = sum(1 for e in expected if ind_scores.get(e, 0.0) >= 0.5)
            rate = hits / len(expected) * 100 if expected else 0
            entry["conditions"][s.condition] = round(rate, 1)

            missed = [e for e in expected if ind_scores.get(e, 0.0) == 0.0]
            if missed:
                misses.append({
                    "problem_id": problem_id,
                    "condition": s.condition,
                    "missed": missed,
                })

        summary.append(entry)

    return {"summary": summary, "misses": misses}


# ---------------------------------------------------------------------------
# Category aggregation
# ---------------------------------------------------------------------------

def _category_aggregation(scores: List[StructuralScore]) -> dict:
    """
    Aggregate avg total score by category and difficulty.
    """
    problem_map = {p.id: p for p in PROBLEMS}

    # Group scores by (grouping_key, condition)
    by_category: Dict[str, Dict[str, List[float]]] = {}
    by_difficulty: Dict[str, Dict[str, List[float]]] = {}

    for s in scores:
        problem = problem_map.get(s.problem_id)
        if not problem:
            continue

        cat = problem.category
        diff = problem.difficulty

        by_category.setdefault(cat, {}).setdefault(s.condition, []).append(s.total_score)
        by_difficulty.setdefault(diff, {}).setdefault(s.condition, []).append(s.total_score)

    # Compute averages
    cat_avgs = {}
    for cat, cond_scores in by_category.items():
        cat_avgs[cat] = {
            c: round(sum(vals) / len(vals), 2)
            for c, vals in cond_scores.items()
        }

    diff_avgs = {}
    for diff, cond_scores in by_difficulty.items():
        diff_avgs[diff] = {
            c: round(sum(vals) / len(vals), 2)
            for c, vals in cond_scores.items()
        }

    return {"by_category": cat_avgs, "by_difficulty": diff_avgs}


# ---------------------------------------------------------------------------
# Auto-observations
# ---------------------------------------------------------------------------

def auto_observations(scores: List[StructuralScore]) -> List[str]:
    """
    Generate automatic insights by comparing conditions.

    Args:
        scores: All scores across all conditions and problems

    Returns:
        List of observation strings
    """
    by_condition: Dict[str, List[StructuralScore]] = {}
    for s in scores:
        by_condition.setdefault(s.condition, []).append(s)

    if len(by_condition) < 2:
        return ["Insufficient conditions for comparison (need at least 2)."]

    observations = []

    # Compute condition averages
    avgs: Dict[str, float] = {}
    word_avgs: Dict[str, float] = {}
    for c, cond_scores in by_condition.items():
        totals = [s.total_score for s in cond_scores]
        avgs[c] = sum(totals) / len(totals) if totals else 0
        wc = [s.word_count for s in cond_scores]
        word_avgs[c] = sum(wc) / len(wc) if wc else 0

    # Overall winner
    best_condition = max(avgs, key=avgs.get)
    worst_condition = min(avgs, key=avgs.get)
    label_best = CONDITION_LABELS.get(best_condition, best_condition)
    label_worst = CONDITION_LABELS.get(worst_condition, worst_condition)

    if avgs[best_condition] - avgs[worst_condition] >= 0.5:
        observations.append(
            f"{label_best} leads with avg {avgs[best_condition]:.2f} vs "
            f"{label_worst} at {avgs[worst_condition]:.2f} "
            f"(+{avgs[best_condition] - avgs[worst_condition]:.2f} delta)."
        )
    else:
        observations.append(
            f"Scores are close: {label_best} ({avgs[best_condition]:.2f}) vs "
            f"{label_worst} ({avgs[worst_condition]:.2f}). "
            f"Delta of {avgs[best_condition] - avgs[worst_condition]:.2f} is within noise."
        )

    # Word count comparison
    wordiest = max(word_avgs, key=word_avgs.get)
    tersest = min(word_avgs, key=word_avgs.get)
    if word_avgs[wordiest] > word_avgs[tersest] * 1.5:
        observations.append(
            f"{CONDITION_LABELS.get(wordiest, wordiest)} produces ~{word_avgs[wordiest]:.0f} words avg "
            f"vs {CONDITION_LABELS.get(tersest, tersest)} at ~{word_avgs[tersest]:.0f} words "
            f"({word_avgs[wordiest] / word_avgs[tersest]:.1f}x longer)."
        )

    # Per-indicator standouts
    for ind_name in INDICATOR_NAMES:
        ind_avgs: Dict[str, float] = {}
        for c, cond_scores in by_condition.items():
            ind_avgs[c] = _indicator_avg(cond_scores, ind_name)

        best_ind = max(ind_avgs, key=ind_avgs.get)
        worst_ind = min(ind_avgs, key=ind_avgs.get)
        delta = ind_avgs[best_ind] - ind_avgs[worst_ind]

        if delta >= 0.3:
            observations.append(
                f"{CONDITION_LABELS.get(best_ind, best_ind)} dominates on '{ind_name}' "
                f"({ind_avgs[best_ind]:.2f} vs {ind_avgs[worst_ind]:.2f})."
            )

    # Skill vs bare direct comparison
    if "skill_injected" in avgs and "bare" in avgs:
        delta = avgs["skill_injected"] - avgs["bare"]
        if delta > 0.5:
            observations.append(
                f"Skill injection adds +{delta:.2f} points over bare baseline."
            )
        elif delta < -0.5:
            observations.append(
                f"Skill injection scores {abs(delta):.2f} points BELOW bare baseline."
            )
        else:
            observations.append(
                f"Skill injection shows negligible difference from bare baseline ({delta:+.2f})."
            )

    # Extended thinking vs skill
    if "extended_thinking" in avgs and "skill_injected" in avgs:
        delta = avgs["extended_thinking"] - avgs["skill_injected"]
        if delta > 0.5:
            observations.append(
                f"Extended thinking outperforms skill injection by +{delta:.2f} points. "
                f"Native reasoning may be sufficient."
            )
        elif delta < -0.5:
            observations.append(
                f"Skill injection outperforms extended thinking by +{abs(delta):.2f} points. "
                f"The framework adds structural value."
            )

    return observations


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def save_reports(scores: List[StructuralScore], reports_dir: Path) -> tuple:
    """
    Save JSON and Markdown reports.

    Args:
        scores: All computed scores
        reports_dir: Path to reports/ directory

    Returns:
        Tuple of (json_path, md_path) for the saved reports
    """
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    json_report = generate_json_report(scores)
    json_path = reports_dir / f"report_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2)

    md_report = generate_markdown_report(scores)
    md_path = reports_dir / f"report_{timestamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    return json_path, md_path
