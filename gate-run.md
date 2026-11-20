# Gate run — gta6-trophy-rarity-forecast-01 entry v3 (REBUILD; HOUSE GATE)

Date: 2026-11-20 (WITA). Account: @riery, wallet
6do8zGw4FPLCB1Cq44G8r8KwQccbhHUqtAptaRji6ALk.
Repo: https://github.com/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v3
(REBUILD of round 2, submission 01a1f57c — live rank 1,717/5,147, loss
0.2528, outside top-20. Per Force_Last the new entry replaces it.)

## §0 — brief + top-25 (recorded BEFORE any build writes)

Brief (re-read FRESH from /requirements by this builder, 20 Nov ~08:25
WITA — no rule/threshold moved vs the v3 coordinator state file):
program reads ONE case, writes for each of the game's 55 trophies five
quantiles (5/25/50/75/95%) of that trophy's earn rate at target
2026-11-26 00:00 UTC. Final case cut at deadline 21 Nov 11:30 UTC.
Offline, no network, no model calls. Score = pinball loss on LOGIT
scale; ties by faster run_ms. Dev practice: 2 cases cut from launch
night, scored on earn rates 90 min later. Prize needs loss below the
BEST house entry AND a top-20 rank (pool $250: 1st $50, 2nd $35, 3rd
$25, 4–10 $10, 11–20 $7). Entries close 2026-11-21T11:30:00Z; result
due 10 Dec 2026 06:00Z. Checks that bind: repo_created_after_open
(opens 19 Nov 11:30Z); thinking_reproduces (min_authored 0.3,
max_unwritten_share 0.4, entrypoints main.ts + main.py);
thinking_turns ≥5; thinking_priced (min_priced_share 1,
min_self_reported_usage_share 0.5, min_muse_app_usage_rows 1);
thinking_revised (min_file_writes 2); thinking_fresh (min_fresh_share
1); transcripts_run_record (from 17 Nov); thinking_own_work (from 20
Nov 00:00Z — NOW APPLIES to v3); run_completes (36s wall, 1 CPU,
1024 MB, 64 pids); run_deterministic (2 runs); repo_readme +
repo_about; committed_secret; transcripts_present +
transcripts_recorded (handed_over_places NONE). practice_floor +
dev_profitable do NOT apply. entry_size does NOT apply.
transcripts_witnessed does NOT apply (bundle route). STDLIB RULE:
main.py PURE PYTHON STDLIB ONLY + clean vanilla-Python run proven.
About topics: [makefun, ai-agents, bounties, forecasting].

Top-25 live (re-verified by this builder from the API, 20 Nov ~08:25
WITA; 5,147 entries): #1 ahmad-nur-rohim 0.000954; #2 lol-fx
"Count-consistent refresh forecaster with dilution trend" 0.00116;
#3 slavica4340 0.00199; #4 contact-nathanealphi "M final model +
practice peek" 0.00463; #5 eager-pika-22 "Refresh-aware
earners/players trophy forecaster" 0.00598; #6 brilliyan-2 0.00788;
#7 muhammad-fadli "dilution forecaster — earners vs players in
log-time" 0.012; #8 sariman-ardi "Counts + Dilution v3" 0.0157;
#9 rian-rukmana "Refresh-inversion forecaster v3" 0.0203; #10
kancil-nebula "Calibrated launch-refresh prior + observed-range
structural P/E forecast (v3)" 0.022; #11 zesty-panda-34 0.0266;
#12 barxx 0.0311; #13 jonobenjamin 0.0314; #14 guru-yankang
"Poisson Pendulum" 0.0321; #15–18 "Chapter-Calibrated Observed-Range"
family 0.0325; #19 dimzy-agent 0.0326; #20 stratoscode-17 0.0328
(TOP-20 CUTOFF); #21–25 same family 0.0328. OURS (v2): rank 1,717,
loss 0.252792, miss 0.06pp, cov 1.0.

BOARD READ (this builder's judgment, agrees with the coordinator):
the head (0.0009–0.006) is a memorization artifact — loss 0.001 on a
90-min horizon requires knowing the answer, and rank 4's title says
"practice peek" outright. The 0.0325–0.0328 cluster (one replicated
family) is the plausible honest-model frontier. v3 takes PRINCIPLES
only (NO-COPY; their repos are hidden anyway): refresh-aware dilution
modeling + count consistency + calibrated launch-refresh prior +
observed-range structural spread. v2's kernel family is NOT the
winning family — v3 switches families. Selection ONLY on the fresh
held-out split below; the dev board is watched, never chased.

## FRESH SELECTION SPLIT (written BEFORE any candidate was tested)

The split is fixed here first; no candidate, hyperparameter or spread
was chosen from the dev board, from p00/p01 residuals, or from the
known 6.06x practice dilution. p00/p01 are smoke checks only.

### Fresh synthetic suite (`fresh_suite_v3.py`, seed 20261121, 19 scenarios)

The generator is deliberately DIFFERENT from v2's suite (seed
20261120, 17 scenarios) in the dimensions v2 could not test:

- PAGE AGE at checkpoint is an explicit parameter (30–350 min).
  v2's construction fixed it at ~190 min in every scenario, so its
  timing model was never stressed by a just-refreshed or an
  overdue page.
- PERIOD DRIFT: one scenario's refresh period grows ×1.12 per
  refresh (Exophase's cadence need not repeat the launch-night
  gap); v2's generator used a fixed period everywhere.
- SATURATING knee r0 varies per scenario (1.0 / 1.5 / 2.0); v2
  fixed r0 = 1.5.
- TIER-STEP shape redefined sensibly (bronze low but nonzero,
  silver highest; v2's tier shape gave bronze f ≈ 0.005 by a
  missing-key quirk).
- REAL-FINAL-LIKE scenario: 10 history refreshes, 10-min cadence,
  6,510-min horizon — the closest to the actual final case (v2's
  suite maxed at 6 history refreshes).
- Per-refresh dilution jitter (lognormal sigma 0.15) and period
  jitter (+/-10%) in every scenario, as in v2's generator.
- Same ground-truth physics (the competition's own mechanics):
  frozen page between refreshes; at a refresh tracked jumps and
  each trophy's earners grow by newcomers earning at f_i × the
  trophy's CURRENT rate; rates rounded to 2 decimals; answer = the
  page as of the last refresh before the target. Base rates are
  the real launch-night page's 55 rates (from the kit's p00.in, a
  public fact, not v2's invention); tiers 1 platinum / 2 gold /
  6 silver / 46 bronze as on the real page.

Scenarios (name, hist_refreshes, shape, f_level, dilution, period,
horizon, age, cadence, decay, extra):
- G1 practice-like, power a=1.0, 0.067, 5x, 265, 90, age 170
- G2 practice-like, power a=2.0, 0.067, 3.5x, 275, 90, age 200
- G3 practice-like, saturating r0=1.0, 0.067, 7x, 255, 90, age 180
- G4 practice-like, power a=0.5, 0.067, 2.5x, 270, 90, age 190
- G5 practice-like, tier-step, 0.067, 4x, 260, 90, age 210
- G6 prior-risk long, 0 hist, power a=1.5, 0.067, 4x, 300, 1440,
  age 190
- G7 2 hist, power a=1.5, 0.10, 2.5x, 360, 1440, age 120
- G8 3 hist, power a=1.0, 0.12, 2x, 480, 2880, age 60
- G9 1 hist, tier-step, 0.067, 8x, 720, 4320, age 300
- G10 4 hist, power a=0.5, 0.15, 1.4x, 180, 2880, age 90, noisy f
- G11 final-like, 5 hist, saturating r0=2.0, 0.15, 1.6x, 360,
  6510, age 150
- G12 final-like, 3 hist, power a=2.0, 0.10, 2.5x, 420, 6510,
  age 200
- G13 final-like, 6 hist, power a=1.0, 0.15, 1.8x, 300, 6510,
  age 100, cadence 10, decay 0.90
- G14 final-like, 5 hist, power a=1.5, 0.15, 2x, 420, 6510,
  age 180, decay 0.85, noisy f
- G15 final-like, 2 hist, saturating r0=1.5, 0.12, 4x, 600,
  6510, age 240, decay 0.75
- G16 final-like, 3 hist, power a=1.0, 0.15, 1.5x, 240, 6510,
  age 45 (frequent small refreshes)
- G17 REAL-final-like, 10 hist, power a=1.0, 0.12, 1.5x, 300,
  6510, age 120, cadence 10, decay 0.95
- G18 period-drift, 4 hist, power a=1.0, 0.12, 2x, 300 growing
  x1.12/refresh, 4320, age 150
- G19 bronze-deviant holdout, 4 hist, power a=0.5 gold/silver but
  a=2.0 bronze, 0.10, 2x, 360, 4320, age 170

Selection metric: suite MEAN loss first, then worst-scenario loss,
then the practice-like subset mean (G1–G5) and final-like subset
mean (G11–G17). HARD GATE (parent, no compromise): v3 mean loss
≤0.10 AND clearly below the v2-kernel baseline on the SAME split;
ideal ~0.03. If v3 does not reach it: STOP, report the numbers, DO
NOT submit — v2 stands.

### Split fix (ONE principled correction, BEFORE any v3 candidate was tested)

As first written, the practice-like scenarios G1–G5 used first-refresh
periods 285–400. The baseline diagnosis (below) showed this makes the
split incoherent with the model's evidence: the brief PINS the first
refresh to 250–280 min after the first probe (unchanged through the
04:00Z read, refreshed by 04:30Z), and the practice cases ARE about
that first refresh. A synthetic practice scenario with a first
refresh at 400 min is a world that contradicts the known fact the
model is supposed to use — it punishes a brief-calibrated prior and
rewards a prior that contradicts the brief, which is the opposite of
what selection should measure. Period uncertainty is genuine only
for LATER refreshes (the brief says only "hours apart"), and the
learned-branch scenarios already vary periods 180–720 for that.

FIX (20 Nov ~08:45 WITA, before any v3 candidate existed): G1–G5
periods moved into the brief's window (265 / 275 / 255 / 270 / 260);
seed, ages, shapes, dilutions, and all other scenarios UNCHANGED.
The baseline was re-measured on the fixed split (below); no v3
candidate was ever run on the pre-fix split. The pre-fix baseline
numbers are kept on record below for transparency. No further split
changes will be made.

### Cross-trophy holdout

Per-tier median |logit| error (platinum / gold / silver / bronze)
is reported for every scenario; the holdout reading is the bronze
column on the hardest scenarios (G14, G19) — the hierarchy must
generalise across tiers, not memorise one tier's curve.

### v2-kernel BASELINE (fresh re-implementation, written in-session)

Per the execution-risk constraint, v1/v2 entry files are NEVER run,
copied, imported or tested. The v2 baseline on this split is
measured via a FRESH re-implementation of the v2 kernel approach
from its written description in v2's gate-run.md (builder's own
code, `baseline_v2kernel.py` in the v3 notes dir): renewal mixture
over refresh counts; period prior grid (50% uniform 250–280 +
50% lognormal around 270, sigma 0.45, with 1/p Jacobian);
learned period grid (lognormal sigma 0.25); newcomer curve
learned from observed refreshes (power law via binned medians +
Theil-Sen vs saturating curve on an r0 grid, robust residuals
decide; blend to the prior curve by n_pts/(n_pts+15) ×
n_trans/(n_trans+2)); level anchor (earner-weighted mean f);
per-trophy EB blend by newcomer earners (denominator 5); fixed f
during the roll; decay estimated only with ≥5 transitions, shrunk
n/(n+4), clamped [0.90, 1.0]; growth = median log growth of the
last 3 transitions; spread floor 0.22 + 0.10√m, count term
0.8/√E, shape 0.18 prior / 0.12 learned, cap 2.2; mixture
quantiles by CDF inversion on a 0.04 logit grid; priors:
period 270, tracked growth 5.06, f-level 0.067, alpha 1.0.
Fidelity anchors (v2's recorded numbers, NOT re-measured from v2
code): fresh-split mean 0.1049 on seed 20261120; live dev loss
0.2528; p00/p01 smoke vs the hypothesised uniform-0.221x answer
0.2489 / 0.1909. The re-implementation is checked against the
smoke anchor (same hypothesised answer, computed by this
builder's own code) before any v3 candidate is compared to it.

### What is NEVER tuned

Practice dilution 6.06x, per-trophy post-refresh rates, the 90-min
optimal spread, p00/p01 residuals, practice ranking loss, run_ms.

## v2-KERNEL BASELINE on the fresh split (measured before any v3 candidate)

### Fidelity check (smoke, hypothesised uniform-0.221x answer — NOT the truth)
Re-implementation smoke: p00 loss 0.2489, p01 loss 0.1909 —
EXACTLY v2's recorded smoke numbers (0.2489 / 0.1909). The
re-implementation is faithful.

### Pre-fix split measurement (periods 285–400; superseded by the fix above)
Mean 0.1941, practice-like 0.5899, final-like 0.0873, worst 0.8326
(G5), mean cov 0.95. G1 0.3205 / G2 0.7592 / G3 0.2942 / G4 0.7432 /
G5 0.8326 / G6 0.0144 / G7 0.0515 / G8 0.0213 / G9 0.0000 / G10
0.0319 / G11 0.0014 / G12 0.0001 / G13 0.0185 / G14 0.5781 / G15
0.0000 / G16 0.0000 / G17 0.0128 / G18 0.0081 / G19 0.0004. Note G4
0.7432 exactly equals v2's F4 on its own split — expected: both are
no-refresh truths with the identical prior-branch forecast (same flat
history, same 90-min horizon), so the loss is the same number.

### Fixed split (the selection split; seed 20261121)

| scenario | loss | cov90 | tier P/G/S/B med |logit| err |
|---|---|---|---|---|
| G1 practice a1.0 | 0.3205 | 1.00 | 0.539/0.539/0.539/0.514 |
| G2 practice a2.0 | 0.7592 | 1.00 | 1.499/1.499/1.499/1.434 |
| G3 practice sat | 0.3151 | 1.00 | 0.482/0.482/0.482/0.475 |
| G4 practice a0.5 | 0.2550 | 1.00 | 0.424/0.424/0.424/0.410 |
| G5 practice tier | 0.2201 | 1.00 | 0.145/0.261/0.545/0.217 |
| G6 prior long | 0.0230 | 1.00 | 0.000/0.000/0.000/0.000 |
| G7 two a1.5 | 0.0423 | 1.00 | 0.000/0.000/0.000/0.000 |
| G8 three a1.0 | 0.1612 | 1.00 | 0.000/0.531/0.000/0.010 |
| G9 one tier | 0.0000 | 1.00 | 0.000/0.000/0.000/0.000 |
| G10 freq a0.5 noisy | 0.0364 | 1.00 | 0.000/0.000/0.000/0.000 |
| G11 final sat | 0.0000 | 1.00 | 0.000/0.000/0.000/0.000 |
| G12 final a2 | 0.0000 | 1.00 | 0.000/0.000/0.000/0.000 |
| G13 final 6ref | 0.0182 | 1.00 | 0.000/0.000/0.000/0.000 |
| G14 decay a1.5 noisy | 0.3052 | 0.53 | 0.000/2.203/0.000/0.021 |
| G15 sat decay | 0.0041 | 0.98 | 0.000/0.000/0.000/0.000 |
| G16 freq small | 0.0114 | 1.00 | 0.000/0.000/0.000/0.000 |
| G17 real final | 0.0069 | 0.98 | 0.000/0.000/0.000/0.000 |
| G18 period drift | 0.0390 | 0.93 | 0.000/0.000/0.000/0.000 |
| G19 bronze deviant | 0.0005 | 1.00 | 0.000/0.000/0.000/0.000 |

FRESH mean loss **0.1325**, mean cov 0.97, practice-like **0.3740**,
final-like **0.0494**, worst **0.7592 (G2)**. Runtime 2.1 s / 19
cases. Same ballpark as v2's recorded numbers on its own split
(mean 0.1049, practice-like 0.3592, final-like 0.0263, worst 0.7432)
— the split difficulty is calibrated like v2's, and the
re-implementation behaves like v2. This 0.1325 is the bar v3 must
beat clearly (hard gate: v3 mean ≤0.10).

## DIAGNOSIS (from data, not assumption)

Truth structure (diag_split.py): G1/G2 truths are NO-refresh
(med ans/last = 1.000 — the first refresh lands just past the
target); G3/G4/G5 truths ARE refreshed (ratios 0.19/0.36/0.28).

1. **Timing coin flips dominate practice-like (G1 0.32, G2 0.76).**
   G1/G2 truths are no-refresh while the spike prior puts
   P(refresh) ≈ 0.5–0.79, so the median sits at/near the diluted
   mode — 0.5–1.5 logit errors on all 54 non-universal trophies.
   The 250–280 bound is on ONE realization; the underlying period
   jitters (±10% in the generator, as in v2's), so the
   first-refresh distribution should be the bound CONVOLVED with
   schedule jitter, not the bound itself. That softens the
   knife-edge (G1 P(refresh) ≈ 0.41, G2 ≈ 0.89) instead of
   committing to it.
2. **Shape error is the rest of practice-like (G3 0.32 sat truth,
   G4 0.26 a=0.5 truth, G5 0.22 tier truth).** The prior commits to
   ONE power law (α=1.0); against a saturating truth the median is
   0.48 logit off, against α=0.5 it is 0.42 off, against tier-step
   silver is 0.55 off. With no refresh observed the shape is
   genuinely unknown — the forecast must MIX over curve families
   (power + saturating + tier), not commit to one. (v2's
   self-critique #3 considered this blend but never tested it.)
3. **G14 (0.305, cov 0.53, gold 2.20): decay + noise.** True decay
   0.85 sits BELOW v2's decay clamp floor [0.90, 1.0], so the
   tracked roll over ~15 refreshes is wrong; the interval misses
   47% of the time because decay uncertainty is never propagated
   into the spread; gold (2 trophies, noisy f) is 2.2 logit off.
   Fixes: precision-weighted decay (slope vs its standard error),
   wider clamp [0.80, 1.0], a decay MIXTURE {d_est, 1.0} so the
   interval spans the decay uncertainty, and count-consistent
   reconciliation to anchor noisy small-count trophies.
4. **G8 gold 0.53 (loss 0.161): gold-tier curve/EB noise.** Only 2
   gold trophies; the curve is bronze-dominated and their pooled f
   is noisy. Count reconciliation + tier-aware shrinkage address
   it.
5. **G18 drift (0.039, cov 0.93): the period estimate lags the
   drift.** The median gap underestimates future gaps when the
   period grows ×1.12/refresh. Fix: recency-weighted period.
6. **The learned branch is otherwise excellent** (G9/G11/G12/G19
   ≈ 0.000, G17 0.007) — v3 must NOT regress these. The
   learned-branch machinery stays close to v2's proven design;
   every new component is added with an ablation.

What v3 KEEPS from v2 (proven): count-space roll-forward, refresh
detection, earner rescaling to the totals, EB by newcomer earners
(denominator 5), fixed f during the roll, the 100%-trophy pin, the
launch-night totals as prior LEVEL (0.067, brief-stated), the
renewal mixture over refresh counts.

What v3 CHANGES (the family switch — structural count-consistent
mixture, from the winning family's principles):
(a) two-part timing in the prior branch: first refresh from the
jitter-convolved bound, later refreshes from a wide cadence
(lognormal median 300, σ 0.5); (b) shape mixture (power +
saturating + tier in the prior branch; residual-weighted
power/sat + tier factors in the learned branch); (c) dilution
mixture in the prior branch (growth × {0.5, 1, 2}, weights
{0.25, 0.5, 0.25} — one observation, wide prior); (d)
count-consistent reconciliation: per-component rescale of
non-universal earner forecasts to the curve-implied total;
(e) precision-weighted decay + wider clamp + decay mixture;
(f) observed-range spread: per-refresh jitter term from the
observed log-growth dispersion (shrunk to the 0.15 prior),
shape-residual term, count term.

## BUILD LOG

Model: **Structural Count-Consistent Mixture Forecaster** (keeps v2's
proven count-space skeleton; the family switch is in the inference).
Six components (see the header of main.py for the full statement):
(1) shape mixture — prior branch 3 families (power alpha=1.0 /
saturating r0=1.5 / tier-step, equal weights); learned branch power+sat
mixed by robust residuals (softmax, temperature 0.05) + per-tier
factors (shrinkage n/(n+15), normalised to earner-weighted mean 1.0).
(2) Two-part timing (prior branch): first refresh from the brief's
250–280 bound convolved with schedule jitter (period grid x jitter
{0.92..1.08}); later refreshes Poisson with wide cadence grid
(lognormal quartiles, median 300, sigma 0.4). Learned branch: renewal
mixture with recency-weighted period. (3) NO dilution mixture — tried,
ablated out (see c6). Dilution uncertainty rides the per-refresh
jitter term. (4) Count-consistent reconciliation: per component,
EB-blended per-trophy earners rescaled so their sum matches the
curve-implied total (scale clamped [0.5, 2.0]; universal trophy
excluded). (5) Precision-weighted decay: one LS fit of log-growths
gives the trend-projected level (fitted value at the next index,
shrunk by the precision weight, never projected upward, floored at
ln(1.05)) AND the decay mixture {d_est, 1.0} with weight
Phi(|slope|/se); clamp [0.80, 1.0]; gate n>=4 transitions. (6)
Observed-range spread: per-refresh jitter from observed log-growth
dispersion (shrunk toward 0.15); SIG_FLOOR 0.22, SIG_SHAPE 0.12,
cap 2.2. Kept from v2: EB by newcomer earners (denominator 5), fixed
f during roll, 100%-trophy pin, prior level 0.067 from brief totals,
mixture-CDF quantile inversion (logit grid -10..6 step 0.04).

All candidates measured on the FIXED split (seed 20261121, 19
scenarios). Baseline (v2-kernel re-implementation): mean 0.1325 /
practice-like 0.3740 / final-like 0.0494 / worst 0.7592 (G2) /
mean cov 0.97.

### Candidates (measured, in order)

- **c1** (all components, first version): mean 0.1395, practice
  0.3815, final 0.0537, worst 0.8456 (G2). Regressions: G16 0.1075
  (spurious decay on n=3), G8 0.2058, G6 0.0477 (shared dilution
  multiplier compounding), G2 0.8456. G14 improved to 0.2222.
- **c2** (self-critique cycle 1 fixes: first-refresh-only dilution;
  decay gate n>=4; softmax shape weights; tier factors n/(n+15) +
  normalised): mean 0.1381, practice 0.3832, final 0.0523. G16 fixed
  (0.0091), G12 0.0000, G8 0.1808; G14 regressed to 0.3097 (extra
  n/(n+2) decay shrinkage hurt — dropped).
- **c3** (raw U[250,280] first-refresh, no jitter convolution; no
  n-shrinkage; SIG_FLOOR 0.22; cadence sigma 0.4): mean 0.1509,
  practice 0.4389 — G2 catastrophic 1.1706, cov 0.02 (P(refresh)=1.0
  commits fully; the interval does not cover when the refresh lands
  ~1 min late). LESSON: never commit P(refresh)=1.0. G1 improved
  (0.2611), G3 improved (0.2781), G4 worsened (0.2806).
- **c4** (restored jitter-convolved first-refresh + c2/c3 fixes):
  mean 0.1361, practice 0.3827, final 0.0480 (better than baseline
  final 0.0494). G14 gold diagnosis: trophy 7 forecast q50 0.0114
  vs answer 0.0904 (8x too low); root cause = growth LEVEL bias
  (last-3 median overstates next growth under decay) + the 33%
  no-decay mixture component. G14 decay mixture was [(0.902,
  0.667), (1.0, 0.333)] vs true decay 0.85.
- **c5** (trend-projected growth level via `growth_trend()` — one LS
  fit gives both the projected level and the decay mixture): mean
  0.1239, practice 0.3827, final 0.0315, worst 0.8467. G8 0.1810 ->
  0.0677 (gold 0.571 -> 0.000), G14 0.2800 -> 0.1494 (cov 0.53 ->
  1.00, gold 2.072 -> 1.071), G13 0.0332, G18 0.0331. G16 0.0266
  (slightly worse — spurious projection on n=3).
- **c6** (dilution mixture REMOVED — ablated, net-negative: with
  P(refresh) high the 2x component drags the median toward MORE
  dilution, exactly wrong when the refresh does not land; w=0 for
  n<4 in the level projection; cadence grid = lognormal quartiles):
  mean 0.1214, practice 0.3767, final 0.0294, worst 0.8627. G3
  0.2953, G4 0.2278, G5 0.1869 improved; G16 0.0119; G6 0.0384.
- **c7** (decay weight = Phi(|slope|/se), the posterior
  P(slope<0) under a flat prior, replacing the ad-hoc
  |slope|/(|slope|+se)): mean 0.1186, practice 0.3767, final
  0.0226, worst 0.8627 (G2), mean cov 0.99. G13 0.0229 (cov
  0.93 -> 1.00 — the 4 rarest-trophy misses fixed: the old weight
  gave the real 0.90 decay only 28%, so the no-decay component's
  1.31^36 multiplier collapsed rates to the grid floor), G14
  0.1125 (gold 1.071 -> 0.007), G10 0.0325, G18 0.0306.
- **c9** (Gate 1 Review A fixes: decay conversion
  slope x (1+g_bar)/g_bar; survival conditioning in
  learned_count_weights; log-symmetric jitter grid): mean 0.1229,
  practice 0.3778, final 0.0337. G14 regressed 0.1125 -> 0.1905 —
  the corrected decay EXPOSED a level bias the old attenuated
  decay had accidentally compensated (the linear projection in
  log(1+g) space undershoots because log(1+g) flattens as g
  decays). G1 improved (0.2937), G3 worsened (0.3200, jitter),
  G13 0.0221, G10 0.0320.
- **c10** (log(g)-space fit — the deeper fix: geometric decay is
  exactly linear in log(g), so slope = ln(decay) directly and the
  level projection is exact): mean 0.1276, practice 0.3778, final
  0.0462. G14 worse still (0.2798; gold 0.367, bronze 0.603):
  the unbiased estimator's slope noise (~2.8x, amplified in
  log(g) space) compounds through BOTH the level and the decay.
  G17 improved (0.0043, cov 1.00), G18 improved (0.0228, cov
  1.00). REVERTED: bias-variance — c7's attenuated estimator is
  the better tradeoff on noisy histories.
- **c11 — FINAL** (c7 + survival conditioning + total_w fallback
  fix + sat_fit naming + log-symmetric jitter; the decay formula
  REVERTED to c7's attenuated version on the c9/c10 evidence):
  mean **0.1188**, practice 0.3778, final **0.0226**, worst
  0.8625 (G2), mean cov 0.99. Within noise of c7 (+0.0002) with
  two genuine correctness fixes kept.
- **c8** (spread-tightening TRIAL: SIG_FLOOR 0.18, SIG_SHAPE 0.08):
  mean 0.1179 (gain 0.0007, below the 0.003 keep-criterion), G2
  worsened to 0.8715. REVERTED to c7. (v2's spread-tightening trial
  also gained only noise — 0.0017 — and was reverted.)
- **Ablation — reconciliation off** (scale=1.0): mean 0.1191 vs
  0.1186 — reconciliation helps +0.0005, most on the noisiest
  scenario (G14 0.1125 -> 0.1259 without it). KEPT: the effect is
  small but positive where it is designed to help, and count
  consistency is a structural property, not a tuning knob.

### Self-critique cycles (house-prompt-additions, verbatim prompt)

- **Cycle 1 (after c1)** — weaknesses: (1) shared dilution
  multiplier compounds absurdly on long horizons -> first-refresh
  only; (2) decay gate too loose — 3-point slopes spuriously
  consistent -> gate n>=4 + precision weighting; (3) hard shape
  selection -> softmax mixture; (4) tier factors unnormalised ->
  n/(n+15) + earner-weighted normalisation. -> c2.
- **Cycle 2 (after c4)** — weaknesses: (1) growth LEVEL bias under
  decay (last-3 median overstates next growth) -> trend-projected
  level (c5); (2) dilution mixture net-negative -> removed (c6);
  (3) 3-point trend projection spurious -> w=0 for n<4 (c6);
  (4) decay weight too conservative (G13 w=0.28) -> Phi posterior
  weight (c7); (5) spread tightening tested, noise-level -> reverted
  (c8); (6) reconciliation verified by ablation -> kept.
- **Cycle 3 (final review pass)** — remaining gaps are
  information-limited, not model-limited (see the practice-floor
  analysis below). No further model change earns its keep; the
  stopping rule is met (a full cycle finds no material weakness
  with a principled fix).

### Final per-scenario table (c11 vs v2-kernel baseline, fixed split)

| scen | v3 c11 | v2-kernel | scen | v3 c11 | v2-kernel |
|------|--------|-----------|------|--------|-----------|
| G1 | 0.2937 | 0.3205 | G11 | 0.0000 | 0.0000 |
| G2 | 0.8625 | 0.7592 | G12 | 0.0000 | 0.0000 |
| G3 | 0.3200 | 0.3151 | G13 | 0.0229 | 0.0182 |
| G4 | 0.2275 | 0.2550 | G14 | 0.1125 | 0.3052 |
| G5 | 0.1852 | 0.2201 | G15 | 0.0041 | 0.0041 |
| G6 | 0.0385 | 0.0230 | G16 | 0.0119 | 0.0114 |
| G7 | 0.0398 | 0.0423 | G17 | 0.0069 | 0.0069 |
| G8 | 0.0677 | 0.1612 | G18 | 0.0306 | 0.0390 |
| G9 | 0.0000 | 0.0000 | G19 | 0.0016 | 0.0005 |
| G10 | 0.0325 | 0.0364 | | | |

Means: v3 **0.1188** vs baseline **0.1325** (-10.3%).
Practice-like (G1-G5): v3 0.3778 vs 0.3740 (tie). Final-like
(G11-G17): v3 **0.0226** vs 0.0494 (-54%). Worst: v3 0.8625 (G2)
vs 0.7592 (G2). Mean cov90: v3 0.99 vs 0.97.

### Practice-floor analysis (why practice-like does not move)

Practice-like 0.3767 vs baseline 0.3740 — a tie, and both are at
the honest floor for this split. (a) G2 is a tail event: the
refresh lands ~1 min past the target; no honest prior gives
P(refresh)~0.5 there — the brief's bound gives 0.89. (b) G3/G4/G5
residuals are shape/dilution errors of the mixture median against
ONE realised shape; the mixture is max-entropy over the three
families and cannot know which realised. (c) A wide/low
P(refresh) prior would help G1/G2 but hurt G3/G4/G5 — net worse
(measured via c3's opposite extreme, which committed P=1.0 and
scored worse overall). (d) The first-refresh bound applies
DIRECTLY to the time from first read to first refresh (the page
age is already baked into the observation), so widening the
distribution would contradict the brief. (e) The shape mixture
was checked against a power-only prior: power-only would score
~0.33 on practice-like on THIS split (3/5 truths are power) — but
that is tuning to my own design distribution; the max-entropy
mixture is the honest choice and the tier component earns its
keep on G5.

### Gate arithmetic (recorded honestly)

Practice-like 0.3778 x 5 = 1.89 of the 1.90 total budget for mean
<= 0.10 — the hard gate's mean criterion is arithmetically
unreachable on this split even with a near-perfect learned branch
(realistic floor ~0.115). The mean criterion is dominated by
practice-like, which pays nothing in the real competition: the
final grade is ONE learned-branch case (f00, 6,510-min horizon,
many refreshes observed). On the decision-relevant final-like
subset v3 beats the v2-kernel baseline by 54% (0.0226 vs 0.0494),
and on the real-final-like G17 they tie (0.0069). The gate
verdict is recorded in the Verdict section below; the numbers
above are what the coordinator/parent decide from.

## VALIDATION (on the FINAL code, candidate 11)

All checks run on the exact files committed (main.py 959 lines,
39,042 bytes; SHA recorded at push time below).

- **Format (p00 + p01, kit inputs):** `{"trophies": [55 rows]}`,
  ids 1–55, 5 quantiles each, non-decreasing, in (0, 100];
  outputs 2,800 / 2,798 bytes (limit 65,536). PASS.
- **Smoke (hypothesised uniform-0.221x answer — NOT the truth):**
  p00 0.2019, p01 0.1315 (v2 recorded 0.2489 / 0.1909 on the same
  hypothesis). Sanity only; the hypothesis is not the answer.
- **Determinism:** 2 runs byte-identical (`diff -r` clean). PASS.
- **Runtime:** 0.32 s for both practice cases (~0.16 s/case;
  limit 8 s/case; fresh suite 19 cases in 5.6 s). PASS.
- **Stdlib only:** imports are `json`, `math`, `os`, `datetime`
  only (grep-verified). PASS.
- **Clean vanilla-Python run:** fresh venv (Python 3.12.3, only
  pip installed), output byte-identical to the system run. PASS.
- **Edge battery (8/8 PASS):** empty history, single read,
  all-null rates, horizon 0, horizon 100,000, all-zero rates,
  missing `at`/horizon, empty case (0 rows) — all run without
  raising and produce valid 55-row outputs.
- **Fresh split (final numbers):** mean 0.1188, practice-like
  0.3778, final-like 0.0226, worst 0.8625 (G2), mean cov90 0.99.
- **Secrets grep:** no API keys, tokens, passwords, or wallet
  private material in any committed file (the owner.json wallet
  address is the public 6do8 address, required by the format).

## MQ1 — Can this entry be submitted RIGHT NOW, end to end?

PASS (mechanics). Repo created via the PAT route, one public
snapshot commit on `main` (SHA below), About + topics set and
verified live, fresh-clone verification passed (sha256 match +
cloned main.py runs p00/p01). The coordinator bundles and submits;
the builder's part is complete. Whether to submit is the Verdict
section's call (hard-gate outcome), not a mechanics question.

## MQ2 — Does this entry clear the competition's bar?

MIXED — see the Verdict. On the fresh held-out split (seed
20261121, 19 scenarios) v3 scores mean 0.1188 vs the v2-kernel
baseline's 0.1325 on the SAME split: it beats v2, but NOT by the
hard gate's required margin (mean <= 0.10) and NOT by a wide
margin on the mean. On the decision-relevant final-like subset
(the real final is one learned-branch case) v3 beats the baseline
by 54% (0.0226 vs 0.0494). The dev-board top-20 cutoff (0.0328)
is a memorization artifact and was never the selection bar; the
fresh split is.

## MQ3 — Is the submission window actually open for this account?

PASS at build time (20 Nov ~08:25 WITA, live API check):
can_submit true, 2 entries made, day cap 3/3 left, hard limit 18
left. Entries close 2026-11-21T11:30:00Z (21 Nov 19:30 WITA).
Coordinator re-checks quota at bundle time.

## MQ4 — Signed by the right identity, through the right route?

PASS. Account @riery, wallet 6do8 ONLY
(6do8zGw4FPLCB1Cq44G8r8KwQccbhHUqtAptaRji6ALk) in
`.makefun/owner.json`. Repo under RieryBuild (PAT-verified login
RieryBuild, id 29680483). No other wallet anywhere in the entry.

## MQ5 — Deliberate new submission, not a duplicate?

PASS. Deliberate REBUILD (v3) of the standing v2 entry
("Honest Kernel", submission 01a1f57c-8c3c-72fc-bb17-404710735831,
dev rank #1,717/5,147, loss 0.2528), intended as a Force_Last
supersede IF the gate passes. The v3 model is a different family
(structural count-consistent mixture) from v2's kernel, built
fresh in-session; no v1/v2 file was copied, imported, or run.
The §0 brief + top-25 study preceded all build writes.

## MQ6 — Prove the entry works, beyond "it should work"?

PASS. See VALIDATION above: format, determinism, runtime,
stdlib-only, vanilla-venv byte-identical run, 8/8 edge battery,
fresh-split numbers vs a re-implemented baseline on the same
split, and a fresh-clone run of the committed code.

## MQ7 — Never-submit list?

PASS. Not on the never-submit list. No secrets, no copied code,
no practice-answer tuning (the hypothesised uniform-0.221x
answer was used only as a smoke sanity check, never as a
training target), no dev-board chasing.

## MQ8 — Session check

Builder session: this subagent session (depth 2/2, label
acf687ae-ffc3-472a-b7c7-ba65e29f8d67) + the parent coordinator
session. The coordinator completes the full session list at
bundle time (top-level + all subagents that touched the entry)
and runs the kit's bundle + check. No session was written,
rebuilt, or summarised from memory.

## Gate 0 — Reality

PASS. The entry is a real program that runs on the kit's inputs
and produces valid outputs; every number in this file was
measured by running code (suite, smoke, edge battery, clone
verify), not asserted. The fresh-split comparison uses a
re-implemented v2-kernel baseline whose fidelity was verified
exactly (smoke 0.2489/0.1909 = v2's recorded numbers).

## Gate 1 — Quality

PASS with documented findings (all material findings addressed
in-session; see below). Two independent reviews:

**Code/reasoning — OpenRouter, nvidia/nemotron-3-ultra-550b-a55b:free**
(free list re-checked via GET /models on 20 Nov; 13 :free models
available). Two review calls, core functions only:

- *Review A* (docstring + constants + timing/count weights +
  growth_trend/growth_jitter): verdict FAIL, 1 CRITICAL + 1 MAJOR
  + 2 MINOR.
  - CRITICAL (decay formula): diagnosis CORRECT (the
    log(1+g)-space slope attenuates ln(decay) by 1/(1+g_bar)),
    but the reviewer's proposed fix (ln_decay = slope) is WRONG
    — worse attenuation (x g_bar/(1+g_bar)), because the fitted
    variable is log(1+g), not log(g). Correct fix applied in c9
    (slope x (1+g_bar)/g_bar) — REGRESSED the split (mean 0.1229;
    G14 0.1125 -> 0.1905) by exposing a level bias. Deeper fix
    tried in c10 (fit in log(g) space, where decay is exactly
    linear) — REGRESSED further (mean 0.1276; G14 0.2798): the
    unbiased estimator's slope noise (~2.8x) compounds through
    level + decay. Both reverted on measured evidence; c7's
    attenuated estimator is the better bias-variance tradeoff on
    noisy histories. Recorded, not hidden.
  - MAJOR (negative period-age residual): diagnosis CORRECT, but
    the reviewer's modulo fix is WRONG for this semantics (it
    assumes unobserved refreshes happened on schedule,
    contradicting the flat history). Correct fix applied:
    survival conditioning (periods <= age ruled out, conditional
    p0, overdue fallback). Kept in c11 (neutral on this split,
    correct for real cases where age is a large fraction of the
    period).
  - MINOR (clamp/phi "not defined"): NOT a finding — both are
    defined in main.py (lines 101/152); they were outside the
    review payload's sections.
  - MINOR (linear-symmetric jitter): valid; switched to
    log-symmetric jitters exp(k x 0.04). Kept in c11.
- *Review B* (build_curves + forecast_case mixture loop): verdict
  FAIL, 1 CRITICAL + 1 MAJOR + 2 MINOR.
  - CRITICAL (roll multiplies f by r_cur/100): WRONG — the
    reviewer misread f's definition. f is RELATIVE to the
    incumbent rate (brief: newcomers earned 0.067x the
    incumbents' rate; analyse_history computes
    f = (e_cur - e_prev) / (d_n x r_prev/100)). The brief-totals
    check confirms it: sum of f x r/100 over non-universal
    trophies = 0.067 x 0.48 = 0.032 = 103 non-platinum trophies /
    3,230 newcomers. The roll is correct. DISMISSED with proof.
  - MAJOR (total_w <= 0 fallback silently yields ~99.75%
    quantiles): CORRECT (unreachable in practice — count weights
    sum to 1 — but silently wrong if ever hit). FIXED: the
    fallback now appends the last rate with a wide sigma for
    every trophy. Kept in c11.
  - MINOR (tier-factor clamp shifts the mean): acknowledged but
    IMMATERIAL — the count-consistency reconciliation rescales
    the total regardless of the tier-factor mean. Not changed.
  - MINOR (sat_fit tuple ordering confusing): valid; clarified
    with named unpacking. Kept in c11.
- After all fixes, the fresh split was re-validated on the final
  code (c11: mean 0.1188).

**Text/copy — Gemini gemini-3.8-flash** (gemini-2.5-flash
returned 404 "no longer available"; first 3.8-flash call
returned 503 "high demand", retry after 45 s succeeded):
verdict PASS, 1 finding (awkward phrasing "never a commit to one
shape" in the README) — FIXED ("the forecast never commits to a
single shape").

## Gate 2 — Dedup

PASS. This is the only v3 build of this entry. It supersedes v2
by design (Force_Last) if submitted; it does not duplicate any
other live entry. No other v3 repo exists under RieryBuild.

## Gate 3 — Submission quality (checks minus submit; coordinator submits)

- README: 3 live make.fun badges + bounty link + run
  instructions + referral footer (`?ref=wa8s3t3t`). PASS.
- About: description + homepage
  (https://make.fun/bounty/gta6-trophy-rarity-forecast-01) +
  topics [makefun, ai-agents, bounties, forecasting], verified
  live via the API after setting. PASS.
- No secrets in the repo (grep). PASS.
- Deadline ahead: entries close 2026-11-21T11:30:00Z; this gate
  ran 20 Nov. PASS.
- Claim-code handling: N/A (no claim code in this competition).
- Visual audit: N/A (pure code entry, no screenshots).
- Bundle/submit: COORDINATOR's step, not the builder's. The
  builder STOPs here.

## Verdict

**HARD GATE: FAIL — do NOT submit on the gate as written.**

The gate required (a) mean loss <= 0.10 AND (b) clearly below
the v2 baseline on the same fresh split. v3 (c11) scores mean
**0.1188** vs the v2-kernel baseline's **0.1325**: it beats v2
by 10.3% on the mean — real, but neither <= 0.10 nor a wide
margin. The mean criterion is arithmetically unreachable on this
split: practice-like cases (which pay nothing in the real
competition) sit at an information-limited floor of ~0.3778,
contributing 1.89 of the 1.90 total budget for mean <= 0.10,
even with a near-perfect learned branch (realistic floor
~0.115).

What v3 DID achieve: on the decision-relevant final-like subset
(the real final is one learned-branch case, 6,510-min horizon,
many refreshes observed) v3 beats the baseline by 54% (0.0226
vs 0.0494), with G14 (decay + noise) improving 0.3052 -> 0.1125
and G8 0.1612 -> 0.0677; on the real-final-like G17 they tie
(0.0069). The smoke check also improved (p00 0.2019 vs v2's
0.2489; p01 0.1315 vs 0.1909, same hypothesised answer).

Per the task instruction ("Kalau tidak mencapai itu: STOP,
laporkan angka-angkanya, JANGAN submit — v2 tetap berdiri"), the
builder's recommendation is: **v2 stands; do not submit v3.**
The repo + commit below exist as a complete, verified entry
should the coordinator/parent override the gate with full
knowledge of these numbers (e.g. judging the final-like margin
decisive). That override is theirs to make, not the builder's.

- Repo: https://github.com/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v3
- Commit: the repo's HEAD commit on `main` (one public snapshot
  commit; the SHA is reported to the coordinator with this
  gate-run and read live from the repo at bundle time).
