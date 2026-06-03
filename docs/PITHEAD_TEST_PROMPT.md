# Sub-analysis prompt: does efficiency≈cost hold at pithead plants?

Paste the block below into a session on branch `claude/keen-newton-P0cFA` to run
the pithead sub-analysis. It is a **side analysis** — keep it separate from the
ECR-fetch work and don't break the pipeline. Background: at a pithead plant freight
(~half of delivered coal cost) is ~zero, so variable cost should collapse toward a
near-pure function of SHR, making efficiency a tighter proxy for cost / merit-order
position than across the whole fleet.

Two traps this prompt guards against: (a) there is no distance-to-mine field, so
"pithead" must be flagged transparently; (b) the modelled variable cost is built
from SHR, so testing efficiency against it is circular — the cost-side test must
use REAL ECR only.

---

```
Side-analysis (keep it separate from the ECR fetch work; don't break the pipeline).
Read CLAUDE.md first if you haven't. Work on branch claude/keen-newton-P0cFA.

HYPOTHESIS TO TEST
At a pithead plant, transport/freight (~half of delivered coal cost) is ~zero, so
variable cost collapses toward being a near-pure function of SHR. Therefore among
pithead plants, EFFICIENCY should be a tighter proxy for COST (and for merit-order
position) than it is across the whole fleet. Test whether the relationship tightens
within the pithead subset vs the rest.

Build analysis/08_pithead_test.py and write results to outputs/08_pithead_test.txt.

1. IDENTIFY PITHEAD PLANTS (transparently; there is no distance-to-mine field):
   - Primary: a documented curated list of well-known mine-mouth/pithead stations
     (coal-belt: e.g. NTPC Talcher, Singrauli, Rihand, Korba, Sipat, Vindhyachal,
     Kahalgaon; NLC/lignite captive; Singareni, Mahanadi-belt, etc.). Put the list
     in the script with a comment on the basis for each, and flag it as a proxy.
   - Cross-check 1: coal-belt grid_region (Eastern, from 03_regions) as a coarse
     supply-side proxy.
   - Cross-check 2 (strongest, if real ECR exists): pithead plants should have
     systematically LOW real ECR and a LARGE modelled-minus-real gap (because the
     model bakes in freight). Report this; it validates the pithead flag.

2. COMPARE RELATIONSHIPS for {full fleet, pithead subset, non-pithead subset},
   using the PLF>=20 convention:
   a. EFFICIENCY vs PLF — r and R² per group. (Secondary test: PLF carries dispatch
      noise from demand/must-run/transmission, so expect tightening but not R²=1.)
   b. EFFICIENCY vs COST — r and R² per group. CRITICAL: use REAL ECR only
      (vc_source=='published_ECR' in data/plant_cost_blended.csv), NOT the modelled
      variable_cost — the modelled cost is constructed from SHR, so testing
      efficiency against it is circular and would look tight everywhere. If real-ECR
      coverage is too thin in either group to be meaningful, say so explicitly and
      report what coverage you have rather than forcing a number.

3. CONTROL FOR THE OBVIOUS CONFOUNDER: pithead plants are disproportionately large
   central baseload (must-run) units, so higher PLF / tighter dispatch could be
   sector/size, not the efficiency-cost mechanism. Re-run the efficiency↔PLF
   comparison WITHIN the Centre sector only (or add a sector + capacity control, or
   an efficiency×pithead interaction in a regression) so the pithead effect isn't
   just sector in disguise.

4. Report honestly: the curated flag is a proxy; the cost-side test needs real ECR;
   state confounders and any thin-coverage caveats. If the data can't support a
   clean conclusion yet (e.g. ECR coverage too low), say exactly that and note it
   becomes answerable once ECR coverage is broader.

5. Commit (clear message) and push to claude/keen-newton-P0cFA. Show me the
   per-group r/R² table and your read on whether the pithead tightening holds.
```

---

## Notes
- **The cost-side test (2b) is the real test of the claim**, and it only works once
  real-ECR coverage is decent in BOTH groups. Early on (only a few pithead ECRs like
  Talcher) the honest answer is "directionally yes but coverage-limited." The
  efficiency↔PLF test (2a) can run today on existing data.
- **Step 3 (confounder control) is the part most analyses skip.** Pithead ≈ big
  central baseload, so without controlling for sector/size you'd likely "confirm"
  the hypothesis for the wrong reason.
