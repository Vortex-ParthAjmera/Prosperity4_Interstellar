import math
from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict, Optional, Tuple

VFE, HP = "VELVETFRUIT_EXTRACT", "HYDROGEL_PACK"
VFE_LIMIT, HP_LIMIT, OPT_LIMIT = 200, 200, 300

# V44: Restored 5000 for "Free Money" sweeps
VEV_STRIKES = {
    "VEV_5000": (5000, 0.218), "VEV_5100": (5100, 0.222), 
    "VEV_5200": (5200, 0.228), "VEV_5300": (5300, 0.235), 
    "VEV_5400": (5400, 0.215), "VEV_5500": (5500, 0.230),
}

_SQRT2_INV = 0.7071067811865476
def _norm_cdf(x: float) -> float: return 0.5 * (1.0 + math.erf(x * _SQRT2_INV))

def _bs_call(S: float, K: float, T: float, sigma: float) -> float:
    if T <= 1e-8 or sigma <= 0: return max(S - K, 0.0)
    sq_T = math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma**2 * T) / (sigma * sq_T)
    return S * _norm_cdf(d1) - K * _norm_cdf(d1 - sigma * sq_T)

class Trader:
    def __init__(self):
        self.vfe_ema = self.hp_ema = None
        self.VFE_ALPHA, self.HP_ALPHA = 0.035, 0.035 # Accelerated HP EMA
        self.current_day = 0
        self.freeze_until_vfe = 0
        self.hp_predator_fade = 0.0
        self.fade_decay = 0.8

    def _mid_price(self, depth: OrderDepth) -> Optional[float]:
        if depth.buy_orders and depth.sell_orders:
            return (max(depth.buy_orders.keys()) + min(depth.sell_orders.keys())) / 2.0
        return None

    def _decode_state(self, trader_data: str):
        if not trader_data: return
        try:
            parts = trader_data.split("|")
            if len(parts) >= 2:
                self.vfe_ema, self.hp_ema = float(parts[0]), float(parts[1])
        except: pass

    def _encode_state(self) -> str:
        return f"{self.vfe_ema:.4f}|{self.hp_ema:.4f}" if self.vfe_ema else ""

    def run(self, state: TradingState):
        self._decode_state(state.traderData)
        result: Dict[str, List[Order]] = {}
        if state.timestamp < 100: self.current_day += 1
        T_rem = max((3.0 - self.current_day + (1_000_000 - state.timestamp)/1_000_000) / 365.0, 1e-5)

        # ─── DEFENSIVE SHIELDS ────────────────────────────────────────────────
        vfe_trades = state.market_trades.get(VFE, [])
        if any(t.buyer in ["Mark 14", "Mark 01"] or t.seller in ["Mark 14", "Mark 01"] for t in vfe_trades):
            self.freeze_until_vfe = state.timestamp + 300

        self.hp_predator_fade *= self.fade_decay
        hp_trades = state.market_trades.get(HP, [])
        for t in hp_trades:
            if t.buyer in ["Mark 14", "Mark 01"]: self.hp_predator_fade += 5.0
            if t.seller in ["Mark 14", "Mark 01"]: self.hp_predator_fade -= 5.0
        self.hp_predator_fade = max(-10.0, min(10.0, self.hp_predator_fade))

        vfe_mid = self._mid_price(state.order_depths.get(VFE))
        hp_mid = self._mid_price(state.order_depths.get(HP))
        if vfe_mid: self.vfe_ema = vfe_mid if not self.vfe_ema else self.VFE_ALPHA * vfe_mid + (1-self.VFE_ALPHA) * self.vfe_ema
        if hp_mid: self.hp_ema = hp_mid if not self.hp_ema else self.HP_ALPHA * hp_mid + (1-self.HP_ALPHA) * self.hp_ema

        # ─── 1. OPTIONS (Vampire Engine) ──────────────────────────────────────
        if vfe_mid:
            for symbol, (K, sigma) in VEV_STRIKES.items():
                if symbol not in state.order_depths: continue
                od, pos = state.order_depths[symbol], state.position.get(symbol, 0)
                theo = _bs_call(vfe_mid, K, T_rem, sigma)
                buy_cap, sell_cap = OPT_LIMIT - pos, OPT_LIMIT + pos
                orders = []

                # V44 TAKER: Tightened edge for ITM to "Vampire" the underlying lag
                if symbol in ["VEV_5100", "VEV_5200"]:
                    t_edge = 0.25 # MICRO-SNIPE
                    m_size = 120
                elif symbol == "VEV_5000":
                    t_edge = 3.0
                    m_size = 20
                else:
                    t_edge = 0.5
                    m_size = 250

                if od.sell_orders and buy_cap > 0 and min(od.sell_orders.keys()) < theo - t_edge:
                    orders.append(Order(symbol, min(od.sell_orders.keys()), buy_cap))
                    buy_cap = 0
                if od.buy_orders and sell_cap > 0 and max(od.buy_orders.keys()) > theo + t_edge:
                    orders.append(Order(symbol, max(od.buy_orders.keys()), -sell_cap))
                    sell_cap = 0

                # V44 MAKER: Slightly tighter edge to jump the queue
                m_edge = 0.8
                skew = (pos / float(OPT_LIMIT)) * 0.8
                if buy_cap > 0: orders.append(Order(symbol, int(math.floor(theo - m_edge - skew)), min(buy_cap, m_size)))
                if sell_cap > 0: orders.append(Order(symbol, int(math.ceil(theo + m_edge - skew)), -min(sell_cap, m_size)))
                result[symbol] = orders

        # ─── 2. VFE & HP (Optimized Shields) ──────────────────────────────────
        if vfe_mid and self.vfe_ema and state.timestamp >= self.freeze_until_vfe:
            od, pos = state.order_depths[VFE], state.position.get(VFE, 0)
            vfe_pos_f = pos / 200.0
            inv_skew = -(vfe_pos_f**3) * 4.5 - (vfe_pos_f * 2.2) # FRIEND BASELINE
            fair_v = self.vfe_ema + inv_skew
            t = 1.0 + 3.5 * (vfe_pos_f**2)
            result[VFE] = [Order(VFE, int(math.floor(fair_v - t)), 200 - pos),
                           Order(VFE, int(math.ceil(fair_v + t)), -(200 + pos))]

        if hp_mid and self.hp_ema:
            od, pos = state.order_depths[HP], state.position.get(HP, 0)
            hp_pos_f = pos / 200.0
            inv_skew = -(hp_pos_f**3) * 12.0 - (hp_pos_f * 2.5)
            fair_v = self.hp_ema + inv_skew + self.hp_predator_fade
            t = 2.0 + 4.0 * (hp_pos_f**2)
            result[HP] = [Order(HP, int(math.floor(fair_v - t)), 200 - pos),
                          Order(HP, int(math.ceil(fair_v + t)), -(200 + pos))]

        return result, 1, self._encode_state()