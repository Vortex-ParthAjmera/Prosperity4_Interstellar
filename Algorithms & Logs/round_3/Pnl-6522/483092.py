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
        self.hidden_dim = 32
        self.learning_rate = 0.001
        import random
        random.seed(42)
        self.W1 = [[(random.random() - 0.5) * 0.1 for _ in range(self.hidden_dim)] for _ in range(8)]
        self.b1 = [0.0] * self.hidden_dim
        self.W2 = [[(random.random() - 0.5) * 0.1] for _ in range(self.hidden_dim)]
        self.b2 = [0.0]
        self._train_from_history()
    
    def _relu(self, x):
        return max(0.0, x)
    
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
        if market_price <= 0 or T <= 0:
            return 0.25
        sigma = 0.25
        for _ in range(25):
            bs = self.black_scholes_call(S, K, T, sigma)
            diff = bs - market_price
            if abs(diff) < 0.1:
                break
            vega = S * math.sqrt(T) * self._ncdf((math.log(S / K) + 0.5 * sigma * sigma * T) / (sigma * math.sqrt(T))) / math.sqrt(2.0 * math.pi)
            if abs(vega) > 1e-8:
                sigma -= diff / vega
            sigma = max(0.01, min(sigma, 1.5))
        return max(0.01, sigma)
    
    def _train_from_history(self):
        training_data = [
            (5250, 5200, 0.02, 96), (5250, 5300, 0.02, 45), (5250, 5400, 0.02, 14),
            (5250, 5500, 0.02, 5), (5200, 5000, 0.024, 260), (5200, 5100, 0.024, 170),
            (5300, 5200, 0.016, 100), (5300, 5300, 0.016, 65), (5250, 5000, 0.02, 253),
            (5250, 5100, 0.02, 165), (5250, 5200, 0.02, 97), (5250, 5300, 0.02, 48),
        ]
        for S, K, T, price in training_data:
            try:
                _ = self.implied_vol(price, S, K, T)
            except:
                pass
    
    def predict_fair(self, S, K, T, market_price, bb, ba, day, position):
        moneyness = S / K if K > 0 else 1.0
        tte_norm = T * 12.0
        spread = (ba - bb) / market_price if market_price > 0 else 0
        
        iv = self.implied_vol(market_price, S, K, T)
        fair = self.black_scholes_call(S, K, T, iv)
        
        if moneyness > 1.05:
            fair = max(fair, market_price * 0.92)
        elif moneyness < 0.95:
            fair = min(fair, market_price * 1.08)
        
        return max(0.0, fair)

class TraderState:
    __slots__ = ('iteration', 'day', 'vfe_price', 'hg_price', 've_price', 'vfe_acc', 'hg_acc', 'vfe_count', 'hg_count')
    
    def __init__(self):
        self.iteration = 0
        self.day = 1
        self.vfe_price = 5250.0
        self.hg_price = 10000.0
        self.ve_price = 5250.0
        self.vfe_acc = 0.0
        self.hg_acc = 0.0
        self.vfe_count = 0
        self.hg_count = 0
    
    def to_json(self):
        return json.dumps({
            'i': self.iteration, 'd': self.day, 'v': self.vfe_price,
            'h': self.hg_price, 've': self.ve_price,
            'vc': self.vfe_count, 'hc': self.hg_count
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
            st.ve_price = d.get('ve', 5250.0)
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
                st.ve_price = mid
                
                vfe_pos = state.position.get(VFE, 0)
                orders = []
                thresh = 4.0
                
                if ba < st.vfe_price - thresh:
                    q = calc_buy_q(VFE, vfe_pos, min(av, 15))
                    if q > 0:
                        orders.append(Order(VFE, int(ba), q))
                
                if bb > st.vfe_price + thresh:
                    q = calc_sell_q(VFE, vfe_pos, min(bv, 15))
                    if q > 0:
                        orders.append(Order(VFE, int(bb), -q))
                
                if vfe_pos > 0 and mid > st.vfe_price + thresh * 2:
                    orders.append(Order(VFE, int(bb), -vfe_pos))
                elif vfe_pos < 0 and mid < st.vfe_price - thresh * 2:
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
                entry_thresh = 40
                exit_thresh = 10
                dev = mid - st.hg_price
                
                if dev < -entry_thresh:
                    q = calc_buy_q(HP, hg_pos, min(av, 15))
                    if q > 0:
                        orders.append(Order(HP, int(ba), q))
                elif dev > entry_thresh:
                    q = calc_sell_q(HP, hg_pos, min(bv, 15))
                    if q > 0:
                        orders.append(Order(HP, int(bb), -q))
                elif abs(dev) < exit_thresh:
                    if hg_pos > 0:
                        orders.append(Order(HP, int(bb), -hg_pos))
                    elif hg_pos < 0:
                        orders.append(Order(HP, int(ba), -hg_pos))
                
                result[HP] = orders
        
        S = st.ve_price if st.ve_price > 0 else 5250.0
        
        for vou in VOUCHERS:
            od = state.order_depths.get(vou)
            if not od:
                continue
            
            bb, ba, bv, av = get_best_bid_ask(od)
            if not bb:
                continue
            
            K = STRIKES.get(vou, 5000)
            mid = (bb + ba) / 2.0 if ba else bb
            
            pos = state.position.get(vou, 0)
            fair = self.nn.predict_fair(S, K, TTE, mid, bb, ba, st.day, pos)
            
            orders = []
            
            if ba < fair - 0.5:
                q = calc_buy_q(vou, pos, min(av, 25))
                if q > 0:
                    orders.append(Order(vou, int(ba), q))
            
            if bb > fair + 0.5:
                q = calc_sell_q(vou, pos, min(bv, 25))
                if q > 0:
                    orders.append(Order(vou, int(bb), -q))
            
            if pos > 0 and TTE < 0.02:
                orders.append(Order(vou, int(bb), -pos))
            elif pos < 0 and ba < fair - 1.0:
                cover_q = calc_buy_q(vou, pos, min(av, abs(pos)))
                if cover_q > 0:
                    orders.append(Order(vou, int(ba), cover_q))
            
            if orders:
                result[vou] = orders
        
        return result, conversions, st.to_json()