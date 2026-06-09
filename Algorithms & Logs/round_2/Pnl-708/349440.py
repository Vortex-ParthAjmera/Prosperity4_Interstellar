from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict

# Configuration
PEPPER = "INTARIAN_PEPPER_ROOT"
OSMIUM = "ASH_COATED_OSMIUM"

# Limits 
PEPPER_LIMIT = 350
OSMIUM_LIMIT = 50

# Optimal Fair Values
OSMIUM_FAIR = 10001 

class Trader:
    def bid(self) -> int:
        """Required for Round 2 bidding mechanism"""
        return 0

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}

        # --- PEPPER LOGIC ---
        if PEPPER in state.order_depths:
            od = state.order_depths[PEPPER]
            pos = state.position.get(PEPPER, 0)
            orders = []
            
            if od.sell_orders and od.buy_orders:
                best_ask = min(od.sell_orders.keys())
                best_bid = max(od.buy_orders.keys())
                fair_pepper = (best_ask + best_bid) / 2
                
                # Buy Taker
                cap = PEPPER_LIMIT - pos
                for price in sorted(od.sell_orders.keys()):
                    if price < fair_pepper and cap > 0:
                        qty = min(abs(od.sell_orders[price]), cap)
                        orders.append(Order(PEPPER, int(price), int(qty)))
                        cap -= qty
                        pos += qty
                
                # Sell Taker
                cap = PEPPER_LIMIT + pos
                for price in sorted(od.buy_orders.keys(), reverse=True):
                    if price > fair_pepper and cap > 0:
                        qty = min(abs(od.buy_orders[price]), cap)
                        orders.append(Order(PEPPER, int(price), int(-qty)))
                        cap -= qty
                        pos -= qty

            if orders:
                result[PEPPER] = orders

        # --- OSMIUM LOGIC ---
        if OSMIUM in state.order_depths:
            od = state.order_depths[OSMIUM]
            pos = state.position.get(OSMIUM, 0)
            bc = OSMIUM_LIMIT - pos # buy capacity
            sc = OSMIUM_LIMIT + pos # sell capacity
            orders = []

            # Taker Orders based on OSMIUM_FAIR
            if od.sell_orders:
                best_ask = min(od.sell_orders.keys())
                if best_ask <= OSMIUM_FAIR - 2 and bc > 0:
                    qty = min(abs(od.sell_orders[best_ask]), bc, 8)
                    orders.append(Order(OSMIUM, int(best_ask), int(qty)))
                    bc -= qty
                    pos += qty

            if od.buy_orders:
                best_bid = max(od.buy_orders.keys())
                if best_bid >= OSMIUM_FAIR + 2 and sc > 0:
                    qty = min(od.buy_orders[best_bid], sc, 8)
                    orders.append(Order(OSMIUM, int(best_bid), int(-qty)))
                    sc -= qty
                    pos -= qty

            # Maker Orders (to capture the spread)
            if bc > 0:
                orders.append(Order(OSMIUM, int(OSMIUM_FAIR - 2), int(min(bc, 8))))
            if sc > 0:
                orders.append(Order(OSMIUM, int(OSMIUM_FAIR + 2), int(-min(sc, 8))))

            if orders:
                result[OSMIUM] = orders

        return result, 0, ""

# --- Local Testing Block ---
if __name__ == "__main__":
    from datamodel import TradingState, OrderDepth
    trader = Trader()
    mock_order_depths = {
        "ASH_COATED_OSMIUM": OrderDepth(buy_orders={9998: 10}, sell_orders={10005: 10}),
        "INTARIAN_PEPPER_ROOT": OrderDepth(buy_orders={10990: 10}, sell_orders={11010: 10})
    }
    state = TradingState(0, {}, mock_order_depths, {}, {}, {"ASH_COATED_OSMIUM": 0, "INTARIAN_PEPPER_ROOT": 0}, {})
    print(f"Bidding: {trader.bid()}")
    print(f"Results: {trader.run(state)}")