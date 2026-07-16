# Iter219 — Temporal consequence-test yield

Status: prospective pre-data measurement gate. Recorded before any instance metadata, repository history,
symbol extraction, overlap outcome, or control outcome is observed.

Predecessor merged master: `470ca3627b7635d9a315cf2811ceb2eed6575fb9`.

Dependency order: this gate executes **before**
`experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`. Iteration numbers record
creation order; the roadmap already runs `iter214 -> iter212`. Reserved roadmap names `iter215`-`iter218`
are unchanged and uncreated.

## Why this gate exists

TCP-1 admission is blocked at `2/11` gates. Two of the nine blockers —
`twelve_task_cohort_and_hidden_tests` and `calibration_controls` — currently require at least two recruited
human authors to write hidden consequence tests, and two more humans to label semantic outcomes. That is a
research-lab dependency, and it is the reason TCP-1 has been unable to move for ten iterations.

This gate tests a cheaper and, if it holds, **more independent** source for those hidden consequence tests:
tests that repository maintainers added *after* a task's base commit. Such tests are authored by people with
no knowledge of TELOS and no conflict of interest, and their chronology is externally verifiable from public
Git history rather than asserted by this repository.

This gate does not test that hypothesis. It tests **one necessary condition** for it: that later-added tests
statically reference the code a task actually touched, at a rate distinguishable from name-collision noise.

## Question

For a coding task frozen at repository commit `T`, do test functions added to that repository within `Δ`
days after `T` statically reference the source symbols that the task's gold patch modified, at a yield
above a matched permutation control?

## Sample

Frozen selection rule, fixed before observation:

- source: SWE-bench Verified instance metadata (`repo`, `base_commit`, `patch`, `created_at`);
- take **every** instance in the dataset — no subsampling, no ranking, no discretionary exclusion;
- objective inclusion criteria, applied mechanically:
  1. the gold patch modifies at least one non-test Python source file;
  2. `base_commit` resolves in a read-only clone of the repository;
  3. the repository's recorded default-branch history contains at least `730` days of commits after
     `base_commit`'s committer date.
- every excluded instance is counted and reported by exact reason. Exclusions are never silent.

The realized dataset revision, each repository's clone URL, and each repository's exact analyzed head SHA are
recorded in the result. They are not chosen; they are whatever resolves at execution time.

## Definitions

Fixed before observation.

**Touched symbols.** For instance `i`, parse each non-test Python source file modified by the gold patch, at
`base_commit`, with `ast`. Map every changed line number to its innermost enclosing `FunctionDef`,
`AsyncFunctionDef`, or `ClassDef`. `S_i` is the resulting set of symbol names. A changed line with no
enclosing definition (module-level code) contributes no symbol.

**Later-added tests.** For window `Δ`, consider commits reachable from the recorded default-branch head, not
reachable from `base_commit`, with committer date in `(date(base_commit), date(base_commit) + Δ]`. `L_i(Δ)`
is the set of test functions **added** by those commits: functions whose name begins with `test_`, defined in
a file matching the repository's test path convention, present after the window and absent at `base_commit`.

**Qualification (primary).** A test `t ∈ L_i(Δ)` qualifies for `i` if the source text of `t`, including its
decorators and body, contains an identifier token exactly equal to some symbol name in `S_i`. Token equality
is exact; substring matches do not count.

**Yield.** `yield_i(Δ) = 1` if at least one test in `L_i(Δ)` qualifies, else `0`.
`Y(Δ) = Σ_i yield_i(Δ) / N`.

**Permutation control.** The control estimates how much yield arises from common identifier names rather
than real code correspondence. Construct a deterministic derangement `π` over the included instances,
restricted so that `π(i)` is never `i` and never shares `i`'s repository. Index `j = π(i)` supplies the
later-added test window; instance `i` supplies the symbol set. `control_i(Δ) = 1` if any test in `L_j(Δ)`
qualifies against `S_i`. Derangement order is generated from the first four bytes of
`SHA-256("telos-iter219-permutation-v1:" + index)` for `index = 1..N`, matching the existing TCP-1 seed
convention. The control is computed from the same code path as the primary; only the pairing changes.

## Analysis

Frozen before observation. All primitives are the existing TCP-1 implementations; this gate adds no new
statistics.

- `Y(Δ)` and `Y_control(Δ)` for `Δ ∈ {90, 180, 365, 730}`, each with the frozen two-sided Wilson interval;
- primary window is `Δ = 365`;
- real versus control is **paired by instance**, so the frozen one-sided exact conditional McNemar test is
  the primary comparison;
- per-repository breakdown reported for every `Δ`;
- every excluded instance and every symbol-extraction failure reported as explicit missingness. Absence is
  never scored as a zero and never as a one.

## Acceptance bars

1. `Y(365) ≥ 0.20` and its Wilson lower bound `≥ 0.10`.
2. One-sided exact conditional McNemar for `Y(365) > Y_control(365)` returns `p < 0.01`, and
   `Y(365) − Y_control(365) ≥ 0.10`.
3. No single repository contributes more than `50%` of all qualifying instances at `Δ = 365`.
4. Symbol extraction succeeds on `≥ 90%` of included instances.
5. Every excluded instance is reported with an exact machine-readable reason.
6. The measurement reproduces byte-for-byte from the committed instrument, the recorded dataset revision, and
   the recorded per-repository head SHAs.
7. No provider or model request, GPU allocation, scientific container, repository test execution, trajectory,
   workflow dispatch, payment, or release occurs.

Bars `1`-`4` failing is a **null**, published at full weight under Standard 2, not a reason to re-cut the
sample, adjust `Δ`, relax a threshold, or change the qualification rule.

## Falsifiers

- Any outcome, overlap count, or control count is observed before this hypothesis is sealed.
- The sample rule, qualification rule, window set, derangement seed, or any bar changes after observation
  without a separately versioned pre-data amendment.
- The permutation control's interval overlaps the primary's at `Δ = 365`: the measured yield is then
  name-collision noise, and the screen is a null regardless of `Y(365)`'s magnitude.
- A single repository drives the result past bar `3`: the yield is a repository-specific artifact, not a
  general property, and must be reported as such.
- Static token overlap is described as proving that a test executes the changed code.
- This screen is described as establishing TCP-1 feasibility, detector efficacy, model behavior, prevalence,
  or state of the art.
- Any TELOS code, state, evidence, branding, or operational authority is imported from Aweb. TELOS,
  Sentinel, Inbar, and Odeya remain related projects that are separate from Aweb.

## Claim boundary

A passing iter219 establishes exactly one thing: that maintainers' later-added tests statically reference
task-touched symbols at a rate above matched name-collision noise.

It does **not** establish that those tests execute the changed code. Static token overlap is a screen, not
coverage. Establishing coverage requires executing the tests against the patch under a gold differential,
which is a separate, later, container-bound gate and is not authorized here.

It does not establish that such tests discriminate semantically wrong patches that pass the visible grader —
that is TCP-1's actual question and requires model output that does not exist.

It does not establish that the twelve-task cohort can be built, that any human role can be retired, or that
any monetary budget can be reduced.

SWE-bench Verified's repositories are a nonrandom sample of mature Python projects; no yield here is a
population rate. The instances are historical and pre-date any current model cutoff. They are used precisely
because their futures are already written and externally auditable. Transferring the yield to post-cutoff
tasks assumes repository test-writing behavior is stable over time. That assumption is disclosed, is not
tested by this gate, and must be re-examined before any cohort is frozen.

The gold patch is used as a proxy for the task's code region because no agent patch exists. That proxy is a
limitation, not a finding.

## Execution envelope

Allowed: read-only retrieval of the public dataset revision; read-only repository clones pinned to recorded
head SHAs; local deterministic static analysis; provider-free tests; local document and receipt generation;
eventual repository publication.

Forbidden: any model or provider request, GPU allocation, accelerator-hour, scientific container, execution
of any cloned repository's test suite, trajectory, workflow dispatch or rerun, deployment, payment, or
release. Cloning a repository is a read of public history; it is never an execution of that repository.

## Publication boundary

Seal this hypothesis before the instrument observes data. Then create one receipt-bound source commit above
merged master `470ca36`, and one handoff-only seal commit. Publish the branch once, open one draft pull
request against `master`, and merge with a two-parent merge commit only after exact-tip push and pull-request
CI pass on Python 3.11 and 3.12, the secret scan is non-blocking, and no substantive review blocker remains.

Publication authorizes no TCP-1 execution, no cohort freeze, no reviewer recruitment, no budget, and no
release.
