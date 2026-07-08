# Pre-registration - Target Survey

Frozen on 2026-07-08 before any Telos benchmark result exists.

## Research Question

Can an autonomous agent completion protocol improve the rate at which long-horizon agents complete
the real objective, rather than only the visible proxy, while preserving or improving ordinary task
success?

The first experiment does not test the protocol yet. It chooses the target. That target must be
worthy of the method before any score-chasing begins.

## The Gate We Are Chasing First

`iter00_target_survey` must identify one benchmark family with all of the following:

1. A public task set or public benchmark lineage.
2. A baseline score or published leaderboard that can be cited.
3. A completion surface richer than a final answer.
4. A way to detect proxy success that is not real completion.
5. A first experiment feasible on local CPU plus API calls or one modest GPU.
6. A clear falsifier that can stop the line before larger runs.

If no candidate clears the gate, the survey result is a null and the repo does not pretend to have
a target.

## Candidate Families

The survey must evaluate at least these five families:

| family | reason for inclusion |
|---|---|
| SWE-bench Verified / coding agents | strong public baseline, real GitHub issues, coding-agent relevance |
| METR RE-Bench / AI R&D agents | long-horizon research engineering, human comparison data |
| tau-bench / service agents | policy adherence, tool use, user interaction, database-state evaluation |
| AgentDojo / adversarial tool agents | utility/security tradeoff, prompt-injection pressure |
| Telos overlay | may be needed if existing benchmarks lack evidence receipts |

## Scoring Rule

Each candidate receives integer scores from 0 to 5:

- `frontier_relevance`
- `public_baseline_quality`
- `falsifiability`
- `evidence_surface`
- `aweb_fit`
- `saturation_risk` as a penalty
- `operational_cost` as a penalty

Adjusted score:

```text
frontier_relevance
+ public_baseline_quality
+ falsifiability
+ evidence_surface
+ aweb_fit
- saturation_risk
- operational_cost
```

The target can freeze only if:

1. adjusted score is at least 16,
2. no positive component is below 3,
3. operational cost is at most 3,
4. the survey names a first-run falsifier,
5. at least two public sources support the target's relevance and baseline.

## What Counts As A Win

The survey wins only by producing a specific next target:

- benchmark name,
- task split or task subset,
- baseline score to compare against,
- Telos receipt fields,
- primary metric,
- falsifier,
- first-run cost envelope.

## What Does Not Count As A Win

- A broad essay about agents.
- A private benchmark with no external anchor.
- A target selected because it sounds important.
- A leaderboard that is already too saturated to reveal a protocol effect.
- A task where the only evidence is the agent's final answer.

## Frozen Output

The result must be published as:

- `experiments/iter00_target_survey/RESULT.md`
- source receipts under `experiments/iter00_target_survey/proof/`
- updated `README.md` status table
- regenerated `HANDOFF.md`

The result may be positive, negative, or blocked. All three are acceptable.
