from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict
import json

PEPPER = "INTARIAN_PEPPER_ROOT"
OSMIUM = "ASH_COATED_OSMIUM"

PEPPER_LIMIT = 350
OSMIUM_LIMIT = 50


class Trader:

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}

        try:
            saved = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            saved = {}

        ema = float(saved.get("ema", 10001))

        # ── PEPPER: bid above ask to guarantee market-order fills ─────────────
        try:
            if PEPPER in state.order_depths:
                od  = state.order_depths[PEPPER]
                pos = state.position.get(PEPPER, 0)
                cap = PEPPER_LIMIT - pos
                orders: List[Order] = []
                if cap > 0 and od.sell_orders:
                    for ask_price in sorted(od.sell_orders.keys()):
                        if cap <= 0:
                            break
                        qty = min(cap, 10)
                        orders.append(Order(PEPPER, int(ask_price) + 2, qty))
                        cap -= qty
                if orders:
                    result[PEPPER] = orders
        except Exception:
            pass

        # ── OSMIUM: EMA fair, buy below fair, sell above fair, recycle at fair ─
        try:
            if OSMIUM in state.order_depths:
                od  = state.order_depths[OSMIUM]
                pos = state.position.get(OSMIUM, 0)

                asks = sorted(od.sell_orders.keys()) if od.sell_orders else []
                bids = sorted(od.buy_orders.keys(), reverse=True) if od.buy_orders else []

                if asks and bids:
                    mid = (int(asks[0]) + int(bids[0])) / 2.0
                elif asks:
                    mid = float(asks[0])
                elif bids:
                    mid = float(bids[0])
                else:
                    mid = ema

                ema = 0.95 * ema + 0.05 * mid
                fair = int(round(ema))

                bc = OSMIUM_LIMIT - pos
                sc = OSMIUM_LIMIT + pos
                orders = []

                # Layer 1: buy any ask strictly below fair
                for ap in asks:
                    if bc <= 0:
                        break
                    if int(ap) < fair:
                        vol = abs(int(od.sell_orders[ap]))
                        qty = min(vol, bc)
                        orders.append(Order(OSMIUM, int(ap), qty))
                        bc -= qty

                # Layer 2: sell any bid strictly above fair
                for bp in bids:
                    if sc <= 0:
                        break
                    if int(bp) > fair:
                        vol = int(od.buy_orders[bp])
                        qty = min(vol, sc)
                        orders.append(Order(OSMIUM, int(bp), -qty))
                        sc -= qty

                # Recycle: if heavily long, offload at fair (free capacity for next dip)
                if pos > 10:
                    for bp in bids:
                        if sc <= 0:
                            break
                        if int(bp) >= fair:
                            vol = int(od.buy_orders[bp])
                            qty = min(vol, sc)
                            orders.append(Order(OSMIUM, int(bp), -qty))
                            sc -= qty

                # Recycle: if heavily short, cover at fair
                if pos < -10:
                    for ap in asks:
                        if bc <= 0:
                            break
                        if int(ap) <= fair:
                            vol = abs(int(od.sell_orders[ap]))
                            qty = min(vol, bc)
                            orders.append(Order(OSMIUM, int(ap), qty))
                            bc -= qty

                # Passive quotes at fair-1 / fair+1 to capture bot trade flow
                bc2 = OSMIUM_LIMIT - pos
                sc2 = OSMIUM_LIMIT + pos
                if bc2 > 0:
                    orders.append(Order(OSMIUM, fair - 1, min(bc2, 10)))
                if sc2 > 0:
                    orders.append(Order(OSMIUM, fair + 1, -min(sc2, 10)))

                if orders:
                    result[OSMIUM] = orders
        except Exception:
            pass

        return result, 0, json.dumps({"ema": round(ema, 4)})