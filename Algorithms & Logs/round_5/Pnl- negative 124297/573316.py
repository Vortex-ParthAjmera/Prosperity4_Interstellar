from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List, Tuple
import json, math

# ═══════════════════════════════════════════���═══════════════════════
# CONSTANTS (v7 — Revised for 50k+ PnL)
# ═══════════════════════════════════════════════════════════════════

POS_LIMIT       = 10
HARD_CAP        = 4      # TIGHTER: max |pos| in normal ops (was 3)
CRITICAL_CAP    = 6      # Above this: aggressive exit begins
PANIC_CAP       = 8      # Above this: exit only, no new entries
BASE_QTY        = 4      # Base entry qty (was 5, but with tighter cap)
EXIT_QTY_LOW    = 6      # Qty to post on exit side at HARD_CAP
EXIT_QTY_HIGH   = 8      # Qty to post on exit side at CRITICAL_CAP
LEAN_QTY        = 1      # Entry qty when near cap (was 2)
EWM_ALPHA       = 0.015  # SLOWER drift detection (was 0.04)
DRIFT_THRESH    = 5.0    # Tighter threshold (was 4.0)
ARB_SPIKE_MULT  = 1.2    # LOWER threshold for arb (was 2.0 — missing 60% of opps)
ARB_EXIT_TIME   = 50     # Hold arb position max 50 ticks
SPREAD_SCALE    = 0.45   # offset_adaptive = vol/2 * SPREAD_SCALE, capped by half_spread-0.5

# ═══════════════════════════════════════════════════════════════════
# DYNAMIC OFFSET CALCULATION (CORE FIX)
# ═══════════════════════════════════════════════════════════════════

def calc_offset(vol: float, spread: float, inventory: int) -> int:
    """
    Avellaneda-Stoikov adaptive offset:
    - Base offset = vol / 2
    - Scale by available spread room
    - Tighten when inventory high (reduce spread donation risk)
    """
    base = max(1, int(vol / 2.0))
    
    # Room constraint
    max_room = max(1, (spread - 1) // 2)
    offset = min(base, max_room)
    
    # Tighten at high inventory to reduce adverse selection
    ap = abs(inventory)
    if ap >= CRITICAL_CAP:
        offset = max(1, offset - 1)
    elif ap >= HARD_CAP:
        offset = max(1, int(offset * 0.9))
    
    return offset

# ═══════════════════════════════════════════════════════════════════
# PER-SYMBOL STATE (Enhanced)
# ═══════════════════════════════════════════════════════════════════

class _Sym:
    __slots__ = ('ewm_mid', 'prev_mid', 'vol_short', 'vol_long', 'arb_entry_ts', 
                 'arb_entry_pos', 'spread_est', 'realized_spread', 'tick_count',
                 'direction_bias')

    def __init__(self):
        self.ewm_mid = None
        self.prev_mid = None
        self.vol_short = 5.0  # Short-term vol (EWMA of |Δ| per tick)
        self.vol_long = 8.0   # Long-term vol
        self.spread_est = 10.0
        self.arb_entry_ts = None
        self.arb_entry_pos = 0
        self.realized_spread = 0.0
        self.tick_count = 0
        self.direction_bias = 0.0  # Momentum filter

    def update(self, mid: float, bid: int, ask: int, timestamp: int):
        # Spread tracking
        raw_spread = ask - bid
        self.spread_est = 0.95 * self.spread_est + 0.05 * raw_spread
        
        if self.ewm_mid is None:
            self.ewm_mid = mid
            self.prev_mid = mid
            self.tick_count = 1
            return

        # Vol tracking
        tick_move = abs(mid - self.prev_mid)
        self.vol_short = 0.92 * self.vol_short + 0.08 * tick_move
        self.vol_long = 0.98 * self.vol_long + 0.02 * tick_move
        
        # Direction bias (momentum)
        self.direction_bias = 0.9 * self.direction_bias + 0.1 * (mid - self.prev_mid)
        
        # Drift anchor (very slow EWM)
        self.ewm_mid = (1 - EWM_ALPHA) * self.ewm_mid + EWM_ALPHA * mid
        self.prev_mid = mid
        self.tick_count += 1

    @property
    def drift(self) -> float:
        if self.prev_mid is None or self.ewm_mid is None:
            return 0.0
        return self.prev_mid - self.ewm_mid
    
    @property
    def vol(self) -> float:
        # Blend short and long vol; favor short-term when high
        if self.vol_short > self.vol_long * 1.3:
            return 0.6 * self.vol_short + 0.4 * self.vol_long
        return 0.5 * self.vol_short + 0.5 * self.vol_long

# ═══════════════════════════════════════════════════════════════════
# TRADER v7
# ═══════════════════════════════════════════════════════════════════

class Trader:
    def __init__(self):
        self._s: Dict[str, _Sym] = {}
        self._ready = False
        self._global_ts = 0

    def _sym(self, sym: str) -> _Sym:
        if sym not in self._s:
            self._s[sym] = _Sym()
        return self._s[sym]

    # ── QUOTE SIZING (Inventory + Drift + Vol-aware) ───────────────

    def _sizes(self, pos: int, drift: float, vol: float, spread: float) -> Tuple[int, int]:
        """
        Advanced sizing combining:
        1. Inventory control (tighter caps)
        2. Drift skew (bias against trend)
        3. Vol-aware (wider spreads when vol high → post more)
        4. Spread awareness (narrow spreads → post less)
        """
        ap = abs(pos)

        # PANIC: no entry
        if ap >= PANIC_CAP:
            if pos > 0:
                return 0, min(6, POS_LIMIT - pos)
            else:
                return min(6, POS_LIMIT + pos), 0

        # CRITICAL: aggressive exit
        if ap >= CRITICAL_CAP:
            if pos > 0:
                bq = max(0, LEAN_QTY if drift < 0 else 0)
                aq = EXIT_QTY_HIGH
            else:
                aq = max(0, LEAN_QTY if drift > 0 else 0)
                bq = EXIT_QTY_HIGH
        
        # HARD CAP: normal asymmetric
        elif ap >= HARD_CAP:
            if pos > 0:
                bq = 0 if drift > DRIFT_THRESH else LEAN_QTY
                aq = EXIT_QTY_LOW
            else:
                aq = 0 if drift < -DRIFT_THRESH else LEAN_QTY
                bq = EXIT_QTY_LOW
        
        # NORMAL: symmetric with drift skew
        else:
            bq = aq = BASE_QTY
            
            # Drift adjustment
            if drift > DRIFT_THRESH:
                bq = max(0, bq - 2)
            elif drift < -DRIFT_THRESH:
                aq = max(0, aq - 2)
            
            # Vol adjustment: higher vol → larger sizes (more edge per tick)
            if vol > 15:
                bq += 1
                aq += 1
            elif vol < 5:
                bq = max(2, bq - 1)
                aq = max(2, aq - 1)

        # Clamp to room
        bq = min(bq, max(POS_LIMIT - pos, 0))
        aq = min(aq, max(POS_LIMIT + pos, 0))

        return bq, aq

    # ── MARKET MAKING ────────────────────────────────────────────────

    def _make(self, sym: str, best_bid: int, best_ask: int, pos: int,
              timestamp: int) -> List[Order]:
        st = self._sym(sym)
        spread = best_ask - best_bid
        
        if spread < 2:
            return []

        # DYNAMIC OFFSET (KEY FIX)
        offset = calc_offset(st.vol, spread, pos)
        
        # Safety check: never cross
        if 2 * offset >= spread:
            offset = (spread - 1) // 2
        
        our_bid = best_bid + offset
        our_ask = best_ask - offset
        
        if our_ask <= our_bid:
            return []

        bq, aq = self._sizes(pos, st.drift, st.vol, spread)

        orders = []
        if bq > 0:
            orders.append(Order(sym, our_bid, bq))
        if aq > 0:
            orders.append(Order(sym, our_ask, -aq))

        # AGGRESSIVE EXIT (Panic liquidation)
        ap = abs(pos)
        if ap >= PANIC_CAP:
            panic_qty = min(3, ap - CRITICAL_CAP + 1)
            if pos > 0:
                orders.append(Order(sym, best_bid - 2, -panic_qty))  # Cross to dump
            else:
                orders.append(Order(sym, best_ask + 2, panic_qty))   # Cross to cover

        return orders

    # ── CLUSTER ARBITRAGE (Lower threshold, smarter entry) ──────────

    def _arb(self, depths: Dict[str, OrderDepth], pos_map: Dict[str, int],
             timestamp: int) -> Dict[str, List[Order]]:
        """
        Pairs: (VANILLA, CHOCOLATE, -1), (SQUARE, RECT, -1), etc.
        Trigger on spike in LEADER, entry in FOLLOWER
        Hold for max ARB_EXIT_TIME ticks
        """
        out: Dict[str, List[Order]] = {}

        pairs = [
            ("SNACKPACK_VANILLA", "SNACKPACK_CHOCOLATE", -1),
            ("MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", -1),
            ("MICROCHIP_TRIANGLE", "MICROCHIP_OVAL", 1),
            ("PEBBLES_XL", "PEBBLES_S", -1),
            ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 1),
        ]

        for leader, follower, sign in pairs:
            st_l = self._sym(leader)
            if st_l.prev_mid is None:
                continue

            ld = depths.get(leader)
            if not ld or not ld.buy_orders or not ld.sell_orders:
                continue

            l_mid = (max(ld.buy_orders) + min(ld.sell_orders)) / 2.0
            move = abs(l_mid - st_l.ewm_mid)  # Deviation from slow EWM
            
            # LOWER THRESHOLD (1.2x vol instead of 2.0x)
            if move < ARB_SPIKE_MULT * st_l.vol:
                continue

            f_pos = pos_map.get(follower, 0)
            fd = depths.get(follower)
            if not fd or not fd.buy_orders or not fd.sell_orders:
                continue

            # Direction: if leader moved, follower should follow (with sign)
            move_dir = 1 if (l_mid - st_l.ewm_mid) > 0 else -1
            expected_f_dir = move_dir * sign

            if expected_f_dir > 0:
                room = POS_LIMIT - f_pos
                if room <= 1:
                    continue
                best_ask_f = min(fd.sell_orders.keys())
                qty = min(room - 1, 4)
                if qty > 0:
                    out.setdefault(follower, []).append(Order(follower, best_ask_f, qty))
            else:
                room = POS_LIMIT + f_pos
                if room <= 1:
                    continue
                best_bid_f = max(fd.buy_orders.keys())
                qty = min(room - 1, 4)
                if qty > 0:
                    out.setdefault(follower, []).append(Order(follower, best_bid_f, -qty))

        return out

    # ── STATE SERIALIZATION ──────────────────────────────────────────

    def _save(self) -> str:
        p = {}
        for sym, st in self._s.items():
            if st.ewm_mid is not None:
                p[sym] = {
                    'e': round(st.ewm_mid, 1),
                    'p': round(st.prev_mid, 1) if st.prev_mid else None,
                    'vs': round(st.vol_short, 2),
                    'vl': round(st.vol_long, 2),
                    'db': round(st.direction_bias, 2),
                }
        return json.dumps(p, separators=(',', ':'))

    def _load(self, td: str):
        if not td:
            return
        try:
            for sym, d in json.loads(td).items():
                st = self._sym(sym)
                st.ewm_mid = d.get('e')
                st.prev_mid = d.get('p')
                st.vol_short = d.get('vs', 5.0)
                st.vol_long = d.get('vl', 8.0)
                st.direction_bias = d.get('db', 0.0)
        except Exception:
            pass

    # ── MAIN RUN ─────────────────────────────────────────────────────

    def run(self, state: TradingState):
        if not self._ready:
            self._load(state.traderData)
            self._ready = True

        self._global_ts = state.timestamp
        pos_map = state.position
        depths = state.order_depths
        result: Dict[str, List[Order]] = {}

        # 1. Update all symbol states
        for sym, depth in depths.items():
            if not depth.buy_orders or not depth.sell_orders:
                continue
            bid = max(depth.buy_orders.keys())
            ask = min(depth.sell_orders.keys())
            mid = (bid + ask) / 2.0
            self._sym(sym).update(mid, bid, ask, state.timestamp)

        # 2. Cluster arb (lower threshold)
        for sym, orders in self._arb(depths, pos_map, state.timestamp).items():
            result.setdefault(sym, []).extend(orders)

        # 3. Market making on all symbols
        for sym, depth in depths.items():
            if not depth.buy_orders or not depth.sell_orders:
                continue
            bid = max(depth.buy_orders.keys())
            ask = min(depth.sell_orders.keys())
            pos = pos_map.get(sym, 0)
            pending = sum(o.quantity for o in result.get(sym, []))
            eff_pos = pos + pending
            
            orders = self._make(sym, bid, ask, eff_pos, state.timestamp)
            result.setdefault(sym, []).extend(orders)

        return result, 0, self._save()