from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional
import json
from dataclasses import dataclass, field
import math

SYM_ACO = "ASH_COATED_OSMIUM"
SYM_IPR = "INTARIAN_PEPPER_ROOT"

POS_LIMIT = 50

IPR_ACCUM_END  = 5000
IPR_HOLD_END   = 993000
IPR_ACCUM_QTY  = 10
IPR_UNWIND_QTY = 5

ACO_EMA_ALPHA   = 0.015
ACO_HALF_NORMAL = 7
ACO_HALF_WIDE   = 9
ACO_HALF_TIGHT  = 6
ACO_MIN_SPREAD  = 5
ACO_MAX_QTY     = 8
ACO_SKEW_FAC    = 0.10
ACO_SKEW_CAP    = 7
ACO_AGGR_THR    = 10
ACO_EOD_TS      = 995000


def _best_bid(od: OrderDepth) -> Optional[int]:
    return max(od.buy_orders) if od.buy_orders else None


def _best_ask(od: OrderDepth) -> Optional[int]:
    return min(od.sell_orders) if od.sell_orders else None


def _bid_vol(od: OrderDepth) -> int:
    bb = _best_bid(od)
    return od.buy_orders[bb] if bb is not None else 0


def _ask_vol(od: OrderDepth) -> int:
    ba = _best_ask(od)
    return abs(od.sell_orders[ba]) if ba is not None else 0


def _mid(od: OrderDepth) -> Optional[float]:
    bb, ba = _best_bid(od), _best_ask(od)
    if bb and ba:
        return (bb + ba) / 2.0
    if bb:
        return float(bb)
    if ba:
        return float(ba)
    return None


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


@dataclass
class ACOState:
    ema: float = 10000.0
    ema_init: bool = False
    ticks: int = 0


@dataclass
class IPRState:
    ticks: int = 0


@dataclass
class RoundState:
    aco: ACOState = field(default_factory=ACOState)
    ipr: IPRState = field(default_factory=IPRState)

    def encode(self) -> str:
        return json.dumps({"aco": self.aco.__dict__, "ipr": self.ipr.__dict__})

    @classmethod
    def decode(cls, s: str) -> "RoundState":
        rs = cls()
        if not s:
            return rs
        try:
            d = json.loads(s)
            if "aco" in d:
                rs.aco = ACOState(**d["aco"])
            if "ipr" in d:
                rs.ipr = IPRState(**d["ipr"])
        except Exception:
            pass
        return rs


def _ipr_orders(od: OrderDepth, pos: int, ts: int, state: IPRState) -> List[Order]:
    orders: List[Order] = []
    bb = _best_bid(od)
    ba = _best_ask(od)

    if ts >= IPR_HOLD_END:
        if pos > 0 and bb is not None:
            orders.append(Order(SYM_IPR, bb, -min(IPR_UNWIND_QTY, pos)))
        return orders

    if ts <= IPR_ACCUM_END and pos < POS_LIMIT:
        remaining = POS_LIMIT - pos
        if ba is not None:
            qty = min(IPR_ACCUM_QTY, remaining)
            orders.append(Order(SYM_IPR, ba, qty))
            extra = min(5, remaining - qty)
            if extra > 0 and ba - 1 > (bb or 0):
                orders.append(Order(SYM_IPR, ba - 1, extra))
        elif bb is not None:
            orders.append(Order(SYM_IPR, bb + 1, min(IPR_ACCUM_QTY, remaining)))

    return orders


def _aco_orders(od: OrderDepth, pos: int, ts: int, state: ACOState) -> List[Order]:
    orders: List[Order] = []
    bb = _best_bid(od)
    ba = _best_ask(od)
    mp = _mid(od)

    if mp is None:
        return orders

    if not state.ema_init:
        state.ema = mp
        state.ema_init = True
    else:
        state.ema = ACO_EMA_ALPHA * mp + (1 - ACO_EMA_ALPHA) * state.ema

    fair = state.ema
    state.ticks += 1

    if ts >= ACO_EOD_TS:
        if pos > 0 and bb is not None:
            orders.append(Order(SYM_ACO, bb, -pos))
        elif pos < 0 and ba is not None:
            orders.append(Order(SYM_ACO, ba, -pos))
        return orders

    if ba is not None and (fair - ba) > ACO_AGGR_THR and pos < POS_LIMIT:
        qty = min(_ask_vol(od), POS_LIMIT - pos, 10)
        if qty > 0:
            orders.append(Order(SYM_ACO, ba, qty))
            return orders

    if bb is not None and (bb - fair) > ACO_AGGR_THR and pos > -POS_LIMIT:
        qty = min(_bid_vol(od), POS_LIMIT + pos, 10)
        if qty > 0:
            orders.append(Order(SYM_ACO, bb, -qty))
            return orders

    if bb is None or ba is None:
        if bb is None and pos < POS_LIMIT:
            orders.append(Order(SYM_ACO, int(fair - 7), min(5, POS_LIMIT - pos)))
        if ba is None and pos > -POS_LIMIT:
            orders.append(Order(SYM_ACO, int(fair + 7), -min(5, POS_LIMIT + pos)))
        return orders

    market_spread = ba - bb
    if market_spread <= ACO_MIN_SPREAD:
        return orders

    if market_spread >= 18:
        half = ACO_HALF_WIDE
    elif market_spread >= 10:
        half = ACO_HALF_NORMAL
    else:
        half = ACO_HALF_TIGHT

    raw_skew = -pos * ACO_SKEW_FAC
    skew = _clamp(int(round(raw_skew)), -ACO_SKEW_CAP, ACO_SKEW_CAP)

    my_bid = int(round(fair + skew - half))
    my_ask = int(round(fair + skew + half))

    my_bid = min(my_bid + 1, bb + 1)
    my_ask = max(my_ask - 1, ba - 1)

    if my_bid >= my_ask:
        my_bid = int(fair) - 1
        my_ask = int(fair) + 1

    bid_room = POS_LIMIT - pos
    ask_room = POS_LIMIT + pos

    bid_qty = _clamp(ACO_MAX_QTY, 0, bid_room)
    ask_qty = _clamp(ACO_MAX_QTY, 0, ask_room)

    if bid_qty > 0:
        orders.append(Order(SYM_ACO, my_bid, bid_qty))
        extra = min(5, bid_room - bid_qty)
        if extra > 0:
            orders.append(Order(SYM_ACO, my_bid - 2, extra))

    if ask_qty > 0:
        orders.append(Order(SYM_ACO, my_ask, -ask_qty))
        extra = min(5, ask_room - ask_qty)
        if extra > 0:
            orders.append(Order(SYM_ACO, my_ask + 2, -extra))

    return orders


class Trader:
    def run(self, state: TradingState):
        rs = RoundState.decode(getattr(state, "traderData", "") or "")
        ts = state.timestamp
        result: Dict[str, List[Order]] = {}

        if SYM_IPR in state.order_depths:
            od = state.order_depths[SYM_IPR]
            pos = state.position.get(SYM_IPR, 0)
            orders = _ipr_orders(od, pos, ts, rs.ipr)
            if orders:
                result[SYM_IPR] = orders

        if SYM_ACO in state.order_depths:
            od = state.order_depths[SYM_ACO]
            pos = state.position.get(SYM_ACO, 0)
            orders = _aco_orders(od, pos, ts, rs.aco)
            if orders:
                result[SYM_ACO] = orders

        return result, 0, rs.encode()