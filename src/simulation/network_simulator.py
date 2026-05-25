"""
SHLM Network Simulator - Self-Healing LoRa Mesh
================================================
A discrete-event simulation of the SHLM protocol for evaluating
packet delivery ratio, latency, self-healing recovery time, and
energy efficiency under various failure scenarios.

Usage:
    python network_simulator.py [--nodes N] [--failure-rate F] [--duration T]

Author: [Your Name]
Date: 2026
"""

import random
import heapq
import time
import math
import json
import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, auto

# Import companion modules
from routing_agent import RoutingAgent, RouteEntry
from energy_model import EnergyModel, NodePowerState
from mobile_relay import MobileRelay, MobileRelayAgent


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class NodeType(Enum):
    SOS_DEVICE = 1
    LOCAL_RELAY = 2
    BACKBONE_RELAY = 3
    MOBILE_RELAY = 4
    GATEWAY = 5


class OperationalMode(Enum):
    NORMAL = 1
    PREPAREDNESS = 2
    DISASTER = 3
    ISOLATED = 4


class PacketType(Enum):
    SOS = 0x01
    HEARTBEAT = 0x02
    ROUTE_REQUEST = 0x03
    ROUTE_REPLY = 0x04
    ROUTE_DOWN = 0x05
    HOP_ACK = 0x06
    END_ACK = 0x07
    RESCUE_ACK = 0x08
    MOBILE_BEACON = 0x0A


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    SYSTEM = 5


class EmergencyType(Enum):
    PEOPLE_TRAPPED = 0x01
    BOAT_NEEDED = 0x02
    MEDICAL = 0x03
    FOOD_WATER = 0x04
    TRAPPED_AND_BOAT = 0x05
    GENERAL_SOS = 0x09



# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class SimConfig:
    """Simulation configuration parameters."""
    # Network topology
    num_sos_nodes: int = 50
    num_local_relays: int = 15
    num_backbone_relays: int = 7
    num_mobile_relays: int = 2
    num_gateways: int = 2

    # Area dimensions (meters)
    area_width: float = 10000.0   # 10 km
    area_height: float = 10000.0  # 10 km

    # LoRa parameters
    tx_power_dbm: float = 14.0       # Local nodes
    tx_power_backbone_dbm: float = 20.0  # Backbone
    frequency_mhz: float = 868.0
    spreading_factor: int = 9
    bandwidth_khz: float = 125.0

    # Communication ranges (meters)
    sos_range: float = 700.0
    local_relay_range: float = 2000.0
    backbone_range: float = 8000.0

    # Protocol parameters
    heartbeat_interval_normal: float = 60.0
    heartbeat_interval_disaster: float = 120.0
    miss_threshold: int = 3
    max_ttl: int = 8
    duplicate_cache_size: int = 200
    message_queue_size: int = 50

    # Simulation parameters
    simulation_duration: float = 7200.0  # 2 hours in seconds
    failure_rate: float = 0.2  # 20% of relays fail
    failure_start_time: float = 600.0  # Failures begin at T+10 min
    sos_generation_rate: float = 0.01  # SOS per second per node (Poisson)
    disaster_start_time: float = 300.0  # Disaster begins at T+5 min

    # Routing weights
    w_rssi: float = 0.30
    w_battery: float = 0.30
    w_hops: float = 0.20
    w_reliability: float = 0.20

    # Random seed for reproducibility
    seed: int = 42



# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class Position:
    """2D position in meters."""
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class Packet:
    """Network packet."""
    packet_id: str
    packet_type: PacketType
    source: str
    destination: str
    priority: Priority
    ttl: int
    hop_count: int = 0
    payload: dict = field(default_factory=dict)
    created_at: float = 0.0
    delivered_at: float = 0.0
    path: List[str] = field(default_factory=list)

    def __lt__(self, other):
        """For priority queue ordering."""
        return self.priority.value < other.priority.value


@dataclass
class Event:
    """Simulation event."""
    time: float
    event_type: str
    node_id: str
    data: dict = field(default_factory=dict)

    def __lt__(self, other):
        return self.time < other.time



# ============================================================
# NODE CLASS
# ============================================================

class Node:
    """Represents a network node in the simulation."""

    def __init__(self, node_id: str, node_type: NodeType,
                 position: Position, config: SimConfig):
        self.node_id = node_id
        self.node_type = node_type
        self.position = position
        self.config = config
        self.mode = OperationalMode.NORMAL
        self.is_alive = True

        # Energy
        self.battery_percent = 100.0
        self.energy_model = EnergyModel(node_type)

        # Routing
        self.routing_agent = RoutingAgent(config)
        self.neighbors: Dict[str, dict] = {}  # node_id -> {rssi, battery, last_seen}
        self.route_table: Dict[str, RouteEntry] = {}

        # Message handling
        self.message_queue: List[Packet] = []
        self.duplicate_cache: Dict[str, float] = {}  # packet_id -> timestamp
        self.stored_messages: List[Packet] = []  # For DTN (isolated mode)

        # Statistics
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_forwarded = 0
        self.packets_dropped = 0
        self.heartbeats_sent = 0

        # Heartbeat tracking
        self.last_heartbeat_sent = 0.0
        self.neighbor_heartbeats: Dict[str, dict] = {}
        # node_id -> {last_seen, consecutive_misses}

    @property
    def tx_range(self) -> float:
        """Get transmission range based on node type."""
        if self.node_type == NodeType.SOS_DEVICE:
            return self.config.sos_range
        elif self.node_type == NodeType.LOCAL_RELAY:
            return self.config.local_relay_range
        elif self.node_type == NodeType.BACKBONE_RELAY:
            return self.config.backbone_range
        elif self.node_type == NodeType.MOBILE_RELAY:
            return self.config.local_relay_range
        elif self.node_type == NodeType.GATEWAY:
            return self.config.backbone_range
        return self.config.sos_range

    def can_reach(self, other: 'Node') -> bool:
        """Check if this node can reach another node."""
        if not self.is_alive or not other.is_alive:
            return False
        distance = self.position.distance_to(other.position)
        return distance <= self.tx_range

    def get_rssi(self, other: 'Node') -> float:
        """Calculate RSSI to another node (simplified log-distance model)."""
        distance = self.position.distance_to(other.position)
        if distance < 1.0:
            distance = 1.0
        # Log-distance path loss: RSSI = TxPower - PL(d)
        # PL(d) = PL(d0) + 10*n*log10(d/d0) + X_sigma
        pl_d0 = 127.41  # Path loss at 1m for 868 MHz
        n = 2.8  # Path loss exponent (rural/suburban)
        x_sigma = random.gauss(0, 3.0)  # Shadow fading (std=3dB)
        path_loss = pl_d0 + 10 * n * math.log10(distance) + x_sigma
        tx_power = (self.config.tx_power_backbone_dbm
                    if self.node_type == NodeType.BACKBONE_RELAY
                    else self.config.tx_power_dbm)
        rssi = tx_power - path_loss
        return rssi

    def is_duplicate(self, packet_id: str, current_time: float) -> bool:
        """Check if packet is a duplicate."""
        if packet_id in self.duplicate_cache:
            return True
        # Clean old entries
        expired = [k for k, v in self.duplicate_cache.items()
                   if current_time - v > 600.0]
        for k in expired:
            del self.duplicate_cache[k]
        return False

    def mark_seen(self, packet_id: str, current_time: float):
        """Mark a packet as seen in duplicate cache."""
        self.duplicate_cache[packet_id] = current_time
        # Enforce cache size limit
        if len(self.duplicate_cache) > self.config.duplicate_cache_size:
            oldest = min(self.duplicate_cache, key=self.duplicate_cache.get)
            del self.duplicate_cache[oldest]

    def enqueue_message(self, packet: Packet):
        """Add message to priority queue."""
        if len(self.message_queue) >= self.config.message_queue_size:
            # Drop lowest priority message
            self.message_queue.sort(key=lambda p: p.priority.value)
            if self.message_queue[-1].priority.value > packet.priority.value:
                dropped = self.message_queue.pop()
                self.packets_dropped += 1
            else:
                self.packets_dropped += 1
                return
        heapq.heappush(self.message_queue, packet)

    def fail(self):
        """Simulate node failure."""
        self.is_alive = False

    def recover(self):
        """Simulate node recovery."""
        self.is_alive = True



# ============================================================
# NETWORK SIMULATOR
# ============================================================

class NetworkSimulator:
    """Main discrete-event network simulator."""

    def __init__(self, config: SimConfig):
        self.config = config
        self.nodes: Dict[str, Node] = {}
        self.event_queue: List[Event] = []
        self.current_time: float = 0.0
        self.rng = random.Random(config.seed)

        # Statistics
        self.total_sos_generated = 0
        self.total_sos_delivered = 0
        self.total_sos_dropped = 0
        self.delivery_latencies: List[float] = []
        self.route_recovery_times: List[float] = []
        self.failure_events: List[dict] = []
        self.mode = OperationalMode.NORMAL

        # Build network
        self._create_topology()
        self._discover_neighbors()

    def _create_topology(self):
        """Create the multi-tier network topology."""
        # Create Gateway(s) — at edge of area (command center)
        for i in range(self.config.num_gateways):
            pos = Position(
                self.config.area_width * 0.9,
                self.config.area_height * (0.3 + 0.4 * i)
            )
            node = Node(f"GW-{i+1:02d}", NodeType.GATEWAY, pos, self.config)
            self.nodes[node.node_id] = node

        # Create Backbone Relays — linear corridor from area center to gateway
        for i in range(self.config.num_backbone_relays):
            frac = (i + 1) / (self.config.num_backbone_relays + 1)
            pos = Position(
                self.config.area_width * (0.1 + frac * 0.75),
                self.config.area_height * (0.4 + self.rng.uniform(-0.1, 0.1))
            )
            node = Node(f"BBR-{i+1:02d}", NodeType.BACKBONE_RELAY, pos, self.config)
            self.nodes[node.node_id] = node

        # Create Local Relays — scattered in area
        for i in range(self.config.num_local_relays):
            pos = Position(
                self.rng.uniform(0.05, 0.6) * self.config.area_width,
                self.rng.uniform(0.1, 0.9) * self.config.area_height
            )
            node = Node(f"LREL-{i+1:02d}", NodeType.LOCAL_RELAY, pos, self.config)
            self.nodes[node.node_id] = node

        # Create SOS Devices — clustered around local relays
        for i in range(self.config.num_sos_nodes):
            # Pick a random local relay to cluster around
            relay_idx = self.rng.randint(0, self.config.num_local_relays - 1)
            relay = self.nodes[f"LREL-{relay_idx+1:02d}"]
            # Place within SOS range of the relay
            angle = self.rng.uniform(0, 2 * math.pi)
            dist = self.rng.uniform(50, self.config.sos_range * 0.8)
            pos = Position(
                relay.position.x + dist * math.cos(angle),
                relay.position.y + dist * math.sin(angle)
            )
            # Clamp to area
            pos.x = max(0, min(self.config.area_width, pos.x))
            pos.y = max(0, min(self.config.area_height, pos.y))
            node = Node(f"SOS-{i+1:03d}", NodeType.SOS_DEVICE, pos, self.config)
            self.nodes[node.node_id] = node

        # Create Mobile Relays — start near gateway
        for i in range(self.config.num_mobile_relays):
            pos = Position(
                self.config.area_width * 0.8,
                self.config.area_height * (0.3 + 0.4 * i)
            )
            node = Node(f"MR-{i+1:02d}", NodeType.MOBILE_RELAY, pos, self.config)
            self.nodes[node.node_id] = node

        print(f"[TOPOLOGY] Created {len(self.nodes)} nodes:")
        print(f"  Gateways: {self.config.num_gateways}")
        print(f"  Backbone Relays: {self.config.num_backbone_relays}")
        print(f"  Local Relays: {self.config.num_local_relays}")
        print(f"  SOS Devices: {self.config.num_sos_nodes}")
        print(f"  Mobile Relays: {self.config.num_mobile_relays}")

    def _discover_neighbors(self):
        """Initial neighbor discovery for all nodes."""
        node_list = list(self.nodes.values())
        for node in node_list:
            if node.node_type == NodeType.SOS_DEVICE:
                continue  # SOS devices don't maintain neighbor tables
            for other in node_list:
                if other.node_id == node.node_id:
                    continue
                if node.can_reach(other):
                    rssi = node.get_rssi(other)
                    if rssi > -120:  # Sensitivity threshold
                        node.neighbors[other.node_id] = {
                            'rssi': rssi,
                            'battery': other.battery_percent,
                            'last_seen': 0.0,
                            'consecutive_misses': 0,
                            'status': 'ACTIVE'
                        }

        # Print connectivity stats
        for node in node_list:
            if node.node_type != NodeType.SOS_DEVICE:
                print(f"  {node.node_id}: {len(node.neighbors)} neighbors")



    def schedule_event(self, time: float, event_type: str,
                       node_id: str, data: dict = None):
        """Schedule an event in the future."""
        event = Event(time, event_type, node_id, data or {})
        heapq.heappush(self.event_queue, event)

    def _schedule_initial_events(self):
        """Schedule heartbeats, SOS generation, failures."""
        # Schedule heartbeats for all relay/backbone/gateway nodes
        for node_id, node in self.nodes.items():
            if node.node_type not in (NodeType.SOS_DEVICE,):
                interval = self.config.heartbeat_interval_normal
                first_hb = self.rng.uniform(0, interval)
                self.schedule_event(first_hb, 'HEARTBEAT', node_id)

        # Schedule disaster mode activation
        self.schedule_event(self.config.disaster_start_time, 'MODE_CHANGE',
                           'SYSTEM', {'new_mode': OperationalMode.DISASTER})

        # Schedule node failures
        relay_nodes = [n for n in self.nodes.values()
                       if n.node_type in (NodeType.LOCAL_RELAY,
                                          NodeType.BACKBONE_RELAY)]
        num_failures = int(len(relay_nodes) * self.config.failure_rate)
        failed_nodes = self.rng.sample(relay_nodes, min(num_failures, len(relay_nodes)))

        for i, node in enumerate(failed_nodes):
            fail_time = self.config.failure_start_time + self.rng.uniform(0, 300)
            self.schedule_event(fail_time, 'NODE_FAILURE', node.node_id)

        # Schedule SOS generation (Poisson process during disaster)
        self._schedule_sos_events()

    def _schedule_sos_events(self):
        """Schedule SOS messages using Poisson process."""
        sos_nodes = [n for n in self.nodes.values()
                     if n.node_type == NodeType.SOS_DEVICE]

        for node in sos_nodes:
            # Each SOS node may generate 1-3 SOS during disaster
            num_sos = self.rng.randint(0, 3)
            for _ in range(num_sos):
                sos_time = self.config.disaster_start_time + \
                           self.rng.exponential(1.0 / self.config.sos_generation_rate)
                if sos_time < self.config.simulation_duration:
                    emergency = self.rng.choice(list(EmergencyType))
                    self.schedule_event(sos_time, 'SOS_GENERATE', node.node_id,
                                        {'emergency_type': emergency})

    def _handle_heartbeat(self, event: Event):
        """Process heartbeat event."""
        node = self.nodes[event.node_id]
        if not node.is_alive:
            return

        # Consume energy for transmission
        node.energy_model.consume_tx(node.battery_percent)
        node.battery_percent = max(0, node.battery_percent -
                                    node.energy_model.heartbeat_cost)
        node.heartbeats_sent += 1
        node.last_heartbeat_sent = self.current_time

        # Notify neighbors
        for neighbor_id in node.neighbors:
            neighbor = self.nodes.get(neighbor_id)
            if neighbor and neighbor.is_alive and node.can_reach(neighbor):
                if neighbor_id in neighbor.neighbor_heartbeats:
                    neighbor.neighbor_heartbeats[neighbor_id] = {
                        'last_seen': self.current_time,
                        'consecutive_misses': 0
                    }
                # Update neighbor info
                if node.node_id in neighbor.neighbors:
                    neighbor.neighbors[node.node_id]['last_seen'] = self.current_time
                    neighbor.neighbors[node.node_id]['battery'] = node.battery_percent
                    neighbor.neighbors[node.node_id]['consecutive_misses'] = 0
                    neighbor.neighbors[node.node_id]['status'] = 'ACTIVE'

        # Check for missed heartbeats from our neighbors (failure detection)
        self._check_neighbor_health(node)

        # Schedule next heartbeat
        interval = (self.config.heartbeat_interval_disaster
                    if self.mode == OperationalMode.DISASTER
                    else self.config.heartbeat_interval_normal)
        self.schedule_event(self.current_time + interval, 'HEARTBEAT', node.node_id)

    def _check_neighbor_health(self, node: Node):
        """Check if any neighbors have gone silent (failure detection)."""
        interval = (self.config.heartbeat_interval_disaster
                    if self.mode == OperationalMode.DISASTER
                    else self.config.heartbeat_interval_normal)
        timeout = 2 * interval

        for neighbor_id, info in list(node.neighbors.items()):
            if info['status'] == 'DOWN':
                continue
            time_since = self.current_time - info.get('last_seen', 0)
            if time_since > timeout:
                info['consecutive_misses'] = info.get('consecutive_misses', 0) + 1
                if info['consecutive_misses'] >= self.config.miss_threshold:
                    info['status'] = 'DOWN'
                    self._trigger_self_healing(node, neighbor_id)



    def _trigger_self_healing(self, detecting_node: Node, failed_node_id: str):
        """Trigger self-healing when a node failure is detected."""
        recovery_start = self.current_time

        # Invalidate routes through failed node
        routes_affected = 0
        for dest, route in list(detecting_node.route_table.items()):
            if route.next_hop == failed_node_id:
                route.status = 'DOWN'
                routes_affected += 1
                # Try to find alternative route
                alt = self._find_alternative_route(detecting_node, dest, failed_node_id)
                if alt:
                    detecting_node.route_table[dest] = alt

        recovery_time = self.current_time - recovery_start + \
                        self.rng.uniform(1.0, 5.0)  # Simulated computation time
        self.route_recovery_times.append(recovery_time)

        self.failure_events.append({
            'time': self.current_time,
            'failed_node': failed_node_id,
            'detected_by': detecting_node.node_id,
            'routes_affected': routes_affected,
            'recovery_time': recovery_time
        })

    def _find_alternative_route(self, node: Node, destination: str,
                                 avoid_node: str) -> Optional[RouteEntry]:
        """Find an alternative route avoiding the failed node."""
        best_route = None
        best_score = -1.0

        for neighbor_id, info in node.neighbors.items():
            if neighbor_id == avoid_node:
                continue
            if info['status'] != 'ACTIVE':
                continue

            # Calculate route score
            rssi_norm = (info['rssi'] + 120) / 80.0  # Normalize -120 to -40
            rssi_norm = max(0, min(1, rssi_norm))
            battery_norm = info['battery'] / 100.0
            hops_norm = 1.0 / self.config.max_ttl  # Assume 1 more hop

            score = (self.config.w_rssi * rssi_norm +
                     self.config.w_battery * battery_norm -
                     self.config.w_hops * hops_norm +
                     self.config.w_reliability * 0.5)  # Default reliability

            if score > best_score:
                best_score = score
                best_route = RouteEntry(
                    destination=destination,
                    next_hop=neighbor_id,
                    hop_count=2,  # Estimate
                    rssi=info['rssi'],
                    battery=info['battery'],
                    quality=int(score * 255),
                    last_updated=self.current_time,
                    status='ACTIVE'
                )

        return best_route

    def _handle_sos_generate(self, event: Event):
        """Generate an SOS packet from an SOS device."""
        node = self.nodes[event.node_id]
        if not node.is_alive:
            return

        self.total_sos_generated += 1

        # Create SOS packet
        packet = Packet(
            packet_id=f"{node.node_id}-{self.current_time:.0f}-{self.total_sos_generated}",
            packet_type=PacketType.SOS,
            source=node.node_id,
            destination="GW-01",  # Primary gateway
            priority=Priority.CRITICAL,
            ttl=self.config.max_ttl,
            hop_count=0,
            payload={
                'emergency_type': event.data['emergency_type'].name,
                'battery': node.battery_percent,
                'zone': node.node_id.split('-')[1] if '-' in node.node_id else '00'
            },
            created_at=self.current_time,
            path=[node.node_id]
        )

        # Find nearest relay to send to
        delivered = self._send_packet(node, packet)
        if not delivered:
            # Store for mobile relay collection
            node.stored_messages.append(packet)

    def _send_packet(self, sender: Node, packet: Packet) -> bool:
        """Attempt to send a packet from sender toward destination."""
        if packet.ttl <= 0:
            self.total_sos_dropped += 1
            sender.packets_dropped += 1
            return False

        # Energy cost
        sender.energy_model.consume_tx(sender.battery_percent)
        sender.battery_percent = max(0, sender.battery_percent -
                                      sender.energy_model.tx_cost)
        sender.packets_sent += 1

        # Find best next hop
        next_hop = self._get_next_hop(sender, packet.destination)
        if next_hop is None:
            # No route available
            if sender.node_type == NodeType.SOS_DEVICE:
                return False  # Will be stored for mobile relay
            sender.packets_dropped += 1
            return False

        next_node = self.nodes[next_hop]
        if not next_node.is_alive or not sender.can_reach(next_node):
            # Path broken — try alternative
            alt_hop = self._get_next_hop(sender, packet.destination,
                                          exclude=next_hop)
            if alt_hop:
                next_node = self.nodes[alt_hop]
            else:
                sender.packets_dropped += 1
                return False

        # Deliver to next hop
        packet.hop_count += 1
        packet.ttl -= 1
        packet.path.append(next_node.node_id)

        # Check if destination reached
        if next_node.node_type == NodeType.GATEWAY:
            self._deliver_to_gateway(next_node, packet)
            return True

        # Forward
        next_node.packets_received += 1
        if not next_node.is_duplicate(packet.packet_id, self.current_time):
            next_node.mark_seen(packet.packet_id, self.current_time)
            next_node.packets_forwarded += 1
            return self._send_packet(next_node, packet)
        else:
            return False  # Duplicate dropped

    def _get_next_hop(self, node: Node, destination: str,
                       exclude: str = None) -> Optional[str]:
        """Get the best next hop toward a destination."""
        # Check route table
        if destination in node.route_table:
            entry = node.route_table[destination]
            if entry.status == 'ACTIVE' and entry.next_hop != exclude:
                return entry.next_hop

        # No route — use routing agent to find best neighbor
        best_hop = None
        best_score = -1.0

        for neighbor_id, info in node.neighbors.items():
            if neighbor_id == exclude:
                continue
            if info['status'] != 'ACTIVE':
                continue

            neighbor = self.nodes.get(neighbor_id)
            if not neighbor or not neighbor.is_alive:
                continue

            # Prefer nodes closer to gateway (higher type number)
            type_bonus = 0.0
            if neighbor.node_type.value > node.node_type.value:
                type_bonus = 0.3
            elif neighbor.node_type == NodeType.GATEWAY:
                type_bonus = 1.0

            rssi_norm = (info['rssi'] + 120) / 80.0
            rssi_norm = max(0, min(1, rssi_norm))
            battery_norm = info['battery'] / 100.0

            score = (self.config.w_rssi * rssi_norm +
                     self.config.w_battery * battery_norm +
                     type_bonus)

            if score > best_score:
                best_score = score
                best_hop = neighbor_id

        return best_hop

    def _deliver_to_gateway(self, gateway: Node, packet: Packet):
        """Handle packet delivery at gateway."""
        self.total_sos_delivered += 1
        packet.delivered_at = self.current_time
        latency = packet.delivered_at - packet.created_at
        self.delivery_latencies.append(latency)
        gateway.packets_received += 1



    def _handle_node_failure(self, event: Event):
        """Simulate a node going down."""
        node = self.nodes[event.node_id]
        node.fail()
        print(f"[{self.current_time:.1f}s] NODE FAILURE: {event.node_id}")

    def _handle_mode_change(self, event: Event):
        """Change network operational mode."""
        new_mode = event.data['new_mode']
        self.mode = new_mode
        for node in self.nodes.values():
            node.mode = new_mode
        print(f"[{self.current_time:.1f}s] MODE CHANGE: {new_mode.name}")

    def run(self):
        """Run the simulation."""
        print(f"\n{'='*60}")
        print(f"SHLM Network Simulation Starting")
        print(f"Duration: {self.config.simulation_duration}s")
        print(f"Failure Rate: {self.config.failure_rate*100:.0f}%")
        print(f"{'='*60}\n")

        self._schedule_initial_events()

        while self.event_queue and self.current_time < self.config.simulation_duration:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time

            if event.event_type == 'HEARTBEAT':
                self._handle_heartbeat(event)
            elif event.event_type == 'SOS_GENERATE':
                self._handle_sos_generate(event)
            elif event.event_type == 'NODE_FAILURE':
                self._handle_node_failure(event)
            elif event.event_type == 'MODE_CHANGE':
                self._handle_mode_change(event)

        self._print_results()

    def _print_results(self):
        """Print simulation results summary."""
        print(f"\n{'='*60}")
        print(f"SIMULATION RESULTS")
        print(f"{'='*60}")

        # Packet Delivery Ratio
        pdr = (self.total_sos_delivered / self.total_sos_generated * 100
               if self.total_sos_generated > 0 else 0)
        print(f"\n--- Delivery Performance ---")
        print(f"Total SOS Generated:  {self.total_sos_generated}")
        print(f"Total SOS Delivered:  {self.total_sos_delivered}")
        print(f"Total SOS Dropped:    {self.total_sos_dropped}")
        print(f"Packet Delivery Ratio: {pdr:.1f}%")

        # Latency
        if self.delivery_latencies:
            avg_lat = sum(self.delivery_latencies) / len(self.delivery_latencies)
            max_lat = max(self.delivery_latencies)
            min_lat = min(self.delivery_latencies)
            print(f"\n--- Latency ---")
            print(f"Average Latency: {avg_lat:.2f}s")
            print(f"Min Latency:     {min_lat:.2f}s")
            print(f"Max Latency:     {max_lat:.2f}s")

        # Self-Healing
        if self.route_recovery_times:
            avg_recovery = sum(self.route_recovery_times) / len(self.route_recovery_times)
            print(f"\n--- Self-Healing ---")
            print(f"Total Failure Events:    {len(self.failure_events)}")
            print(f"Avg Route Recovery Time: {avg_recovery:.2f}s")

        # Energy
        print(f"\n--- Energy ---")
        alive_nodes = [n for n in self.nodes.values() if n.is_alive]
        if alive_nodes:
            avg_battery = sum(n.battery_percent for n in alive_nodes) / len(alive_nodes)
            min_battery = min(n.battery_percent for n in alive_nodes)
            print(f"Avg Battery Remaining: {avg_battery:.1f}%")
            print(f"Min Battery Remaining: {min_battery:.1f}%")

        # Node statistics
        print(f"\n--- Network Activity ---")
        total_sent = sum(n.packets_sent for n in self.nodes.values())
        total_fwd = sum(n.packets_forwarded for n in self.nodes.values())
        total_drop = sum(n.packets_dropped for n in self.nodes.values())
        print(f"Total Packets Sent:      {total_sent}")
        print(f"Total Packets Forwarded: {total_fwd}")
        print(f"Total Packets Dropped:   {total_drop}")

        print(f"\n{'='*60}")

    def get_results_dict(self) -> dict:
        """Return results as dictionary for further analysis."""
        pdr = (self.total_sos_delivered / self.total_sos_generated * 100
               if self.total_sos_generated > 0 else 0)
        avg_latency = (sum(self.delivery_latencies) / len(self.delivery_latencies)
                       if self.delivery_latencies else 0)
        avg_recovery = (sum(self.route_recovery_times) / len(self.route_recovery_times)
                        if self.route_recovery_times else 0)

        return {
            'pdr_percent': pdr,
            'avg_latency_s': avg_latency,
            'max_latency_s': max(self.delivery_latencies) if self.delivery_latencies else 0,
            'avg_recovery_time_s': avg_recovery,
            'total_sos_generated': self.total_sos_generated,
            'total_sos_delivered': self.total_sos_delivered,
            'failure_events': len(self.failure_events),
            'failure_rate': self.config.failure_rate,
            'num_nodes': len(self.nodes),
        }


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='SHLM Network Simulator')
    parser.add_argument('--nodes', type=int, default=50,
                        help='Number of SOS nodes (default: 50)')
    parser.add_argument('--failure-rate', type=float, default=0.2,
                        help='Relay failure rate 0.0-1.0 (default: 0.2)')
    parser.add_argument('--duration', type=float, default=7200,
                        help='Simulation duration in seconds (default: 7200)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed (default: 42)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output JSON file for results')
    args = parser.parse_args()

    config = SimConfig(
        num_sos_nodes=args.nodes,
        failure_rate=args.failure_rate,
        simulation_duration=args.duration,
        seed=args.seed,
    )

    sim = NetworkSimulator(config)
    sim.run()

    if args.output:
        results = sim.get_results_dict()
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
