#!/usr/bin/env python3
"""
A/B Evaluation Orchestrator

Runs 4 experimental conditions across 11 test problems, caches raw API
responses, scores them with 13 deterministic structural indicators (max 13.0),
and generates comparison reports with category aggregation and expected
indicator hit-rate analysis.

Usage:
    # Full run (44 API calls)
    python run_evaluation.py

    # Smoke test (2 calls)
    python run_evaluation.py --problems arch-tradeoffs-01 --conditions bare,skill_injected

    # Re-score cached responses without API calls
    python run_evaluation.py --rescore-only

    # Regenerate reports from existing scores
    python run_evaluation.py --report-only

    # Force re-run even if cached
    python run_evaluation.py --force
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic

from problems import PROBLEMS, get_problem, get_all_problem_ids
from scoring import score_response, rescore_from_raw, save_scores
from report import save_reports

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-6"
TEMPERATURE = 1.0
MAX_TOKENS = 16_000
EXTENDED_THINKING_BUDGET = 10_000

SKILL_PATH = Path(__file__).parent.parent / "skills" / "awesome-thinking" / "SKILL.md"
RESULTS_DIR = Path(__file__).parent / "results"

ALL_CONDITIONS = ["bare", "extended_thinking", "skill_injected", "sequential_thinking_mcp"]

# Retry config
MAX_RETRIES = 3
BACKOFF_SECONDS = [30, 60, 120]


# ---------------------------------------------------------------------------
# Skill content loader
# ---------------------------------------------------------------------------

def load_skill_content() -> str:
    """Load the awesome-thinking SKILL.md content."""
    if not SKILL_PATH.exists():
        print(f"ERROR: SKILL.md not found at {SKILL_PATH}", file=sys.stderr)
        sys.exit(1)
    return SKILL_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# API call functions
# ---------------------------------------------------------------------------

def _call_with_retry(fn, description: str):
    """
    Call fn() with exponential backoff on rate limit errors.

    Args:
        fn: Callable that makes the API call
        description: Human-readable description for progress output

    Returns:
        The API response
    """
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except anthropic.RateLimitError as e:
            wait = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
            print(f"  Rate limited on {description}. Waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})...")
            time.sleep(wait)
        except anthropic.APIError as e:
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
                print(f"  API error on {description}: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Failed after {MAX_RETRIES} retries: {description}")


def call_api_bare(client: anthropic.Anthropic, prompt: str) -> dict:
    """
    Condition A: Bare — no system prompt, no extended thinking.

    Returns:
        Dict with response_text and metadata
    """
    def _call():
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )
        return response

    response = _call_with_retry(_call, "bare")
    text = _extract_text(response)

    return {
        "response_text": text,
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }


def call_api_extended_thinking(client: anthropic.Anthropic, prompt: str) -> dict:
    """
    Condition B: Extended Thinking — no system prompt, thinking enabled.

    Returns:
        Dict with response_text, thinking_text, and metadata
    """
    def _call():
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            thinking={
                "type": "adaptive",
            },
            messages=[{"role": "user", "content": prompt}],
        )
        return response

    response = _call_with_retry(_call, "extended_thinking")

    # Extract visible text and thinking separately
    text = ""
    thinking_text = ""
    for block in response.content:
        if block.type == "thinking":
            thinking_text += block.thinking
        elif block.type == "text":
            text += block.text

    return {
        "response_text": text,
        "thinking_text": thinking_text,
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }


def call_api_skill_injected(client: anthropic.Anthropic, prompt: str, skill_content: str) -> dict:
    """
    Condition C: Skill-Injected — SKILL.md as system prompt, no extended thinking.

    Returns:
        Dict with response_text and metadata
    """
    def _call():
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=skill_content,
            messages=[{"role": "user", "content": prompt}],
        )
        return response

    response = _call_with_retry(_call, "skill_injected")
    text = _extract_text(response)

    return {
        "response_text": text,
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }


def call_api_sequential_thinking_mcp(client: anthropic.Anthropic, prompt: str) -> dict:
    """
    Condition D: Sequential Thinking MCP — simulates the tool-use loop.

    Provides the model with the same tool definition the Sequential Thinking MCP
    server exposes, then loops: each time the model calls the tool, we return a
    simulated server response (the real server is just a stateful notepad). The
    loop ends when the model stops calling the tool (produces a text response)
    or when nextThoughtNeeded is false.

    Returns:
        Dict with response_text (all thoughts + final text) and metadata
    """
    # Tool definition matching the MCP server's schema exactly
    seq_thinking_tool = {
        "name": "sequentialthinking",
        "description": (
            "A detailed tool for dynamic and reflective problem-solving through thoughts.\n"
            "This tool helps analyze problems through a flexible thinking process that can adapt and evolve.\n"
            "Each thought can build on, question, or revise previous insights as understanding deepens.\n\n"
            "When to use this tool:\n"
            "- Breaking down complex problems into steps\n"
            "- Planning and design with room for revision\n"
            "- Analysis that might need course correction\n"
            "- Problems where the full scope might not be clear initially\n"
            "- Problems that require a multi-step solution\n"
            "- Tasks that need to maintain context over multiple steps\n"
            "- Situations where irrelevant information needs to be filtered out\n\n"
            "Key features:\n"
            "- You can adjust total_thoughts up or down as you progress\n"
            "- You can question or revise previous thoughts\n"
            "- You can add more thoughts even after reaching what seemed like the end\n"
            "- You can express uncertainty and explore alternative approaches\n"
            "- Not every thought needs to build linearly - you can branch or backtrack\n"
            "- Generates a solution hypothesis\n"
            "- Verifies the hypothesis based on the Chain of Thought steps\n"
            "- Repeats the process until satisfied\n"
            "- Provides a correct answer\n\n"
            "Parameters explained:\n"
            "- thought: Your current thinking step, which can include:\n"
            "  * Regular analytical steps\n"
            "  * Revisions of previous thoughts\n"
            "  * Questions about previous decisions\n"
            "  * Realizations about needing more analysis\n"
            "  * Changes in approach\n"
            "  * Hypothesis generation\n"
            "  * Hypothesis verification\n"
            "- nextThoughtNeeded: True if you need more thinking, even if at what seemed like the end\n"
            "- thoughtNumber: Current number in sequence (can go beyond initial total if needed)\n"
            "- totalThoughts: Current estimate of thoughts needed (can be adjusted up/down)\n"
            "- isRevision: A boolean indicating if this thought revises previous thinking\n"
            "- revisesThought: If is_revision is true, which thought number is being reconsidered\n"
            "- branchFromThought: If branching, which thought number is the branching point\n"
            "- branchId: Identifier for the current branch (if any)\n"
            "- needsMoreThoughts: If reaching end but realizing more thoughts needed\n\n"
            "You should:\n"
            "1. Start with an initial estimate of needed thoughts, but be ready to adjust\n"
            "2. Feel free to question or revise previous thoughts\n"
            "3. Don't hesitate to add more thoughts if needed, even at the \"end\"\n"
            "4. Express uncertainty when present\n"
            "5. Mark thoughts that revise previous thinking or branch into new paths\n"
            "6. Ignore information that is irrelevant to the current step\n"
            "7. Generate a solution hypothesis when appropriate\n"
            "8. Verify the hypothesis based on the Chain of Thought steps\n"
            "9. Repeat the process until satisfied with the solution\n"
            "10. Provide a single, ideally correct answer as the final output\n"
            "11. Only set nextThoughtNeeded to false when truly done and a satisfactory answer is reached"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Your current thinking step",
                },
                "nextThoughtNeeded": {
                    "type": "boolean",
                    "description": "Whether another thought step is needed",
                },
                "thoughtNumber": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Current thought number",
                },
                "totalThoughts": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Estimated total thoughts needed",
                },
                "isRevision": {
                    "type": "boolean",
                    "description": "Whether this revises previous thinking",
                },
                "revisesThought": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Which thought is being reconsidered",
                },
                "branchFromThought": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Branching point thought number",
                },
                "branchId": {
                    "type": "string",
                    "description": "Branch identifier",
                },
                "needsMoreThoughts": {
                    "type": "boolean",
                    "description": "If more thoughts are needed",
                },
            },
            "required": ["thought", "nextThoughtNeeded", "thoughtNumber", "totalThoughts"],
        },
    }

    # State tracking (mirrors the MCP server's lib.ts)
    thought_history = []
    branches = {}
    total_input_tokens = 0
    total_output_tokens = 0

    # Build initial messages
    messages = [{"role": "user", "content": prompt}]

    MAX_TURNS = 30  # Safety limit to prevent infinite loops

    for turn in range(MAX_TURNS):
        def _call():
            return client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                tools=[seq_thinking_tool],
                messages=messages,
            )

        response = _call_with_retry(_call, f"seq_thinking turn {turn + 1}")
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # Check if the model produced a tool call or a text response
        tool_use_block = None
        text_blocks = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "sequentialthinking":
                tool_use_block = block
            elif block.type == "text":
                text_blocks.append(block.text)

        if tool_use_block is None:
            # Model stopped calling the tool — we're done
            break

        # Extract thought data from tool input
        tool_input = tool_use_block.input
        thought_data = {
            "thought": tool_input.get("thought", ""),
            "thoughtNumber": tool_input.get("thoughtNumber", turn + 1),
            "totalThoughts": tool_input.get("totalThoughts", 5),
            "nextThoughtNeeded": tool_input.get("nextThoughtNeeded", True),
            "isRevision": tool_input.get("isRevision", False),
            "revisesThought": tool_input.get("revisesThought"),
            "branchFromThought": tool_input.get("branchFromThought"),
            "branchId": tool_input.get("branchId"),
            "needsMoreThoughts": tool_input.get("needsMoreThoughts", False),
        }
        thought_history.append(thought_data)

        # Track branches (matching MCP server behavior)
        if thought_data.get("branchFromThought") and thought_data.get("branchId"):
            bid = thought_data["branchId"]
            if bid not in branches:
                branches[bid] = []
            branches[bid].append(thought_data)

        # Build simulated server response (matches lib.ts processThought output)
        server_response = json.dumps({
            "thoughtNumber": thought_data["thoughtNumber"],
            "totalThoughts": thought_data["totalThoughts"],
            "nextThoughtNeeded": thought_data["nextThoughtNeeded"],
            "branches": list(branches.keys()),
            "thoughtHistoryLength": len(thought_history),
        }, indent=2)

        # Append assistant message (with the tool call) and tool result
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": server_response,
            }],
        })

        # If model said nextThoughtNeeded=false, do one more turn for final answer
        if not thought_data["nextThoughtNeeded"]:
            # Make one final call to get the text summary
            def _final_call():
                return client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    tools=[seq_thinking_tool],
                    messages=messages,
                )
            final_response = _call_with_retry(_final_call, "seq_thinking final")
            total_input_tokens += final_response.usage.input_tokens
            total_output_tokens += final_response.usage.output_tokens

            # Check for any additional tool calls vs text
            for block in final_response.content:
                if block.type == "text":
                    text_blocks.append(block.text)
                elif block.type == "tool_use" and block.name == "sequentialthinking":
                    # Model wants more thoughts despite saying done — continue loop
                    tool_input = block.input
                    thought_history.append({
                        "thought": tool_input.get("thought", ""),
                        "thoughtNumber": tool_input.get("thoughtNumber", 0),
                        "totalThoughts": tool_input.get("totalThoughts", 0),
                        "nextThoughtNeeded": tool_input.get("nextThoughtNeeded", False),
                    })
            break

    # Assemble full response: all thoughts + final text
    # This matches what a user would see: the thought content from each tool call
    # plus any final text response
    thought_texts = []
    for td in thought_history:
        prefix = f"Thought {td['thoughtNumber']}/{td['totalThoughts']}"
        if td.get("isRevision") and td.get("revisesThought"):
            prefix += f" (Revising Thought {td['revisesThought']})"
        elif td.get("branchFromThought") and td.get("branchId"):
            prefix += f" (Branch {td['branchId']} from Thought {td['branchFromThought']})"
        thought_texts.append(f"{prefix}: {td['thought']}")

    full_text = "\n\n".join(thought_texts)
    if text_blocks:
        full_text += "\n\n" + "\n".join(text_blocks)

    return {
        "response_text": full_text,
        "thought_count": len(thought_history),
        "branches": list(branches.keys()),
        "turns": turn + 1,
        "model": MODEL,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "stop_reason": "tool_loop_complete",
    }


def _extract_text(response) -> str:
    """Extract text content from an API response."""
    parts = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Raw response persistence
# ---------------------------------------------------------------------------

def raw_path(problem_id: str, condition: str) -> Path:
    """Get the file path for a cached raw response."""
    return RESULTS_DIR / "raw" / f"{problem_id}__{condition}.json"


def save_raw(problem_id: str, condition: str, data: dict) -> Path:
    """Save raw API response to disk."""
    path = raw_path(problem_id, condition)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "problem_id": problem_id,
        "condition": condition,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **data,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return path


def is_cached(problem_id: str, condition: str) -> bool:
    """Check if a raw response is already cached."""
    return raw_path(problem_id, condition).exists()


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

MAX_WORKERS = 7  # Parallel API calls (one per problem)


def _run_single(
    client: anthropic.Anthropic,
    problem_id: str,
    condition: str,
    skill_content: str,
    force: bool,
    label: str,
) -> tuple:
    """
    Run a single problem/condition pair. Returns (problem_id, condition, StructuralScore).
    Thread-safe: each call is independent.
    """
    problem = get_problem(problem_id)

    if not force and is_cached(problem_id, condition):
        print(f"{label} {problem_id} / {condition} — cached")
        with open(raw_path(problem_id, condition), "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("response_text", "")
    else:
        print(f"{label} Running {problem_id} / {condition}...")

        if condition == "bare":
            data = call_api_bare(client, problem.prompt)
        elif condition == "extended_thinking":
            data = call_api_extended_thinking(client, problem.prompt)
        elif condition == "skill_injected":
            data = call_api_skill_injected(client, problem.prompt, skill_content)
        elif condition == "sequential_thinking_mcp":
            data = call_api_sequential_thinking_mcp(client, problem.prompt)
        else:
            raise ValueError(f"Unknown condition '{condition}'")

        save_raw(problem_id, condition, data)
        text = data.get("response_text", "")
        print(f"  Done: {problem_id} / {condition} — {data.get('output_tokens', '?')} tokens, {len(text.split())} words.")

    score = score_response(text, problem_id, condition)
    return (problem_id, condition, score)


def run_evaluation(
    problem_ids: list,
    conditions: list,
    force: bool = False,
) -> list:
    """
    Run the A/B evaluation across specified problems and conditions.
    Uses ThreadPoolExecutor for parallel API calls.

    Args:
        problem_ids: List of problem IDs to evaluate
        conditions: List of condition names to run
        force: If True, re-run even if cached

    Returns:
        List of StructuralScore objects
    """
    client = anthropic.Anthropic()
    skill_content = load_skill_content() if "skill_injected" in conditions else ""

    # Build task list
    tasks = []
    for problem_id in problem_ids:
        for condition in conditions:
            tasks.append((problem_id, condition))

    total = len(tasks)
    scores = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for idx, (problem_id, condition) in enumerate(tasks, 1):
            label = f"[{idx}/{total}]"
            future = executor.submit(
                _run_single, client, problem_id, condition,
                skill_content, force, label,
            )
            futures[future] = (problem_id, condition)

        for future in as_completed(futures):
            problem_id, condition = futures[future]
            try:
                _, _, score = future.result()
                scores.append(score)
            except Exception as e:
                print(f"  ERROR: {problem_id} / {condition} failed: {e}")

    return scores


def main():
    parser = argparse.ArgumentParser(
        description="A/B Evaluation: awesome-thinking Skill vs Opus 4.6 Native Reasoning"
    )
    parser.add_argument(
        "--problems",
        type=str,
        default=None,
        help="Comma-separated problem IDs (default: all 7)",
    )
    parser.add_argument(
        "--conditions",
        type=str,
        default=None,
        help="Comma-separated conditions (default: all 3: bare,extended_thinking,skill_injected)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run even if responses are cached",
    )
    parser.add_argument(
        "--rescore-only",
        action="store_true",
        help="Re-score cached responses without making API calls",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Regenerate reports from existing scores (implies --rescore-only)",
    )

    args = parser.parse_args()

    # Parse problem IDs
    if args.problems:
        problem_ids = [p.strip() for p in args.problems.split(",")]
        # Validate
        all_ids = get_all_problem_ids()
        for pid in problem_ids:
            if pid not in all_ids:
                print(f"ERROR: Unknown problem ID '{pid}'. Valid: {all_ids}", file=sys.stderr)
                sys.exit(1)
    else:
        problem_ids = get_all_problem_ids()

    # Parse conditions
    if args.conditions:
        conditions = [c.strip() for c in args.conditions.split(",")]
        for c in conditions:
            if c not in ALL_CONDITIONS:
                print(f"ERROR: Unknown condition '{c}'. Valid: {ALL_CONDITIONS}", file=sys.stderr)
                sys.exit(1)
    else:
        conditions = ALL_CONDITIONS

    # Handle rescore/report modes
    if args.report_only or args.rescore_only:
        print("Re-scoring from cached raw responses...")
        scores = rescore_from_raw(RESULTS_DIR)

        if not scores:
            print("No cached responses found. Run the evaluation first.")
            sys.exit(1)

        print(f"Re-scored {len(scores)} responses.")
        save_scores(scores, RESULTS_DIR)

        print("Generating reports...")
        json_path, md_path = save_reports(scores, RESULTS_DIR / "reports")
        print(f"JSON report: {json_path}")
        print(f"Markdown report: {md_path}")
        return

    # Full evaluation run
    print(f"Starting evaluation: {len(problem_ids)} problems x {len(conditions)} conditions "
          f"= {len(problem_ids) * len(conditions)} calls")
    print(f"Model: {MODEL}")
    print(f"Problems: {problem_ids}")
    print(f"Conditions: {conditions}")
    print()

    scores = run_evaluation(problem_ids, conditions, force=args.force)

    # Save scores
    save_scores(scores, RESULTS_DIR)
    print(f"\nScored {len(scores)} responses.")

    # Generate reports
    print("Generating reports...")
    json_path, md_path = save_reports(scores, RESULTS_DIR / "reports")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    print("\nDone!")


if __name__ == "__main__":
    main()
