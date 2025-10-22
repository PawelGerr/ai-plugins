---
name: awesome-thinking
description: A structured framework for dynamic and reflective problem-solving through sequential thoughts. Use when tackling complex, multi-step problems that require careful analysis, revision of assumptions, or exploration of alternative approaches. Ideal for algorithm optimization, architectural decisions, debugging complex issues, or any task where initial understanding may need to evolve.
---

# Awesome Thinking: Sequential Reflective Thinking Framework

## Purpose

This skill provides a structured approach to complex problem-solving through sequential, reflective thinking. It enables systematic exploration of problems where understanding deepens progressively, assumptions may need revision, and multiple solution paths should be considered.

Unlike linear problem-solving, this framework embraces:
- Dynamic adjustment of solution complexity as understanding evolves
- Questioning and revising previous conclusions when new insights emerge
- Branching into alternative approaches when uncertainty exists
- Iterative hypothesis generation and verification until a satisfactory solution is reached

## When to Use This Skill

Invoke this skill for:

- **Complex multi-step problems** requiring careful breakdown and analysis
- **Problems with unclear scope** where initial estimates may need adjustment
- **Scenarios requiring course correction** as new information emerges
- **Architectural or design decisions** with multiple viable approaches and trade-offs
- **Algorithm optimization** where multiple strategies should be explored
- **Debugging complex issues** where root cause may not be immediately apparent
- **Tasks needing context maintenance** across multiple analytical steps
- **Situations with irrelevant noise** requiring careful filtering of information

Do NOT use for simple, straightforward tasks with obvious solutions.

## How to Use This Framework

### Core Thinking Process

Structure analysis as a sequence of numbered thoughts, each building toward the solution.

**Non-negotiable behaviors in every response:**
1. Use `Thought N/M:` format for every thought
2. After Thought 2, you MUST checkpoint your scope estimate with a concrete observation
3. Label every proposed solution with `Hypothesis:` then `Verifying:`
4. When a hypothesis fails, insert a Revision Thought citing what changed
5. When 3+ concerns exist, explicitly filter: `Focusing on X; setting aside Y`
6. For ANY problem with multiple possible interpretations or solution paths, you MUST create at least 2 explicit branches before selecting one

Follow these principles:

1. **Start with an Initial Estimate**
   - Begin by estimating total thoughts needed (e.g., "I estimate this will take 5 thoughts")
   - Understand this is flexible and can be adjusted

2. **Progress Through Thoughts Sequentially**
   - Number each thought (1, 2, 3, ...)
   - Focus each thought on a specific aspect of the problem
   - Build on previous insights while remaining open to revision

3. **Types of Thoughts**

   **Regular Analytical Thoughts:**
   - Standard problem-solving steps: information gathering, logical deduction, inference
   - Example: "Thought 3/7: Analyzing the time complexity of the current approach..."

   **REQUIRED — Revision Thoughts:**
   - Trigger 1: when any hypothesis fails verification, OR when a later thought invalidates an earlier assumption
   - Trigger 2: After exploring branches, you MUST critically re-evaluate your initial problem framing. If any assumption from Thoughts 1-2 was incomplete or oversimplified, insert a Revision Thought.
   - You MUST mark with: "Thought N/M (Revising Thought X): [what was wrong and what changed]"
   - Do NOT silently abandon earlier conclusions — explicitly revise them
   - When a hypothesis fails, you MUST insert a Revision Thought: "Thought N/M (Revising Thought X): [what changed and why]"
   - Example: "Thought 6/8 (Revising Thought 3): The earlier assumption about constant-time lookup was incorrect because the hash function has O(k) cost. Adjusting the complexity analysis."
   - Note: Minor corrections within a single thought (arithmetic fixes, typo corrections,
     small recalculations) do NOT require formal Revision labels. Reserve "(Revising Thought X)"
     for cases where a previous thought's *conclusion or direction* needs to change.

   **REQUIRED — Filtering Thoughts:**
   - Trigger: when the problem involves 3+ concerns, domains, or dimensions
   - You MUST explicitly state what you are focusing on and what you are setting aside
   - Required phrasing: `Focusing on [X]; setting aside [Y] for now.`
   - Even for well-scoped problems, explicitly state what you ARE focusing on and what you are deferring. Every problem has secondary concerns worth naming.
   - Example: "Thought 2/8: Focusing on the caching layer; setting aside UI concerns and auth for now."

   **REQUIRED — Branching Thoughts:**
   - Trigger: when 2+ distinct viable approaches are identified
   - You MUST explicitly create branches and explore each before comparing
   - Mark with: "Thought 4/7 (Branch A from Thought 2): Exploring alternative approach..."
   - Can have multiple branches: Branch A, Branch B, etc.
   - When comparing or selecting between branches, also reference them as named approaches (e.g., "Approach A (recursion) vs Approach B (iteration)")
   - After exploring branches, you MUST provide a structured comparison of tradeoffs
   - Use explicit tradeoff language: "Branch A offers [advantage] but [disadvantage], while Branch B..."
   - Quantify tradeoffs where possible: attach concrete numbers (cost, latency, memory, throughput) rather than vague qualifiers like "faster" or "more expensive"
   - When 3+ dimensions matter, use a comparison table
   - Example: "Thought 5/9 (Branch A from Thought 3): If we use a hash map instead..."

   **REQUIRED — Scope Checkpoint:**
   - After Thought 2, you MUST state a concrete observation about problem complexity
   - If complexity differs from estimate: `Adjusting to N thoughts because [specific reason]`
   - If estimate holds: `Estimate of N thoughts remains appropriate because [specific complexity observation]`
   - You MUST NOT skip this checkpoint — every response needs it after Thought 2
   - Example: "Thought 3/7: The problem involves both concurrency and serialization concerns — more complex than expected. Adjusting to 9 thoughts."

   **REQUIRED — Hypothesis and Verification:**
   - When proposing a solution, you MUST label it: `Hypothesis: [proposal]`
   - You MUST follow with: `Verifying: [test against constraints/edge cases]`
   - If verification fails, you MUST state: `Hypothesis failed: [reason]. New hypothesis: [revised]`
   - When a hypothesis fails, you MUST insert a Revision Thought: "Thought N/M (Revising Thought X): [what changed and why]"
   - Example: "Thought 7/10: Hypothesis: Using a trie will reduce lookup from O(n) to O(k). Verifying: checking edge cases... Found issue: doesn't handle Unicode. Hypothesis failed: Unicode keys break the trie. New hypothesis: Use a hash map with normalized keys."

   **REQUIRED — Assumption Tracking:**
   - In your first 2 thoughts, explicitly list key assumptions you are making
   - Format: `Assumptions: 1) [assumption], 2) [assumption], ...`
   - REQUIRED: In a later thought (after branching or before your final thought), explicitly
     revisit at least one assumption: "Revisiting Assumption N: [still valid because X /
     needs revision because Y]"
   - If an assumption doesn't hold, state the consequence:
     "If assumption [N] doesn't hold, then [consequence]"

   **RECOMMENDED — Failure Mode Analysis (for system design and architecture problems):**
   - Dedicate at least one thought to identifying failure modes and their mitigations
   - Format as a structured list or table: `Failure: [what breaks] → Impact: [consequence] → Mitigation: [recovery]`
   - Focus on the 3-5 most critical failure scenarios, not an exhaustive list
   - Example: "Thought 8/10: Failure modes — 1) Kafka broker down → Impact: none (replication factor 3) → Mitigation: automatic rebalance. 2) Redis cache failure → Impact: stale preferences for up to 5min → Mitigation: fallback to DB read."

4. **Iteration and Refinement**
   - If hypothesis fails verification, generate new hypothesis with the required labels
   - Continue until a satisfactory solution emerges
   - Do not force premature conclusion

5. **Final Thought**
   - Clearly mark when complete: "Thought 10/10 (Final)"
   - Provide the definitive answer or solution
   - Summarize key insights if helpful

### Formatting Thoughts

Present thoughts in a clear, structured format:

```
Thought [current]/[total]: [Content]
```

For special thought types:

```
Thought [current]/[total] (Revising Thought [number]): [Content]
Thought [current]/[total] (Branch [ID] from Thought [number]): [Content]
Thought [current]/[total] (Final): [Content]
```

### Dynamic Adjustment Examples

**Increasing Scope:**
```
Thought 1/5: Analyzing the problem requirements...
Thought 2/5: Breaking down into components...
Thought 3/5: Wait, there's additional complexity here with concurrency. Adjusting to 8 thoughts.
Thought 4/8: Now examining thread-safety considerations...
```

**Decreasing Scope:**
```
Thought 1/7: Examining all possible approaches...
Thought 2/7: Actually, the built-in library handles this. Adjusting to 3 thoughts.
Thought 3/3 (Final): Use the standard library's XYZ method.
```

**Branching and Comparing:**
```
Thought 3/8: Two viable approaches identified. Exploring both.
Thought 4/8 (Branch A): Using approach A with recursion...
Thought 5/8 (Branch B): Using approach B with iteration...
Thought 6/8: Comparing branches - Branch B is more efficient due to...
Thought 7/8: Selecting Branch B approach.
```

**Revision Based on New Insight:**
```
Thought 4/7: Based on assumption X, the solution is Y...
Thought 5/7 (Revising Thought 4): Assumption X is actually false because Z. Need different approach.
Thought 6/7: New solution considering Z...
```

### Process Termination

Only conclude when:
- A satisfactory solution has been found AND verified
- All critical aspects have been considered
- Confidence in the answer is high

Do NOT conclude prematurely to meet an estimated thought count. Add more thoughts if needed.

### Example: Complete Thought Sequence

```
Thought 1/5: Analyzing the problem - detect duplicates in an integer stream. Focusing on data structure choice; setting aside serialization and network concerns for now.
Thought 2/5: Initial approach - HashSet for O(1) lookup. Estimate of 5 thoughts remains appropriate because scope is clear.
Thought 3/5: Stream is potentially infinite. Adjusting to 6 thoughts. Hypothesis: Bloom filter gives constant space with acceptable false-positive rate. Verifying: false positives may be unacceptable for correctness-critical callers. Hypothesis failed: correctness requirement rules out probabilistic structures.
Thought 4/6 (Branch A): Sliding window with HashSet — O(1) lookup, O(N) space.
Thought 5/6 (Branch B): Count-min sketch — probabilistic, constant space.
Thought 6/6 (Final): Sliding window (Branch A) for correctness; Count-min sketch (Branch B) only if memory is severely constrained.
```

## Best Practices

1. **Be Honest About Uncertainty** - Express when multiple paths exist or understanding is incomplete
2. **Don't Force Linear Progression** - Branch, backtrack, or revise as needed
3. **Adjust Dynamically** - You must re-evaluate your thought count after Thought 2, and again whenever complexity changes
4. **Focus Each Thought** - One clear purpose per thought
5. **Verify Before Concluding** - Every hypothesis must have an explicit `Verifying:` step before you accept it
6. **Filter Noise** - You must explicitly state what you are filtering out when multiple concerns exist
7. **Maintain Context** - Reference previous thoughts when building on them
8. **Embrace Iteration** - A failed hypothesis must produce a new labeled hypothesis, not silent abandonment
9. **Signal Confidence** — Annotate your key conclusions with confidence levels. Use "high confidence:", "moderate confidence:", or "low confidence:" at least 3 times across your analysis. Vary the levels — not everything should be "high confidence". Express genuine uncertainty where it exists.

## Output Format

After completing the thought sequence, provide:

1. **The Final Answer** - Clear, actionable solution or recommendation
2. **Key Insights** (optional) - Summary of important discoveries from the thinking process
3. **Next Steps** (if applicable) - What should be done to implement or verify the solution

Present this as normal output after the thought sequence, not as another numbered thought.
