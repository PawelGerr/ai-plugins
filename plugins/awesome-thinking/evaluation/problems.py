#!/usr/bin/env python3
"""
Test Problem Definitions for A/B Evaluation

Defines 11 carefully designed problems spanning architecture, debugging,
algorithm optimization, system design, ambiguous requirements, and
performance. Each problem is categorized by type and difficulty to
enable per-category analysis.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TestProblem:
    """A single test problem for the A/B evaluation."""
    id: str
    category: str
    title: str
    prompt: str
    expected_indicators: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard


PROBLEMS: List[TestProblem] = [
    TestProblem(
        id="arch-tradeoffs-01",
        category="architecture",
        title="Notification System Design",
        prompt=(
            "Design a notification system that must handle 50,000 notifications per second "
            "across multiple channels (email, SMS, push, in-app). Requirements:\n"
            "- At-least-once delivery guarantee\n"
            "- Users can set per-channel preferences and quiet hours\n"
            "- Must support batching (e.g., digest emails)\n"
            "- Budget constraint: minimize infrastructure cost\n"
            "- Must handle provider failover (e.g., if Twilio is down, fall back to another SMS provider)\n\n"
            "What architecture would you propose? Discuss the key trade-offs in your design, "
            "particularly around consistency vs. availability, cost vs. reliability, "
            "and real-time vs. batched delivery."
        ),
        expected_indicators=[
            "numbered_thoughts", "branching_alternatives", "distinct_approaches",
            "explicit_filtering", "structural_complexity", "quantified_tradeoffs",
            "failure_mode_analysis"
        ],
        difficulty="hard",
    ),
    TestProblem(
        id="debug-unclear-01",
        category="debugging",
        title="Stale Data Under Load",
        prompt=(
            "Our Python web app (Flask + SQLAlchemy + Redis cache + PostgreSQL with read replicas) "
            "intermittently shows stale data to users. Symptoms:\n"
            "- After a user updates their profile, about 10% of subsequent page loads show old data\n"
            "- The issue is worse during peak traffic (2-5 PM)\n"
            "- Direct database queries always show correct data\n"
            "- The issue resolves itself after 5-15 minutes\n"
            "- We recently scaled from 1 to 3 read replicas\n"
            "- Redis cache TTL is set to 10 minutes\n\n"
            "What are the possible root causes? Walk through your diagnostic process "
            "and recommend a fix."
        ),
        expected_indicators=[
            "numbered_thoughts", "hypothesis_testing", "explicit_revision",
            "scope_adjustment", "distinct_approaches", "assumption_tracking"
        ],
        difficulty="medium",
    ),
    TestProblem(
        id="algo-opt-01",
        category="algorithm",
        title="Real-time Anomaly Detection",
        prompt=(
            "Design an algorithm for real-time anomaly detection in a high-throughput event stream. "
            "Constraints:\n"
            "- Events arrive at ~100,000/sec, each with a numeric value and category tag\n"
            "- Must detect anomalies within 100ms of event arrival\n"
            "- Available memory: 512MB maximum\n"
            "- Anomalies are defined as values >3 standard deviations from the rolling mean "
            "for that category\n"
            "- There are ~10,000 distinct categories\n"
            "- The distribution of values per category may shift over time (concept drift)\n"
            "- False positive rate must be below 1%\n\n"
            "Propose an algorithm, analyze its complexity, and discuss how you'd handle "
            "the concept drift problem."
        ),
        expected_indicators=[
            "numbered_thoughts", "branching_alternatives", "hypothesis_testing",
            "structural_complexity", "distinct_approaches"
        ],
        difficulty="hard",
    ),
    TestProblem(
        id="multi-constraint-01",
        category="system_design",
        title="Distributed Rate Limiter",
        prompt=(
            "Design a distributed rate limiter with these constraints:\n"
            "- 5 data centers across 3 continents\n"
            "- Global rate limit: 1000 requests/sec per API key\n"
            "- Local rate limit: 500 requests/sec per API key per DC\n"
            "- P99 latency for rate limit check must be <5ms\n"
            "- Must handle clock skew up to 50ms between DCs\n"
            "- Must handle network partitions (DCs temporarily unable to communicate)\n"
            "- Must handle burst traffic (10x normal for up to 30 seconds)\n"
            "- Rate limit decisions must be consistent within 5% accuracy\n\n"
            "How would you build this? Address the tension between accuracy and latency, "
            "and explain what happens during a network partition."
        ),
        expected_indicators=[
            "numbered_thoughts", "branching_alternatives", "scope_adjustment",
            "explicit_filtering", "distinct_approaches", "structural_complexity",
            "quantified_tradeoffs", "failure_mode_analysis"
        ],
        difficulty="hard",
    ),
    TestProblem(
        id="ambiguous-req-01",
        category="requirements",
        title="Document Search System",
        prompt=(
            "Build a document search system for our company.\n\n"
            "We have about 50,000 internal documents (mix of PDFs, Word docs, "
            "and wiki pages). People complain they can't find things. "
            "Some documents are confidential.\n\n"
            "Make it good."
        ),
        expected_indicators=[
            "scope_adjustment", "explicit_filtering", "numbered_thoughts",
            "branching_alternatives", "hypothesis_testing"
        ],
        difficulty="medium",
    ),
    TestProblem(
        id="debug-perf-01",
        category="performance",
        title="React TTI Optimization",
        prompt=(
            "Our React SPA has a Time to Interactive (TTI) of 8.2 seconds on mobile. "
            "Here's what we know:\n"
            "- Bundle size: 2.1MB (gzipped: 680KB)\n"
            "- Largest Contentful Paint: 4.1s\n"
            "- Total Blocking Time: 3,200ms\n"
            "- First Contentful Paint: 1.8s\n"
            "- We use Redux with 47 reducers loaded at startup\n"
            "- 12 third-party analytics/tracking scripts\n"
            "- Server-side rendering is not currently used\n"
            "- The app makes 23 API calls on initial page load\n"
            "- We use moment.js, lodash (full import), and three.js for a small 3D widget\n\n"
            "Create a prioritized optimization plan to get TTI under 3 seconds. "
            "For each optimization, estimate the expected TTI impact."
        ),
        expected_indicators=[
            "numbered_thoughts", "distinct_approaches", "explicit_filtering",
            "structural_complexity", "scope_adjustment", "quantified_tradeoffs"
        ],
        difficulty="medium",
    ),
    TestProblem(
        id="system-design-01",
        category="system_design",
        title="Real-time Collaborative Editor",
        prompt=(
            "Design a real-time collaborative text editor (like Google Docs). "
            "Start with basic requirements, then I'll add constraints.\n\n"
            "Initial requirements:\n"
            "- Support up to 20 simultaneous editors per document\n"
            "- Changes must appear within 200ms for all users\n"
            "- Must handle conflict resolution when users edit the same section\n"
            "- Must support undo/redo per user\n"
            "- Documents can be up to 1MB of text\n\n"
            "Additional constraint 1: Now it needs to support offline editing with "
            "sync when reconnected.\n\n"
            "Additional constraint 2: Add support for rich text (bold, italic, headers, "
            "lists, embedded images) while maintaining real-time collaboration.\n\n"
            "Walk through how your design evolves as each constraint is added."
        ),
        expected_indicators=[
            "numbered_thoughts", "scope_adjustment", "explicit_revision",
            "branching_alternatives", "structural_complexity", "distinct_approaches",
            "quantified_tradeoffs", "failure_mode_analysis"
        ],
        difficulty="hard",
    ),
    TestProblem(
        id="simple-crud-bug-01",
        category="debugging",
        title="Pagination Off-by-One",
        prompt=(
            "Here is a pagination function from our REST API:\n\n"
            "```python\n"
            "def get_page(items, page, per_page=20):\n"
            "    start = page * per_page\n"
            "    end = start + per_page\n"
            "    total_pages = len(items) // per_page\n"
            "    return {\n"
            "        'data': items[start:end],\n"
            "        'page': page,\n"
            "        'total_pages': total_pages,\n"
            "        'has_next': page < total_pages\n"
            "    }\n"
            "```\n\n"
            "Users report:\n"
            "- Page 1 returns the same results as page 0\n"
            "- The last page of results is sometimes missing\n"
            "- A collection with 21 items says total_pages is 1\n\n"
            "Find the bugs and provide the fix."
        ),
        expected_indicators=["numbered_thoughts", "hypothesis_testing"],
        difficulty="easy",
    ),
    TestProblem(
        id="algo-graph-01",
        category="algorithm",
        title="Time-Varying Shortest Path",
        prompt=(
            "You have a directed graph where edge weights change over time. "
            "Formally: weight(u, v, t) gives the cost of traversing edge (u,v) "
            "if you depart node u at time t. Weights are given as piecewise-linear "
            "functions over discrete time steps 0..T.\n\n"
            "Properties:\n"
            "- N = 10,000 nodes, M = 50,000 edges, T = 1,000 time steps\n"
            "- Some edges have FIFO property (departing later means arriving later), "
            "but not all — some edges have time windows where leaving earlier is better\n"
            "- You need the shortest path from s to d, departing at time t0\n"
            "- Standard Dijkstra assumes static weights and will fail on non-FIFO edges\n\n"
            "Design an algorithm that correctly finds the shortest path. Analyze its "
            "time complexity and discuss what makes this harder than standard shortest path."
        ),
        expected_indicators=[
            "numbered_thoughts", "branching_alternatives", "hypothesis_testing",
            "distinct_approaches"
        ],
        difficulty="hard",
    ),
    TestProblem(
        id="trap-complexity-01",
        category="algorithm",
        title="Bracket Matching with Constraints",
        prompt=(
            "You are given a string containing brackets: (), [], {}, and <>. "
            "The string may also contain:\n"
            "- Arbitrary non-bracket characters between brackets\n"
            "- Up to 10 million characters in length\n"
            "- Nested brackets up to depth 1,000\n"
            "- A 'priority ordering' where <> must never appear directly inside [], "
            "but all other nestings are allowed\n"
            "- The string arrives as a stream (character by character)\n\n"
            "Design an algorithm that validates whether the bracket structure is correct "
            "(properly nested, properly closed, and respects the priority constraint). "
            "It must run in O(n) time and O(d) space where d is the maximum nesting depth.\n\n"
            "The constraints sound complex. Think carefully about whether they actually "
            "change the fundamental approach."
        ),
        expected_indicators=[
            "scope_adjustment", "explicit_filtering", "numbered_thoughts"
        ],
        difficulty="medium",
    ),
    TestProblem(
        id="progressive-constraints-01",
        category="system_design",
        title="Message Queue with Progressive Constraints",
        prompt=(
            "Design a message queue system. Start with the base design, then "
            "I'll add constraints that may force you to revise.\n\n"
            "Base requirements:\n"
            "- Publish/subscribe with topic-based routing\n"
            "- At-least-once delivery\n"
            "- Multiple consumer groups per topic\n"
            "- Message retention for 7 days\n\n"
            "Constraint 1: Messages must be delivered in strict global order "
            "across all topics — not just per-topic ordering, but a total order "
            "that all consumers observe identically.\n\n"
            "Constraint 2: The system must handle 500,000 messages/sec with "
            "P99 publish latency under 10ms. You cannot sacrifice the ordering "
            "guarantee from Constraint 1.\n\n"
            "Constraint 3: The system must survive the complete loss of any "
            "single data center without losing messages or violating ordering. "
            "Explain what happens to latency and throughput during failover.\n\n"
            "Walk through how your design changes with each constraint. "
            "Be explicit about what breaks and what you need to revise."
        ),
        expected_indicators=[
            "scope_adjustment", "explicit_revision", "failure_mode_analysis",
            "quantified_tradeoffs"
        ],
        difficulty="hard",
    ),
]


def get_problem(problem_id: str) -> TestProblem:
    """
    Look up a problem by ID.

    Args:
        problem_id: The unique problem identifier

    Returns:
        The matching TestProblem

    Raises:
        ValueError: If problem_id not found
    """
    for p in PROBLEMS:
        if p.id == problem_id:
            return p
    valid_ids = [p.id for p in PROBLEMS]
    raise ValueError(f"Unknown problem ID '{problem_id}'. Valid IDs: {valid_ids}")


def get_all_problem_ids() -> List[str]:
    """Return all problem IDs."""
    return [p.id for p in PROBLEMS]
