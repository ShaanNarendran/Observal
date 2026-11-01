<!-- SPDX-FileCopyrightText: 2026 Shaan Narendran <shaannaren06@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Discovery optimization workflow

Use `mcp`, `skill` or `hook` for `TYPE` throughout. Every step below is one run of this skill; step 7 is the next run.

## 1. Check the component

```bash
observal registry skill show NAMESPACE/SLUG --output json
observal registry version list skill NAMESPACE/SLUG --output json
```

Use `registry mcp show` or `registry hook show` for those types. Confirm the user owns it and note the current description and the highest version, including any release still pending.

## 2. Reuse or generate a report

```bash
observal ops insights show --component skill NAMESPACE/SLUG latest --section discovery --output json
observal ops insights generate --component skill NAMESPACE/SLUG --discovery --wait --output json
```

Reuse the latest report only if its `data.listing_version` equals the current approved version and `data.state` is `assessed`. Otherwise generate. Generation spends a model call and needs verified sessions; if it fails for lack of them, stop and say so. After generating, read the section with the first command.

## 3. Show the suggestions

For each entry in `data.suggestions` show the example search, the suggested description, the rationale, the listing fields it rests on (`listing_evidence_keys`), and `relevance_before` to `relevance_after`, described as the ARD ranker applied to an invented search. If `suggestions` is empty or `state` is `unknown` or `unavailable`, report that and stop.

Ask which one to apply, or for the user's own wording. Check the final text against the `show` output: no capability the component lacks, no stuffed keywords, and no more than 600 characters.

## 4. Record the baseline

For each example search the chosen suggestion used:

```bash
observal discover search "EXAMPLE SEARCH" --output json
```

Find the entry in `results` whose `obs:nativeRef` starts with `NAMESPACE/SLUG@`. Record its 1-based position, the number of results, its `score` and `matchedOn`. Record "not found" if it is absent. Use the example search word for word.

## 5. Publish for review

Take the next patch version above every version in the list, including pending ones.

```bash
observal registry version publish skill NAMESPACE/SLUG --version NEXT --description "FINAL DESCRIPTION" --changelog "CHANGELOG" --output json
```

Write the changelog in exactly this shape so a later run can read it:

```text
ARD discovery update (insight report REPORT_ID).
Baseline from real ARD search on YYYY-MM-DD, listing vCURRENT:
- "EXAMPLE SEARCH": position P of N, score S, matched TERMS
```

The release starts `pending` and the output carries `review_number`. Read it back with `registry version list` to verify. For a skill, compare the first lines of the returned `skill_md_content` with the new description and tell the user if its frontmatter `description` differs. Then say it is awaiting review number N, that a reviewer must approve it, and that you did not and will not approve it. Give the command to run this skill again once it is approved.

## 6. If publishing fails

A version that already exists means a stale list: read it again and pick the next patch. A validation error is reported as is. Do not retry without reading the release list first.

## 7. The next run: did it help?

```bash
observal registry version list skill NAMESPACE/SLUG --output json
```

Find the release whose `changelog` begins with `ARD discovery update`. If its `status` is `pending`, report that it is still awaiting review and stop. If it was rejected, report the reason and stop. If it is `approved`, repeat each baseline search from step 4 using the quoted example searches in its changelog, and show a table: example search, before and now for position, score and matched terms.

Give a verdict per search: improved, unchanged or worse. Add the caveats that matter: the index uses the latest approved release, so a later release changes what is indexed; other listings may have changed; and when the position is already first, only the score and matched terms can show an effect. If nothing improved, say so. Do not respond by editing the description toward the query. Offer a fresh report for the current release instead.
