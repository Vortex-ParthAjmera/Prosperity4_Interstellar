<div align="center">

<pre>
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🤖  A L G O R I T H M   I N D E X  —  V E R S I O N   H I S T O R Y     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
</pre>

[![Competition](https://img.shields.io/badge/IMC-Prosperity%204-FF6B6B?style=for-the-badge)]()
[![Team](https://img.shields.io/badge/TEAM-I%20am%20QT-45B7D1?style=for-the-badge)]()
[![Rank](https://img.shields.io/badge/FINAL%20RANK-3%2C523-4ECDC4?style=for-the-badge)]()

</div>

---

## 📌 PnL Timestamp System Explained

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   🧪  99.9K TIMESTAMP  =  ITERATION EXPERIMENTS (The Grind)               │
│       ├─ Screenshots of individual algorithm test runs                       │
│       ├─ Multiple algos submitted per round to IMC portal                   │
│       ├─ Folders in "Algorithms & Logs/" named after their 99.9K PnL      │
│       └─ DO NOT count toward final ranking                                   │
│                                                                             │
│   🏆  999.9K TIMESTAMP =  FINAL SUBMITTED ALGORITHM (The One That Counted)  │
│       ├─ Single best-performing algo we chose to submit                     │
│       ├─ PnL shown here is our OFFICIAL round PnL                          │
│       ├─ This determined our leaderboard rank                                │
│       └─ ONE screenshot per round: ScreenShots/Pnl/As per 999.9K/        │
│                                                                             │
│   📌  WORKFLOW: Test N algos (99.9K) → pick best → submit (999.9K).      │
│       The 999.9K PnL is our official score.                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Map

All algorithms and logs are stored in `Algorithms & Logs/`:

```
Algorithms & Logs/
├── round_1/
│   ├── Pnl- 2471/     (257217.json, 257217.log, 257217.py)  ← 🧪 Iteration v1
│   ├── Pnl- 3924/     (213297.json, 213297.log, 213297.py)  ← 🧪 Iteration v2
│   └── Pnl-6577/      (257344.json, 257344.log, 257344.py)  ← 🧪 Best iteration (tested)
├── round_2/
│   ├── Pnl- 7247/     (322716.json, 322716.log, 322716.py)  ← 🧪 Iteration v1
│   ├── Pnl-708/       (349440.json, 349440.log, 349440.py)  ← 🧪 Iteration v2
│   ├── Pnl-7975/      (349276.json, 349276.log, 349276.py)  ← 🧪 Iteration v3
│   └── Pnl-8065/      (350036.json, 350036.log, 350036.py)  ← 🧪 Best iteration (tested)
├── round_3/
│   ├── Pnl- negative 448/  (462035.json, 462035.log, 462035.py)  ← 🧪 Iteration v1 (loss)
│   ├── Pnl-2392/         (482527.json, 482527.log, 482527.py)  ← 🧪 Iteration v2
│   └── Pnl-6522/          (483092.json, 483092.log, 483092.py)  ← 🧪 Best iteration (tested)
├── round_4/
│   ├── Pnl- 27054/    (512468.json, 512468.log, 512468.py)  ← 🧪 Iteration v1 (SAFE, +27K)
│   └── Pnl- 30920/    (541990.json, 541990.log, 541990.py)  ← 🧪 Iteration v2 (SAFE, +31K)
└── round_5/
    ├── Pnl- 13050/    (572837.json, 572837.log, 572837.py)  ← 🧪 Iteration v1
    ├── Pnl- 22008/    (579329.json, 579329.log, 579329.py)  ← 🧪 Iteration v2 (best tested)
    └── Pnl- negative 124297/  (573316.json, 573316.log, 573316.py)  ← 🧪 Iteration v3 (DISASTER)
```

Each folder contains:
- `.py` — Source code submitted to IMC portal for that test run
- `.log` — Execution logs from the trading session
- `.json` — Exported data / state snapshots

---

## 🪐 Round 1 — Intara: Foundation

### Iteration History

| Folder | PnL (Tested) | Strategy | Status |
|--------|-------------|----------|--------|
| `Pnl- 2471` | +2,471 | Basic market making | 🧪 Tested |
| `Pnl- 3924` | +3,924 | Momentum detection | 🧪 Tested |
| `Pnl-6577` | +6,577 | Inventory skew MM | 🧪 Best Tested |
| **🏆 999.9K Final** | **+60,941** | **Combined best performers** | **✅ SUBMITTED** |

### Final Submission
- **Strategy:** Market making with inventory skew
- **Products:** TG01 Ash-coated Osmium, TG02 Intarian Pepper Root
- **Live PnL:** +60,941 XIRECs | **Rank:** 3,814
- **Parameters:** Spread 3–5 ticks, inventory target ±50 units, skew factor 0.3/unit deviation
- **Note:** Too conservative. Missed volatility that manual traders captured.
- **Iteration Lesson:** Started with basic MM (+2,471), added momentum (+3,924), refined inventory skew (+6,577). The final submission combined the best elements across iterations.

---

## 🪐 Round 2 — Intara: Ascension

### Iteration History

| Folder | PnL (Tested) | Strategy | Status |
|--------|-------------|----------|--------|
| `Pnl- 7247` | +7,247 | Improved MM spread | 🧪 Tested |
| `Pnl-708` | +708 | Mean reversion | 🧪 Tested |
| `Pnl-7975` | +7,975 | Trend overlay | 🧪 Tested |
| `Pnl-8065` | +8,065 | Hybrid MM + trend | 🧪 Best Tested |
| **🏆 999.9K Final** | **+79,260** | **Combined best performers** | **✅ SUBMITTED** |

### Final Submission
- **Strategy:** Hybrid market making + momentum overlay
- **Products:** TG01 Ash-coated Osmium, TG02 Intarian Pepper Root
- **Live PnL:** +79,260 XIRECs | **Rank:** 3,033
- **Parameters:** Base spread 4 ticks, trend threshold 3 consecutive ticks, max position 100 units
- **Note:** Better than R1 but still lagging manual performance significantly.
- **Iteration Lesson:** 4 iterations tested. Mean reversion was a failure (+708). Hybrid approach won. The final submission combined the best-performing elements.

---

## 🌑 Round 3 — Solvenar: Options Introduction

### Iteration History

| Folder | PnL (Tested) | Strategy | Status |
|--------|-------------|----------|--------|
| `Pnl- negative 448` | -448 | Hydrogel MM only | 🧪 Tested (loss) |
| `Pnl-2392` | +2,392 | VEV BS pricing | 🧪 Tested |
| `Pnl-6522` | +6,522 | Delta-neutral VEV + Velvetfruit | 🧪 Best Tested |
| **🏆 999.9K Final** | **+26,681** | **Combined best performers** | **✅ SUBMITTED** |

### Final Submission
- **Strategy:** Delta-neutral market making + options valuation
- **Products:** TG01 Hydrogel Packs, TG02 Velvetfruit Extract, TG03 VEV Options
- **Live PnL:** +26,681 XIRECs | **Rank:** **1,088** (Best algo round)
- **Parameters:**
  - VEV fair value: Black-Scholes with 7-day TTE
  - Delta hedge ratio: Recalculated every 10 ticks
  - Volatility estimate: Rolling 20-tick realized vol
- **Note:** Best algorithmic performance. BS model worked under stable vol conditions.
- **Iteration Lesson:** v1 lost money (-448) — pure MM without options was insufficient. v2 added BS pricing (+2,392). v3 added delta hedging (+6,522). The final submission scaled the winning approach.

---

## 🌑 Round 4 — Solvenar: The Tragedy

### Iteration History

| Folder | PnL (Tested) | Strategy | Status |
|--------|-------------|----------|--------|
| `Pnl- 27054` | +27,054 | Conservative MM | 🧪 SAFE — NOT SUBMITTED ❌ |
| `Pnl- 30920` | +30,920 | Conservative MM v2 | 🧪 SAFE — NOT SUBMITTED ❌ |
| **🏆 999.9K Final** | **-235,563** | **VEV gamma + Aether exotics** | **💥 SUBMITTED — DISASTER** |

### What We Tested vs What We Submitted

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TESTED:  Pnl- 27054  →  +27,054  (Conservative MM)                        │
│  TESTED:  Pnl- 30920  →  +30,920  (Conservative MM v2)                     │
│                                                                             │
│  SUBMITTED:  ???  →  -235,563  (Gamma Scalping + Exotics)                 │
│                                                                             │
│  ❌ We had SAFE algos in the repo. We submitted the dangerous one.          │
│     Overconfidence killed us.                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Final Submission (The Mistake)
- **Strategy:** VEV gamma scalping + Aether Crystal exotic mispricing
- **Products:** All R3 products + Aether Crystal + Exotic Options (Contract Size: 3,000)
- **Live PnL:** **-235,563 XIRECs** | **Rank:** 2,611
- **Failures:**
  1. Backtested on low-volatility sample data. Live vol was 3x higher.
  2. No hard stop-loss. Gamma exposure exploded.
  3. 3,000 contract size not factored into position sizing.
  4. Exotic option convexity mispriced.
- **The Irony:** Our conservative iterations (`Pnl- 27054` and `Pnl- 30920`) were sitting in the repo, making positive PnL. We didn't submit them. We submitted an untested overfitted strategy instead.

---

## 🌑 Round 5 — Solvenar: Ignith Market

### Iteration History

| Folder | PnL (Tested) | Strategy | Status |
|--------|-------------|----------|--------|
| `Pnl- 13050` | +13,050 | Ultra-conservative MM | 🧪 Tested |
| `Pnl- 22008` | +22,008 | Dynamic spread Ignith | 🧪 Best Tested |
| `Pnl- negative 124297` | -124,297 | High-risk adaptation | 🧪 Tested (DISASTER) |
| **🏆 999.9K Final** | **-79,798** | **Weighted / risk-adjusted** | **✅ SUBMITTED** |

### Final Submission
- **Strategy:** Conservative market making with hard risk controls
- **Products:** 10 New Ignith Market Items (TG01–TG10)
- **Live PnL:** -79,798 XIRECs | **Rank:** 1,695
- **Parameters:**
  - Max position per product: 20 units
  - Daily loss limit: -20,000 XIRECs (hard stop)
  - Spread width: 5–8 ticks
  - No options exposure
- **Note:** Losses were capped vs -235K in R4. Kill switches and position limits worked.
- **Iteration Lesson:** v3 (`Pnl- negative 124297`) was a brutal reminder. We learned from it and adjusted the final submission to be more conservative. The -79,798 final PnL was painful but survivable.

---

## 📊 Algorithm Performance Matrix

| Round | Best Tested | Live Algo PnL | Algo Rank | Strategy | Outcome |
|:-----:|:-----------:|:-------------:|:---------:|:---------|:-------:|
| 1 | +6,577 | +60,941 | 3,814 | Market Making | 🟡 |
| 2 | +8,065 | +79,260 | 3,033 | Hybrid MM+Trend | 🟡 |
| 3 | +6,522 | +26,681 | **1,088** | Options + MM | 🟢 |
| 4 | +30,920 (not submitted) | **-235,563** | 2,611 | Gamma + Exotics | 🔴 |
| 5 | +22,008 | -79,798 | 1,695 | Conservative MM | 🟡 |

---

## 🔬 Key Metrics Across All Rounds

| Metric | R1 | R2 | R3 | R4 | R5 |
|--------|-----|-----|-----|--------|--------|
| **Iterations Tested** | 3 | 4 | 3 | 2 | 3 |
| **Best Tested PnL** | +6,577 | +8,065 | +6,522 | +30,920 | +22,008 |
| **Final Submitted PnL** | +60,941 | +79,260 | +26,681 | -235,563 | -79,798 |
| **Max Drawdown** | -8,000 | -12,000 | -15,000 | -235,563 | -79,798 |
| **Win Rate** | 52% | 54% | 58% | 31% | 48% |
| **Trades/Day** | 450 | 520 | 680 | 890 | 340 |
| **Position Limit** | 100 | 100 | 80 | 200 | 20 |

---

<div align="center">

**Team I am QT — IMC Prosperity 4 Finalists**

</div>
