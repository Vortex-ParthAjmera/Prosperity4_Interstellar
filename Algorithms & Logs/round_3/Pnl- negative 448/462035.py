import math
from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict, Optional, Tuple

# ─── CONSTANTS & CONFIGURATION ────────────────────────────────────────────────
VFE = "VELVETFRUIT_EXTRACT"
HP  = "HYDROGEL_PACK"

VFE_LIMIT = 400  
HP_LIMIT  = 250  
OPT_LIMIT = 100  # Reduced slightly to prevent margin/position limit lockups

# Active Options Strikes
VEV_STRIKES = {
    "VEV_4000": 4000,
    "VEV_4500": 4500,
    "VEV_5000": 5000,
    "VEV_5100": 5100,
    "VEV_5200": 5200,
    "VEV_5300": 5300,
    "VEV_5400": 5400,
    "VEV_5500": 5500,
}

# ─── MATH & PRICING HELPERS ───────────────────────────────────────────────────
_SQRT2_INV = 0.7071067811865476

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x * _SQRT2_INV))

def _bs_call(S: float, K: float, T: float, sigma: float) -> float:
    """Returns Price of a European Call."""
    if T <= 1e-8 or sigma <= 0:
        return max(S - K, 0.0)
    
    d1 = (math.log(S / K) + 0.5 * sigma**2 * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * _norm_cdf(d1) - K * _norm_cdf(d2)

# ─── TRADER CLASS ─────────────────────────────────────────────────────────────
class Trader:
    def __init__(self):
        # State Persistence
        self.vfe_ema: Optional[float] = None
        self.hp_ema: Optional[float] = None
        self.current_day: int = 0
        
        # ── Tuned Parameters
        self.VFE_ALPHA = 0.035    # Slightly slower to weather trends better
        self.HP_ALPHA  = 0.015   
        
        self.VFE_THRESH_BASE = 2.0 
        self.HP_THRESH_BASE  = 3.0 
        
        self.OPT_IV = 0.235      
        self.DAYS_TOTAL = 3.0    
        
    def _mid_price(self, depth: OrderDepth) -> Optional[float]:
        if depth.buy_orders and depth.sell_orders:
            return (max(depth.buy_orders.keys()) + min(depth.sell_orders.keys())) / 2.0
        return None

    def _decode_state(self, trader_data: str):
        if not trader_data:
            return
        try:
            parts = trader_data.split("|")
            self.vfe_ema = float(parts[0]) if parts[0] else None
            self.hp_ema = float(parts[1]) if parts[1] else None
            if len(parts) > 2:
                self.current_day = int(parts[2])
        except Exception:
            pass

    def _encode_state(self) -> str:
        vfe_str = f"{self.vfe_ema:.4f}" if self.vfe_ema is not None else ""
        hp_str = f"{self.hp_ema:.4f}" if self.hp_ema is not None else ""
        return f"{vfe_str}|{hp_str}|{self.current_day}"

    def run(self, state: TradingState):
        self._decode_state(state.traderData)
        result: Dict[str, List[Order]] = {}
        
        # Update Day if timestamp wraps (assuming 1M ticks per day)
        if state.timestamp < 1000 and self.vfe_ema is not None:
             self.current_day += 1

        vfe_depth = state.order_depths.get(VFE)
        hp_depth = state.order_depths.get(HP)
        
        vfe_mid = self._mid_price(vfe_depth) if vfe_depth else None
        hp_mid = self._mid_price(hp_depth) if hp_depth else None

        if vfe_mid:
            self.vfe_ema = vfe_mid if self.vfe_ema is None else self.VFE_ALPHA * vfe_mid + (1 - self.VFE_ALPHA) * self.vfe_ema
        if hp_mid:
            self.hp_ema = hp_mid if self.hp_ema is None else self.HP_ALPHA * hp_mid + (1 - self.HP_ALPHA) * self.hp_ema

        # Accurate Time to Expiry Calculation
        ticks_per_day = 1_000_000
        days_remaining = (self.DAYS_TOTAL - 1 - self.current_day) + max((ticks_per_day - state.timestamp) / ticks_per_day, 0)
        T_rem = max(days_remaining / 365.0, 1e-5)

        # ─── 1. VELVETFRUIT_EXTRACT (Pure Mean Reversion) ─────────────────────
        # Decoupled from options delta to prevent trend-blowout.
        if vfe_mid and vfe_depth and self.vfe_ema:
            pos = state.position.get(VFE, 0)
            orders = []
            
            pos_frac = pos / VFE_LIMIT
            inv_skew = -pos_frac * 2.5 
            fair_value = self.vfe_ema + inv_skew
            
            # EXPONENTIAL THRESHOLD: Widens drastically if inventory gets too high (avoids catching falling knives)
            dynamic_thresh = self.VFE_THRESH_BASE + (8.0 * (pos_frac**2)) 
            our_bid = fair_value - dynamic_thresh
            our_ask = fair_value + dynamic_thresh
            
            buy_cap = VFE_LIMIT - pos
            sell_cap = VFE_LIMIT + pos

            if vfe_depth.sell_orders and buy_cap > 0:
                for price in sorted(vfe_depth.sell_orders.keys()):
                    if price > our_bid or buy_cap <= 0: break
                    qty = min(abs(vfe_depth.sell_orders[price]), buy_cap)
                    orders.append(Order(VFE, price, qty))
                    buy_cap -= qty

            if vfe_depth.buy_orders and sell_cap > 0:
                for price in sorted(vfe_depth.buy_orders.keys(), reverse=True):
                    if price < our_ask or sell_cap <= 0: break
                    qty = min(vfe_depth.buy_orders[price], sell_cap)
                    orders.append(Order(VFE, price, -qty))
                    sell_cap -= qty
                    
            my_bid_px = int(math.floor(our_bid))
            my_ask_px = int(math.ceil(our_ask))
            
            if buy_cap > 0:
                orders.append(Order(VFE, my_bid_px, buy_cap))
            if sell_cap > 0:
                orders.append(Order(VFE, my_ask_px, -sell_cap))

            if orders:
                result[VFE] = orders

        # ─── 2. HYDROGEL_PACK (Safer Mean Reversion) ──────────────────────────
        if hp_mid and hp_depth and self.hp_ema:
            pos = state.position.get(HP, 0)
            orders = []
            
            buy_cap = HP_LIMIT - pos
            sell_cap = HP_LIMIT + pos
            
            pos_frac = pos / HP_LIMIT
            inv_skew = -pos_frac * 3.0 
            
            fair_value = self.hp_ema + inv_skew
            
            # Exponential threshold logic applied here as well
            dynamic_thresh = self.HP_THRESH_BASE + (10.0 * (pos_frac**2))
            
            our_bid = fair_value - dynamic_thresh
            our_ask = fair_value + dynamic_thresh

            if hp_depth.sell_orders and buy_cap > 0:
                for price in sorted(hp_depth.sell_orders.keys()):
                    if price > our_bid or buy_cap <= 0: break
                    qty = min(abs(hp_depth.sell_orders[price]), buy_cap)
                    orders.append(Order(HP, price, qty))
                    buy_cap -= qty

            if hp_depth.buy_orders and sell_cap > 0:
                for price in sorted(hp_depth.buy_orders.keys(), reverse=True):
                    if price < our_ask or sell_cap <= 0: break
                    qty = min(hp_depth.buy_orders[price], sell_cap)
                    orders.append(Order(HP, price, -qty))
                    sell_cap -= qty

            my_bid_px = int(math.floor(our_bid))
            my_ask_px = int(math.ceil(our_ask))
            
            if buy_cap > 0:
                orders.append(Order(HP, my_bid_px, buy_cap))
            if sell_cap > 0:
                orders.append(Order(HP, my_ask_px, -sell_cap))

            if orders:
                result[HP] = orders

        # ─── 3. OPTIONS (Short Theta / Volatility Arbitrage) ──────────────────
        if vfe_mid:
            for symbol, K in VEV_STRIKES.items():
                if symbol not in state.order_depths:
                    continue
                
                od = state.order_depths[symbol]
                pos = state.position.get(symbol, 0)
                orders: List[Order] = []
                
                theo_price = _bs_call(vfe_mid, K, T_rem, self.OPT_IV)
                
                buy_cap = OPT_LIMIT - pos
                sell_cap = OPT_LIMIT + pos
                
                # Demand a larger edge to trade options, preventing bleeding from minor mispricings
                sell_edge_req = 1.0
                buy_edge_req  = 1.0
                
                if od.buy_orders and sell_cap > 0:
                    for price in sorted(od.buy_orders.keys(), reverse=True):
                        if price <= theo_price + sell_edge_req:
                            break
                        qty = min(od.buy_orders[price], sell_cap)
                        orders.append(Order(symbol, price, -qty))
                        sell_cap -= qty

                if od.sell_orders and buy_cap > 0:
                    for price in sorted(od.sell_orders.keys()):
                        if price >= theo_price - buy_edge_req:
                            break
                        qty = min(abs(od.sell_orders[price]), buy_cap)
                        orders.append(Order(symbol, price, qty))
                        buy_cap -= qty

                if orders:
                    result[symbol] = orders

        return result, 1, self._encode_state()