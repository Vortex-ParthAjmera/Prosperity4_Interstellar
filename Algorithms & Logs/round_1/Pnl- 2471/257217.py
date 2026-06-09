from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List
import json

class Trader:
    def run(self, state: TradingState):
        res: Dict[str, List[Order]] = {}
        emas = {}
        
        try:
            if state.traderData:
                emas = json.loads(state.traderData)
        except:
            pass

        for sym, od in state.order_depths.items():
            pos = state.position.get(sym, 0)
            orders: List[Order] = []
            
            limit = 50
            
            bids = od.buy_orders
            asks = od.sell_orders
            
            if not bids or not asks:
                continue
                
            bb = max(bids.keys())
            ba = min(asks.keys())
            bv = bids[bb]
            av = abs(asks[ba])
            
            micro_price = (bb * av + ba * bv) / (bv + av)
            
            alpha = 0.15 
            if sym not in emas:
                emas[sym] = micro_price
            else:
                emas[sym] = emas[sym] * (1 - alpha) + micro_price * alpha
                
            fair = emas[sym]
            
            half_spread = 1.0 
            skew_factor = 0.25
            
            if sym == "INTARIAN_PEPPER_ROOT":
                half_spread = 1.5
                skew_factor = 0.35
                
            skew = pos * skew_factor
            
            my_bid = int(round(fair - half_spread - skew))
            my_ask = int(round(fair + half_spread - skew))
            
            my_bid = min(my_bid, int(fair) - 1)
            my_ask = max(my_ask, int(fair) + 1)
            
            bid_vol = limit - pos
            ask_vol = -limit - pos
            
            if ba < fair - 0.5 and bid_vol > 0:
                take = min(av, bid_vol)
                orders.append(Order(sym, ba, take))
                bid_vol -= take
                
            if bb > fair + 0.5 and ask_vol < 0:
                take = min(bv, abs(ask_vol))
                orders.append(Order(sym, bb, -take))
                ask_vol += take
                
            if bid_vol > 0:
                orders.append(Order(sym, my_bid, bid_vol))
            if ask_vol < 0:
                orders.append(Order(sym, my_ask, ask_vol))
                
            if orders:
                res[sym] = orders
                
        return res, 0, json.dumps(emas)