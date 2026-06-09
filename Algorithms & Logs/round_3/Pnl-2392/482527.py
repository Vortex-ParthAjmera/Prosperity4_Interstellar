from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List
import math
import json

VFE = "VELVETFRUIT_EXTRACT"
HP = "HYDROGEL_PACK"
VOUCHERS = ["VEV_4000", "VEV_4500", "VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500", "VEV_6000", "VEV_6500"]
STRIKES = {"VEV_4000": 4000, "VEV_4500": 4500, "VEV_5000": 5000, "VEV_5100": 5100, "VEV_5200": 5200, "VEV_5300": 5300, "VEV_5400": 5400, "VEV_5500": 5500, "VEV_6000": 6000, "VEV_6500": 6500}
POSITION_LIMITS = {VFE: 200, HP: 200}
POSITION_LIMITS.update({v: 300 for v in VOUCHERS})
TTE_DAYS = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0}

class NeuralOptionModel:
    def __init__(self):
        self._ncdf = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
        self._train_iv()
    
    def _ncdf(self, x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    
    def black_scholes_call(self, S, K, T, sigma):
        if T <= 1e-9 or sigma <= 1e-9:
            return max(S - K, 0.0)
        try:
            sqrtT = math.sqrt(T)
            d1 = (math.log(S / K) + 0.5 * sigma * sigma * T) / (sigma * sqrtT)
            d2 = d1 - sigma * sqrtT
            return S * self._ncdf(d1) - K * self._ncdf(d2)
        except:
            return max(S - K, 0.0)
    
    def implied_vol(self, market_price, S, K, T):
        if market_price <= 0 or T <= 0 or S <= 0 or K <= 0:
            return 0.25
        intrinsic = max(S - K, 0.0)
        if market_price <= intrinsic:
            return 0.01
        sigma = 0.25
        for _ in range(30):
            bs = self.black_scholes_call(S, K, T, sigma)
            diff = bs - market_price
            if abs(diff) < 0.1:
                break
            vega = S * math.sqrt(T) * self._ncdf((math.log(S / K) + 0.5 * sigma * sigma * T) / (sigma * math.sqrt(T))) / math.sqrt(2.0 * math.pi)
            if abs(vega) > 1e-8:
                sigma -= diff / vega
            sigma = max(0.01, min(sigma, 1.5))
        return max(0.01, min(sigma, 1.5))
    
    def _train_iv(self):
        training_data = [
            (5250, 4000, 0.02, 1250), (5250, 4500, 0.02, 750), (5250, 5000, 0.02, 255),
            (5250, 5100, 0.02, 170), (5250, 5200, 0.02, 100), (5250, 5300, 0.02, 52),
            (5250, 5400, 0.02, 23), (5250, 5500, 0.02, 8), (5200, 5000, 0.024, 265),
            (5200, 5100, 0.024, 180), (5300, 5200, 0.016, 110), (5300, 5300, 0.016, 80),
        ]
        self.iv_history = []
        for S, K, T, price in training_data:
            try:
                iv = self.implied_vol(price, S, K, T)
                self.iv_history.append((K, iv))
            except:
                pass
    
    def analyze_iv_surface(self, S, vouchers_data):
        if not vouchers_data:
            return {}
        ivs = {}
        for vou, (K, price, bb, ba) in vouchers_data.items():
            if price > 0 and K > 0:
                iv = self.implied_vol(price, S, K, 0.02)
                ivs[vou] = iv
        if not ivs:
            return {}
        avg_iv = sum(ivs.values()) / len(ivs) if ivs else 0.25
        return {"ivs": ivs, "avg_iv": avg_iv}
    
    def predict_fair(self, S, K, T, market_price, bb, ba, vou_iv=None):
        K = float(K)
        if K <= 0 or S <= 0:
            return market_price
        intrinsic = max(S - K, 0)
        if vou_iv:
            iv = vou_iv
        else:
            iv = self.implied_vol(market_price, S, K, T)
        sigma = max(iv, 0.08)
        fair = self.black_scholes_call(S, K, T, sigma)
        moneyness = S / K
        if moneyness > 1.03:
            fair = max(fair, market_price * 0.92)
        elif moneyness < 0.97:
            fair = min(fair, market_price * 1.08)
        spread = ba - bb if ba and bb else 0
        if spread < 1.5 and spread > 0:
            fair = fair - 0.2
        return max(intrinsic, fair)

class TraderState:
    __slots__ = ('iteration', 'day', 'vfe_price', 'hg_price', 'vfe_count', 'hg_count')
    
    def __init__(self):
        self.iteration = 0
        self.day = 1
        self.vfe_price = 5250.0
        self.hg_price = 10000.0
        self.vfe_count = 0
        self.hg_count = 0
    
    def to_json(self):
        return json.dumps({
            'i': self.iteration, 'd': self.day, 'v': self.vfe_price,
            'h': self.hg_price, 'vc': self.vfe_count, 'hc': self.hg_count
        }, separators=(',', ':'))
    
    @staticmethod
    def from_json(data):
        st = TraderState()
        try:
            d = json.loads(data)
            st.iteration = d.get('i', 0)
            st.day = d.get('d', 1)
            st.vfe_price = d.get('v', 5250.0)
            st.hg_price = d.get('h', 10000.0)
            st.vfe_count = d.get('vc', 0)
            st.hg_count = d.get('hc', 0)
        except:
            pass
        return st

def get_best_bid_ask(order_depth):
    bb = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
    ba = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None
    bv = order_depth.buy_orders[bb] if bb else 0
    av = order_depth.sell_orders[ba] if ba else 0
    return bb, ba, abs(bv), abs(av)

def calc_buy_q(symbol, pos, vol):
    limit = POSITION_LIMITS.get(symbol, 50)
    room = limit - pos
    return min(vol, room) if room > 0 else 0

def calc_sell_q(symbol, pos, vol):
    limit = POSITION_LIMITS.get(symbol, 50)
    room = limit + pos
    return min(vol, room) if room > 0 else 0

class Trader:
    def __init__(self):
        self.nn = NeuralOptionModel()
    
    def bid(self):
        return 15
    
    def run(self, state):
        try:
            if state.traderData and state.traderData.startswith('{'):
                st = TraderState.from_json(state.traderData)
            else:
                st = TraderState()
        except:
            st = TraderState()
        st.iteration += 1
        if state.timestamp > 0 and state.timestamp % 100000 == 0:
            st.day = min(st.day + 1, 7)
        result = {}
        conversions = 0
        TTE = TTE_DAYS.get(st.day, 5) / 252.0
        
        vfe_od = state.order_depths.get(VFE)
        if vfe_od:
            bb, ba, bv, av = get_best_bid_ask(vfe_od)
            if bb and ba:
                mid = (bb + ba) / 2.0
                if st.vfe_count == 0:
                    st.vfe_price = mid
                else:
                    alpha = 2.0 / (st.vfe_count + 1)
                    st.vfe_price = alpha * mid + (1 - alpha) * st.vfe_price
                st.vfe_count += 1
                vfe_pos = state.position.get(VFE, 0)
                orders = []
                thresh = 3.5
                if ba < st.vfe_price - thresh:
                    q = calc_buy_q(VFE, vfe_pos, min(av, 20))
                    if q > 0:
                        orders.append(Order(VFE, int(ba), q))
                if bb > st.vfe_price + thresh:
                    q = calc_sell_q(VFE, vfe_pos, min(bv, 20))
                    if q > 0:
                        orders.append(Order(VFE, int(bb), -q))
                if vfe_pos > 35 and mid > st.vfe_price + thresh * 2:
                    orders.append(Order(VFE, int(bb), -vfe_pos))
                elif vfe_pos < -35 and mid < st.vfe_price - thresh * 2:
                    orders.append(Order(VFE, int(ba), -vfe_pos))
                result[VFE] = orders
        
        hg_od = state.order_depths.get(HP)
        if hg_od:
            bb, ba, bv, av = get_best_bid_ask(hg_od)
            if bb and ba:
                mid = (bb + ba) / 2.0
                if st.hg_count == 0:
                    st.hg_price = mid
                else:
                    alpha = 1.5 / (st.hg_count + 1)
                    st.hg_price = alpha * mid + (1 - alpha) * st.hg_price
                st.hg_count += 1
                hg_pos = state.position.get(HP, 0)
                orders = []
                entry_thresh = 35
                exit_thresh = 8
                dev = mid - st.hg_price
                if dev < -entry_thresh:
                    q = calc_buy_q(HP, hg_pos, min(av, 20))
                    if q > 0:
                        orders.append(Order(HP, int(ba), q))
                elif dev > entry_thresh:
                    q = calc_sell_q(HP, hg_pos, min(bv, 20))
                    if q > 0:
                        orders.append(Order(HP, int(bb), -q))
                elif abs(dev) < exit_thresh:
                    if hg_pos > 0:
                        orders.append(Order(HP, int(bb), -hg_pos))
                    elif hg_pos < 0:
                        orders.append(Order(HP, int(ba), -hg_pos))
                result[HP] = orders
        
        S = st.vfe_price if st.vfe_price > 0 else 5250.0
        
        vouchers_data = {}
        for vou in VOUCHERS:
            od = state.order_depths.get(vou)
            if od:
                bb, ba, bv, av = get_best_bid_ask(od)
                if bb and ba:
                    mid = (bb + ba) / 2.0
                    K = STRIKES.get(vou, 5000)
                    vouchers_data[vou] = (K, mid, bb, ba)
        
        iv_analysis = self.nn.analyze_iv_surface(S, vouchers_data)
        avg_iv = iv_analysis.get("avg_iv", 0.25)
        
        active_vouchers = VOUCHERS
        for vou in active_vouchers:
            od = state.order_depths.get(vou)
            if not od:
                continue
            bb, ba, bv, av = get_best_bid_ask(od)
            if not bb:
                continue
            K = STRIKES.get(vou, 5000)
            mid = (bb + ba) / 2.0 if ba else bb
            if av < 1:
                continue
            ivs = iv_analysis.get("ivs", {})
            vou_iv = ivs.get(vou, 0.25)
            pos = state.position.get(vou, 0)
            fair = self.nn.predict_fair(S, K, TTE, mid, bb, ba, vou_iv)
            orders = []
            deviation = abs(vou_iv - avg_iv) / avg_iv if avg_iv > 0 else 0
            edge = 0.2 if deviation > 0.12 else 0.4
            if ba < fair - edge:
                q = calc_buy_q(vou, pos, min(av, 60))
                if q > 0:
                    orders.append(Order(vou, int(ba), q))
            if bb > fair + edge:
                q = calc_sell_q(vou, pos, min(bv, 60))
                if q > 0:
                    orders.append(Order(vou, int(bb), -q))
            if pos > 0 and TTE < 0.015:
                orders.append(Order(vou, int(bb), -pos))
            elif pos < 0 and ba < fair - 0.6:
                cover_q = calc_buy_q(vou, pos, min(av, abs(pos)))
                if cover_q > 0:
                    orders.append(Order(vou, int(ba), cover_q))
            if orders:
                result[vou] = orders
        
        if st.day >= 6:
            for vou in VOUCHERS:
                pos = state.position.get(vou, 0)
                if pos != 0:
                    od = state.order_depths.get(vou)
                    if od:
                        bb, ba, _, _ = get_best_bid_ask(od)
                        if bb and pos > 0:
                            result[vou] = [Order(vou, int(bb), -pos)]
                        elif ba and pos < 0:
                            result[vou] = [Order(vou, int(ba), -pos)]
        return result, conversions, st.to_json()