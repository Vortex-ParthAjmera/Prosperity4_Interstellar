<div align="center">

<pre>
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎯  M A N U A L   T R A D I N G   L O G                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
</pre>

[![Competition](https://img.shields.io/badge/IMC-Prosperity%204-FF6B6B?style=for-the-badge)]()
[![Team](https://img.shields.io/badge/TEAM-I%20am%20QT-45B7D1?style=for-the-badge)]()
[![Rank](https://img.shields.io/badge/FINAL%20RANK-3%2C523-4ECDC4?style=for-the-badge)]()

</div>

---

## 📸 Screenshot Index

All manual trading screenshots are stored in `ScreenShots/Manual_Trades/`:

```
ScreenShots/Manual_Trades/
├── Trade_Made/
│   ├── round_1/01.png
│   ├── round_2/01.png
│   ├── round_3/01.png
│   ├── round_4/01.png
│   └── round_5/01.png
└── Results/
    ├── round_1/01.png
    ├── round_2/01.png ... 02.png
    ├── round_3/01.png ... 02.png
    ├── round_4/001.png
    └── round_5/01.png
```

---

## 🪐 Round 1 — Intara: Pattern Recognition

### Performance
| Metric | Value | Rank |
|--------|-------|------|
| Manual PnL | +80,000 | **43** ⭐ |
| Algo PnL | +60,941 | 3,814 |
| Manual vs Algo | +19,059 | — |

### Strategy
- **Order Book Reading:** Monitored bid-ask spreads on TG01 Ash-coated Osmium and TG02 Intarian Pepper Root.
- **Fair Value Estimation:** Used recent trade prices to estimate fair value when spreads were wide.
- **Aggressive Early Positioning:** Took directional bets in the first 30 minutes based on opening auction dynamics.
- **Scalping:** Captured 1–2 tick moves repeatedly.

### Why Manual Beat Algo
- Algorithm was too conservative — waited for confirmation before entering.
- Manual traders read microstructure (order book imbalance, spoofing patterns) faster than the algo's threshold logic.
- Human intuition detected fake walls and real support levels faster.

### Evidence
| File | Path |
|------|------|
| Trades | `ScreenShots/Manual_Trades/Trade_Made/round_1/01.png` |
| Results | `ScreenShots/Manual_Trades/Results/round_1/01.png` |
| Algo PnL | `ScreenShots/Pnl/As per 999.9K Timestamp/round_1/total pnl 60941.png` |

---

## 🪐 Round 2 — Intara: Investment Discipline

### Performance
| Metric | Value | Rank |
|--------|-------|------|
| Manual PnL | +83,433 | 556 |
| Algo PnL | +79,260 | 3,033 |
| Manual vs Algo | +4,173 | — |

### Strategy
- **Trend Identification:** Identified persistent directional moves from Round 1 data.
- **Investment Sizing:** Allocated 60% of capital to the stronger trend (TG02 Intarian Pepper Root).
- **Hold Discipline:** Resisted scalping. Held positions for 2–3 hours.
- **Pyramiding:** Added to winning positions on pullbacks.

### Why Manual Beat Algo
- Algo was designed for market making (small, frequent profits).
- Manual strategy captured larger trend moves that algos missed.
- Lower transaction costs = higher net PnL.

### Evidence
| File | Path |
|------|------|
| Trades | `ScreenShots/Manual_Trades/Trade_Made/round_2/01.png` |
| Results | `ScreenShots/Manual_Trades/Results/round_2/01.png` ... `02.png` |
| Algo PnL | `ScreenShots/Pnl/As per 999.9K Timestamp/round_2/total pnl.png` |

---

## 🌑 Round 3 — Solvenar: Options Intuition

### Performance
| Metric | Value | Rank |
|--------|-------|------|
| Manual PnL | +75,496 | **219** ⭐ |
| Algo PnL | +26,681 | 1,088 |
| Manual vs Algo | +48,815 | — |

### Strategy
- **Theta Selling:** Sold near-the-money VEV options (VEV_5000, VEV_5200) early when TTE was highest.
- **Deep OTM Lottery:** Bought cheap deep OTM VEVs (VEV_6500) as asymmetric bets.
- **Delta Awareness:** Monitored underlying Velvetfruit Extract price to avoid delta run-over.
- **Time Decay Exploitation:** Closed short option positions before TTE dropped below 3 days.

### VEV Trades
| Contract | Action | Rationale | PnL Contribution |
|----------|--------|-----------|----------------|
| VEV_5000 | Short | High theta, ATM, sold at TTE=7 | +25,000 |
| VEV_5200 | Short | Slightly OTM, safer than 5000 | +18,000 |
| VEV_6500 | Long | Cheap lottery ticket | +8,000 |
| VEV_4500 | Short | Conservative, deep ITM protection | +12,000 |
| VEV_4000 | Avoid | Too deep ITM, low premium | 0 |

### Why Manual Beat Algo
- Algo's BS model was mathematically correct but slow to adapt to implied vol shifts.
- Manual traders could sense when the market was overpricing/underpricing options.
- Human judgment on profit-taking timing (before TTE=3) exceeded the algo's fixed schedule.

### Evidence
| File | Path |
|------|------|
| Trades | `ScreenShots/Manual_Trades/Trade_Made/round_3/01.png` |
| Results | `ScreenShots/Manual_Trades/Results/round_3/01.png` ... `02.png` |
| Algo PnL | `ScreenShots/Pnl/As per 999.9K Timestamp/round_3/01.png` |

---

## 🌑 Round 4 — Solvenar: The Manual Disaster

### Performance
| Metric | Value | Rank |
|--------|-------|------|
| Manual PnL | -223,683 | 1,507 |
| Algo PnL | -235,563 | 2,611 |
| Combined | -357,069 | 3,579 |

### Strategy: Aether Crystal Exotic Options
- Saw "opportunity" in Aether Crystal exotic options across strikes.
- Sized up positions to "recover" algo losses.
- Traded without a pre-written plan — pure improvisation.
- Revenge trading: every loss led to a bigger bet.

### What Went Wrong
- "Mispricing" was actually risk premium for hidden convexity.
- Contract size of 3,000 turned small bets into massive exposures.
- Did not understand exotic features (barriers, path dependency).
- Emotional trading after algo losses destroyed discipline.

### Regrettable Trades
| Trade | Reasoning | Reality | Loss |
|-------|-----------|---------|------|
| Long Aether Call Spread | "Cheap vol" | Vol was cheap for a reason | -85,000 |
| Short Exotic Straddle | "Theta harvest" | Gamma risk exploded | -72,000 |
| Double Down | "It will revert" | It did not | -45,000 |
| No Stop Loss | "One more tick" | 30 ticks later | -21,683 |

### Evidence
| File | Path |
|------|------|
| Trades | `ScreenShots/Manual_Trades/Trade_Made/round_4/01.png` |
| Results | `ScreenShots/Manual_Trades/Results/round_4/001.png` |
| Algo PnL | `ScreenShots/Pnl/As per 999.9K Timestamp/round_4/total pnl.png` |

---

## 🌑 Round 5 — Solvenar: Ignith Market Recovery

### Performance
| Metric | Value | Rank |
|--------|-------|------|
| Manual PnL | +26,412 | 1,606 |
| Algo PnL | -79,798 | 1,695 |
| Net Round | -53,386 | — |

### Market Context
- **New Market:** Ignith (one-time access)
- **Budget:** 1,000,000 XIRECs
- **Data Source:** Ashflow Alpha (news/articles)
- **Constraint:** Trading fees applied per product volume
- **Products:** 10 New Ignith Items (TG01–TG10)

### Strategy: News-Based Directional Trading
1. **News Analysis:** Read Ashflow Alpha articles to identify trending products.
2. **Fee Optimization:** Batched trades to minimize per-transaction fees.
3. **Directional Bets:** Long positions on products with positive news momentum.
4. **Risk Caps:** Max 10% of budget per product, max 30% total exposure.
5. **Quick Exits:** Took profit at 5% gain, cut losses at 3% drawdown.

### Products Traded
| Product | News Signal | Action | PnL | Fee Impact |
|---------|-------------|--------|-----|------------|
| TG05 Domestic Robotics | "Automation boom" | Long | +12,000 | -800 |
| TG03 Organic Microchip | "Supply shortage" | Long | +8,500 | -650 |
| TG08 Construction Panels | "Infrastructure expansion" | Long | +5,200 | -420 |
| TG02 Vertical Sleeping Pods | Mixed signals | Avoid | 0 | 0 |
| TG09 Liquid Breath Oxygen | "Tourism decline" | Short | +2,800 | -310 |
| Others | No clear signal | No trade | 0 | 0 |

### Why It Worked
- Careful reading of Ashflow Alpha instead of headline scanning.
- Fee awareness meant fewer, larger trades.
- Risk caps prevented a Round 4 repeat.
- Written plan existed BEFORE the round started.

### Evidence
| File | Path |
|------|------|
| Trades | `ScreenShots/Manual_Trades/Trade_Made/round_5/01.png` |
| Results | `ScreenShots/Manual_Trades/Results/round_5/01.png` |
| Algo PnL | `ScreenShots/Pnl/As per 999.9K Timestamp/round_5/total pnl.png` |

---

## 📊 Manual vs Algorithmic Comparison

| Round | Manual PnL | Manual Rank | Algo PnL | Algo Rank | Winner | Gap |
|:-----:|:----------:|:-----------:|:--------:|:---------:|:------:|:---:|
| 1 | +80,000 | **43** ⭐ | +60,941 | 3,814 | Manual | +19,059 |
| 2 | +83,433 | 556 | +79,260 | 3,033 | Manual | +4,173 |
| 3 | +75,496 | **219** ⭐ | +26,681 | 1,088 | Manual | +48,815 |
| 4 | -223,683 | 1,507 | -235,563 | 2,611 | Algo (less bad) | +11,880 |
| 5 | +26,412 | 1,606 | -79,798 | 1,695 | Manual | +106,210 |
| **Total** | **+41,658** | — | **-148,459** | — | **Manual** | **+190,117** |

**Insight:** Manual trading outperformed algorithms by 190,117 XIRECs over the competition. Intuition is strong — systematic execution needs improvement.

---

## 🎯 Manual Trading Playbook (Prosperity 5)

### Pre-Round Checklist
- [ ] Read ALL news/articles provided.
- [ ] Write down 3 specific strategies before trading starts.
- [ ] Set daily loss limit (e.g., -20,000 XIRECs).
- [ ] Set daily win limit (e.g., +50,000 XIRECs — take profit).
- [ ] Identify 2 products to focus on, 3 to avoid.
- [ ] Calculate trading fees for intended position sizes.

### During Round Rules
- [ ] No revenge trading. If algo is down, take a 30-minute break.
- [ ] No position size increases to recover losses.
- [ ] No trading without a written rationale.
- [ ] Screenshot every major position.
- [ ] Stop when daily loss limit is hit.

### Post-Round Review
- [ ] Screenshot final PnL dashboard immediately.
- [ ] Log every trade with rationale and outcome.
- [ ] Identify 1 thing that worked, 1 that did not.
- [ ] Update this file before the next round.

---

<div align="center">

**Team I am QT — IMC Prosperity 4 Finalists**

</div>
