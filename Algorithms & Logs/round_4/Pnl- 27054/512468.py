import math
from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict, Optional, Tuple

VFE, HP = "VELVETFRUIT_EXTRACT", "HYDROGEL_PACK"
VFE_LIMIT, HP_LIMIT, OPT_LIMIT = 200, 200, 300

VEV_STRIKES = {
    "VEV_4000": (4000, 0.220), "VEV_4500": (4500, 0.225),
    "VEV_5000": (5000, 0.218), "VEV_5100": (5100, 0.222),
    "VEV_5200": (5200, 0.228), "VEV_5300": (5300, 0.235),
    "VEV_5400": (5400, 0.215), "VEV_5500": (5500, 0.230),
}

_SQRT2_INV = 0.7071067811865476
_TTE = 4.0 / 365.0

def _norm_cdf(x: float) -> float: return 0.5 * (1.0 + math.erf(x * _SQRT2_INV))

def _bs_call(S: float, K: float, T: float, sigma: float) -> float:
    if T <= 1e-8 or sigma <= 0: return max(S - K, 0.0)
    sq_T = math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma**2 * T) / (sigma * sq_T)
    return S * _norm_cdf(d1) - K * _norm_cdf(d1 - sigma * sq_T)

def _implied_vol(price: float, S: float, K: float, T: float) -> float:
    if price <= 0.1 or T <= 0 or S <= K:
        return 0.23
    sigma = 0.23
    for _ in range(25):
        p = _bs_call(S, K, T, sigma)
        if p < price:
            sigma += 0.015
        else:
            sigma -= 0.015
        sigma = max(0.05, min(sigma, 1.0))
    return sigma

def _bs_delta(S: float, K: float, T: float, sigma: float) -> float:
    if T <= 1e-8 or sigma <= 0: return 1.0 if S > K else 0.0
    sq_T = math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma**2 * T) / (sigma * sq_T)
    return _norm_cdf(d1)

class Trader:
    def __init__(self):
        self.vfe_ema = self.hp_ema = None
        self.VFE_ALPHA, self.HP_ALPHA = 0.035, 0.020
        self.current_day = 0
        self.freeze_until_vfe = 0
        self.hp_predator_fade = 0.0
        self.fade_decay = 0.8
        self.vfe_chunk = 40
        self.hp_chunk = 100
        self.mark14_buying = False
        
    def _mid_price(self, depth: OrderDepth) -> Optional[float]:
        if depth.buy_orders and depth.sell_orders:
            return (max(depth.buy_orders.keys()) + min(depth.sell_orders.keys())) / 2.0
        return None
    
    def _calculate_options_delta(self, state: TradingState, vfe_mid: float) -> float:
        total = 0.0
        for symbol, (K, sigma) in VEV_STRIKES.items():
            pos = state.position.get(symbol, 0)
            if pos == 0: continue
            od = state.order_depths.get(symbol)
            if not od or not od.buy_orders or not od.sell_orders: continue
            mkt_mid = self._mid_price(od)
            if mkt_mid and mkt_mid > 1:
                sigma = _implied_vol(mkt_mid, vfe_mid, K, _TTE)
            delta = _bs_delta(vfe_mid, K, _TTE, sigma)
            total += pos * delta
        return total
    
    def _decode_state(self, trader_data: str):
        if not trader_data: return
        try:
            parts = trader_data.split("|")
            self.vfe_ema, self.hp_ema = float(parts[0]), float(parts[1])
        except: pass

    def _encode_state(self) -> str:
        return f"{self.vfe_ema:.4f}|{self.hp_ema:.4f}" if self.vfe_ema else ""

    def run(self, state: TradingState):
        self._decode_state(state.traderData)
        result: Dict[str, List[Order]] = {}
        if state.timestamp < 100: self.current_day += 1
        T_rem = max((3.0 - self.current_day + (1_000_000 - state.timestamp)/1_000_000) / 365.0, 1e-5)

        vfe_trades = state.market_trades.get(VFE, [])
        buy_act = sell_act = 0
        for t in vfe_trades:
            if "Mark 14" in str(t.buyer): buy_act += t.quantity
            if "Mark 14" in str(t.seller): sell_act += t.quantity
        self.mark14_buying = buy_act > sell_act
        
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

        options_delta = 0.0
        if vfe_mid:
            options_delta = self._calculate_options_delta(state, vfe_mid)

        if vfe_mid:
            for symbol, (K, base_sigma) in VEV_STRIKES.items():
                if symbol not in state.order_depths: continue
                od, pos = state.order_depths[symbol], state.position.get(symbol, 0)
                
                mkt_mid = self._mid_price(od)
                if mkt_mid and mkt_mid > 1:
                    sigma = _implied_vol(mkt_mid, vfe_mid, K, _TTE)
                else:
                    sigma = base_sigma
                
                theo = _bs_call(vfe_mid, K, T_rem, sigma)
                buy_cap, sell_cap = OPT_LIMIT - pos, OPT_LIMIT + pos
                orders = []

                liquid = symbol in ["VEV_5300", "VEV_5400", "VEV_5500"]
                edge = 0.6 if liquid else 0.8
                
                if od.sell_orders and buy_cap > 0:
                    for price in sorted(od.sell_orders.keys()):
                        if price > theo - edge: break
                        qty = min(abs(od.sell_orders[price]), buy_cap)
                        orders.append(Order(symbol, price, qty))
                        buy_cap -= qty
                        if buy_cap <= 0: break
                
                if od.buy_orders and sell_cap > 0:
                    for price in sorted(od.buy_orders.keys(), reverse=True):
                        if price < theo + edge: break
                        qty = min(od.buy_orders[price], sell_cap)
                        orders.append(Order(symbol, price, -qty))
                        sell_cap -= qty
                        if sell_cap <= 0: break

                maker_size = 200 if liquid else 100
                skew = (pos / float(OPT_LIMIT)) * 0.5
                if buy_cap > 0: orders.append(Order(symbol, int(math.floor(theo - 0.9 - skew)), min(buy_cap, maker_size)))
                if sell_cap > 0: orders.append(Order(symbol, int(math.ceil(theo + 0.9 - skew)), -min(sell_cap, maker_size)))
                result[symbol] = orders

        if vfe_mid and self.vfe_ema and state.timestamp >= self.freeze_until_vfe:
            od, pos = state.order_depths[VFE], state.position.get(VFE, 0)
            buy_cap = VFE_LIMIT - pos
            sell_cap = VFE_LIMIT + pos
            
            pos_frac = pos / float(VFE_LIMIT)
            inv_skew = -(pos/float(VFE_LIMIT))**3 * 5.0 - (pos_frac * 2.5)
            fair_v = self.vfe_ema + inv_skew
            
            if options_delta > 0.15:
                fair_v -= 1.0 * min(options_delta, 0.6)
            
            if self.mark14_buying and buy_act > 0:
                vfe_bid = int(math.floor(fair_v - 0.5))
                vfe_ask = int(math.ceil(fair_v + 20.0))
            else:
                t = 1.2 + 4.0 * pos_frac**2
                vfe_bid = int(math.floor(fair_v - t))
                vfe_ask = int(math.ceil(fair_v + t))
            
            orders = []
            
            if od.sell_orders and buy_cap > 0:
                for price in sorted(od.sell_orders.keys()):
                    if price > vfe_bid: break
                    qty = min(abs(od.sell_orders[price]), buy_cap, self.vfe_chunk)
                    if qty > 0:
                        orders.append(Order(VFE, price, qty))
                        buy_cap -= qty
            
            if od.buy_orders and sell_cap > 0:
                for price in sorted(od.buy_orders.keys(), reverse=True):
                    if price < vfe_ask: break
                    qty = min(od.buy_orders[price], sell_cap, self.vfe_chunk)
                    if qty > 0:
                        orders.append(Order(VFE, price, -qty))
                        sell_cap -= qty
            
            if buy_cap > 0:
                orders.append(Order(VFE, vfe_bid, min(buy_cap, self.vfe_chunk)))
            if sell_cap > 0:
                orders.append(Order(VFE, vfe_ask, -min(sell_cap, self.vfe_chunk)))
            
            result[VFE] = orders

        if hp_mid and self.hp_ema:
            od, pos = state.order_depths[HP], state.position.get(HP, 0)
            buy_cap = HP_LIMIT - pos
            sell_cap = HP_LIMIT + pos
            
            pos_frac = pos / float(HP_LIMIT)
            inv_skew = -(pos/float(HP_LIMIT))**3 * 12.0 - (pos_frac * 2.5)
            fair_v = self.hp_ema + inv_skew + self.hp_predator_fade
            t = 2.5 + 4.0 * pos_frac**2
            
            hp_bid = int(math.floor(fair_v - t))
            hp_ask = int(math.ceil(fair_v + t))
            
            orders = []
            
            if od.sell_orders and buy_cap > 0:
                for price in sorted(od.sell_orders.keys()):
                    if price > hp_bid: break
                    qty = min(abs(od.sell_orders[price]), buy_cap, self.hp_chunk)
                    if qty > 0:
                        orders.append(Order(HP, price, qty))
                        buy_cap -= qty
            
            if od.buy_orders and sell_cap > 0:
                for price in sorted(od.buy_orders.keys(), reverse=True):
                    if price < hp_ask: break
                    qty = min(od.buy_orders[price], sell_cap, self.hp_chunk)
                    if qty > 0:
                        orders.append(Order(HP, price, -qty))
                        sell_cap -= qty
            
            if buy_cap > 0:
                orders.append(Order(HP, hp_bid, min(buy_cap, self.hp_chunk)))
            if sell_cap > 0:
                orders.append(Order(HP, hp_ask, -min(sell_cap, self.hp_chunk)))
            
            result[HP] = orders

        return result, 1, self._encode_state()