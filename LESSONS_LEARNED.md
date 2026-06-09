<div align="center">

<pre>
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   📚  L E S S O N S   L E A R N E D  —  P O S T - M O R T E M              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
</pre>

[![Competition](https://img.shields.io/badge/IMC-Prosperity%204-FF6B6B?style=for-the-badge)]()
[![Team](https://img.shields.io/badge/TEAM-I%20am%20QT-45B7D1?style=for-the-badge)]()
[![Rank](https://img.shields.io/badge/FINAL%20RANK-3%2C523-4ECDC4?style=for-the-badge)]()

</div>

---

## 🎯 Executive Summary

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  Competition:     IMC Prosperity 4                                            ║
║  Team:            I am QT                                                     ║
║  Final Rank:      3,523 / ~18,000 (Top 19%)                                   ║
║  Final PnL:       -410,455 XIRECs                                           ║
║  Best Round:      Rank 1,050 (Round 3)                                        ║
║  Worst Round:     Rank 3,579 (Round 4) — -357,069 XIRECs                    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

This document contains the primary mistakes, failures, and insights from 5 rounds of IMC Prosperity 4. The goal is to ensure these errors are not repeated in Prosperity 5.

---

## 💥 Mistake #1: Overfitting to Sample Data (Round 4)

**Cost:** 235,563 XIRECs

### What Happened
- Backtested VEV gamma scalping on provided sample data with low volatility and stable mean-reversion.
- Optimized parameters to maximize sample PnL.
- Deployed live with full confidence.

### Live Result
- Realized volatility was 3x the sample data.
- Gamma exposure, profitable in backtests, became a massive liability.
- No stop-losses existed. Positions ran until catastrophic losses.
- Position sizing was based on sample variance — completely inappropriate for live conditions.

### The Fix
- Never optimize on sample data without adversarial stress testing (2x, 3x, 5x volatility multipliers).
- Use walk-forward validation, not in-sample optimization.
- Set position limits based on worst-case scenarios, not best-case backtests.

> **"The backtest said we'd make 40K. The market said we'd lose 180K. The market was right."** — Yashvardhan Dobhal

---

## 💥 Mistake #2: Ignoring Contract Size Multipliers (Round 4)

**Cost:** 55,563+ XIRECs

### What Happened
- Traded Aether Crystal exotic options without fully accounting for the 3,000 contract size.
- Assumed position sizing from previous rounds (contract size = 1) would scale linearly.
- Did not recalculate risk metrics for the new multiplier.

### Live Result
- A 10-unit position became 30,000-unit exposure.
- A 1-tick move became a 3,000 XIREC move.
- "Conservative" 2% risk per trade became 60% risk per trade.
- Exotic option convexity amplified this further.

### The Fix
- Read contract specifications as the first step, not an afterthought.
- Recalculate Kelly Criterion, VaR, and position limits for every new instrument.
- Build contract size verification into the deployment pipeline.
- When in doubt, reduce position size by 10x before scaling up.

> **"I saw 'contract size: 3,000' and thought 'that's just a number.' It wasn't. It was a death sentence."** — Parth Ajmera

---

## 💥 Mistake #3: Revenge Trading in Manual Rounds (Round 4)

**Cost:** 223,683 XIRECs

### What Happened
- After the algo disaster, entered the manual round emotionally charged.
- Increased position sizes to "make back" algo losses.
- Traded without a pre-written plan.

### Live Result
- Every intuitive trade moved against us.
- Doubled down on losers.
- Combined Round 4 loss: -357,069 XIRECs.

### The Fix
- Write the manual trading plan BEFORE the round starts. No exceptions.
- If algo PnL is negative, take a mandatory 30-minute break before manual trading.
- Never increase position size to recover losses. Decrease it.
- Set a daily loss limit and stop trading when it is hit.

> **"The algo bled. Then we bled manually. The market didn't care about our feelings."** — Piyush Kothari

---

## 💥 Mistake #4: Underutilizing Risk Management (Rounds 1–3)

### What Happened
- No hard stop-losses in R1–R3.
- Position limits were soft targets that could be overridden.
- No daily drawdown limits.
- No correlation checks between manual and algo trades.

### Live Result
- In R1–R3, forgiving markets masked the lack of controls.
- In R4, the absence of risk controls turned a bad day into a catastrophe.
- No kill switch existed to stop the algo when PnL hit -50K.

### The Fix
- Hard stop-losses: -20,000 XIRECs per day, per algo, per product.
- Position limits enforced by code, not by discretion.
- Circuit breaker: Auto-stop trading if drawdown exceeds 10% of starting capital.
- These were implemented in R5 and prevented a repeat of R4.

> **"Risk management is like a seatbelt. You don't need it until you need it. Then you REALLY need it."** — Aashu Joshi

---

## 💥 Mistake #5: Misunderstanding Exotic Options (Round 4)

### What Happened
- Assumed Aether Crystal exotic options could be priced with standard Black-Scholes.
- Did not account for path dependency, barrier features, or implied volatility skew.
- Attempted to "arbitrage" mispriced strikes.

### Live Result
- The market was more efficient than assumed.
- "Arbitrage" was actually hidden gamma/vega risk.
- Exotic features triggered against us.
- Combined with 3,000 contract size, small pricing errors became massive losses.

### The Fix
- If every Greek of an exotic is not understood, do not trade it.
- Build full Monte Carlo simulation before trading path-dependent options.
- When the market offers "free money," assume something is being missed.
- Start with 1-unit positions on new instruments, not 100-unit.

> **"We thought we found alpha. We found a trap disguised as alpha."** — Yashvardhan Dobhal

---

## ✅ What Worked

### Manual Trading Excellence (Rounds 1 & 3)
- **R1:** Rank 43 globally in manual trading.
- **R3:** Rank 219 globally in manual trading.
- **Why:** Pattern recognition on order book depth, rapid adaptation to microstructure, intuitive fair value estimation before algos converged.
- **Lesson:** Human intuition outperforms algorithms in new, chaotic environments. The key is knowing when to switch from manual to systematic.

### Badge Strategy (Round 1)
- **Result:** 13 badges unlocked.
- **Why:** Badges required specific trading behaviors that also improved PnL. Unlocking badges early provided better data access in later rounds.
- **Lesson:** Meta-game mechanics (badges, unlocks) can be as important as pure PnL in competitions.

### Rapid Learning (Round 3 — Options)
- **Result:** Learned Black-Scholes in 48 hours, built delta-hedging algo, achieved Rank 1,088.
- **Why:** Team divided learning (Yash studied math, Parth coded, Aashu tested, Piyush validated). Built "good enough" fast, iterated based on live feedback.
- **Lesson:** Speed of learning exceeds depth of knowledge in short competitions. Build v1 fast, iterate on live data.

### Recovery (Round 5)
- **Result:** After -357K in R4, finished R5 with -79K algo and +26K manual, securing Rank 3,523.
- **Why:** Did not quit. Implemented hard risk controls overnight. Piyush turned Ignith manual round positive.
- **Lesson:** Survival is a valid strategy. Finishing is a victory.

---

## 🔮 Prosperity 5 Action Items

| # | Lesson | P4 Mistake | P5 Fix |
|:-:|:-------|:-----------|:-------|
| 1 | Overfitting | Optimized on sample data | Adversarial backtesting + walk-forward validation |
| 2 | Contract Size | Ignored 3,000 multiplier | Auto-recalculate risk for every new instrument |
| 3 | Emotion | Revenge traded manually | Pre-written plans + mandatory cooling-off periods |
| 4 | Risk Controls | Soft limits, no kill switches | Hard-coded circuit breakers |
| 5 | Exotics | Traded what was not understood | Full Monte Carlo + 1-unit testing before scaling |
| 6 | Correlation | Manual + algo same direction | Correlation check + automatic deleveraging |
| 7 | Speed | Spent too long perfecting v1 | Ship v1 in 24 hours, iterate on live data |
| 8 | Documentation | Lessons in heads, not files | Real-time logging + post-round retrospective within 6 hours |
| 9 | Team Health | Burned out by Round 4 | Scheduled breaks, rotating sleep shifts |
| 10 | Humility | Assumed market understanding | Start every round assuming zero knowledge |

---

<div align="center">

**Team I am QT — IMC Prosperity 4 Finalists**

</div>
