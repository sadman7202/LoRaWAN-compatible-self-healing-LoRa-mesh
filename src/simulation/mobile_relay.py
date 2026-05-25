"""
Mobile Relay - Store-and-Forward DTN Simulation
================================================
Simulates boat/backpack mobile relays that physically move through
the deployment area, collecting stored messages from isolated nodes
and delivering them to the gateway when in range.

Implements the Mobile Relay Agent (Agent #6 in the 7-agent framework)
which prioritizes SOS collection based on severity, distance, and
message count.

Author: [Your Name]
Date: 2026
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, auto


class MobileRelayType(Enum):
    BOAT = 1
    BACKPACK = 2


class MobileRelayState(Enum):
    IDLE = auto()           # At base, not deployed
    SCANNING = auto()       # Moving through area, scanning for beacons
    COLLECTING = auto()     # Near isolated node, collecting messages
    RETURNING = auto()      # Heading back toward gateway
    UPLOADING = auto()      # In gateway range, uploading buffer


@dataclass
class Position:
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class StoredMessage:
    """A message stored in the mobile relay buffer."""
    message_id: str
    source_node: str
    priority: int        # 1=CRITICAL, 5=SYSTEM
    emergency_type: str
    created_at: float
    collected_at: float
    zone: str



@dataclass
class DetectedBeacon:
    """A beacon detected from an isolated node."""
    node_id: str
    position: Position
    distance: float
    priority: int
    message_count: int
    time_isolated_hours: float


# ============================================================
# MOBILE RELAY AGENT (Agent #6)
# ============================================================

class MobileRelayAgent:
    """
    Intelligent agent that decides the order in which the mobile
    relay should approach isolated nodes for message collection.
    
    Scoring formula:
        CollectionScore = w1 * PriorityValue 
                        + w2 * (1 / Distance) 
                        + w3 * MessageCount
    
    Where:
        w1 = 0.50 (priority dominates)
        w2 = 0.30 (closer = better, saves time/fuel)
        w3 = 0.20 (more messages = more value)
    """

    def __init__(self, w_priority=0.50, w_distance=0.30, w_messages=0.20):
        self.w_priority = w_priority
        self.w_distance = w_distance
        self.w_messages = w_messages

    def prioritize_collection(self, beacons: List[DetectedBeacon]) -> List[DetectedBeacon]:
        """
        Sort detected beacons by collection priority (highest first).
        
        Args:
            beacons: List of detected beacon signals from isolated nodes
            
        Returns:
            Sorted list (highest priority first)
        """
        if not beacons:
            return []

        # Normalize values for scoring
        max_distance = max(b.distance for b in beacons) or 1.0
        max_messages = max(b.message_count for b in beacons) or 1

        scored = []
        for beacon in beacons:
            # Priority value: CRITICAL(1)=1.0, HIGH(2)=0.8, MED(3)=0.6, LOW(4)=0.4
            priority_score = max(0.0, 1.0 - (beacon.priority - 1) * 0.2)

            # Distance score: closer = higher (inverse normalized)
            distance_score = 1.0 - (beacon.distance / max_distance) if max_distance > 0 else 1.0

            # Message count score: more messages = higher
            message_score = beacon.message_count / max_messages if max_messages > 0 else 0.0

            # Weighted combination
            total_score = (self.w_priority * priority_score +
                          self.w_distance * distance_score +
                          self.w_messages * message_score)

            scored.append((total_score, beacon))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored]



# ============================================================
# MOBILE RELAY CLASS
# ============================================================

class MobileRelay:
    """
    Simulates a mobile relay (boat or backpack) that physically
    moves through the deployment area.
    """

    def __init__(self, relay_id: str, relay_type: MobileRelayType,
                 start_position: Position, gateway_position: Position,
                 speed_mps: float = 2.0, collection_range: float = 500.0,
                 buffer_capacity: int = 100):
        """
        Args:
            relay_id: Unique identifier (e.g., "MR-01")
            relay_type: BOAT or BACKPACK
            start_position: Initial position (usually near gateway)
            gateway_position: Position of the command gateway
            speed_mps: Movement speed in meters per second
                       (boat ~3-5 m/s, backpack ~1.5 m/s)
            collection_range: LoRa range for collecting messages (m)
            buffer_capacity: Maximum messages that can be stored
        """
        self.relay_id = relay_id
        self.relay_type = relay_type
        self.position = Position(start_position.x, start_position.y)
        self.gateway_position = gateway_position
        self.speed_mps = speed_mps
        self.collection_range = collection_range
        self.buffer_capacity = buffer_capacity

        self.state = MobileRelayState.IDLE
        self.buffer: List[StoredMessage] = []
        self.agent = MobileRelayAgent()

        # Movement tracking
        self.target_position: Optional[Position] = None
        self.path: List[Position] = []  # Waypoints to visit
        self.total_distance_traveled = 0.0

        # Statistics
        self.messages_collected = 0
        self.messages_delivered = 0
        self.nodes_visited = 0
        self.collection_events: List[dict] = []

    @property
    def buffer_remaining(self) -> int:
        return self.buffer_capacity - len(self.buffer)

    @property
    def is_buffer_full(self) -> bool:
        return len(self.buffer) >= self.buffer_capacity

    def deploy(self, target_area_center: Position):
        """Deploy mobile relay toward target area."""
        self.state = MobileRelayState.SCANNING
        self.target_position = target_area_center

    def move_toward(self, target: Position, time_step: float) -> bool:
        """
        Move toward target position for one time step.
        
        Returns True if target reached.
        """
        distance = self.position.distance_to(target)
        move_distance = self.speed_mps * time_step

        if move_distance >= distance:
            # Reached target
            self.total_distance_traveled += distance
            self.position = Position(target.x, target.y)
            return True
        else:
            # Move toward target
            dx = target.x - self.position.x
            dy = target.y - self.position.y
            ratio = move_distance / distance
            self.position.x += dx * ratio
            self.position.y += dy * ratio
            self.total_distance_traveled += move_distance
            return False

    def scan_for_beacons(self, isolated_nodes: List[dict]) -> List[DetectedBeacon]:
        """
        Scan for SOS beacons from isolated nodes within range.
        
        Args:
            isolated_nodes: List of dicts with keys:
                node_id, position, priority, message_count, isolation_time
        
        Returns:
            List of detected beacons within collection_range
        """
        detected = []
        for node_info in isolated_nodes:
            node_pos = node_info['position']
            distance = self.position.distance_to(node_pos)

            if distance <= self.collection_range:
                beacon = DetectedBeacon(
                    node_id=node_info['node_id'],
                    position=node_pos,
                    distance=distance,
                    priority=node_info['priority'],
                    message_count=node_info['message_count'],
                    time_isolated_hours=node_info.get('isolation_time', 0)
                )
                detected.append(beacon)

        return detected

    def collect_messages(self, node_id: str, messages: List[dict],
                         current_time: float) -> int:
        """
        Collect stored messages from an isolated node.
        
        Args:
            node_id: ID of the node being collected from
            messages: List of message dicts to collect
            current_time: Current simulation time
            
        Returns:
            Number of messages actually collected
        """
        collected = 0
        # Sort by priority (CRITICAL first)
        sorted_msgs = sorted(messages, key=lambda m: m.get('priority', 5))

        for msg in sorted_msgs:
            if self.is_buffer_full:
                break
            stored = StoredMessage(
                message_id=msg['packet_id'],
                source_node=node_id,
                priority=msg.get('priority', 3),
                emergency_type=msg.get('emergency_type', 'UNKNOWN'),
                created_at=msg.get('created_at', 0),
                collected_at=current_time,
                zone=msg.get('zone', '00')
            )
            self.buffer.append(stored)
            collected += 1

        self.messages_collected += collected
        self.nodes_visited += 1
        self.collection_events.append({
            'node_id': node_id,
            'time': current_time,
            'messages_collected': collected,
            'buffer_level': len(self.buffer)
        })
        return collected

    def upload_to_gateway(self, current_time: float) -> List[StoredMessage]:
        """
        Upload all buffered messages to the gateway.
        
        Returns list of delivered messages.
        """
        delivered = list(self.buffer)
        self.messages_delivered += len(delivered)
        self.buffer.clear()
        self.state = MobileRelayState.IDLE
        return delivered

    def is_near_gateway(self) -> bool:
        """Check if mobile relay is within gateway range."""
        return self.position.distance_to(self.gateway_position) <= self.collection_range

    def get_stats(self) -> dict:
        """Return collection statistics."""
        return {
            'relay_id': self.relay_id,
            'type': self.relay_type.name,
            'messages_collected': self.messages_collected,
            'messages_delivered': self.messages_delivered,
            'nodes_visited': self.nodes_visited,
            'total_distance_km': self.total_distance_traveled / 1000.0,
            'buffer_current': len(self.buffer),
            'collection_events': len(self.collection_events),
        }


# ============================================================
# DEMO / TEST
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("MOBILE RELAY SIMULATION DEMO")
    print("=" * 60)

    # Setup
    gateway_pos = Position(9000, 5000)
    relay = MobileRelay(
        relay_id="MR-01",
        relay_type=MobileRelayType.BOAT,
        start_position=Position(8000, 5000),
        gateway_position=gateway_pos,
        speed_mps=3.0,  # Boat speed
        collection_range=700.0,
        buffer_capacity=50
    )

    # Simulate isolated nodes
    isolated_nodes = [
        {'node_id': 'SOS-014', 'position': Position(2000, 4000),
         'priority': 1, 'message_count': 3, 'isolation_time': 2.0},
        {'node_id': 'SOS-019', 'position': Position(2500, 4500),
         'priority': 1, 'message_count': 1, 'isolation_time': 1.5},
        {'node_id': 'SOS-025', 'position': Position(3000, 3500),
         'priority': 3, 'message_count': 2, 'isolation_time': 3.0},
        {'node_id': 'SOS-031', 'position': Position(1500, 5000),
         'priority': 2, 'message_count': 4, 'isolation_time': 4.0},
    ]

    # Deploy relay
    relay.deploy(Position(2500, 4500))
    print(f"\nRelay {relay.relay_id} deployed toward isolated area")

    # Simulate movement toward first cluster
    time_step = 10.0  # 10 second steps
    sim_time = 0.0
    while sim_time < 3600:  # 1 hour max
        # Move toward target
        if relay.target_position:
            reached = relay.move_toward(relay.target_position, time_step)
            if reached:
                print(f"  T+{sim_time:.0f}s: Reached target area")
                relay.state = MobileRelayState.SCANNING

        # Scan for beacons
        if relay.state == MobileRelayState.SCANNING:
            beacons = relay.scan_for_beacons(isolated_nodes)
            if beacons:
                # Agent prioritizes collection order
                prioritized = relay.agent.prioritize_collection(beacons)
                print(f"  T+{sim_time:.0f}s: Detected {len(beacons)} beacons")
                for b in prioritized:
                    print(f"    → {b.node_id} (P{b.priority}, {b.distance:.0f}m, "
                          f"{b.message_count} msgs)")

                # Collect from highest priority node
                target_beacon = prioritized[0]
                # Simulate collection
                fake_messages = [
                    {'packet_id': f'{target_beacon.node_id}-msg-{i}',
                     'priority': target_beacon.priority,
                     'emergency_type': 'PEOPLE_TRAPPED',
                     'created_at': sim_time - 600,
                     'zone': '03'}
                    for i in range(target_beacon.message_count)
                ]
                collected = relay.collect_messages(
                    target_beacon.node_id, fake_messages, sim_time)
                print(f"  T+{sim_time:.0f}s: Collected {collected} messages "
                      f"from {target_beacon.node_id}")

                # Remove visited node from isolated list
                isolated_nodes = [n for n in isolated_nodes
                                  if n['node_id'] != target_beacon.node_id]

                if not isolated_nodes or relay.is_buffer_full:
                    # Return to gateway
                    relay.state = MobileRelayState.RETURNING
                    relay.target_position = gateway_pos
                    print(f"  T+{sim_time:.0f}s: Returning to gateway")

        # Check if near gateway for upload
        if relay.state == MobileRelayState.RETURNING and relay.is_near_gateway():
            delivered = relay.upload_to_gateway(sim_time)
            print(f"  T+{sim_time:.0f}s: Uploaded {len(delivered)} messages to gateway")
            break

        sim_time += time_step

    # Print stats
    print(f"\n--- Mobile Relay Statistics ---")
    stats = relay.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
