# makefun-gta6-trophy-rarity-forecast-01-v3

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v3/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v3/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

Structural count-consistent mixture forecaster for GTA VI trophy rarity in week one. It forecasts each trophy's earn rate at the horizon as five quantiles (0.05 / 0.25 / 0.5 / 0.75 / 0.95) on the logit scale, scored by pinball loss.

How it works, in brief:

- **Count space, not rate space.** Every forecast rolls trophy *earners* forward through refreshes, so the arithmetic stays honest when the tracked-player base multiplies.
- **Shape mixture.** The newcomer curve is a mixture over three families (power law, saturating, tier-step) in the no-refresh branch, and a residual-weighted power/saturating mix with per-tier factors once refreshes have been observed — the forecast never commits to a single shape.
- **Two-part timing.** The first refresh follows the brief's 250–280 minute bound convolved with schedule jitter; later refreshes follow a wide cadence distribution. Once refreshes are observed, a renewal mixture with a recency-weighted period takes over, conditioned on the page having survived to its current age.
- **Count-consistent reconciliation.** Per mixture component, the noisy per-trophy earner forecasts are rescaled so their sum matches the total implied by the newcomer curve.
- **Trend-projected growth + precision-weighted decay.** One least-squares fit of log growth gives both the next refresh's level (never projected upward) and a decay mixture weighted by the posterior probability that the trend is real.
- **Observed-range spread.** Interval width comes from the dispersion actually observed in the history, not a fixed constant.

Pure Python standard library only — no numpy, no pandas, no network. Deterministic: two runs produce byte-identical output.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=output python3 main.py
```

Each `*.in` file in the input directory is one case; each produces a `*.out` file with `{"trophies": [{"id": 1, "q": [q05, q25, q50, q75, q95]}, ...]}` for all 55 trophies.

---

<sub>Entered on [make.fun](https://make.fun/?ref=wa8s3t3t&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>
