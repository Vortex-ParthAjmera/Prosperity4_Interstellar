from datamodel import OrderDepth, TradingState, Order
import json
import numpy as np

S = 'ASH_COATED_OSMIUM'
D = 'INTARIAN_PEPPER_ROOT'
PL = {S: 50, D: 50}
SFV = 10000

class Trader:
    def run(self, state: TradingState) -> tuple:
        r, c = {}, 0
        td = {}
        ps = state.position
        
        if S in state.order_depths:
            od = state.order_depths[S]
            p = ps.get(S, 0)
            mb = PL[S] - p
            ms = PL[S] + p
            bl = sorted([(bp, abs(bv)) for bp, bv in od.buy_orders.items()], key=lambda x: -x[0])
            sl = sorted([(sp, abs(sv)) for sp, sv in od.sell_orders.items()], key=lambda x: x[0])
            bb = bl[0][0] if bl else None
            ba = sl[0][0] if sl else None
            o = []
            if bb and ba:
                for sp, sv in sl:
                    if sp <= SFV - 1: q = min(sv, mb); o.append(Order(S, int(sp), q)); mb -= q
                    elif sp <= SFV and p < 0: q = min(sv, abs(p)); o.append(Order(S, int(sp), q)); mb -= q
                for bp, bv in bl:
                    if bp >= SFV + 1: q = min(bv, ms); o.append(Order(S, int(bp), -q)); ms -= q
                    elif bp >= SFV and p > 0: q = min(bv, p); o.append(Order(S, int(bp), -q)); ms -= q
                bpp = int(bb + 1)
                app = int(ba - 1)
                for bp, bv in bl:
                    if bv > 1 and bp + 1 < SFV: bpp = max(bpp, bp + 1); break
                    elif bp < SFV: bpp = max(bpp, bp); break
                for sp, sv in sl:
                    if sv > 1 and sp - 1 > SFV: app = min(app, sp - 1); break
                    elif sp > SFV: app = min(app, sp); break
                if bpp >= SFV: bpp = SFV - 1
                if app <= SFV: app = SFV + 1
                if mb > 0: o.append(Order(S, bpp, mb))
                if ms > 0: o.append(Order(S, app, -ms))
            r[S] = o
        
        if D in state.order_depths:
            od = state.order_depths[D]
            p = ps.get(D, 0)
            mb = PL[D] - p
            ms = PL[D] + p
            bl = sorted([(bp, abs(bv)) for bp, bv in od.buy_orders.items()], key=lambda x: -x[0])
            sl = sorted([(sp, abs(sv)) for sp, sv in od.sell_orders.items()], key=lambda x: x[0])
            bb = bl[0][0] if bl else None
            ba = sl[0][0] if sl else None
            o = []
            if bb and ba:
                mid = (bb + ba) / 2
                l = {}
                try:
                    if state.traderData: l = json.loads(state.traderData)
                except: pass
                h = l.get('h', [])
                h.append(mid)
                if len(h) > 100: h = h[-100:]
                td['h'] = h
                tr = 0
                if len(h) >= 30:
                    r1 = np.mean(h[-15:])
                    r2 = np.mean(h[-30:-15])
                    ch = (r1 - r2) / r2
                    tr = 1 if ch > 0.008 else (-1 if ch < -0.008 else 0)
                sg = l.get('s', 0)
                for t in state.market_trades.get(D, []):
                    if t.timestamp > state.timestamp - 200:
                        if t.buyer == 'Olivia': sg = 1
                        elif t.seller == 'Olivia': sg = -1
                if sg: td['s'] = sg
                d = tr or sg
                if d == 1:
                    tp = min(PL[D], p + 25)
                    if p < tp and ba:
                        q = min(tp - p, mb)
                        o.append(Order(D, int(ba), q)); p += q
                    if p > 35 and bb:
                        q = min(p - 35, ms)
                        o.append(Order(D, int(bb), -int(q)))
                elif d == -1:
                    tp = max(-PL[D], p - 25)
                    if p > tp and bb:
                        q = min(p - tp, ms)
                        o.append(Order(D, int(bb), -int(q))); p -= q
                    if p < -35 and ba:
                        q = min(abs(p) - 35, mb)
                        o.append(Order(D, int(ba), int(q)))
                else:
                    em = l.get('e', mid)
                    em = 0.12 * mid + 0.88 * em
                    td['e'] = em
                    bp = int(bb + 1) if bb else int(em - 1)
                    ap = int(ba - 1) if ba else int(em + 1)
                    if bp >= em: bp = int(em - 1)
                    if ap <= em: ap = int(em + 1)
                    if mb > 0: o.append(Order(D, bp, mb))
                    if ms > 0: o.append(Order(D, ap, -ms))
            r[D] = o
        
        try: ftd = json.dumps(td)
        except: ftd = ''
        return r, c, ftd