#!/usr/bin/env python3
"""
Structural Indicator Scoring for A/B Evaluation

Detects 13 structural indicators in LLM responses using deterministic
regex/heuristic patterns. No LLM-as-judge — all scores are reproducible.

Indicators:
  1. Numbered thoughts        — Sequential thinking structure
  2. Explicit revision        — Self-correction patterns
  3. Branching alternatives   — Multiple approach exploration
  4. Scope adjustment         — Dynamic complexity recognition
  5. Hypothesis testing       — Hypothesis + verification cycle
  6. Explicit filtering       — Noise filtering / focus statements
  7. Structural complexity    — Formatting element count (headers, tables, code blocks)
  8. Distinct approaches      — Count of named solution strategies
  9. Assumption tracking      — Explicit assumption identification + challenging
 10. Tradeoff analysis        — Structured comparison with pros/cons
 11. Confidence calibration   — Explicit uncertainty/confidence signaling
 12. Quantified tradeoffs     — Numbers with units in comparison context
 13. Failure mode analysis    — Explicit failure scenarios with mitigations
"""

import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pathlib import Path
import json


@dataclass
class IndicatorResult:
    """Result from a single structural indicator detector."""
    name: str
    detected: bool
    count: int
    evidence: List[str] = field(default_factory=list)
    score: float = 0.0


@dataclass
class StructuralScore:
    """Complete scoring result for one response."""
    problem_id: str
    condition: str
    indicators: List[IndicatorResult] = field(default_factory=list)
    total_score: float = 0.0
    word_count: int = 0
    distinct_approaches: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict for JSON persistence."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StructuralScore":
        """Deserialize from dict."""
        indicators = [IndicatorResult(**ind) for ind in data.get("indicators", [])]
        return cls(
            problem_id=data["problem_id"],
            condition=data["condition"],
            indicators=indicators,
            total_score=data["total_score"],
            word_count=data["word_count"],
            distinct_approaches=data["distinct_approaches"],
        )


# ---------------------------------------------------------------------------
# Detector functions
# ---------------------------------------------------------------------------

def detect_numbered_thoughts(text: str) -> IndicatorResult:
    """
    Detect numbered thought sequences.

    Patterns: 'Thought N/M', 'Step N:', numbered lists (1. 2. 3.),
    'Phase N:', 'Part N:'
    """
    patterns = [
        r"[Tt]hought\s+\d+\s*/\s*\d+",
        r"[Ss]tep\s+\d+\s*:",
        r"[Pp]hase\s+\d+\s*:",
        r"[Pp]art\s+\d+\s*:",
    ]
    # Also detect substantial numbered lists (lines starting with "N. ")
    numbered_list_pattern = r"^\d+\.\s+\S"

    evidence = []
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        count += len(matches)
        evidence.extend(matches[:3])  # Keep up to 3 examples per pattern

    # Count numbered list items (only if 3+ to avoid false positives)
    list_matches = re.findall(numbered_list_pattern, text, re.MULTILINE)
    if len(list_matches) >= 3:
        count += len(list_matches)
        evidence.append(f"Numbered list with {len(list_matches)} items")

    if count >= 3:
        score = 1.0
    elif count >= 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="numbered_thoughts",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_explicit_revision(text: str) -> IndicatorResult:
    """
    Detect self-correction and revision patterns.

    Patterns: 'revising', 'actually my earlier', 'correcting',
    'I was wrong', 'on second thought', 'wait,', 'let me reconsider'
    """
    patterns = [
        r"[Rr]evis(?:ing|ed|e)[,.\s]",
        r"[Aa]ctually[,\s]+(?:my\s+earlier|the\s+previous|upon\s+reflection)",
        r"[Cc]orrecting\s+(?:my|the|this)",
        r"[Ii]\s+was\s+wrong",
        r"[Oo]n\s+second\s+thought",
        r"[Ww]ait,\s",
        r"[Ll]et\s+me\s+reconsider",
        r"[Aa]ctually,\s+(?:that|this|I)",
        r"[Ii]\s+need\s+to\s+revise",
        r"[Rr]ethinking[,.\s]",
        r"[Uu]pon\s+(?:further\s+)?reflection",
        r"[Hh]ypothesis\s+failed",
        r"[Bb]ut\s+wait",
        r"[Tt]hat(?:'s|\s+is)\s+(?:not\s+right|incorrect|wrong)",
        r"[Nn]ow\s+I\s+(?:see|realize|understand)\s+that",
        r"[Mm]y\s+(?:initial|earlier|previous)\s+(?:estimate|assumption|thought|analysis)",
        r"[Ll]et\s+me\s+(?:re-?(?:examine|think|evaluate|assess)|step\s+back)",
        r"[Aa]fter\s+(?:further|more)\s+(?:thought|analysis|consideration)",
        r"\(Revising\s+(?:Thought|assumption)",
        r"[Ll]et\s+me\s+re-?prioritize",
    ]

    evidence = []
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        count += len(matches)
        evidence.extend(matches[:2])

    if count >= 2:
        score = 1.0
    elif count == 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="explicit_revision",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_branching_alternatives(text: str) -> IndicatorResult:
    """
    Detect exploration of alternative approaches.

    Patterns: 'Branch A/B', 'Alternative approach', 'Option N',
    'Approach N:', 'another option', 'alternatively'
    """
    patterns = [
        r"[Bb]ranch\s+[A-Z]",
        r"[Aa]lternativ(?:e|ely)\s+(?:approach|solution|option|strategy|design|method|way)",
        r"[Oo]ption\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Aa]pproach\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Aa]nother\s+(?:option|approach|strategy|way|method|possibility)",
        r"[Aa]lternatively[,\s]",
        r"[Oo]n\s+the\s+other\s+hand",
        r"[Ww]e\s+could\s+(?:also|instead|alternatively)",
        r"[Ss]olution\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Ss]trategy\s+(?:\d+|[A-Z])\s*[:\-]",
    ]

    evidence = []
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        count += len(matches)
        evidence.extend(matches[:2])

    if count >= 2:
        score = 1.0
    elif count == 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="branching_alternatives",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_scope_adjustment(text: str) -> IndicatorResult:
    """
    Detect recognition that scope/complexity is different than expected.

    Patterns: 'more complex than', 'adjusting to', 'expanding scope',
    'simpler than', 'this requires more'
    """
    patterns = [
        r"[Mm]ore\s+complex\s+than\s+(?:initially|originally|first|expected|I\s+thought)",
        r"[Aa]djusting\s+to\s+\d+",
        r"[Ee]xpanding\s+(?:the\s+)?scope",
        r"[Ss]impler\s+than\s+(?:initially|originally|first|expected|I\s+thought)",
        r"[Tt]his\s+(?:requires|needs|demands)\s+more\s+(?:analysis|thought|consideration)",
        r"[Ll]et\s+me\s+(?:expand|extend|broaden|narrow)",
        r"[Tt]his\s+is\s+(?:more|less)\s+(?:complex|complicated|involved|straightforward)",
        r"[Ii]\s+(?:under|over)estimated",
        r"[Nn]eed(?:s|ing)?\s+(?:more|additional|further)\s+(?:analysis|thought|steps)",
        r"[Ee]stimate\s+of\s+\d+\s+thoughts\s+remains?\s+appropriate",
    ]

    evidence = []
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        count += len(matches)
        evidence.extend(matches[:2])

    score = 1.0 if count > 0 else 0.0

    return IndicatorResult(
        name="scope_adjustment",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_hypothesis_testing(text: str) -> IndicatorResult:
    """
    Detect hypothesis generation AND verification cycle.

    Must have BOTH a stated hypothesis AND a test/verification of it.
    """
    hypothesis_patterns = [
        r"[Hh]ypothesis\s*(?:\d+)?\s*:",
        r"[Mm]y\s+hypothesis\s+is",
        r"[Ii]\s+hypothesize\s+that",
        r"[Ll]ikely\s+(?:cause|reason|explanation)\s*:",
        r"[Pp]ossible\s+(?:root\s+)?cause\s*(?:\d+)?\s*:",
        r"[Tt]heory\s*:",
        r"[Ii]\s+(?:suspect|believe|think)\s+(?:the|this|that)\s+(?:root\s+)?cause",
    ]

    verification_patterns = [
        r"[Vv]erif(?:y|ying|ied|ication)",
        r"[Tt]est(?:ing|ed)?\s+(?:this|the|my|our)\s+(?:hypothesis|theory|assumption)",
        r"[Cc]heck(?:ing|ed)?\s+(?:this|the|my|our|against|whether|if)",
        r"[Cc]onfirm(?:ing|ed|s)?",
        r"[Rr]efut(?:e|ed|ing)",
        r"[Vv]alidat(?:e|ing|ed)",
        r"[Ee]vidence\s+(?:for|against|suggests|supports|contradicts)",
        r"[Tt]his\s+(?:confirms|contradicts|supports|disproves)",
    ]

    hypothesis_found = False
    verification_found = False
    evidence = []

    for pattern in hypothesis_patterns:
        matches = re.findall(pattern, text)
        if matches:
            hypothesis_found = True
            evidence.extend(matches[:2])

    for pattern in verification_patterns:
        matches = re.findall(pattern, text)
        if matches:
            verification_found = True
            evidence.extend(matches[:2])

    if hypothesis_found and verification_found:
        score = 1.0
    elif hypothesis_found or verification_found:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="hypothesis_testing",
        detected=hypothesis_found or verification_found,
        count=(1 if hypothesis_found else 0) + (1 if verification_found else 0),
        evidence=evidence[:5],
        score=score,
    )


def detect_explicit_filtering(text: str) -> IndicatorResult:
    """
    Detect noise filtering / explicit focus statements.

    Patterns: 'ignoring X for now', 'out of scope', 'focusing on',
    'setting aside', 'not relevant here'
    """
    patterns = [
        r"[Ii]gnoring\s+\S+.*?\s+for\s+now",
        r"[Oo]ut\s+of\s+scope",
        r"[Ff]ocusing\s+(?:on|specifically\s+on)",
        r"[Ss]etting\s+aside",
        r"[Nn]ot\s+relevant\s+(?:here|now|to\s+this)",
        r"[Ll]et(?:'s|[\s]+us)\s+(?:focus|concentrate|narrow)",
        r"[Ff]or\s+(?:the\s+)?(?:purpose|scope)\s+of\s+this",
        r"[Ww]e\s+(?:can|will|should)\s+(?:ignore|skip|defer|set\s+aside)",
        r"[Pp]utting\s+(?:aside|that\s+aside)",
        r"[Bb]eyond\s+the\s+scope",
    ]

    evidence = []
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        count += len(matches)
        evidence.extend(matches[:2])

    if count >= 2:
        score = 1.0
    elif count == 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="explicit_filtering",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_structural_complexity(text: str) -> IndicatorResult:
    """
    Measure structural formatting complexity of the response.

    Counts structural elements: markdown headers, table data rows, code blocks,
    indented sub-lists, bold section labels (line-anchored **Label**: only).

    Scoring: >=40 elements -> 1.0, 20-39 -> 0.75, 10-19 -> 0.5, <10 -> 0.0
    """
    evidence = []
    count = 0

    # Markdown headers
    headers = re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE)
    count += len(headers)
    if headers:
        evidence.append(f"{len(headers)} headers")

    # Table data rows (exclude separator rows like |---|---|)
    table_rows = re.findall(r"^\|(?![-:| ]+\|).+\|.+\|", text, re.MULTILINE)
    count += len(table_rows)
    if table_rows:
        evidence.append(f"{len(table_rows)} table rows")

    # Code blocks (``` ... ```)
    code_blocks = re.findall(r"```[\s\S]*?```", text)
    count += len(code_blocks)
    if code_blocks:
        evidence.append(f"{len(code_blocks)} code blocks")

    # Indented sub-lists (lines starting with 2+ spaces followed by - or *)
    sub_lists = re.findall(r"^  +[-*]\s+\S", text, re.MULTILINE)
    count += len(sub_lists)
    if sub_lists:
        evidence.append(f"{len(sub_lists)} sub-list items")

    # Bold section labels — line-anchored **Label**: only (avoids inline false positives)
    bold_labels = re.findall(r"^\*\*[A-Z][^*]{1,40}\*\*\s*:", text, re.MULTILINE)
    count += len(bold_labels)
    if bold_labels:
        evidence.append(f"{len(bold_labels)} bold labels")

    if count >= 40:
        score = 1.0
    elif count >= 20:
        score = 0.75
    elif count >= 10:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="structural_complexity",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_distinct_approaches(text: str) -> IndicatorResult:
    """
    Count explicitly named solution approaches.

    Looks for labeled approaches, options, strategies, or solutions
    that represent meaningfully different paths.
    """
    patterns = [
        r"[Aa]pproach\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Oo]ption\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Ss]olution\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Ss]trategy\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Mm]ethod\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Dd]esign\s+(?:\d+|[A-Z])\s*[:\-]",
        r"[Pp]attern\s+(?:\d+|[A-Z])\s*[:\-]",
    ]

    # Also detect "**Name approach**:" or "### Name approach" style headings
    # Require keyword near start (within first ~2 words) to avoid false positives
    # from long document titles like "# Real-Time Collaborative Text Editor Design"
    heading_patterns = [
        r"#{1,4}\s+(?:[A-Z]\w*\s+){0,2}(?:[Aa]pproach|[Ss]olution|[Ss]trategy|[Oo]ption)",
        r"\*\*(?:[A-Z]\w*\s+){0,2}(?:[Aa]pproach|[Ss]olution|[Ss]trategy|[Oo]ption)\b[^*]*\*\*",
    ]

    evidence = []
    labeled_count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        labeled_count += len(matches)
        evidence.extend(matches[:2])

    heading_count = 0
    for pattern in heading_patterns:
        matches = re.findall(pattern, text)
        heading_count += len(matches)
        evidence.extend(matches[:2])

    # Count unique Branch IDs (Branch A, Branch B, etc.) as distinct approaches
    branch_ids = set(re.findall(r"[Bb]ranch\s+([A-Z])", text))
    branch_count = len(branch_ids)
    if branch_ids:
        evidence.append(f"Branches: {', '.join(sorted(branch_ids))}")

    # Use max of labeled+heading vs branch count to avoid double-counting
    # (branches often overlap with labeled approaches)
    count = max(labeled_count + heading_count, branch_count)

    if count >= 2:
        score = 1.0
    elif count == 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="distinct_approaches",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_assumption_tracking(text: str) -> IndicatorResult:
    """
    Detect explicit identification and challenging of assumptions.

    Must have BOTH enumeration of assumptions AND challenging of at least one.
    """
    enumeration_patterns = [
        r"[Aa]ssum(?:ptions?|ing|e)\s*(?:\d+)?\s*:",
        r"\*\*[Aa]ssum(?:ptions?|ing|e)s?\s*(?:\d+)?\s*:?\s*\*\*",
        r"[Kk]ey\s+assumption",
        r"[Ii]mplicit\s+assumption",
        r"[Ww]e(?:'re|\s+are)\s+assuming",
    ]

    challenging_patterns = [
        r"[Cc]halleng(?:e|ing)\s+(?:this|the|our|my)\s+assumption",
        r"[Ii]f\s+(?:this|that|the)?\s*assumption\s*(?:\d+\s+)?(?:is\s+wrong|doesn't\s+hold|fails)",
        r"[Qq]uestion(?:ing)?\s+(?:whether|if|the\s+assumption)",
        r"[Rr]evisit(?:ing|ed)?\s+[Aa]ssumption",
        r"[Rr]evising\s+(?:[Tt]hought\s+\d+'s\s+)?assumption",
        r"[Aa]ssumptions?\s+revisited",
        r"[Rr]econsider(?:ing)?\s+(?:my\s+|our\s+|the\s+)?(?:earlier\s+|initial\s+)?assumptions?",
        r"[Aa]ssumption.{0,30}(?:needs?\s+(?:revision|revisiting|updating)|was\s+(?:wrong|incorrect|incomplete))",
        r"[Ii]f\s+assumption\s*\(?\d+\)?.{0,120}(?:doesn't\s+hold|is\s+wrong|fails)",
    ]

    enumeration_found = False
    challenging_found = False
    evidence = []

    for pattern in enumeration_patterns:
        matches = re.findall(pattern, text)
        if matches:
            enumeration_found = True
            evidence.extend(matches[:2])

    for pattern in challenging_patterns:
        matches = re.findall(pattern, text)
        if matches:
            challenging_found = True
            evidence.extend(matches[:2])

    if enumeration_found and challenging_found:
        score = 1.0
    elif enumeration_found or challenging_found:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="assumption_tracking",
        detected=enumeration_found or challenging_found,
        count=(1 if enumeration_found else 0) + (1 if challenging_found else 0),
        evidence=evidence[:5],
        score=score,
    )


def detect_tradeoff_analysis(text: str) -> IndicatorResult:
    """
    Detect structured comparison of alternatives with explicit pros/cons
    or tradeoff dimensions.
    """
    patterns = [
        r"[Tt]rade-?off",
        r"[Pp]ros?\s+(?:and|&|\/)\s+[Cc]ons?",
        r"[Aa]dvantage|[Dd]isadvantage",
        r"[Ss]trength|[Ww]eakness",
        r"\|.*\|.*\|",  # Markdown table rows (3+ columns)
        r"[Bb]ranch\s+[A-Z]\s+(?:is|has|offers|provides)\s+.*(?:but|while|whereas|however)",
        r"(?:better|worse|faster|slower|simpler|more\s+complex)\s+(?:than|compared\s+to)",
    ]

    evidence = []
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        count += len(matches)
        evidence.extend(matches[:2])

    if count >= 3:
        score = 1.0
    elif count >= 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="tradeoff_analysis",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_confidence_calibration(text: str) -> IndicatorResult:
    """
    Detect explicit uncertainty/confidence signaling.
    """
    patterns = [
        r"[Cc]onfiden(?:t|ce)\s+(?:level|that|in|is)",
        r"[Hh]igh\s+confidence",
        r"[Mm]oderate(?:-high)?\s+confidence",
        r"\((?:high|moderate|low|moderate-high)\s+confidence\)",
        r"[Uu]ncertain(?:ty)?",
        r"[Ll]ikelihood",
        r"[Pp]robabilit(?:y|ies)",
        r"[Hh]igh(?:ly)?\s+(?:likely|confident|certain)",
        r"[Ll]ow\s+confidence",
        r"[Nn]ot\s+(?:fully\s+)?(?:certain|sure|confident)",
        r"[Rr]oughly|[Aa]pproximately",
        r"\d+%\s+(?:chance|likely|confident|certain|probability)",
        r"P\([^)]+\)\s*[=~<>≈]",
        r"[Ii]\s+don't\s+know\s+(?:which|what|whether|if|how)",
        r"[Mm]ay\s+(?:need|require)\s+(?:experimentation|testing|tuning|further)",
    ]

    evidence = []
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, text)
        count += len(matches)
        evidence.extend(matches[:2])

    if count >= 3:
        score = 1.0
    elif count >= 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="confidence_calibration",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_quantified_tradeoffs(text: str) -> IndicatorResult:
    """
    Detect quantified comparisons with units in tradeoff context.

    Looks for numbers with units (ms, MB, %, $/req, req/s, etc.) appearing
    near comparison language (vs, tradeoff, whereas, Branch A, etc.).
    Also catches direct patterns like ~40ms vs ~120ms.

    Scoring: >=3 instances -> 1.0, 1-2 -> 0.5, 0 -> 0.0
    """
    evidence = []
    count = 0

    # Direct comparison patterns: ~40ms vs ~120ms, 10MB vs 100MB, etc.
    direct_patterns = re.findall(
        r"~?\d+[\d.,]*\s*(?:ms|s|sec|MB|GB|KB|TB|%|req/s|\$/req|ops/s|QPS|TPS|[μu]s|ns)"
        r"\s+(?:vs\.?|versus)\s+"
        r"~?\d+[\d.,]*\s*(?:ms|s|sec|MB|GB|KB|TB|%|req/s|\$/req|ops/s|QPS|TPS|[μu]s|ns)",
        text,
    )
    count += len(direct_patterns)
    evidence.extend(direct_patterns[:2])

    # Numbers with units in paragraphs containing comparison context
    comparison_words = re.compile(
        r"\b(?:vs\.?|versus|tradeoff|trade-off|whereas|compared\s+to|"
        r"Branch\s+[A-Z]|Option\s+[A-Z]|Approach\s+[A-Z]|"
        r"instead\s+of|rather\s+than|at\s+the\s+(?:cost|expense)\s+of|"
        r"but\s+(?:requires?|costs?|adds?|increases?))\b",
        re.IGNORECASE,
    )
    number_with_unit = re.compile(
        r"\b\d+[\d.,]*\s*(?:ms|s|sec|seconds?|MB|GB|KB|TB|%|"
        r"req/s|requests?/s(?:ec)?|\$/req|ops/s|QPS|TPS|[μu]s|ns|"
        r"bytes?|minutes?|hours?|days?|x\s+(?:faster|slower|more|less))\b"
    )

    for para in re.split(r"\n\s*\n", text):
        if comparison_words.search(para):
            nums = number_with_unit.findall(para)
            if nums:
                count += len(nums)
                evidence.extend(nums[:2])

    if count >= 3:
        score = 1.0
    elif count >= 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="quantified_tradeoffs",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


def detect_failure_mode_analysis(text: str) -> IndicatorResult:
    """
    Detect explicit failure mode analysis with mitigations.

    Patterns detected:
    - Arrow format: Failure: X -> Impact: Y -> Mitigation: Z
    - "Failure mode(s)" as section heading
    - "If X goes down/fails" with mitigation in same or next paragraph
    - "What happens when" failure scenarios
    - Table-based failure analysis (| Failure | Impact | Mitigation |)
    - Scenario/case-based failure descriptions (headings, "Scenario: ...")
    - "Fail open/closed/safe/fast" decision patterns

    Scoring: >=2 scenarios -> 1.0, 1 -> 0.5, 0 -> 0.0
    """
    evidence = []
    count = 0

    # Arrow format chains
    arrow_patterns = re.findall(
        r"[Ff]ailure\s*:.*?[\u2192→].*?(?:[Ii]mpact|[Mm]itigation|[Rr]ecovery)\s*:",
        text,
    )
    count += len(arrow_patterns)
    evidence.extend([m[:80] for m in arrow_patterns[:2]])

    # "Failure mode(s)" as heading or bold label
    heading_patterns = re.findall(
        r"(?:^#{1,4}\s+.*[Ff]ailure\s+[Mm]odes?|^\*\*[Ff]ailure\s+[Mm]odes?\*\*)",
        text,
        re.MULTILINE,
    )
    count += len(heading_patterns)
    evidence.extend(heading_patterns[:2])

    # "If X goes down/fails" with nearby mitigation language
    if_fails_pattern = re.compile(
        r"[Ii]f\s+(?:the\s+)?(?:\w+\s+){0,3}"
        r"(?:goes?\s+down|fails?|crashes?|becomes?\s+unavailable|is\s+(?:down|unavailable|unreachable))",
    )
    mitigation_pattern = re.compile(
        r"(?:mitigat|fallback|failover|recover|redundan|backup|retry|circuit.?break|degrad)",
        re.IGNORECASE,
    )

    paragraphs = re.split(r"\n\s*\n", text)
    for i, para in enumerate(paragraphs):
        if if_fails_pattern.search(para):
            # Check current paragraph and next paragraph for mitigation
            window = para
            if i + 1 < len(paragraphs):
                window += " " + paragraphs[i + 1]
            if mitigation_pattern.search(window):
                count += 1
                match = if_fails_pattern.search(para)
                evidence.append(match.group()[:80])

    # "What happens when/if" failure scenarios
    what_happens = re.findall(
        r"[Ww]hat\s+happens\s+(?:when|if)\s+(?:the\s+)?(?:\w+\s+){0,3}"
        r"(?:fails?|goes?\s+down|crashes?|is\s+(?:lost|unavailable))",
        text,
    )
    count += len(what_happens)
    evidence.extend([m[:80] for m in what_happens[:2]])

    # Table-based failure analysis: header row with Failure + Impact/Mitigation columns
    failure_table = re.compile(
        r"^\|[^|]*[Ff]ailure[^|]*\|[^|]*(?:[Ii]mpact|[Mm]itigation|[Rr]ecovery)[^|]*\|",
        re.MULTILINE,
    )
    if failure_table.search(text):
        # Count data rows following the header (exclude separator rows)
        table_data_rows = re.findall(
            r"^\|(?![-:| ]+\|)[^|]+\|[^|]+\|[^|]+\|",
            text, re.MULTILINE,
        )
        # Subtract 1 for the header row itself
        data_count = max(len(table_data_rows) - 1, 1)
        count += data_count
        evidence.append(f"Failure table with {data_count} scenarios")

    # Scenario-based failure descriptions
    scenario_patterns = re.findall(
        r"(?:^#{1,4}\s+.*(?:[Ff]ailure|[Ff]ault|[Oo]utage|[Pp]artition)|"
        r"[Ss]cenario\s*(?:\d+)?\s*:\s*.*(?:fail|down|loss|partition|outage))",
        text,
        re.MULTILINE,
    )
    count += len(scenario_patterns)
    evidence.extend([m[:80] for m in scenario_patterns[:2]])

    # Fail open/closed decision patterns
    fail_open_closed = re.findall(
        r"fail\s+(?:open|closed|safe|fast|silent)",
        text,
        re.IGNORECASE,
    )
    count += len(fail_open_closed)
    evidence.extend(fail_open_closed[:2])

    if count >= 2:
        score = 1.0
    elif count == 1:
        score = 0.5
    else:
        score = 0.0

    return IndicatorResult(
        name="failure_mode_analysis",
        detected=count > 0,
        count=count,
        evidence=evidence[:5],
        score=score,
    )


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

ALL_DETECTORS = [
    detect_numbered_thoughts,
    detect_explicit_revision,
    detect_branching_alternatives,
    detect_scope_adjustment,
    detect_hypothesis_testing,
    detect_explicit_filtering,
    detect_structural_complexity,
    detect_distinct_approaches,
    detect_assumption_tracking,
    detect_tradeoff_analysis,
    detect_confidence_calibration,
    detect_quantified_tradeoffs,
    detect_failure_mode_analysis,
]


def score_response(text: str, problem_id: str, condition: str) -> StructuralScore:
    """
    Score a single LLM response across all 13 structural indicators.

    Args:
        text: The visible response text (not internal thinking)
        problem_id: Which test problem this response is for
        condition: Which experimental condition (bare, extended_thinking, skill_injected)

    Returns:
        StructuralScore with all indicator results and total score (max 13.0)
    """
    indicators = [detector(text) for detector in ALL_DETECTORS]
    total_score = sum(ind.score for ind in indicators)
    word_count = len(text.split())

    # Get distinct approaches count from the specific detector
    approaches_result = next(
        (ind for ind in indicators if ind.name == "distinct_approaches"), None
    )
    distinct_approaches = approaches_result.count if approaches_result else 0

    return StructuralScore(
        problem_id=problem_id,
        condition=condition,
        indicators=indicators,
        total_score=total_score,
        word_count=word_count,
        distinct_approaches=distinct_approaches,
    )


def rescore_from_raw(results_dir: Path) -> List[StructuralScore]:
    """
    Re-score all cached raw responses without making new API calls.

    Args:
        results_dir: Path to the results/ directory containing raw/ subfolder

    Returns:
        List of StructuralScore objects for all cached responses
    """
    raw_dir = results_dir / "raw"
    if not raw_dir.exists():
        return []

    scores = []
    for raw_file in sorted(raw_dir.glob("*.json")):
        with open(raw_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        text = data.get("response_text", "")
        problem_id = data.get("problem_id", "")
        condition = data.get("condition", "")

        if text and problem_id and condition:
            score = score_response(text, problem_id, condition)
            scores.append(score)

    return scores


def save_scores(scores: List[StructuralScore], results_dir: Path) -> None:
    """Save computed scores to the scores/ subdirectory."""
    scores_dir = results_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)

    for score in scores:
        filename = f"{score.problem_id}__{score.condition}.json"
        filepath = scores_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(score.to_dict(), f, indent=2)
