<div align="center">

<pre>
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🚀  P R O S P E R I T Y   5  —  P R E P A R A T I O N   R O A D M A P   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
</pre>

[![Team](https://img.shields.io/badge/TEAM-I%20am%20QT-45B7D1?style=for-the-badge)]()
[![Competition](https://img.shields.io/badge/TARGET-Prosperity%205-FF6B6B?style=for-the-badge)]()
[![Rank](https://img.shields.io/badge/P4%20RANK-3%2C523-4ECDC4?style=for-the-badge)]()

</div>

---

## 📊 Baseline

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  Metric              │  Prosperity 4  │  Top 100 Avg  │  Gap               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Final Rank          │  3,523         │  ~100         │  -3,423            ║
║  Best Round Rank     │  1,050         │  ~50          │  -1,000            ║
║  Best Algo Rank      │  1,088         │  ~40          │  -1,048            ║
║  Best Manual Rank    │  43            │  ~20          │  -23               ║
║  Worst Round PnL     │  -357,069      │  ~-50,000     │  -307,069          ║
║  Win Rate (Algo)     │  48%           │  ~65%         │  -17%              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Key Insight:** Manual trading is elite (Rank 43). Algorithmic execution is the bottleneck. Prosperity 5 focus: close the algo gap.

---

## 🗓️ Pre-Competition Timeline (4 Weeks)

### Week 1: Infrastructure & Risk
- [ ] Build adversarial backtesting engine (2x, 3x, 5x volatility stress tests).
- [ ] Implement hard circuit breakers (auto-stop at -10% drawdown).
- [ ] Create contract size calculator — auto-recalculates risk for every new instrument.
- [ ] Design real-time PnL dashboard with team alerts.
- [ ] Write pre-round strategy templates (one per expected instrument type).

### Week 2: Strategy Library
- [ ] Rebuild market making engine with dynamic spread (not fixed).
- [ ] Build momentum detection with regime switching (trend vs. mean-reversion).
- [ ] Rebuild options pricing with Monte Carlo + Heston model (not just Black-Scholes).
- [ ] Build news sentiment parser for manual trading rounds.
- [ ] Test all strategies on out-of-sample data from Prosperity 4 logs.

### Week 3: Team Drills
- [ ] Mock Round 1: 48-hour simulated competition using Prosperity 4 data.
- [ ] Mock Round 2: Introduce new instruments mid-competition. Test adaptation speed.
- [ ] Mock Round 3: Simulate Round 4-style disaster. Test kill switches and team response.
- [ ] Define role clarity: Parth (algo), Yash (quant), Aashu (strategy), Piyush (manual + risk).
- [ ] Communication protocol: who decides what, when, and how fast.

### Week 4: Recovery & Mental Prep
- [ ] Review all LESSONS_LEARNED.md entries as a team.
- [ ] Build "disaster response playbook" — what to do if we lose 50K in 1 hour.
- [ ] Set sleep schedules. No all-nighters before submission deadlines.
- [ ] Prepare backup power and stable internet for competition days.
- [ ] Mental clarity protocol: Round 4 panic cost 357K. Emotional control is an edge.

---

## 🎮 Competition Strategy — Round by Round

### Round 1: Foundation
**Goal:** Establish base, unlock badges, test algos safely.

| Do | Don't |
|----|-------|
| Deploy conservative market making | Do not experiment with new strategies |
| Focus on manual trading (team strength) | Do not ignore badge opportunities |
| Log every algo behavior meticulously | Do not over-optimize on sample data |

**Target:** Rank < 2,000 | PnL > +100,000 | Badges > 10

---

### Round 2: Ascension
**Goal:** Clear the planet, qualify for next stage.

| Do | Don't |
|----|-------|
| Scale up working strategies from R1 | Do not introduce untested algos |
| Maintain manual trading discipline | Do not get greedy with position sizes |
| Build meta-game awareness (leaderboard dynamics) | Do not chase rank at the expense of risk |

**Target:** Clear target (200K–500K) | Rank < 1,500

---

### Round 3: The Reset
**Goal:** Adapt fast, learn new instruments, capture early alpha.

| Do | Don't |
|----|-------|
| Read ALL documentation in first 2 hours | Do not assume old strategies work |
| Deploy v1 of new strategy within 24 hours | Do not spend 48 hours "perfecting" v1 |
| Manual trade aggressively (new instruments = human edge) | Do not ignore new mechanics |
| Iterate algo based on live feedback (v2 by Day 2) | Do not stick to v1 if it is losing |

**Target:** Rank < 1,000 | PnL > +50,000 | Top 5% manual

---

### Round 4: The Test
**Goal:** Survive. Do not blow up. Preserve capital for Round 5.

| Do | Don't |
|----|-------|
| Reduce position sizes by 50% | Do not overfit to sample data |
| Activate all kill switches | Do not trade exotics you do not fully understand |
| Manual trade with strict loss limits | Do not revenge trade |
| If algo is losing, STOP and reassess | Do not double down to recover |

**Target:** PnL > -50,000 (survive) | Rank < 3,000

---

### Round 5: The Finale
**Goal:** Finish strong. Secure final rank. Show growth.

| Do | Don't |
|----|-------|
| Deploy best-performing strategy from R1–R3 | Do not experiment in the final round |
| Manual trade with news-based strategy | Do not ignore fees or new mechanics |
| Take screenshots for the repo | Do not forget to log lessons in real-time |
| Celebrate when it is over | Do not blame teammates |

**Target:** Rank < 2,000 | PnL > -20,000 | Finish with pride

---

## 🧠 Mental Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. 24-Hour Rule                                                            │
│     Ship v1 within 24 hours of a new round starting.                       │
│     Perfect is the enemy of profitable.                                     │
│                                                                             │
│  2. 50% Rule                                                                │
│     When introducing new instruments, cut position sizes by 50%            │
│     for the first 24 hours.                                                 │
│                                                                             │
│  3. Sample Data Lie                                                         │
│     Sample data is seductive. Trust it for structure, not params.          │
│                                                                             │
│  4. Manual First                                                            │
│     In new markets, manual trading beats algorithms for 48 hours.          │
│                                                                             │
│  5. Red Dashboard Protocol                                                  │
│     If PnL is -20,000, stop for 30 minutes.                                │
│     If -50,000, stop for the day. No exceptions.                           │
│                                                                             │
│  6. Team Over Rank                                                          │
│     We compete as a team. We win as a team. No blame.                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack Upgrades

| Tool | Prosperity 4 | Prosperity 5 Upgrade | Owner |
|------|-------------|----------------------|-------|
| Backtesting | Basic pandas | Walk-forward + adversarial stress tests | Yash |
| Risk Engine | Soft limits | Hard-coded circuit breakers | Parth |
| Options Pricing | Black-Scholes | Heston model + Monte Carlo | Yash |
| News Parser | Manual reading | NLP sentiment analysis (basic) | Aashu |
| Communication | WhatsApp | Discord with bot alerts | Parth |
| Logging | Post-round | Real-time PnL dashboard + auto-screenshots | Parth |
| Version Control | Basic Git | Branch per round, tag per submission | Parth |

---

## 📈 Success Metrics

### Primary Goals (Must Achieve)
- [ ] Final Rank < **1,000** (vs 3,523 in P4)
- [ ] No single round loss > **100,000 XIRECs** (vs 357K in P4)
- [ ] Algo win rate > **60%** (vs 48% in P4)
- [ ] Manual trading rank < **100** in at least one round (vs 43 in P4)

### Stretch Goals (Nice to Have)
- [ ] Final Rank < **500**
- [ ] Top 10 manual trading rank in any round
- [ ] Positive PnL in all 5 rounds
- [ ] Build a strategy that other teams copy

### Process Goals (Most Important)
- [ ] Complete pre-competition prep 1 week early
- [ ] Zero all-nighters during competition
- [ ] Every round documented in repo within 6 hours
- [ ] Team retrospective after every round
- [ ] No blame, only learning, even in disaster

---

<div align="center">

**Team I am QT — Prosperity 4 Finalists | Prosperity 5 Contenders**

</div>
