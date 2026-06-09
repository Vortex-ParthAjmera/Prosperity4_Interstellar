from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List, Tuple
import json, math

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

POS_LIMIT       = 10
NORMAL_CAP      = 2      # Tighter control
LEAN_CAP        = 5      # Earlier lean trigger
URGENCY_CAP     = 7      # Trigger aggressive exit
BASE_QTY        = 4      # More aggressive quoting
LEAN_QTY        = 2
EXIT_QTY        = 7      # Larger exits

EWM_ALPHA_FAST  = 0.08   # Faster drift detection
EWM_ALPHA_SLOW  = 0.02   # Slow trend anchor
DRIFT_THRESH    = 2.5    # Lower threshold
MOMENTUM_WINDOW = 8      # Last N ticks for momentum

# Adaptive spread thresholds
SPREAD_WIDE     = 25     # Widen when spread exceeds this
SPREAD_NARROW   = 8      # Tighten when spread below this
VOL_SPIKE_MULT  = 1.8    # Widen spread on vol spike

ARB_SPIKE_MULT  = 1.4    # More aggressive arb (was 2.0)
ARB_QTY         = 4      # Larger arb positions

# ═══════════════════════════════════════════════════════════════════
# ENHANCED OFFSETS (Dynamic, not fixed)
# ═══════════════════════════════════════════════════════════════════

BASE_OFFSET: Dict[str, float] = {
    "SNACKPACK_CHOCOLATE":           2.5,
    "SNACKPACK_VANILLA":             2.5,
    "SNACKPACK_PISTACHIO":           2.0,
    "SNACKPACK_STRAWBERRY":          2.5,
    "SNACKPACK_RASPBERRY":           2.5,
    "PEBBLES_XS":                    3.0,
    "PEBBLES_S":                     4.5,
    "PEBBLES_M":                     6.0,
    "PEBBLES_L":                     5.5,
    "PEBBLES_XL":                    7.0,
    "GALAXY_SOUNDS_DARK_MATTER":     4.0,
    "GALAXY_SOUNDS_BLACK_HOLES":     5.0,
    "GALAXY_SOUNDS_PLANETARY_RINGS": 5.0,
    "GALAXY_SOUNDS_SOLAR_WINDS":     5.0,
    "GALAXY_SOUNDS_SOLAR_FLAMES":    4.0,
    "UV_VISOR_YELLOW":               5.0,
    "UV_VISOR_AMBER":                3.5,
    "UV_VISOR_ORANGE":               4.0,
    "UV_VISOR_RED":                  5.0,
    "UV_VISOR_MAGENTA":              5.0,
    "OXYGEN_SHAKE_MORNING_BREATH":   4.0,
    "OXYGEN_SHAKE_EVENING_BREATH":   4.0,
    "OXYGEN_SHAKE_MINT":             4.0,
    "OXYGEN_SHAKE_CHOCOLATE":        4.0,
    "OXYGEN_SHAKE_GARLIC":           5.0,
    "MICROCHIP_CIRCLE":              2.5,
    "MICROCHIP_OVAL":                2.5,
    "MICROCHIP_SQUARE":              5.5,
    "MICROCHIP_RECTANGLE":           2.5,
    "MICROCHIP_TRIANGLE":            3.0,
    "PANEL_1X2":                     4.0,
    "PANEL_2X2":                     3.5,
    "PANEL_1X4":                     2.5,
    "PANEL_2X4":                     3.5,
    "PANEL_4X4":                     3.5,
    "TRANSLATOR_SPACE_GRAY":         3.0,
    "TRANSLATOR_ASTRO_BLACK":        3.0,
    "TRANSLATOR_ECLIPSE_CHARCOAL":   3.0,
    "TRANSLATOR_GRAPHITE_MIST":      3.0,
    "TRANSLATOR_VOID_BLUE":          3.0,
    "SLEEP_POD_LAMB_WOOL":           3.5,
    "SLEEP_POD_POLYESTER":           4.0,
    "SLEEP_POD_SUEDE":               4.0,
    "SLEEP_POD_NYLON":               3.5,
    "SLEEP_POD_COTTON":              4.0,
    "ROBOT_VACUUMING":               2.5,
    "ROBOT_MOPPING":                 3.0,
    "ROBOT_DISHES":                  2.5,
    "ROBOT_LAUNDRY":                 2.5,
    "ROBOT_IRONING":                 1.5,
}

CORR_PAIRS: List[Tuple[str, str, int, float]] = [
    ("SNACKPACK_VANILLA",        "SNACKPACK_CHOCOLATE",    -1, 0.926),
    ("SNACKPACK_CHOCOLATE",      "SNACKPACK_VANILLA",      -1, 0.926),
    ("MICROCHIP_SQUARE",         "MICROCHIP_RECTANGLE",    -1, 0.882),
    ("MICROCHIP_RECTANGLE",      "MICROCHIP_SQUARE",       -1, 0.882),
    ("MICROCHIP_TRIANGLE",       "MICROCHIP_OVAL",          1, 0.870),
    ("PEBBLES_XL",               "PEBBLES_S",              -1, 0.834),
    ("PEBBLES_S",                "PEBBLES_XL",             -1, 0.834),
    ("SLEEP_POD_COTTON",         "SLEEP_POD_POLYESTER",     1, 0.875),
]

LEADER_VOL: Dict[str, float] = {
    "MICROCHIP_SQUARE": 19.7, "MICROCHIP_RECTANGLE": 9.8,
    "MICROCHIP_TRIANGLE": 11.3,
    "PEBBLES_XL": 24.8, "PEBBLES_S": 12.0,
    "SNACKPACK_VANILLA": 5.4, "SNACKPACK_CHOCOLATE": 5.4,
    "SLEEP_POD_COTTON": 10.0,
}

# ═══════════════════════════════════════════════════════════════════
# ENHANCED STATE TRACKING
# ═══════════════════════════════════════════════════════════════════

class _Sym:
    __slots__ = ('ewm_mid_fast', 'ewm_mid_slow', 'prev_mid', 'vol_est',
                 'momentum_buffer', 'last_spread', 'trade_intensity')

    def __init__(self):
        self.ewm_mid_fast: float = None
        self.ewm_mid_slow: float = None
        self.prev_mid: float = None
        self.vol_est: float = 8.0
        self.momentum_buffer: List[float] = []
        self.last_spread: float = 15.0
        self.trade_intensity: float = 0.0

    def update(self, mid: float, spread: float, volume_signal: float):
        if self.ewm_mid_fast is None:
            self.ewm_mid_fast = mid
            self.ewm_mid_slow = mid
        else:
            if self.prev_mid is not None:
                tick_move = abs(mid - self.prev_mid)
                self.vol_est = 0.90 * self.vol_est + 0.10 * tick_move
                
                # Momentum buffer (last N ticks)
                self.momentum_buffer.append(mid - self.prev_mid)
                if len(self.momentum_buffer) > MOMENTUM_WINDOW:
                    self.momentum_buffer.pop(0)
            
            self.ewm_mid_fast = (1 - EWM_ALPHA_FAST) * self.ewm_mid_fast + EWM_ALPHA_FAST * mid
            self.ewm_mid_slow = (1 - EWM_ALPHA_SLOW) * self.ewm_mid_slow + EWM_ALPHA_SLOW * mid
        
        self.prev_mid = mid
        self.last_spread = spread
        self.trade_intensity = 0.95 * self.trade_intensity + 0.05 * volume_signal

    @property
    def drift_signal(self) -> float:
        if self.ewm_mid_fast is None:
            return 0.0
        return self.prev_mid - self.ewm_mid_slow

    @property
    def momentum(self) -> float:
        if len(self.momentum_buffer) < 3:
            return 0.0
        return sum(self.momentum_buffer[-3:]) / 3.0

    @property
    def is_volatile(self) -> bool:
        return self.vol_est > 12.0

    @property
    def is_crowded(self) -> bool:
        return self.trade_intensity > 0.6


# ═══════════════════════════════════════════════════════════════════
# TRADER v7 — Enhanced
# ═══════════════════════════════════════════════════════════════════

class Trader:
    """
    Prosperity Round 5 v7
    
    Improvements:
    • Dynamic offset based on spread and volatility
    • Momentum-aware position sizing
    • Faster drift detection with dual EWM
    • Adaptive spread response (predator shielding)
    • Aggressive cluster arbitrage
    • Enhanced liquidation logic
    """

    def __init__(self):
        self._s: Dict[str, _Sym] = {}
        self._ready = False

    def _sym(self, sym: str) -> _Sym:
        if sym not in self._s:
            self._s[sym] = _Sym()
        return self._s[sym]

    def _dynamic_offset(self, sym: str, spread: float) -> int:
        """Calculate offset based on spread, volatility, and crowding."""
        base = BASE_OFFSET.get(sym, 3.0)
        st = self._sym(sym)
        
        # Adjust for volatility
        if st.is_volatile:
            base *= 1.1  # Wider on high vol
        
        # Adjust for crowding (adaptive shielding)
        if st.is_crowded:
            base *= 1.15  # Much wider when busy
        
        # Constrain to spread
        max_offset = max(1, (spread - 1) // 2)
        offset = min(int(base), max_offset)
        return max(1, offset)

    def _sizes(self, pos: int, drift: float, momentum: float,
               is_volatile: bool) -> Tuple[int, int]:
        """
        Enhanced sizing with momentum and volatility awareness.
        """
        ap = abs(pos)

        # Base inventory logic
        if pos >= POS_LIMIT:
            return (0, POS_LIMIT + pos) if pos < POS_LIMIT else (0, 0)
        if pos <= -POS_LIMIT:
            return (POS_LIMIT - pos, 0) if pos > -POS_LIMIT else (0, 0)

        if pos > 0:
            if ap >= URGENCY_CAP:
                bq, aq = 0, EXIT_QTY
            elif ap >= LEAN_CAP:
                bq, aq = LEAN_QTY, EXIT_QTY
            elif ap > NORMAL_CAP:
                bq, aq = LEAN_QTY, BASE_QTY + 1
            else:
                bq, aq = BASE_QTY, BASE_QTY
        elif pos < 0:
            if ap >= URGENCY_CAP:
                bq, aq = EXIT_QTY, 0
            elif ap >= LEAN_CAP:
                bq, aq = EXIT_QTY, LEAN_QTY
            elif ap > NORMAL_CAP:
                bq, aq = BASE_QTY + 1, LEAN_QTY
            else:
                bq, aq = BASE_QTY, BASE_QTY
        else:
            bq, aq = BASE_QTY, BASE_QTY

        # Drift adjustment (more aggressive)
        if abs(drift) >= DRIFT_THRESH:
            if drift > 0:
                bq = max(0, bq - 2)
            else:
                aq = max(0, aq - 2)

        # Momentum boost (if momentum aligns with our position, add)
        if momentum > 1.0 and pos <= NORMAL_CAP:
            aq = min(POS_LIMIT - pos, aq + 1)
        elif momentum < -1.0 and pos >= -NORMAL_CAP:
            bq = min(POS_LIMIT + pos, bq + 1)

        # Clamp to room
        bq = min(bq, max(POS_LIMIT - pos, 0))
        aq = min(aq, max(POS_LIMIT + pos, 0))

        return bq, aq

    def _make(self, sym: str, best_bid: int, best_ask: int,
              pos: int, spread: float) -> List[Order]:
        """Enhanced market making with dynamic offset."""
        if spread < 2:
            return []

        st = self._sym(sym)
        offset = self._dynamic_offset(sym, spread)

        if 2 * offset >= spread:
            offset = max(1, (spread - 1) // 2)

        our_bid = best_bid + offset
        our_ask = best_ask - offset

        if our_ask <= our_bid:
            return []

        drift = st.drift_signal
        momentum = st.momentum
        bq, aq = self._sizes(pos, drift, momentum, st.is_volatile)

        orders: List[Order] = []
        if bq > 0:
            orders.append(Order(sym, our_bid, bq))
        if aq > 0:
            orders.append(Order(sym, our_ask, -aq))

        # Aggressive liquidation
        ap = abs(pos)
        if ap >= URGENCY_CAP:
            if pos > 0:
                cross_qty = min(4, pos - LEAN_CAP + 2)
                if cross_qty > 0:
                    orders.append(Order(sym, best_bid, -cross_qty))
            else:
                cross_qty = min(4, -pos - LEAN_CAP + 2)
                if cross_qty > 0:
                    orders.append(Order(sym, best_ask, cross_qty))

        return orders

    def _arb(self, depths: Dict[str, OrderDepth],
             pos_map: Dict[str, int]) -> Dict[str, List[Order]]:
        """Enhanced cluster arb with momentum confirmation."""
        out: Dict[str, List[Order]] = {}

        for leader, follower, sign, _ in CORR_PAIRS:
            st_l = self._sym(leader)
            if st_l.prev_mid is None or st_l.ewm_mid_slow is None:
                continue

            ld = depths.get(leader)
            if not ld or not ld.buy_orders or not ld.sell_orders:
                continue

            l_mid = (max(ld.buy_orders) + min(ld.sell_orders)) / 2
            move = l_mid - st_l.prev_mid
            vol = LEADER_VOL.get(leader, st_l.vol_est)

            # Lower threshold + momentum confirmation
            if abs(move) < ARB_SPIKE_MULT * vol:
                continue

            if st_l.momentum * sign < 0.5:  # Momentum should align
                continue

            expected_dir = (1 if move > 0 else -1) * sign
            f_pos = pos_map.get(follower, 0)
            fd = depths.get(follower)

            if not fd:
                continue

            if expected_dir > 0:
                room = POS_LIMIT - f_pos
                if room <= 0 or not fd.sell_orders:
                    continue
                best_ask_f = min(fd.sell_orders.keys())
                qty = min(room, ARB_QTY)
                out.setdefault(follower, []).append(Order(follower, best_ask_f, qty))
            else:
                room = POS_LIMIT + f_pos
                if room <= 0 or not fd.buy_orders:
                    continue
                best_bid_f = max(fd.buy_orders.keys())
                qty = min(room, ARB_QTY)
                out.setdefault(follower, []).append(Order(follower, best_bid_f, -qty))

        return out

    def _save(self) -> str:
        p = {}
        for sym, st in self._s.items():
            if st.ewm_mid_fast is not None:
                p[sym] = {
                    'f': round(st.ewm_mid_fast, 2),
                    's': round(st.ewm_mid_slow, 2),
                    'p': round(st.prev_mid, 2),
                    'v': round(st.vol_est, 3),
                    'ti': round(st.trade_intensity, 3),
                }
        return json.dumps(p, separators=(',', ':'))

    def _load(self, td: str):
        if not td:
            return
        try:
            for sym, d in json.loads(td).items():
                st = self._sym(sym)
                st.ewm_mid_fast = d.get('f')
                st.ewm_mid_slow = d.get('s')
                st.prev_mid = d.get('p')
                st.vol_est = d.get('v', 8.0)
                st.trade_intensity = d.get('ti', 0.0)
        except Exception:
            pass

    def run(self, state: TradingState):
        if not self._ready:
            self._load(state.traderData)
            self._ready = True

        pos_map = state.position
        depths = state.order_depths
        result: Dict[str, List[Order]] = {}

        # Update all symbols
        for sym, depth in depths.items():
            if not depth.buy_orders or not depth.sell_orders:
                continue

            best_bid = max(depth.buy_orders.keys())
            best_ask = min(depth.sell_orders.keys())
            mid = (best_bid + best_ask) / 2.0
            spread = best_ask - best_bid

            # Volume signal from depth
            total_bid_vol = sum(depth.buy_orders.values())
            total_ask_vol = sum(depth.sell_orders.values())
            vol_signal = (total_bid_vol + total_ask_vol) / 100.0

            self._sym(sym).update(mid, spread, vol_signal)

        # Cluster arb
        for sym, orders in self._arb(depths, pos_map).items():
            result.setdefault(sym, []).extend(orders)

        # Market making
        for sym, depth in depths.items():
            if not depth.buy_orders or not depth.sell_orders:
                continue

            best_bid = max(depth.buy_orders.keys())
            best_ask = min(depth.sell_orders.keys())
            spread = best_ask - best_bid
            pos = pos_map.get(sym, 0)

            pending = sum(o.quantity for o in result.get(sym, []))
            eff_pos = pos + pending

            orders = self._make(sym, best_bid, best_ask, eff_pos, spread)
            result.setdefault(sym, []).extend(orders)

        return result, 0, self._save()