---
# SPDX-FileCopyrightText: 2026 Shaan Narendran <shaannaren06@gmail.com>
# SPDX-License-Identifier: Apache-2.0
name: observal-ard-seo
command: observal
description: "Improves how an owned MCP server, skill or hook is found in Observal discovery (ARD): turns its Insights report into reviewed description edits, publishes the chosen edit as a new release for review, and later measures the real search result. Use when the user wants an owned component to be easier to discover, asks for ARD or discovery suggestions or a better listing description, or asks whether an earlier discovery edit helped."
version: 1.0.0
owner: observal
---

# Improving how a component is discovered

## Execution contract

1. Execute commands with a 60 second timeout. Use a longer timeout only for `--wait` report generation.
2. **Use machine output by default:** add `--output json` whenever supported.
3. Run `--help` before acting when a path or flag is uncertain.
4. Work on one component at a time, by the exact `NAMESPACE/SLUG` the user named, and confirm they own it.
5. Never approve, publish or otherwise act on the review of the release you create. Stop at "awaiting review".
6. Verify every mutation by reading the release back with `registry version list`.
7. Never repeat secrets or other users' prompts, transcripts or tool arguments.

Read [Discovery optimization workflow](references/discovery-optimization.md) completely before executing.

## Decision rules

- This skill changes only what a listing says about itself. It cannot raise a rank, and usage never boosts relevance. Never promise ranking, traffic or installs.
- A suggestion's example search is invented by the model for illustration. Never describe it as something users searched for, and never describe its relevance figures as a search position.
- Apply a suggestion only after the user has seen its text and evidence and approved it, or approved their own edit of it. Every claim in the description must be supported by the listing, its published files or the report evidence. Refuse keyword stuffing and capabilities the component does not have.
- Write no suggestion of your own. If the report has no suggestions, or its discovery state is `unknown` or `unavailable`, say so and stop.
- A report needs verified sessions. If generation fails because the component has none, report that and stop; there is no usage-free path.
- Agents are out of scope: their discovery advice is read-only here.
- For a skill, the new release keeps its `SKILL.md` unchanged, and harnesses read the description in that file's own frontmatter. Tell the user when the two now differ. Do not edit the files unasked.
- A measured result is a real search on this server at that moment. Report rank, score, matched terms and the number of results together, and say plainly when nothing improved.

## Completion

Report the component and version, the report ID, the exact description applied, the baseline measurements, the new release's version, status and review number, and the command to run this skill again after approval. On a follow-up, report the before and after table and a verdict per query.
