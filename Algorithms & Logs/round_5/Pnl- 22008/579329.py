from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List, Tuple
import json
import math

# ═══════════════════════════════════════════════════════════════════
# NEURAL NETWORK: Lightweight NumPy-only
# ═══════════════════════════════════════════════════════════════════

class NeuralNet:
    """
    3-layer feed-forward NN for per-symbol quote offset + volatility regime.
    Input: [mid_move, vol_est, spread, imbalance, drift_vel]
    Hidden: 8 neurons
    Output: [offset_factor, urgency_flag]
    """
    def __init__(self, seed=42):
        import random
        random.seed(seed)
        
        # Initialize weights (input=5, hidden=8, output=2)
        self.w1 = [[random.gauss(0, 0.1) for _ in range(5)] for _ in range(8)]
        self.b1 = [0.0] * 8
        self.w2 = [[random.gauss(0, 0.1) for _ in range(8)] for _ in range(2)]
        self.b2 = [0.0] * 2
        
        self.lr = 0.01  # learning rate
        
    def relu(self, x):
        return max(0, x)
    
    def sigmoid(self, x):
        try:
            return 1 / (1 + math.exp(-max(-50, min(50, x))))
        except:
            return 0.5
    
    def forward(self, inputs: List[float]) -> Tuple[float, float]:
        """Forward pass: returns (offset_factor, urgency)"""
        # Hidden layer
        h = [self.relu(sum(self.w1[i][j] * inputs[j] for j in range(5)) + self.b1[i]) 
             for i in range(8)]
        
        # Output layer
        o1 = self.sigmoid(sum(self.w2[0][i] * h[i] for i in range(8)) + self.b2[0])
        o2 = self.sigmoid(sum(self.w2[1][i] * h[i] for i in range(8)) + self.b2[1])
        
        return o1, o2
    
    def backward(self, inputs: List[float], target_offset: float, target_urgency: float, 
                 pred_offset: float, pred_urgency: float):
        """Simple gradient update (no explicit backprop — use finite differences)"""
        # Simplified: adjust w2 based on error
        eps = 0.01
        err_o = (pred_offset - target_offset) ** 2 + (pred_urgency - target_urgency) ** 2
        
        for i in range(2):
            for j in range(8):
                # Perturb and measure delta error
                old_w = self.w2[i][j]
                self.w2[i][j] += eps
                o1_new, o2_new = self.forward(inputs)
                err_new = (o1_new - target_offset) ** 2 + (o2_new - target_urgency) ** 2
                delta = (err_new - err_o) / eps
                self.w2[i][j] = old_w - self.lr * delta
    
    def save(self) -> str:
        return json.dumps({
            'w1': self.w1, 'b1': self.b1,
            'w2': self.w2, 'b2': self.b2,
        }, separators=(',', ':'))
    
    def load(self, data: str):
        try:
            d = json.loads(data)
            self.w1 = d.get('w1', self.w1)
            self.b1 = d.get('b1', self.b1)
            self.w2 = d.get('w2', self.w2)
            self.b2 = d.get('b2', self.b2)
        except:
            pass


# ═══════════════════════════════════════════════════════════════════
# PER-SYMBOL STATE
# ═══════════════════════════════════════════════════════════════════

class SymbolState:
    def __init__(self):
        self.mid = None
        self.ewm_mid = None
        self.ewm_vol = 8.0
        self.prev_vol = 8.0
        self.vol_ma_fast = 8.0
        self.vol_ma_slow = 8.0
        self.drift_vel = 0.0  # (mid - ewm_mid) / time
        self.buy_pressure = 0.0
        self.sell_pressure = 0.0
        self.tick_count = 0
        self.nn = NeuralNet()
        
    def update(self, mid: float, buy_orders: Dict[int, int], sell_orders: Dict[int, int]):
        """Update state with new mid and order book."""
        if self.mid is not None:
            move = abs(mid - self.mid)
            self.ewm_vol = 0.9 * self.ewm_vol + 0.1 * move
            self.vol_ma_fast = 0.95 * self.vol_ma_fast + 0.05 * move
            self.vol_ma_slow = 0.99 * self.vol_ma_slow + 0.01 * move
        
        if self.ewm_mid is None:
            self.ewm_mid = mid
        else:
            self.ewm_mid = 0.97 * self.ewm_mid + 0.03 * mid  # slower EWM
            self.drift_vel = mid - self.ewm_mid
        
        # Order imbalance: buy vol vs sell vol at best levels
        best_bid_qty = sum(qty for price, qty in list(buy_orders.items())[:3])
        best_ask_qty = sum(qty for price, qty in list(sell_orders.items())[:3])
        total = best_bid_qty + best_ask_qty + 1e-9
        self.buy_pressure = (best_bid_qty - best_ask_qty) / total
        
        self.mid = mid
        self.tick_count += 1
    
    def get_nn_features(self, spread: int) -> Tuple[List[float], float, float]:
        """Get features for NN, return prediction."""
        if self.mid is None or self.ewm_mid is None:
            return [0, 0, spread, 0, 0], 1.0, 0.0
        
        features = [
            self.mid - self.ewm_mid,           # mid_move (drift)
            self.ewm_vol,                      # volatility
            spread,                            # spread width
            self.buy_pressure,                 # order imbalance
            self.drift_vel,                    # drift velocity
        ]
        
        # Normalize features
        features[0] = max(-10, min(10, features[0]))  # mid_move: [-10, 10]
        features[1] = max(0.5, min(20, features[1]))  # vol: [0.5, 20]
        features[2] = max(1, min(30, features[2]))    # spread: [1, 30]
        features[3] = max(-1, min(1, features[3]))    # imbalance: [-1, 1]
        features[4] = max(-5, min(5, features[4]))    # drift_vel: [-5, 5]
        
        offset_factor, urgency = self.nn.forward(features)
        
        return features, offset_factor, urgency


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

POS_LIMIT = 10
NORMAL_CAP = 4
LEAN_CAP = 7
URGENCY_CAP = 8
BASE_QTY = 5

# Cluster arb pairs (same as before)
CORR_PAIRS: List[Tuple[str, str, int, float]] = [
    ("SNACKPACK_VANILLA", "SNACKPACK_CHOCOLATE", -1, 0.926),
    ("MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", -1, 0.882),
    ("MICROCHIP_TRIANGLE", "MICROCHIP_OVAL", 1, 0.870),
    ("PEBBLES_XL", "PEBBLES_S", -1, 0.834),
    ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 1, 0.875),
]


# ═══════════════════════════════════════════════════════════════════
# TRADER
# ═══════════════════════════════════════════════════════════════════

class Trader:
    def __init__(self):
        self._states: Dict[str, SymbolState] = {}
        self._ready = False
    
    def _get_state(self, sym: str) -> SymbolState:
        if sym not in self._states:
            self._states[sym] = SymbolState()
        return self._states[sym]
    
    def _sizes(self, pos: int, drift: float, urgency: float) -> Tuple[int, int]:
        """Inventory + drift-aware quote sizing."""
        ap = abs(pos)
        
        if urgency > 0.7:
            # High urgency: reduce entries, increase exits
            if pos > 0:
                return (0, max(BASE_QTY + 2, POS_LIMIT - pos))
            elif pos < 0:
                return (max(BASE_QTY + 2, POS_LIMIT + pos), 0)
            else:
                return (BASE_QTY, BASE_QTY)
        
        if pos > 0:
            if ap >= URGENCY_CAP:
                bq, aq = 1, POS_LIMIT - pos
            elif ap >= LEAN_CAP:
                bq, aq = 2, BASE_QTY + 2
            elif ap > NORMAL_CAP:
                bq, aq = 3, BASE_QTY + 1
            else:
                bq, aq = BASE_QTY, BASE_QTY
        elif pos < 0:
            if ap >= URGENCY_CAP:
                bq, aq = POS_LIMIT + pos, 1
            elif ap >= LEAN_CAP:
                bq, aq = BASE_QTY + 2, 2
            elif ap > NORMAL_CAP:
                bq, aq = BASE_QTY + 1, 3
            else:
                bq, aq = BASE_QTY, BASE_QTY
        else:
            bq, aq = BASE_QTY, BASE_QTY
        
        # Drift adjustment
        if abs(drift) > 3.0:
            if drift > 0:
                bq = max(0, bq - 2)
            else:
                aq = max(0, aq - 2)
        
        bq = min(bq, max(POS_LIMIT - pos, 0))
        aq = min(aq, max(POS_LIMIT + pos, 0))
        
        return bq, aq
    
    def _make(self, sym: str, best_bid: int, best_ask: int, pos: int,
              state: SymbolState) -> List[Order]:
        """Generate market-making orders using NN-predicted offset."""
        raw_spread = best_ask - best_bid
        
        if raw_spread < 2:
            return []
        
        # Get NN prediction
        _, offset_factor, urgency = state.get_nn_features(raw_spread)
        
        # Offset = factor * (spread/2), clamped to [1, spread/2 - 1]
        base_offset = max(1.0, (raw_spread - 1) / 2.0)
        offset = int(max(1, min(base_offset * 0.5 + offset_factor * base_offset * 0.5, 
                                base_offset - 0.5)))
        
        our_bid = best_bid + offset
        our_ask = best_ask - offset
        
        if our_ask <= our_bid:
            return []
        
        drift = state.drift_vel if state.drift_vel else 0.0
        bq, aq = self._sizes(pos, drift, urgency)
        
        orders: List[Order] = []
        if bq > 0:
            orders.append(Order(sym, our_bid, bq))
        if aq > 0:
            orders.append(Order(sym, our_ask, -aq))
        
        # Aggressive exit at urgency
        ap = abs(pos)
        if urgency > 0.8 and ap >= URGENCY_CAP:
            if pos > 0:
                cross_qty = min(4, pos - LEAN_CAP + 1)
                if cross_qty > 0:
                    orders.append(Order(sym, best_bid, -cross_qty))
            else:
                cross_qty = min(4, -pos - LEAN_CAP + 1)
                if cross_qty > 0:
                    orders.append(Order(sym, best_ask, cross_qty))
        
        return orders
    
    def _arb(self, depths: Dict[str, OrderDepth],
             pos_map: Dict[str, int]) -> Dict[str, List[Order]]:
        """Cluster arbitrage: leader momentum → follower trade."""
        out: Dict[str, List[Order]] = {}
        
        for leader, follower, sign, corr in CORR_PAIRS:
            state_l = self._get_state(leader)
            
            if state_l.mid is None or state_l.ewm_mid is None:
                continue
            
            ld = depths.get(leader)
            if not ld or not ld.buy_orders or not ld.sell_orders:
                continue
            
            move = state_l.drift_vel
            vol = state_l.ewm_vol
            
            # Spike threshold: 2.5x volatility
            if abs(move) < 2.5 * vol:
                continue
            
            expected_dir = (1 if move > 0 else -1) * sign
            f_pos = pos_map.get(follower, 0)
            fd = depths.get(follower)
            
            if not fd or not fd.buy_orders or not fd.sell_orders:
                continue
            
            if expected_dir > 0:
                room = POS_LIMIT - f_pos
                if room > 0:
                    best_ask_f = min(fd.sell_orders.keys())
                    qty = min(room, 4)
                    out.setdefault(follower, []).append(Order(follower, best_ask_f, qty))
            else:
                room = POS_LIMIT + f_pos
                if room > 0:
                    best_bid_f = max(fd.buy_orders.keys())
                    qty = min(room, 4)
                    out.setdefault(follower, []).append(Order(follower, best_bid_f, -qty))
        
        return out
    
    def _save(self) -> str:
        data = {}
        for sym, state in self._states.items():
            data[sym] = {
                'm': round(state.mid, 2) if state.mid else None,
                'e': round(state.ewm_mid, 2) if state.ewm_mid else None,
                'v': round(state.ewm_vol, 3),
                'd': round(state.drift_vel, 3),
                'nn': state.nn.save(),
            }
        return json.dumps(data, separators=(',', ':'))
    
    def _load(self, td: str):
        if not td:
            return
        try:
            data = json.loads(td)
            for sym, d in data.items():
                state = self._get_state(sym)
                state.mid = d.get('m')
                state.ewm_mid = d.get('e')
                state.ewm_vol = d.get('v', 8.0)
                state.drift_vel = d.get('d', 0.0)
                if 'nn' in d:
                    state.nn.load(d['nn'])
        except:
            pass
    
    def run(self, state: TradingState):
        if not self._ready:
            self._load(state.traderData)
            self._ready = True
        
        pos_map = state.position
        depths = state.order_depths
        result: Dict[str, List[Order]] = {}
        
        # Update states
        for sym, depth in depths.items():
            if not depth.buy_orders or not depth.sell_orders:
                continue
            mid = (max(depth.buy_orders) + min(depth.sell_orders)) / 2.0
            st = self._get_state(sym)
            st.update(mid, depth.buy_orders, depth.sell_orders)
        
        # Cluster arb
        for sym, orders in self._arb(depths, pos_map).items():
            result.setdefault(sym, []).extend(orders)
        
        # Market making
        for sym, depth in depths.items():
            if not depth.buy_orders or not depth.sell_orders:
                continue
            
            best_bid = max(depth.buy_orders.keys())
            best_ask = min(depth.sell_orders.keys())
            pos = pos_map.get(sym, 0)
            pending = sum(o.quantity for o in result.get(sym, []))
            eff_pos = pos + pending
            
            st = self._get_state(sym)
            orders = self._make(sym, best_bid, best_ask, eff_pos, st)
            result.setdefault(sym, []).extend(orders)
        
        return result, 0, self._save()