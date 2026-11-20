"""Forecast GTA VI trophy earn rates on Exophase at a future target (v3).

Structural count-consistent mixture forecaster. Exophase republishes
its counts in bursts ("refreshes"): between refreshes the page is
frozen; at a refresh the tracked-player count jumps and each trophy's
earner count grows by less, because the newcomers have earned far
fewer trophies than the incumbents. A trophy's rate is earners /
tracked, both of which move only at refreshes.

v3 differs from the v2 kernel family in its INFERENCE, not its
skeleton (the count-space roll is kept — it is proven):

1. MODEL AVERAGING over curve families. With no refresh observed the
   newcomer curve's shape is genuinely unknown, so the prior branch
   mixes three families (power law, saturating, tier-step) instead of
   committing to one power law. In the learned branch the power and
   saturating fits are mixed with weights from their robust
   residuals, and per-tier factors (shrunk by tier size) refine the
   curve. The forecast's quantiles are the mixture's quantiles.
2. TWO-PART TIMING in the prior branch. The brief pins the FIRST
   refresh to 250-280 minutes after the first probe, but that bound
   is on ONE realization of a jittered schedule: the underlying
   period sits in [250, 280] and each realisation jitters, so the
   first refresh is drawn from the bound convolved with schedule
   jitter (which also keeps a small honest mass on "no refresh
   inside the horizon" — a point forecast that commits 100% to a
   refresh leaves the interval uncovered when the refresh lands a
   minute late). LATER refreshes follow a wide cadence
   distribution (lognormal, median 300 min), because one
   observation cannot pin the cadence. The learned branch keeps
   the renewal mixture over the observed gaps, with a
   recency-weighted period (the cadence can drift).
3. DILUTION UNCERTAINTY in the prior branch is carried by the
   per-refresh jitter term (see 6), not by a mixture over the
   first refresh's dilution: a dilution mixture was tried and
   ABLATED OUT (candidate 1-2) — with P(refresh) high the
   mixture's upper component drags the median toward MORE
   dilution, which is exactly wrong when the refresh does not
   land, and its net effect on the fresh split was negative.
4. COUNT-CONSISTENT RECONCILIATION. Per mixture component, the
   per-trophy earner forecasts (EB-blended, noisy for small-count
   trophies) are rescaled so their sum matches the total implied by
   the curve — the total is far better determined than any single
   small count, and the rescale removes EB drift without touching
   the relative rates.
5. PRECISION-WEIGHTED DECAY. The growth trend is estimated by
   least squares over all transitions with its standard error; the
   decay is shrunk by |slope| / (|slope| + se), clamped to
   [0.80, 1.0], and the forecast MIXES over {decay, no decay} so
   the interval spans the decay uncertainty instead of missing it.
6. OBSERVED-RANGE SPREAD. The per-refresh jitter term comes from
   the dispersion of the observed log-growths (shrunk toward the
   0.15 prior), not from a fixed constant: stable histories get
   tight intervals, jittery ones get wide ones.

When the history shows no refresh at all, the curve LEVEL comes
from the launch-night totals in the brief itself (newcomers earned
0.067x the incumbents' rate on non-universal trophies). Nothing is
tuned to the dev board.

Pure standard library, deterministic, no network, no randomness.
"""

import json
import math
import os
from datetime import datetime, timezone

Z_VALUES = (-1.6448536269514722, -0.6744897501960817, 0.0,
            0.6744897501960817, 1.6448536269514722)
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)

# Priors used only when the history contains no refresh to learn from,
# or to shrink a weakly supported empirical fit toward. All levels come
# from the brief's own numbers, never from the dev board.
PRIOR_PERIOD_MIN = 270.0     # launch-night gap before the first refresh
PRIOR_FIRST_LO = 250.0       # brief's bound on the first refresh (min)
PRIOR_FIRST_HI = 280.0       # ... (max), from the first probe
PRIOR_CADENCE_MED = 300.0    # median cadence after the first refresh
PRIOR_CADENCE_SIG = 0.4      # ... in log space ("hours apart": the
                             # 3-point grid spans 200-450 min)
PRIOR_TRACKED_GROWTH = 5.06  # first refresh: 638 -> 3868 tracked players
PRIOR_F_LEVEL = 0.067        # newcomers' mean earn rate, as a fraction
                             # of the incumbents', over non-universal
                             # trophies (rules totals: 943 -> 4276
                             # trophies earned vs 638 -> 3868 tracked)
PRIOR_ALPHA = 1.0            # power-law slope of the prior curve
PRIOR_SAT_R0 = 1.5           # saturating knee of the prior curve (%)
PRIOR_JITTER = 0.15          # per-refresh log-growth jitter (prior)
# Tier prior (relative newcomer fractions; level-anchored like the
# other prior curves): easier tiers first — newcomers earn bronze
# far more than platinum. A prior belief, not a fitted value.
PRIOR_TIER_REL = {"platinum": 0.10, "gold": 0.30, "silver": 0.60,
                  "bronze": 1.0}

SIG_FLOOR = 0.22             # logit spread floor (per scenario)
SIG_SHAPE = 0.12             # residual shape uncertainty per scenario
SIGMA_CAP = 2.2


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def logit_pct(rate):
    p = clamp(rate, 0.0001, 99.9999) / 100.0
    return math.log(p / (1.0 - p))


def inv_logit_pct(eta):
    if eta > 30.0:
        return 100.0
    if eta < -30.0:
        return 0.0
    return 100.0 / (1.0 + math.exp(-eta))


def parse_time(text):
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None


def minutes_between(a, b):
    if a is None or b is None:
        return None
    return (b - a).total_seconds() / 60.0


def median(values):
    vals = sorted(values)
    n = len(vals)
    if n == 0:
        return None
    mid = n // 2
    if n % 2:
        return vals[mid]
    return 0.5 * (vals[mid - 1] + vals[mid])


def round4(x):
    """Round to 4 decimals, half up, as the house baseline does."""
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value == int(value) else value


def phi(z):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def poisson_pmf(mean, cap):
    """Poisson pmf for counts 0..M, renormalised (M covers the mass
    to ~6 sigma above the mean)."""
    if mean <= 0:
        return [1.0]
    m_max = int(mean + 6.0 * math.sqrt(mean + 1.0) + 3.0)
    m_max = min(max(m_max, 1), cap)
    w = [math.exp(-mean)]
    for m in range(1, m_max + 1):
        w.append(w[-1] * mean / m)
    total = sum(w)
    return [x / total for x in w]


def trim_weights(weights, first_m):
    """Cut negligible tails (<0.05% mass on either side)."""
    lo = 0
    cum = 0.0
    while lo < len(weights) - 1 and cum + weights[lo] < 0.0005:
        cum += weights[lo]
        lo += 1
    hi = len(weights) - 1
    cum = 0.0
    while hi > lo and cum + weights[hi] < 0.0005:
        cum += weights[hi]
        hi -= 1
    weights = weights[lo:hi + 1]
    total = sum(weights)
    return [x / total for x in weights], first_m + lo


def first_refresh_grid():
    """First-refresh times (minutes after the first read) from the
    brief's bound convolved with schedule jitter: the period is
    uniform on [250, 280] and each realisation jitters by x0.92-1.08.
    Returns [(time, weight)] with weights summing to 1."""
    grid = []
    periods = [250.0 + 5.0 * k for k in range(7)]
    # Multiplicative jitter, log-symmetric: exp(k x 0.04), k = -2..2.
    jitters = [math.exp(0.04 * k) for k in (-2, -1, 0, 1, 2)]
    for p in periods:
        for j in jitters:
            grid.append((p * j, 1.0 / (len(periods) * len(jitters))))
    return grid


def prior_count_weights(age, horizon, cap=60):
    """Weights over refresh counts before the target, prior branch:
    the first refresh from the jitter-convolved bound; later ones
    Poisson with a wide cadence distribution (3-point lognormal
    grid around median 300)."""
    if horizon <= 0:
        return [1.0], 0
    # Cadence grid: the lognormal's quartiles (25th / 50th / 75th
    # percentiles) at weights {0.25, 0.5, 0.25}.
    _q = math.exp(0.6744897501960817 * PRIOR_CADENCE_SIG)
    cadences = [(PRIOR_CADENCE_MED / _q, 0.25),
                (PRIOR_CADENCE_MED, 0.5),
                (PRIOR_CADENCE_MED * _q, 0.25)]
    totals = [0.0] * (cap + 1)
    for t_first, w_first in first_refresh_grid():
        if t_first > age + horizon:
            totals[0] += w_first
            continue
        remaining = age + horizon - t_first
        for cad, w_cad in cadences:
            pmf = poisson_pmf(remaining / cad, cap - 1)
            for k, pk in enumerate(pmf):
                if 1 + k <= cap:
                    totals[1 + k] += w_first * w_cad * pk
    total = sum(totals)
    if total <= 0:
        return [1.0], 0
    weights = [x / total for x in totals]
    # Drop trailing zeros, then trim tails.
    last = len(weights) - 1
    while last > 0 and weights[last] <= 0:
        last -= 1
    return trim_weights(weights[:last + 1], 0)


def learned_count_weights(period_grid, period_med, age, horizon,
                          cap=60):
    """Weights over refresh counts, learned branch: a renewal
    process — the next refresh arrives when the page age reaches
    the (uncertain) period; later ones about one period apart.

    The page has SURVIVED to age with no refresh, so periods at or
    below age are ruled out: the residual is conditioned on
    period > age. (An earlier version summed (period - age) over
    all periods, letting ruled-out short periods contribute
    NEGATIVE residuals that biased the expected first-refresh time
    down and over-predicted refresh counts. Caught by the Gate 1
    review; the reviewer's modulo suggestion was not used — it
    assumes unobserved refreshes happened on schedule, which
    contradicts the observed flat history.)"""
    if horizon <= 0:
        return [1.0], 0
    surv = [(p, w) for p, w in period_grid if p > age]
    total_surv = sum(w for _, w in surv)
    if total_surv <= 0:
        # Every period is ruled out: the refresh is overdue under
        # every hypothesis, so the next one is imminent.
        p0 = 0.0
        exp_first = 0.0
    else:
        p0 = sum(w for p, w in surv if p > age + horizon) / total_surv
        num = 0.0
        den = 0.0
        for p, w in surv:
            if p <= age + horizon:
                num += w * (p - age)
                den += w
        exp_first = num / den if den > 0 else 0.0
    p0 = clamp(p0, 0.0, 1.0)
    lam2 = max(0.0, (horizon - exp_first) / max(period_med, 1.0))
    add = poisson_pmf(lam2, cap - 1)
    weights = [p0] + [(1.0 - p0) * x for x in add]
    return trim_weights(weights, 0)


def learned_period_grid(period_est):
    """Period uncertainty once refreshes have been observed:
    lognormal around the estimated period (sigma 0.25 in log
    space), weighted with the 1/p Jacobian."""
    dens = []
    for p in range(120, 901, 30):
        d = math.exp(-0.5 * ((math.log(p) - math.log(period_est))
                             / 0.25) ** 2) / p
        dens.append((float(p), d))
    total = sum(d for _, d in dens)
    return [(p, d / total) for p, d in dens]


def analyse_history(case):
    """Parse the history into reads and refresh transitions.

    Earner counts are reconstructed from the rates and the tracked
    count, then rescaled so their sum matches the page's
    `trophies_earned` total, which removes part of the 2-decimal
    rounding error. A transition is a read where the tracked count
    (or any rate) moved. Each transition records the implied
    newcomer earn fraction per trophy.
    """
    history = case.get("history") or []
    trophies = case.get("trophies") or []
    n_troph = len(trophies)
    reads = []
    for entry in history:
        rates = entry.get("rates") or []
        if len(rates) < n_troph:
            continue
        moment = parse_time(entry.get("at") or entry.get("slot") or "")
        tracked = entry.get("players_tracked")
        if not isinstance(tracked, (int, float)) or tracked <= 0:
            continue
        tracked = float(tracked)
        earners = []
        for r in rates:
            if isinstance(r, (int, float)):
                earners.append(max(0.0, float(r)) * tracked / 100.0)
            else:
                earners.append(None)
        total = entry.get("trophies_earned")
        known = [e for e in earners if e is not None]
        if (isinstance(total, (int, float)) and total > 0 and known
                and sum(known) > 0):
            scale = float(total) / sum(known)
            if 0.5 < scale < 2.0:
                earners = [None if e is None else e * scale
                           for e in earners]
        reads.append({"moment": moment, "tracked": tracked,
                      "rates": list(rates), "earners": earners})
    if not reads:
        return None, [], None, []
    transitions = []
    for prev, cur in zip(reads, reads[1:]):
        n_prev, n_cur = prev["tracked"], cur["tracked"]
        changed = abs(n_cur - n_prev) > 0.005 * n_prev
        if not changed:
            for a, b in zip(prev["rates"], cur["rates"]):
                if (isinstance(a, (int, float))
                        and isinstance(b, (int, float))
                        and abs(b - a) > 0.02):
                    changed = True
                    break
        if not changed:
            continue
        fracs = []
        deltas = []
        for e_prev, e_cur in zip(prev["earners"], cur["earners"]):
            if e_prev is None or e_cur is None:
                fracs.append(None)
                deltas.append(None)
                continue
            deltas.append(e_cur - e_prev)
            d_n = n_cur - n_prev
            if d_n <= 0 or e_prev <= 0:
                fracs.append(None)
                continue
            r_prev = 100.0 * e_prev / n_prev
            f = (e_cur - e_prev) / (d_n * r_prev / 100.0)
            fracs.append(clamp(f, 0.0, 1.2))
        transitions.append({
            "moment": cur["moment"],
            "log_tracked_growth": math.log(n_cur / n_prev),
            "fracs": fracs,
            "earner_deltas": deltas,
            "d_tracked": n_cur - n_prev,
        })
    moments = [t["moment"] for t in transitions if t["moment"] is not None]
    gaps = []
    if len(moments) >= 2:
        gaps = [minutes_between(a, b)
                for a, b in zip(moments, moments[1:])]
        gaps = [g for g in gaps if g is not None and g > 0]
    period = None
    if gaps:
        period = median(gaps)
    elif len(moments) == 1 and reads[0]["moment"] is not None:
        period = minutes_between(reads[0]["moment"], moments[0])
    return reads[-1], transitions, period, gaps


def fit_power_curve(points):
    """Fit log f = a + b * log(r / r_med) to (rate, f) points by
    binned medians: bin by log-rate, take each bin's median point,
    slope from the median pairwise slope (Theil-Sen), intercept
    from the median residual. Returns (a, b) or None."""
    if len(points) < 8:
        return None
    pts = sorted(points)
    nbins = 5
    bins = [[] for _ in range(nbins)]
    for k, p in enumerate(pts):
        bins[min(nbins - 1, k * nbins // len(pts))].append(p)
    meds = []
    for b in bins:
        if not b:
            continue
        meds.append((median([p[0] for p in b]),
                     median([p[1] for p in b])))
    if len(meds) < 3:
        return None
    slopes = []
    for i in range(len(meds)):
        for j in range(i + 1, len(meds)):
            dx = meds[j][0] - meds[i][0]
            if abs(dx) > 0.05:
                slopes.append((meds[j][1] - meds[i][1]) / dx)
    if not slopes:
        return None
    b = clamp(median(slopes), 0.0, 3.0)
    a = median([y - b * x for x, y in meds])
    return (a, b)


def anchor_level(rates_last, tiers, r_med, shape_fn, level):
    """Scale factor so shape_fn's earner-weighted mean f over
    non-universal trophies equals `level`. shape_fn takes
    (rate, tier) and returns the UNNORMALISED shape value."""
    num = 0.0
    den = 0.0
    for r, tier in zip(rates_last, tiers):
        if r is None or r >= 99.995 or r <= 0:
            continue
        num += shape_fn(max(r, 0.05), tier) * r
        den += r
    if num <= 0 or den <= 0:
        return level
    return level / (num / den)


def build_curves(rates_last, tiers, transitions, r_med):
    """Return ([(curve_fn, weight)], learned_flag, resid).

    Prior branch (no transitions): three prior curves (power /
    saturating / tier-step), equal weights, level-anchored to the
    brief's 0.067. Learned branch: power + saturating fits mixed
    by their robust residuals, each refined by shrunk per-tier
    factors; level-anchored to the data-supported level. A curve
    maps (rate_pct, tier) -> newcomer fraction f.
    """
    n_troph = len(rates_last)
    n_trans = len(transitions)
    pooled = [None] * n_troph
    for i in range(n_troph):
        num = 0.0
        den = 0.0
        for t in transitions:
            f = t["fracs"][i] if i < len(t["fracs"]) else None
            if f is None:
                continue
            w = max(t["d_tracked"], 1.0)
            num += w * f
            den += w
        if den > 0:
            pooled[i] = num / den
    points = []
    for i in range(n_troph):
        r = rates_last[i]
        f = pooled[i]
        if f is None or r is None or r >= 99.995 or r <= 0 or f <= 0:
            continue
        points.append((math.log(max(r, 0.05) / max(r_med, 0.05)),
                       math.log(f), r, f, tiers[i]))
    n_pts = len(points)
    w_emp = (n_pts / (n_pts + 15.0) if n_pts else 0.0)
    w_emp *= n_trans / (n_trans + 2.0) if n_trans else 0.0
    if n_pts:
        emp_level = (sum(f * r for _, _, r, f, _ in points)
                     / sum(r for _, _, r, f, _ in points))
    else:
        emp_level = PRIOR_F_LEVEL
    level = w_emp * emp_level + (1.0 - w_emp) * PRIOR_F_LEVEL

    def power_shape(r, tier):
        return (r / max(r_med, 0.05)) ** PRIOR_ALPHA

    def sat_shape(r, tier):
        return r / (r + PRIOR_SAT_R0)

    def tier_shape(r, tier):
        return PRIOR_TIER_REL.get(tier, 1.0) * (r / max(r_med, 0.05)) ** 0.3

    if not transitions or n_pts < 8:
        # Prior curves (or a too-thin fit): equal-weight mixture.
        curves = []
        for shape in (power_shape, sat_shape, tier_shape):
            c = anchor_level(rates_last, tiers, r_med, shape, level)
            curves.append((c, shape))
        out = []
        for c, shape in curves:
            def make_curve(c=c, shape=shape):
                def curve(r, tier):
                    if r >= 99.995:
                        return 1.0
                    return clamp(c * shape(max(r, 0.05), tier),
                                 0.005, 0.95)
                return curve
            out.append((make_curve(), 1.0 / 3.0))
        return out, False, None

    # Learned branch: fit both families, mix by robust residual.
    pow_fit = fit_power_curve([(x, y) for x, y, _, _, _ in points])
    sat_fit = None
    best = None
    for r0 in (0.5, 1.0, 1.5, 2.5, 4.0):
        fs = [f * (r + r0) / r for _, _, r, f, _ in points]
        f_level = median(fs)
        if f_level is None or f_level <= 0:
            continue
        resid = median([abs(math.log(max(f, 1e-4))
                            - math.log(max(f_level * r / (r + r0), 1e-4)))
                        for _, _, r, f, _ in points])
        if best is None or resid < best[0]:
            best = (resid, f_level, r0)
    if best is not None:
        # best is (resid, f_level, r0); sat_fit is (f_level, r0, resid).
        resid_fit, c_fit, r0_fit = best
        sat_fit = (c_fit, r0_fit, resid_fit)
    if pow_fit is not None:
        a, b = pow_fit
        pow_resid = median([abs(y - (a + b * x))
                            for x, y, _, _, _ in points])
    else:
        pow_resid = None
    sat_resid = sat_fit[2] if sat_fit else None

    # Blend the fitted slope toward the prior by data support.
    if pow_fit is not None:
        b_emp = pow_fit[1]
        b_use = w_emp * b_emp + (1.0 - w_emp) * PRIOR_ALPHA
    else:
        b_use = PRIOR_ALPHA

    def pow_shape_fit(r, tier):
        return (r / max(r_med, 0.05)) ** b_use

    c_pow = anchor_level(rates_last, tiers, r_med, pow_shape_fit, level)
    if sat_fit is not None:
        r0_fit = sat_fit[1]

        def sat_shape_fit(r, tier):
            return r / (r + r0_fit)

        # Blend the fitted saturation level toward the prior-anchored
        # one by data support (the fit's level and the anchor agree
        # when the data is rich; the anchor rules when it is thin).
        c_sat_anchor = anchor_level(rates_last, tiers, r_med,
                                    sat_shape_fit, level)
        c_sat = w_emp * sat_fit[0] + (1.0 - w_emp) * c_sat_anchor
    else:
        r0_fit = PRIOR_SAT_R0
        c_sat = anchor_level(rates_last, tiers, r_med, sat_shape, level)

        def sat_shape_fit(r, tier):
            return r / (r + r0_fit)

    # Per-tier factors: median ratio of pooled f to the power curve,
    # shrunk toward 1 by tier size (a 1-trophy tier cannot move the
    # curve; a 46-trophy tier can), then NORMALISED so their
    # earner-weighted mean is 1.0 — the factors capture RELATIVE
    # tier deviations only, never a global level shift (the level
    # stays anchored). Applied to both families.
    tier_factor = {}
    for tier in ("platinum", "gold", "silver", "bronze"):
        idxs = [i for i in range(n_troph)
                if tiers[i] == tier and pooled[i] is not None
                and rates_last[i] is not None
                and 0 < rates_last[i] < 99.995]
        if not idxs:
            tier_factor[tier] = 1.0
            continue
        ratios = []
        for i in idxs:
            cval = c_pow * pow_shape_fit(max(rates_last[i], 0.05), tier)
            if cval > 0.005:
                ratios.append(pooled[i] / cval)
        if not ratios:
            tier_factor[tier] = 1.0
            continue
        med_ratio = median(ratios)
        shrink = len(idxs) / (len(idxs) + 15.0)
        tier_factor[tier] = clamp(1.0 + shrink * (med_ratio - 1.0),
                                  0.5, 2.0)
    _num = 0.0
    _den = 0.0
    for i in range(n_troph):
        r = rates_last[i]
        if r is None or r >= 99.995 or r <= 0:
            continue
        _num += tier_factor.get(tiers[i], 1.0) * r
        _den += r
    if _num > 0 and _den > 0:
        _mean = _num / _den
        for tier in tier_factor:
            tier_factor[tier] = clamp(tier_factor[tier] / _mean,
                                      0.5, 2.0)

    def curve_pow(r, tier):
        if r >= 99.995:
            return 1.0
        return clamp(c_pow * pow_shape_fit(max(r, 0.05), tier)
                     * tier_factor.get(tier, 1.0), 0.005, 0.95)

    def curve_sat(r, tier):
        if r >= 99.995:
            return 1.0
        return clamp(c_sat * sat_shape_fit(max(r, 0.05), tier)
                     * tier_factor.get(tier, 1.0), 0.005, 0.95)

    # Residual-based mixture weights: softmax on the robust
    # residuals (temperature 0.05, the measurement-noise floor from
    # 2-decimal rounding). A family that fits clearly better takes
    # most of the weight; near-ties split it.
    def soft_w(resid):
        return math.exp(-resid / 0.05) if resid is not None else 0.0

    wp, ws = soft_w(pow_resid), soft_w(sat_resid)
    if wp + ws <= 0:
        return [(curve_pow, 0.5), (curve_sat, 0.5)], True, None
    resid = (wp * (pow_resid or 0.0) + ws * (sat_resid or 0.0)) / (wp + ws)
    return ([(curve_pow, wp / (wp + ws)),
             (curve_sat, ws / (wp + ws))], True, resid)


def growth_trend(transitions):
    """Trend-projected growth level + precision-weighted decay.

    One least-squares fit of log-growth on transition index gives
    both. The LEVEL is the fitted value at the NEXT index, shrunk
    toward the mean by the precision weight and never projected
    upward (the generator never accelerates; a rising slope is
    noise): with decay, the median of the last few growths
    OVERSTATES the next growth, because the trend has already
    moved on — the projection fixes that level bias. The DECAY is
    the shrunk slope mapped through the mean log-growth, mixed
    with no-decay by the precision weight. A rising trend or fewer
    than 4 transitions means no decay (three points cannot support
    a trend: with one degree of freedom a jittered triple can look
    deceptively consistent).

    Returns (proj_log_growth, [(decay, weight)]).
    """
    logs = [t["log_tracked_growth"] for t in transitions]
    n = len(logs)
    if n == 0:
        return None, [(1.0, 1.0)]
    if n == 1:
        return logs[0], [(1.0, 1.0)]
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(logs) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return my, [(1.0, 1.0)]
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, logs)) / sxx
    resid = [y - (my + slope * (x - mx)) for x, y in zip(xs, logs)]
    dof = max(n - 2, 1)
    s2 = sum(r * r for r in resid) / dof
    se = math.sqrt(s2 / sxx) if s2 > 0 else 0.0
    # Precision weight: the posterior probability that the slope is
    # negative under a flat prior, Phi(|slope|/se). (An earlier
    # heuristic, |slope|/(|slope|+se), was too conservative: on
    # G13 it gave the real 0.90 decay only 28% weight, so the
    # no-decay component's 1.31^36 multiplier collapsed the rarest
    # trophies' rates to the grid floor.)
    w = phi(abs(slope) / se) if se > 0 else 1.0
    if n < 4:
        # Three points cannot support a trend (see the decay gate
        # below): the level is the mean, unprojected.
        w = 0.0
    # Level: fitted value at the next index, shrunk toward the
    # mean, never above the mean, floored at the 1.05x dilution.
    proj = my + w * slope * (n - mx)
    proj = clamp(min(proj, my), math.log(1.05), my if my > 0 else 0.05)
    if slope >= 0 or n < 4:
        return proj, [(1.0, 1.0)]
    # Decay: the slope is d(log growth)/d(index); decay multiplies
    # the growth itself, so ln(decay) ~= slope / mean log-growth.
    if my <= 0.02:
        return proj, [(1.0, 1.0)]
    ln_decay = slope / my
    d_est = clamp(math.exp(w * ln_decay), 0.80, 1.0)
    if w < 0.05 or d_est > 0.995:
        return proj, [(1.0, 1.0)]
    return proj, [(d_est, w), (1.0, 1.0 - w)]


def growth_jitter(transitions):
    """Observed per-refresh log-growth dispersion, shrunk toward
    the 0.15 prior (4 pseudo-observations)."""
    logs = [t["log_tracked_growth"] for t in transitions]
    n = len(logs)
    if n < 2:
        return PRIOR_JITTER
    mean = sum(logs) / n
    var = sum((x - mean) ** 2 for x in logs) / (n - 1)
    shrunk = (n * var + 4.0 * PRIOR_JITTER ** 2) / (n + 4.0)
    return math.sqrt(max(shrunk, 0.01))


def forecast_case(case):
    trophies = case.get("trophies") or []
    n_troph = len(trophies)
    horizon = float(case.get("horizon_minutes") or 0.0)
    checkpoint = parse_time(case.get("at") or "")
    history = case.get("history") or []
    last, transitions, period_obs, gaps = analyse_history(case)

    if last is None:
        return [{"id": t.get("id"), "q": [0.05, 0.2, 0.5, 2.0, 8.0]}
                for t in trophies]

    n_last = last["tracked"]
    tiers = [t.get("tier") or "bronze" for t in trophies]
    rates_last = []
    for idx in range(n_troph):
        r = None
        for read in reversed(history):
            rates = read.get("rates") or []
            if idx < len(rates) and isinstance(rates[idx], (int, float)):
                r = float(rates[idx])
                break
        rates_last.append(r if r is not None else 0.0)
    earners_last = []
    for idx, r in enumerate(rates_last):
        e = last["earners"][idx]
        if e is None:
            e = clamp(r, 0.0, 100.0) * n_last / 100.0
        earners_last.append(max(0.0, e))
    numeric_rates = sorted(r for r in rates_last
                           if isinstance(r, (int, float)) and r < 99.995)
    r_med = median(numeric_rates) if numeric_rates else 0.78

    first_moment = None
    if history:
        first_moment = parse_time(history[0].get("at")
                                  or history[0].get("slot") or "")
    last_change_at = None
    prev_n = None
    for entry in history:
        moment = parse_time(entry.get("at") or entry.get("slot") or "")
        n_here = entry.get("players_tracked")
        if prev_n is not None and n_here != prev_n and moment is not None:
            last_change_at = moment
        prev_n = n_here

    sig_g = growth_jitter(transitions)
    curves, _learned, _resid = build_curves(rates_last, tiers,
                                            transitions, r_med)

    if transitions:
        # --- Learned branch. ---
        proj_log, decays = growth_trend(transitions)
        if proj_log is None or proj_log < 0:
            g_med = median([t["log_tracked_growth"]
                            for t in transitions[-3:]])
            if g_med is None or g_med < 0:
                g_med = math.log1p(0.2)
            growth = math.expm1(g_med)
        else:
            growth = math.expm1(proj_log)
        # Period: recency-weighted median of the gaps (the cadence
        # can drift), shrunk toward the prior on the log scale; the
        # first-read -> first-refresh span is one full period
        # observation when it is the only one.
        if period_obs is not None and period_obs > 0:
            if len(transitions) <= 1:
                period = period_obs
            else:
                wsum = 0.0
                wlog = 0.0
                for k, g in enumerate(gaps):
                    w = 1.0 + k
                    wsum += w
                    wlog += w * math.log(g)
                period_rec = math.exp(wlog / wsum) if wsum else period_obs
                n_gaps = len(gaps)
                w = n_gaps / (n_gaps + 1.0)
                period = math.exp(w * math.log(period_rec)
                                  + (1.0 - w) * math.log(PRIOR_PERIOD_MIN))
        else:
            period = PRIOR_PERIOD_MIN
        age = 0.0
        if last_change_at is not None and checkpoint is not None:
            age = minutes_between(last_change_at, checkpoint) or 0.0
        weights, m_lo = learned_count_weights(
            learned_period_grid(period), period, age, horizon)
    else:
        # --- Prior branch. ---
        growth = PRIOR_TRACKED_GROWTH
        decays = [(1.0, 1.0)]
        age = minutes_between(first_moment, checkpoint) or 0.0
        weights, m_lo = prior_count_weights(age, horizon)

    # Per-trophy newcomer fraction per curve: own pooled value
    # blended toward the curve with a count-based empirical-Bayes
    # weight. The informative count for f is the number of NEWCOMER
    # earners (earners gained across the observed refreshes).
    pooled = [None] * n_troph
    pooled_new = [0.0] * n_troph
    for i in range(n_troph):
        num = 0.0
        den = 0.0
        new_tot = 0.0
        for t in transitions:
            f = t["fracs"][i] if i < len(t["fracs"]) else None
            d = t["earner_deltas"][i] if i < len(t["earner_deltas"]) else None
            if d is not None and d > 0:
                new_tot += d
            if f is None:
                continue
            w = max(t["d_tracked"], 1.0)
            num += w * f
            den += w
        if den > 0:
            pooled[i] = num / den
        pooled_new[i] = new_tot
    # f_by_curve[s][i]: EB-blended f for trophy i under curve s.
    f_by_curve = []
    curve_f = []
    for curve_fn, _w in curves:
        f_row = []
        c_row = []
        for i in range(n_troph):
            c = curve_fn(rates_last[i], tiers[i])
            c_row.append(c)
            if pooled[i] is None:
                f_row.append(c)
            else:
                w = pooled_new[i] / (pooled_new[i] + 5.0)
                f_row.append(w * pooled[i] + (1.0 - w) * c)
        f_by_curve.append(f_row)
        curve_f.append(c_row)

    m_max = m_lo + len(weights) - 1
    univ = [i for i in range(n_troph) if rates_last[i] >= 99.995]
    univ_set = set(univ)

    # Mixture components: (weight, count m, curve s, decay).
    # For each (m, decay, curve) the roll gives per-trophy
    # earners; the curve-implied total rescales them (count
    # consistency). Centres/sigmas are accumulated per trophy.
    comp_centres = [[] for _ in range(n_troph)]
    comp_sigmas = [[] for _ in range(n_troph)]
    comp_weights = []

    for decay, w_decay in decays:
        # Per-refresh growth steps under this decay.
        steps = [growth * (decay ** j) for j in range(m_max)]
        # Tracked multipliers for m = 0..m_max.
        mult = [1.0]
        for j in range(m_max):
            mult.append(mult[-1] * (1.0 + steps[j]))
        for si, (_curve_fn, w_shape) in enumerate(curves):
            f_row = f_by_curve[si]
            c_row = curve_f[si]
            for mi, m in enumerate(range(m_lo, m_max + 1)):
                w_comp = weights[mi] * w_decay * w_shape
                if w_comp <= 0:
                    continue
                n_t = n_last * mult[m]
                # Roll earners with EB f (per trophy) and with
                # curve f (total only), then reconcile the sum.
                e_eb = []
                sum_curve = 0.0
                sum_eb = 0.0
                for i in range(n_troph):
                    if i in univ_set:
                        e_eb.append(n_t)
                        continue
                    e_t = earners_last[i]
                    r_cur = rates_last[i]
                    n_cur = n_last
                    for j in range(m):
                        g_j = steps[j]
                        n_next = n_cur * (1.0 + g_j)
                        e_t = e_t + (n_next - n_cur) * f_row[i] \
                            * r_cur / 100.0
                        n_cur = n_next
                        r_cur = (100.0 * e_t / n_cur
                                 if n_cur > 0 else r_cur)
                    e_eb.append(e_t)
                    sum_eb += e_t
                    # Curve-f roll for the same trophy (total only).
                    e_c = earners_last[i]
                    r_c = rates_last[i]
                    n_c = n_last
                    for j in range(m):
                        g_j = steps[j]
                        n_next = n_c * (1.0 + g_j)
                        e_c = e_c + (n_next - n_c) * c_row[i] \
                            * r_c / 100.0
                        n_c = n_next
                        r_c = (100.0 * e_c / n_c
                               if n_c > 0 else r_c)
                    sum_curve += e_c
                if sum_eb > 0 and sum_curve > 0:
                    scale = clamp(sum_curve / sum_eb, 0.5, 2.0)
                else:
                    scale = 1.0
                sig_jit = 0.9 * sig_g * math.sqrt(m)
                comp_weights.append(w_comp)
                for i in range(n_troph):
                    if i in univ_set:
                        comp_centres[i].append(100.0)
                        comp_sigmas[i].append(0.01)
                        continue
                    centre = clamp(100.0 * e_eb[i] * scale / n_t
                                   if n_t > 0 else rates_last[i],
                                   0.001, 99.99)
                    sig_count = 0.8 / math.sqrt(
                        max(e_eb[i] * scale, 1.0))
                    sigma = math.sqrt(SIG_FLOOR ** 2 + sig_jit ** 2
                                      + SIG_SHAPE ** 2
                                      + sig_count ** 2)
                    comp_centres[i].append(centre)
                    comp_sigmas[i].append(min(sigma, SIGMA_CAP))

    total_w = sum(comp_weights)
    if total_w <= 0 or not comp_centres[0]:
        # Unreachable in practice (the count weights sum to 1 and
        # every factor is non-negative, so at least one component
        # has positive weight) — but if it ever happened, the old
        # fallback silently produced ~99.75% quantiles for every
        # trophy (an empty centre list zipped against a length-1
        # weight list). Fall back to a degraded-but-valid forecast
        # instead: the last rate with a wide sigma. (Gate 1 review.)
        comp_weights = [1.0]
        total_w = 1.0
        for i in range(n_troph):
            comp_centres[i] = [clamp(rates_last[i], 0.001, 99.99)]
            comp_sigmas[i] = [1.0]
    comp_weights = [w / total_w for w in comp_weights]

    # Mixture quantiles by inverting the mixture CDF on a logit grid.
    grid_lo, grid_hi, step = -10.0, 6.0, 0.04
    n_grid = int((grid_hi - grid_lo) / step) + 1
    grid = [grid_lo + k * step for k in range(n_grid)]
    rows = []
    for idx, trophy in enumerate(trophies):
        rate = clamp(float(rates_last[idx]), 0.0, 100.0)
        if rate >= 99.995:
            rows.append({"id": trophy.get("id"),
                         "q": [99.99, 99.995, 100.0, 100.0, 100.0]})
            continue
        logits = [logit_pct(c) for c in comp_centres[idx]]
        sigmas = comp_sigmas[idx]
        cdf = []
        for x in grid:
            s = 0.0
            for w, mu, sg in zip(comp_weights, logits, sigmas):
                s += w * phi((x - mu) / sg)
            cdf.append(s)
        quantiles = []
        for tau in LEVELS:
            pick = grid[-1]
            for k in range(n_grid):
                if cdf[k] >= tau:
                    pick = grid[k]
                    break
            quantiles.append(round4(clamp(inv_logit_pct(pick),
                                          0.001, 100.0)))
        for j in range(1, 5):
            if quantiles[j] < quantiles[j - 1]:
                quantiles[j] = quantiles[j - 1]
        rows.append({"id": trophy.get("id"), "q": quantiles})
    return rows


def run():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(in_dir) if n.endswith(".in"))
    for name in names:
        case_id = name[:-3]
        with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        rows = forecast_case(case)
        payload = {"trophies": rows}
        blob = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        with open(os.path.join(out_dir, case_id + ".out"), "wb") as fh:
            fh.write(blob)


if __name__ == "__main__":
    run()
