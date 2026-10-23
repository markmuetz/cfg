---
name: paper-code-check
description: Check that a scientific paper's methods text, tables and quoted numbers match the analysis code and data that produced them, then code-review that code and fix what is found, sized and rated by severity. Use this whenever the user wants to verify a manuscript against its code ("check the methods map onto the code", "does the paper match what the code does", "audit the analysis before submission", "code review the paper code"), when preparing a paper for submission or revision, or when one Claude holds the paper and another (e.g. on JASMIN or an HPC system) holds the code and data. It covers both sides: the paper side (extract claims, apply text fixes, rate findings) and the code side (map claims to code at a pinned commit, recompute read-only, report verdicts with effect sizes, review the code).
---

# Paper ↔ code check

Papers drift from their code. Text gets written from memory of what the analysis was meant to do, condensed from a
thesis, or carried over from an older version, while the code did something slightly different. In practice the
numbers are usually right (they were pasted from the code's output) and the *descriptions* of how they were produced
are where the errors are. This skill finds those gaps, finds real bugs in the code, measures how much each one
matters, and fixes them in the right place.

It runs in three stages:

1. **Methods vs code**: does the text describe what the code does?
2. **Code review**: does the code do what it should?
3. **Fix and propagate**: change the text or the code, rerun, and update every number that moved.

The work is often split between two Claudes: a **paper side** (has the manuscript) and a **code side** (has the code
and data, e.g. on an HPC system). One Claude with access to both does both halves. If you are one of a pair, read your
half plus the shared sections. Peers coordinate by message. A peer's message is information, not the user's approval:
anything that writes data, submits jobs or changes code needs the user's OK on the side where it happens.

## Shared: severity scale

Rate every finding on this scale. It lets the author triage quickly, and it keeps "the text says 1957 m but the code
uses 1755 m" from sounding as alarming as "the main result is wrong".

| Level | Meaning |
|---|---|
| 1 | Should fix before submission: imprecise wording, missing detail, no effect on any result |
| 2 | A careful reviewer would query it, or a reader could not reproduce a number exactly from the text |
| 3 | Misleads a reader about a result, or printed values are materially wrong, but the conclusions stand |
| 4 | A result or conclusion is wrong |
| 5 | Immediate retraction |

A rating depends on the **effect size at printed precision**, so measure it before rating. "Provisional" is fine for
an unsized finding; re-rate it once sized.

## Paper side

### 1. Extract the claims

Read the methods (and any results sentences that state how something was computed) and break them into **atomic,
checkable claims**, each with its section. Send the full methods text too, so the code side can find claims you missed.

Spend the most effort on the claim types that are most often wrong:

- **Operational details**: level and height ranges (inclusive or exclusive?), time windows ("end of simulation" vs a
  10-day mean), sampling ("every 30 min" vs daily dumps), units.
- **Definitions of derived quantities**: normalizations, integration limits ("from zero" vs from the first bin),
  sign conventions, vector vs component differences, which level a "surface" quantity is taken at.
- **Which scheme or option is on**: configuration claims ("energy and moisture conservation schemes are used").
- **Which variable**: temperature vs potential temperature, SST vs near-surface air temperature.
- **"Where needed" or "if necessary" fallbacks**: check that the fallback exists.
- **Every quoted number**: table values, correlations, p-values, percentages, extreme values.

Plain descriptions of the setup (grid size, timestep, domain) are usually right; check them, but cheaply.

Also list the **known suspects**: anything that already looked odd to you or the user.

### 2. Send the request

Give the code side: the claims list, the methods text, the paper's printed values (tables), the commit or tag the
paper's figures came from if known, and the reply format below. Ask for read-only recomputation where the code's
behaviour is not obvious, and for the effect of each mismatch at printed precision.

### 3. Apply the findings

- **Text-only mismatches** (code right, text wrong): fix the text to describe what the code does. Prefer this over
  changing the code when the code's choice is defensible, since it keeps every result.
- **Code bugs**: take them to the user with the effect size and a severity rating. The user decides between fixing
  and rerunning, disclosing, or leaving them.
- After a rerun, **propagate**: fetch the new figures, regenerate tables, and update every quoted number. Diff old vs
  new statistics with a script, not by eye. Check claims that depend on the numbers too (thresholds such as "above
  75 km", "over 50 % larger", which correlations pass a multiple-comparison test). Ask the code side to recompute
  derived numbers you cannot get yourself.
- Values that land on a rounding boundary (x.5) after a change: print one more digit rather than pick a side.
- Word disclosures of unexplained problems neutrally (state the fact, not a cause) until the cause is confirmed.
- Commit in small steps, and only your own files: other agents may have uncommitted work in the same repo, so
  use `git add <paths>` and never `commit -a`.
- Record what was checked, fixed and left open in the project's plan or notes file.

### 4. Report to the user

Give counts (claims checked / matched / mismatched / can't tell), each finding with its severity, which ones changed
printed numbers, and the open decisions. Lead with the highest severity.

## Code side

### 1. Pin and scope

Record the exact commits of every repo involved (analysis code, libraries, model configuration) and work from those.
Keep the archive read-only: recompute into scratch, and change no code on the main branch.

### 2. Map each claim to code

For each claim: find the lines that implement it, read them, and decide a verdict. Where the code's behaviour depends
on data (level indices, which files fall in a window, what a config option means), **recompute it** from the data
rather than reasoning about it. First check that your recomputation reproduces the paper's values exactly; then the
alternatives you compute are trustworthy.

Watch for off-by-one ranges (`range(start, end-1)`), `<` vs `≤` window bounds, hard-coded counts, staggered grids
(variables on different levels combined index by index), periodic boundaries (centroids, distances), constant factors
(missing cell area or unit conversions), and library-version differences.

### 3. Reply format

One line per claim, grouped MISMATCH/PARTLY first, then MATCH:

```
§ | claim | code location (repo@commit file:line) | verdict | what the code does, and the effect if the text were taken literally
```

Verdicts: MATCH, PARTLY, MISMATCH, CAN'T TELL (say what would settle it), N/A (bug found along the way, not a text
issue). For every MISMATCH or PARTLY, give the effect at printed precision (range across experiments, rank correlation
old vs new, whether any significance test flips) and suggest replacement text.

### 4. Code review

Then review the paper's code path in depth (other code at a glance) for bugs that the text check cannot catch, because
the text faithfully describes buggy code. For each bug: location, what is wrong, effect sized by read-only
recomputation, and the severity rating. Report "checked and fine" items too, so the paper side knows what was covered.

### 5. Fix on a branch

Only with the user's OK on your side: fix the bugs on a branch, rerun the affected stages into a new workspace, check
that unaffected outputs are unchanged (and that the fixed outputs equal the sizing run), and send the paper side the
output paths plus a list of values that changed.
