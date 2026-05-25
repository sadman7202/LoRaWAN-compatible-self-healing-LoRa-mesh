"""
Routing Agent - AI-Driven Multi-Criteria Path Selection
=======================================================
Implements the intelligent routing agent that selects optimal
paths based on RSSI, battery level, hop count, and historical
reliability. Supports multiple routing strategies for comparison.

Author: [Your Name]
Date: 2026
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, auto
import math
import random


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class RouteEntry:
    """Single route table entry."""
    destination: str
    next_hop: str
    hop_count: int
    rssi: float          # dBm (negative value)
    battery: float       # 0-100%
    quality: int         # 0-255 composite score
    last_updated: float  # Timestamp
    status: str = 'ACTIVE'  # ACTIVE, STALE, DOWN
    success_count: int = 0
    attempt_count: int = 0

    @property
    def reliability(self) -> float:
        """Historical delivery reliability."""
        if self.attempt_count == 0:
            return 0.5  # Default 50% for unknown routes
        return self.success_count / self.attempt_count


class RoutingStrategy(Enum):
    """Available routing strategies for comparison."""
    SHORTEST_PATH = auto()      # Minimum hops only
    BEST_RSSI = auto()          # Strongest signal only
    AODV_BASIC = auto()         # Standard AODV (hops + freshness)
    AI_MULTICRITERIA = auto()   # Our proposed: RSSI + Battery + Hops + Reliability
    FLOODING = auto()           # Broadcast to all neighbors (baseline)



# ============================================================
# ROUTING AGENT
# ============================================================

class RoutingAgent:
    """
    AI-driven routing agent implementing multi-criteria path selection.
    
    The agent scores each possible next-hop using a weighted combination:
        Score = w1*RSSI + w2*Battery - w3*Hops + w4*Reliability
    
    Weights are tunable and can change based on operational mode
    (normal vs disaster).
    """

    def __init__(self, config=None):
        """
        Initialize routing agent with configuration.
        
        Args:
            config: SimConfig object with routing weights
        """
        # Default weights (can be overridden by config)
        self.w_rssi = 0.30
        self.w_battery = 0.30
        self.w_hops = 0.20
        self.w_reliability = 0.20

        # Disaster mode weights (battery more critical)
        self.w_rssi_disaster = 0.25
        self.w_battery_disaster = 0.35
        self.w_hops_disaster = 0.15
        self.w_reliability_disaster = 0.25

        # Strategy
        self.strategy = RoutingStrategy.AI_MULTICRITERIA
        self.is_disaster_mode = False

        # Normalization bounds
        self.rssi_min = -120.0  # dBm (worst acceptable)
        self.rssi_max = -40.0   # dBm (best possible)
        self.max_hops = 8

        if config:
            self.w_rssi = getattr(config, 'w_rssi', self.w_rssi)
            self.w_battery = getattr(config, 'w_battery', self.w_battery)
            self.w_hops = getattr(config, 'w_hops', self.w_hops)
            self.w_reliability = getattr(config, 'w_reliability', self.w_reliability)
            self.max_hops = getattr(config, 'max_ttl', self.max_hops)

    def set_disaster_mode(self, enabled: bool):
        """Switch to disaster-optimized weights."""
        self.is_disaster_mode = enabled

    def set_strategy(self, strategy: RoutingStrategy):
        """Change routing strategy (for comparison experiments)."""
        self.strategy = strategy

    @property
    def weights(self) -> Tuple[float, float, float, float]:
        """Get current active weights based on mode."""
        if self.is_disaster_mode:
            return (self.w_rssi_disaster, self.w_battery_disaster,
                    self.w_hops_disaster, self.w_reliability_disaster)
        return (self.w_rssi, self.w_battery, self.w_hops, self.w_reliability)

    def normalize_rssi(self, rssi: float) -> float:
        """Normalize RSSI to [0, 1] range."""
        normalized = (rssi - self.rssi_min) / (self.rssi_max - self.rssi_min)
        return max(0.0, min(1.0, normalized))

    def normalize_battery(self, battery: float) -> float:
        """Normalize battery percentage to [0, 1]."""
        return max(0.0, min(1.0, battery / 100.0))

    def normalize_hops(self, hop_count: int) -> float:
        """Normalize hop count to [0, 1] (higher = worse)."""
        return max(0.0, min(1.0, hop_count / self.max_hops))

    def compute_route_score(self, rssi: float, battery: float,
                            hop_count: int, reliability: float) -> float:
        """
        Compute composite route quality score.
        
        Args:
            rssi: Signal strength in dBm (e.g., -80)
            battery: Battery percentage of next hop (0-100)
            hop_count: Number of hops on this path
            reliability: Historical success rate (0.0-1.0)
        
        Returns:
            Score in range [0, 1] where higher is better
        """
        w1, w2, w3, w4 = self.weights

        rssi_norm = self.normalize_rssi(rssi)
        battery_norm = self.normalize_battery(battery)
        hops_norm = self.normalize_hops(hop_count)
        reliability_norm = max(0.0, min(1.0, reliability))

        # Weighted combination (hops is penalty, so subtracted)
        score = (w1 * rssi_norm +
                 w2 * battery_norm -
                 w3 * hops_norm +
                 w4 * reliability_norm)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))



    def select_best_route(self, candidates: List[dict],
                          exclude_nodes: List[str] = None) -> Optional[dict]:
        """
        Select the best next-hop from a list of candidates.
        
        Args:
            candidates: List of dicts with keys:
                - node_id: str
                - rssi: float
                - battery: float
                - hop_count: int
                - reliability: float
                - node_type_value: int (higher = closer to gateway)
            exclude_nodes: List of node IDs to avoid (failed nodes)
        
        Returns:
            Best candidate dict, or None if no valid route
        """
        if exclude_nodes is None:
            exclude_nodes = []

        valid = [c for c in candidates
                 if c['node_id'] not in exclude_nodes
                 and c.get('status', 'ACTIVE') == 'ACTIVE']

        if not valid:
            return None

        if self.strategy == RoutingStrategy.FLOODING:
            return valid  # Return ALL (for flooding baseline)

        if self.strategy == RoutingStrategy.SHORTEST_PATH:
            return min(valid, key=lambda c: c['hop_count'])

        if self.strategy == RoutingStrategy.BEST_RSSI:
            return max(valid, key=lambda c: c['rssi'])

        if self.strategy == RoutingStrategy.AODV_BASIC:
            # AODV: prefer fewer hops, break ties by freshness
            return min(valid, key=lambda c: (c['hop_count'], -c.get('last_seen', 0)))

        # AI_MULTICRITERIA (proposed approach)
        best = None
        best_score = -1.0

        for candidate in valid:
            score = self.compute_route_score(
                rssi=candidate['rssi'],
                battery=candidate['battery'],
                hop_count=candidate['hop_count'],
                reliability=candidate.get('reliability', 0.5)
            )

            # Bonus for nodes closer to gateway in the hierarchy
            type_bonus = candidate.get('node_type_value', 0) * 0.05
            score += type_bonus

            if score > best_score:
                best_score = score
                best = candidate
                best['score'] = score

        return best

    def update_reliability(self, route: RouteEntry, success: bool):
        """Update route reliability after delivery attempt."""
        route.attempt_count += 1
        if success:
            route.success_count += 1

    def should_escalate_priority(self, retry_count: int,
                                  current_priority: int) -> int:
        """
        Determine if message priority should be escalated after failures.
        
        Args:
            retry_count: Number of failed attempts
            current_priority: Current priority value (1=CRITICAL, 5=SYSTEM)
        
        Returns:
            New priority value (may be escalated)
        """
        if retry_count > 6 and current_priority > 1:
            return current_priority - 1  # Escalate (lower number = higher priority)
        return current_priority


# ============================================================
# COMPARISON BASELINES
# ============================================================

class FloodingRouter:
    """
    Baseline 1: Simple flooding — broadcast every message to all neighbors.
    No intelligence, no route tables.
    """

    def __init__(self):
        self.strategy = RoutingStrategy.FLOODING

    def select_next_hops(self, neighbors: List[str],
                         exclude: List[str] = None) -> List[str]:
        """Return ALL alive neighbors (flooding)."""
        exclude = exclude or []
        return [n for n in neighbors if n not in exclude]


class ShortestPathRouter:
    """
    Baseline 2: Shortest path — always choose minimum hop count.
    No energy awareness, no signal quality consideration.
    """

    def __init__(self):
        self.strategy = RoutingStrategy.SHORTEST_PATH

    def select_next_hop(self, candidates: List[dict]) -> Optional[dict]:
        """Select candidate with minimum hop count."""
        valid = [c for c in candidates if c.get('status') == 'ACTIVE']
        if not valid:
            return None
        return min(valid, key=lambda c: c['hop_count'])


class AODVRouter:
    """
    Baseline 3: AODV-style routing — reactive route discovery
    with hop count as primary metric.
    """

    def __init__(self):
        self.strategy = RoutingStrategy.AODV_BASIC
        self.route_table: Dict[str, RouteEntry] = {}
        self.sequence_number = 0

    def select_next_hop(self, candidates: List[dict],
                        destination: str) -> Optional[dict]:
        """AODV route selection: minimum hops, freshest sequence."""
        valid = [c for c in candidates if c.get('status') == 'ACTIVE']
        if not valid:
            return None
        # AODV: prefer fewer hops, then higher sequence number
        return min(valid, key=lambda c: (c['hop_count'],
                                          -c.get('sequence', 0)))

    def route_request(self, source: str, destination: str) -> dict:
        """Generate AODV RREQ."""
        self.sequence_number += 1
        return {
            'type': 'RREQ',
            'source': source,
            'destination': destination,
            'hop_count': 0,
            'sequence': self.sequence_number
        }


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def compare_routing_strategies(candidates: List[dict]) -> dict:
    """
    Compare all routing strategies on the same candidate set.
    Useful for generating comparison tables in the paper.
    
    Returns dict of {strategy_name: selected_candidate}
    """
    results = {}

    # AI Multi-criteria
    agent = RoutingAgent()
    results['AI_MULTICRITERIA'] = agent.select_best_route(candidates)

    # Shortest path
    sp = ShortestPathRouter()
    results['SHORTEST_PATH'] = sp.select_next_hop(candidates)

    # Best RSSI
    agent.set_strategy(RoutingStrategy.BEST_RSSI)
    results['BEST_RSSI'] = agent.select_best_route(candidates)

    # AODV
    aodv = AODVRouter()
    results['AODV'] = aodv.select_next_hop(candidates, 'GW-01')

    return results


if __name__ == '__main__':
    # Demo: compare strategies on sample data
    sample_candidates = [
        {'node_id': 'BBR-01', 'rssi': -75, 'battery': 85,
         'hop_count': 2, 'reliability': 0.95, 'node_type_value': 3,
         'status': 'ACTIVE', 'last_seen': 100},
        {'node_id': 'BBR-02', 'rssi': -90, 'battery': 45,
         'hop_count': 1, 'reliability': 0.70, 'node_type_value': 3,
         'status': 'ACTIVE', 'last_seen': 95},
        {'node_id': 'LREL-03', 'rssi': -65, 'battery': 12,
         'hop_count': 3, 'reliability': 0.88, 'node_type_value': 2,
         'status': 'ACTIVE', 'last_seen': 80},
        {'node_id': 'BBR-03', 'rssi': -95, 'battery': 92,
         'hop_count': 2, 'reliability': 0.60, 'node_type_value': 3,
         'status': 'ACTIVE', 'last_seen': 90},
    ]

    print("=" * 60)
    print("ROUTING STRATEGY COMPARISON")
    print("=" * 60)
    print("\nCandidates:")
    for c in sample_candidates:
        print(f"  {c['node_id']}: RSSI={c['rssi']}dBm, "
              f"Batt={c['battery']}%, Hops={c['hop_count']}, "
              f"Rel={c['reliability']:.2f}")

    results = compare_routing_strategies(sample_candidates)
    print("\nResults:")
    for strategy, choice in results.items():
        if choice:
            if isinstance(choice, list):
                print(f"  {strategy}: ALL ({len(choice)} nodes)")
            else:
                print(f"  {strategy}: {choice['node_id']} "
                      f"(score={choice.get('score', 'N/A')})")
        else:
            print(f"  {strategy}: No valid route")

    # Show AI agent scoring in detail
    print("\n--- AI Multi-Criteria Scoring Detail ---")
    agent = RoutingAgent()
    for c in sample_candidates:
        score = agent.compute_route_score(
            c['rssi'], c['battery'], c['hop_count'], c['reliability'])
        print(f"  {c['node_id']}: score = {score:.4f}")
