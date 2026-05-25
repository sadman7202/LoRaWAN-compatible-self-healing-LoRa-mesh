# Self-Healing LoRa Mesh Routing Protocol Specification

## Protocol Name: SHLM (Self-Healing LoRa Mesh)

### Version: 1.0 (Research Draft)

---

## 1. Overview

### 1.1 Purpose
The SHLM protocol defines a multi-hop, self-healing routing mechanism for LoRa-based mesh networks designed specifically for disaster emergency communication. It combines reactive route discovery with proactive heartbeat-based link monitoring and AI-driven path selection.

### 1.2 Design Goals
1. **Reliability**: Achieve >95% SOS delivery under partial network failure
2. **Self-Healing**: Automatically recover from relay node failures within 30 seconds
3. **Energy Efficiency**: Maximize node operational lifetime (target: >72 hours)
4. **Low Latency**: SOS-to-gateway delivery within 5 minutes
5. **Scalability**: Support 20-100 nodes in a 100 sq km area
6. **Simplicity**: Implementable on resource-constrained MCUs (ESP32, 520KB RAM)

### 1.3 Protocol Classification
- **Type**: Hybrid (Proactive heartbeat + Reactive route discovery)
- **Topology**: Multi-tier hierarchical mesh
- **Intelligence**: AI-driven multi-criteria path selection
- **Failure Recovery**: Autonomous self-healing with mobile relay fallback

---

## 2. Network Architecture

### 2.1 Node Types and Roles

| Node Type | Role | Routing Capability | Power Budget |
|-----------|------|-------------------|--------------|
| SOS Device (Type 1) | Generate emergency messages | Source only (no forwarding) | Low (battery) |
| Local Relay (Type 2) | Collect & forward within cluster | Full routing | Medium (solar+battery) |
| Backbone Relay (Type 3) | Long-range inter-cluster routing | Full routing + priority | High (solar+battery) |
| Mobile Relay (Type 4) | Store-and-forward for isolated nodes | DTN routing | Medium (battery) |
| Gateway (Type 5) | Destination sink, rescue coordination | Sink + ACK generation | High (mains/solar/IPS) |

### 2.2 Network Topology Layers

```
Layer 3 (Long-range):  Gateway <---> Backbone Relays (5-8 km spacing)
Layer 2 (Mid-range):   Backbone <---> Local Relays (1-2 km spacing)
Layer 1 (Short-range): Local Relay <---> SOS Devices (300-700 m)
Layer 0 (DTN):         Mobile Relay <---> Isolated Nodes (opportunistic)
```

### 2.3 Communication Parameters

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Frequency | 868 MHz / 915 MHz (region-dependent) | ISM band, no license required |
| Spreading Factor | SF7 (local), SF9 (backbone), SF12 (emergency) | Range vs. throughput trade-off |
| Bandwidth | 125 kHz | Standard LoRa BW, good sensitivity |
| Coding Rate | 4/5 (normal), 4/8 (emergency) | Error correction trade-off |
| Tx Power | 14 dBm (local), 20 dBm (backbone) | Range requirement |
| Max Payload | 51 bytes (SF12) to 222 bytes (SF7) | LoRa PHY limitation |
| Channel | Multi-channel (8 channels) | Collision avoidance |

---

## 3. Addressing Scheme

### 3.1 Node Address Format
Each node has a unique 4-byte address:

```
[Type][Zone][Sequence]
 1B    1B    2B

Type: 0x01=SOS, 0x02=LocalRelay, 0x03=Backbone, 0x04=Mobile, 0x05=Gateway
Zone: 0x01-0xFF (deployment zone identifier)
Sequence: 0x0001-0xFFFF (unique within zone)
```

**Examples:**
```
SOS-TGH-014:     0x01 0x03 0x00 0x0E  (Type=SOS, Zone=3, Seq=14)
LREL-TGH-07:     0x02 0x03 0x00 0x07  (Type=LocalRelay, Zone=3, Seq=7)
BBR-TGH-04:      0x03 0x00 0x00 0x04  (Type=Backbone, Zone=0(global), Seq=4)
BR-TGH-02:       0x04 0x00 0x00 0x02  (Type=Mobile, Zone=0, Seq=2)
GATEWAY-01:      0x05 0x00 0x00 0x01  (Type=Gateway, Zone=0, Seq=1)
```

### 3.2 Broadcast Address
```
0xFF 0xFF 0xFF 0xFF  — All nodes (used for heartbeat, route discovery)
```

### 3.3 Zone Broadcast
```
0xFF 0x03 0xFF 0xFF  — All nodes in Zone 3
```

---

## 4. Operational Modes

### 4.1 Normal Mode
- Heartbeat interval: 60 seconds
- All traffic types allowed
- Full routing table maintenance
- Normal Tx power

### 4.2 Preparedness Mode (T-24h before disaster)
- Heartbeat interval: 30 seconds (increased monitoring)
- Route verification messages sent
- Battery status broadcast
- Health check initiated

### 4.3 Disaster Mode (Active emergency)
- Heartbeat interval: 120 seconds (save energy)
- Emergency packets get absolute priority
- Non-critical traffic suppressed
- Reduced Tx power for local comms, max power for backbone
- Battery conservation active

### 4.4 Isolated Mode (No path to gateway)
- Heartbeat interval: 300 seconds (maximum energy saving)
- Messages stored in local buffer
- Periodic beacon broadcast (every 60s) for mobile relay detection
- Emergency-only transmission

---

## 5. Routing Algorithm

### 5.1 Route Table Structure
Each routing node maintains a route table:

```
struct RouteEntry {
    uint32_t destination;      // Target node address
    uint32_t next_hop;         // Next hop address
    uint8_t  hop_count;        // Number of hops to destination
    int8_t   rssi;             // Last known RSSI to next_hop
    uint8_t  next_hop_battery; // Battery level of next_hop (0-100%)
    uint8_t  route_quality;    // Composite route score (0-255)
    uint32_t last_updated;     // Timestamp of last update
    uint8_t  status;           // ACTIVE=1, STALE=2, DOWN=3
};
```

### 5.2 Route Score Calculation (AI Routing Agent)

The routing agent computes a composite score for each possible path:

```
RouteScore(path) = w1 × NormalizedRSSI(path) 
                 + w2 × NormalizedBattery(path)
                 - w3 × NormalizedHops(path)
                 + w4 × ReliabilityHistory(path)
```

Where:
- `NormalizedRSSI` = (RSSI - RSSI_min) / (RSSI_max - RSSI_min), range [0,1]
- `NormalizedBattery` = min_battery_on_path / 100, range [0,1]
- `NormalizedHops` = hop_count / max_hops, range [0,1]
- `ReliabilityHistory` = successful_deliveries / total_attempts, range [0,1]

**Default weights:**
```
w1 = 0.30  (signal strength)
w2 = 0.30  (battery health)
w3 = 0.20  (hop count penalty)
w4 = 0.20  (historical reliability)
```

**Disaster mode weights (prioritize reliability):**
```
w1 = 0.25
w2 = 0.35  (battery more important — no recharge possible)
w3 = 0.15
w4 = 0.25  (reliability more important)
```

### 5.3 Route Discovery Process

#### Step 1: Local Route Check
```
if route_table.has_active_route(destination):
    return route_table.get_best_route(destination)
```

#### Step 2: Neighbor Discovery (if no route known)
```
broadcast ROUTE_REQUEST {
    source: self.address,
    destination: target_address,
    ttl: MAX_TTL (default: 8),
    timestamp: current_time
}
```

#### Step 3: Route Reply
When a node receives a ROUTE_REQUEST and either IS the destination or HAS a route:
```
unicast ROUTE_REPLY {
    source: self.address,
    destination: requester.address,
    path: [node1, node2, ..., target],
    metrics: {rssi: [], battery: [], hops: N}
}
```

#### Step 4: Route Selection
The requesting node collects all ROUTE_REPLY messages within a timeout window (default: 5 seconds) and selects the path with the highest RouteScore.

### 5.4 Route Maintenance

#### Periodic Route Refresh
Every `ROUTE_REFRESH_INTERVAL` (default: 300 seconds in normal mode):
- Verify top-2 routes to gateway are still active
- Update metrics (RSSI, battery levels)
- Prune stale entries (last_updated > 600 seconds ago)

#### Triggered Route Update
When a metric changes significantly:
```
if abs(new_rssi - cached_rssi) > 10 dBm:
    update_route_entry()
    
if next_hop_battery dropped below 20%:
    trigger_alternate_route_search()
```

---

## 6. Self-Healing Mechanism

### 6.1 Heartbeat Protocol

Each node periodically broadcasts a heartbeat:

```
HEARTBEAT {
    source: self.address,
    type: self.node_type,
    battery: self.battery_percent,
    mode: self.operational_mode,
    neighbor_count: len(self.neighbors),
    uptime: self.uptime_seconds,
    sequence: self.heartbeat_seq++
}
```

Heartbeat intervals by mode:
```
Normal:        60 seconds
Preparedness:  30 seconds
Disaster:     120 seconds
Isolated:     300 seconds
```

### 6.2 Failure Detection Algorithm

```
ALGORITHM: Failure Detection

Constants:
    MISS_THRESHOLD = 3          // consecutive misses to declare failure
    HEARTBEAT_TIMEOUT = 2 × heartbeat_interval  // expected receive window

For each neighbor N in neighbor_table:
    if (current_time - N.last_heartbeat_received) > HEARTBEAT_TIMEOUT:
        N.consecutive_misses++
        
        if N.consecutive_misses >= MISS_THRESHOLD:
            N.status = DOWN
            trigger_self_healing(N)
        elif N.consecutive_misses >= 1:
            N.status = STALE
            // Continue monitoring, don't route through
```

### 6.3 Self-Healing Procedure

```
ALGORITHM: Self-Healing Route Recovery

Input: Failed node N_failed

1. DETECT:
   - Mark N_failed as DOWN in neighbor table
   - Log failure event (timestamp, node_id, last_battery, last_rssi)

2. INVALIDATE:
   - For each route R in route_table:
       if R.next_hop == N_failed OR N_failed in R.path:
           R.status = DOWN
           affected_messages.add(R.pending_messages)

3. DISCOVER:
   - For each affected destination D:
       alternate_routes = find_routes_avoiding(N_failed, D)
       if alternate_routes is not empty:
           best = select_by_route_score(alternate_routes)
           install_route(D, best)
       else:
           // No alternate fixed path exists
           set_mode(ISOLATED) for affected source nodes
           enable_mobile_relay_beacon()

4. NOTIFY:
   - Broadcast ROUTE_DOWN message to neighbors:
     ROUTE_DOWN {
         failed_node: N_failed.address,
         affected_destinations: [D1, D2, ...],
         timestamp: current_time
     }

5. RECOVER PENDING:
   - For each message M in affected_messages:
       if new_route_exists(M.destination):
           forward(M, new_route)
       else:
           store_for_mobile_relay(M)

6. MONITOR:
   - Continue monitoring N_failed
   - If heartbeat resumes:
       N_failed.status = ACTIVE
       recalculate_all_routes()  // May re-include recovered node
```

### 6.4 Recovery Time Analysis

```
Worst-case detection time = MISS_THRESHOLD × HEARTBEAT_TIMEOUT
                          = 3 × (2 × 120s)  [disaster mode]
                          = 720 seconds (12 minutes)

Typical detection time   = MISS_THRESHOLD × heartbeat_interval
                         = 3 × 120s [disaster mode]
                         = 360 seconds (6 minutes)

Normal mode detection    = 3 × 60s = 180 seconds (3 minutes)

Route recalculation time = ~1-5 seconds (local computation)
Route verification time  = ~2-10 seconds (RTT to verify new path)

Total recovery time (normal mode):  ~185-195 seconds
Total recovery time (disaster mode): ~365-375 seconds
```

> **NOTE**: For the paper, you may want to optimize these values. The heartbeat interval in disaster mode could be reduced to 60s if energy budget allows, giving ~185s recovery.

---

## 7. Message Priority System

### 7.1 Priority Levels

| Priority | Value | Description | Queue Position | Max Retries |
|----------|-------|-------------|----------------|-------------|
| CRITICAL | 0x01 | Life-threatening (trapped, medical) | Front | 12 |
| HIGH | 0x02 | Urgent (boat needed, elderly/children) | Second | 8 |
| MEDIUM | 0x03 | Important (food/water request) | Third | 6 |
| LOW | 0x04 | Status update, heartbeat | Back | 3 |
| SYSTEM | 0x05 | Route updates, ACKs | Interleaved | 4 |

### 7.2 Priority Classification (Priority Agent)

The Priority Agent on SOS nodes classifies messages:

```
ALGORITHM: Priority Classification

Input: emergency_type (from button press)

if emergency_type contains "TRAPPED" or "MEDICAL":
    priority = CRITICAL
elif emergency_type contains "BOAT_NEEDED" or "CHILDREN" or "ELDERLY":
    priority = HIGH
elif emergency_type contains "FOOD" or "WATER":
    priority = MEDIUM
else:
    priority = LOW

// Escalation rule:
if message.retry_count > 6 AND priority > CRITICAL:
    priority = priority - 1  // Escalate after many failures
```

### 7.3 Queue Management

```
ALGORITHM: Priority Queue Insertion

Input: message M with priority P

queue.insert_at_priority_position(M, P)

// Ensure CRITICAL messages are always at front
// Within same priority: FIFO order
// Queue max size: 50 messages per node
// If queue full: drop oldest LOW priority message
```

---

## 8. Duplicate Detection

### 8.1 Message ID Structure
Each message has a globally unique ID:

```
MESSAGE_ID = [SOURCE_ADDR (4B)] + [TIMESTAMP (4B)] + [SEQUENCE (2B)]
Total: 10 bytes unique identifier
```

### 8.2 Duplicate Detection Table

Each relay maintains a recent message cache:

```
struct DuplicateCache {
    message_id: bytes[10],
    first_seen: uint32_t,
    forward_count: uint8_t
};

// Cache size: 200 entries (LRU eviction)
// Entry lifetime: 600 seconds (10 minutes)
```

### 8.3 Duplicate Handling Algorithm

```
ALGORITHM: Duplicate Check

Input: received message M

if duplicate_cache.contains(M.message_id):
    entry = duplicate_cache.get(M.message_id)
    entry.forward_count++
    DROP M  // Already processed
    return

// Not a duplicate
duplicate_cache.add(M.message_id, current_time, 0)
process_and_forward(M)
```

---

## 9. ACK (Acknowledgment) Mechanism

### 9.1 ACK Types

| ACK Type | Direction | Meaning |
|----------|-----------|---------|
| HOP_ACK | Next-hop → Sender | "I received your packet" |
| END_ACK | Gateway → Source | "Your SOS reached the command center" |
| RESCUE_ACK | Gateway → Source | "Rescue team has been assigned" |
| RESOLVE_ACK | Gateway → Source | "Incident resolved" |

### 9.2 Retry Policy

```
RETRY_SCHEDULE = [
    0,      // Immediate first send
    30,     // Retry 1: after 30 seconds
    60,     // Retry 2: after 60 seconds
    180,    // Retry 3: after 3 minutes
    300,    // Retry 4+: every 5 minutes
]

MAX_RETRIES = based on priority level (see Section 7.1)
```

### 9.3 ACK Routing
ACKs follow the reverse path of the original message:
```
Gateway → BBR-04 → LREL-07 → SOS-014

// If reverse path broken, ACK uses current best route to source
```

---

## 10. Mobile Relay Protocol (DTN Layer)

### 10.1 Mobile Relay Beacon

Mobile relays periodically broadcast their presence:

```
MOBILE_RELAY_BEACON {
    source: self.address,
    type: MOBILE_RELAY,
    gps_lat: current_latitude,
    gps_lon: current_longitude,
    buffer_capacity: remaining_slots,
    gateway_reachable: bool,
    timestamp: current_time
}

Beacon interval: 10 seconds (scanning mode)
```

### 10.2 Store-and-Forward Handshake

```
SEQUENCE:

1. Mobile Relay broadcasts BEACON
2. Isolated node detects BEACON (RSSI > threshold)
3. Isolated node sends TRANSFER_REQUEST {
       source: self.address,
       message_count: N,
       total_bytes: B,
       highest_priority: P
   }
4. Mobile Relay responds TRANSFER_ACCEPT {
       max_messages: M,  // How many it can accept
       priority_threshold: P_min  // Minimum priority it will accept
   }
5. Isolated node sends messages one-by-one (highest priority first)
6. Mobile Relay sends HOP_ACK for each received message
7. When done: TRANSFER_COMPLETE from both sides
```

### 10.3 Mobile Relay Collection Priority (Mobile Relay Agent)

```
ALGORITHM: Collection Priority Ordering

Input: List of detected SOS beacons with (node_id, priority, distance, message_count)

For each detected beacon B:
    collection_score(B) = w1 × priority_value(B.priority)
                        + w2 × (1.0 / B.distance)
                        + w3 × B.message_count

Sort beacons by collection_score (descending)
Approach highest-scoring beacon first

Weights:
    w1 = 0.50 (priority dominates)
    w2 = 0.30 (closer is better — saves time/fuel)
    w3 = 0.20 (more messages = more value)
```

### 10.4 Gateway Upload

When mobile relay enters gateway range:
```
1. Mobile Relay detects Gateway beacon (or known gateway address responds)
2. Mobile Relay sends BATCH_UPLOAD_REQUEST {
       message_count: N,
       oldest_message_age: T_oldest,
       priorities: [count_per_priority_level]
   }
3. Gateway responds BATCH_UPLOAD_ACCEPT
4. Mobile Relay sends all buffered messages (CRITICAL first)
5. Gateway processes, sends END_ACKs back through network
6. Mobile Relay clears delivered messages from buffer
```

---

## 11. Security Considerations (Future Work)

### 11.1 Threats
- **Replay attacks**: Attacker rebroadcasts old SOS messages
- **Spoofing**: Fake SOS from non-authorized devices
- **Jamming**: Intentional interference on LoRa channels
- **Tampering**: Physical compromise of relay nodes

### 11.2 Proposed Mitigations (for future implementation)
- **Message authentication**: HMAC-SHA256 with pre-shared keys
- **Replay protection**: Timestamp + sequence number validation
- **Node authentication**: Challenge-response during join
- **Encryption**: AES-128 for payload (LoRaWAN compatible)

> **NOTE**: Security is acknowledged as future work in the paper. The current protocol focuses on functional correctness and self-healing.

---

## 12. Protocol State Machine

### 12.1 Node State Machine

```
                    ┌─────────────┐
                    │   INIT      │
                    └──────┬──────┘
                           │ (power on, load config)
                           ▼
                    ┌─────────────┐
              ┌────▶│   NORMAL    │◀────┐
              │     └──────┬──────┘     │
              │            │            │
              │   (flood   │   (all     │
              │   warning) │   clear)   │
              │            ▼            │
              │     ┌─────────────┐    │
              │     │ PREPAREDNESS│    │
              │     └──────┬──────┘    │
              │            │            │
              │   (flood   │            │
              │   starts)  │            │
              │            ▼            │
              │     ┌─────────────┐    │
              │     │  DISASTER   │────┘
              │     └──────┬──────┘
              │            │
              │   (all paths│
              │    lost)    │
              │            ▼
              │     ┌─────────────┐
              └─────│  ISOLATED   │
                    └─────────────┘
                     (mobile relay
                      or path restored)
```

### 12.2 Message State Machine

```
CREATED → QUEUED → SENT → WAITING_ACK → DELIVERED
                     │                       │
                     │ (timeout)             │ (RESCUE_ACK)
                     ▼                       ▼
                  RETRYING              RESCUE_ASSIGNED
                     │                       │
                     │ (max retries)         │ (RESOLVE_ACK)
                     ▼                       ▼
              STORED_FOR_DTN             RESOLVED
                     │
                     │ (mobile relay collects)
                     ▼
                  DELIVERED
```

---

## 13. Configuration Parameters Summary

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| HEARTBEAT_INTERVAL_NORMAL | 60s | 30-120s | Heartbeat period in normal mode |
| HEARTBEAT_INTERVAL_DISASTER | 120s | 60-300s | Heartbeat period in disaster mode |
| MISS_THRESHOLD | 3 | 2-5 | Consecutive misses to declare failure |
| MAX_TTL | 8 | 4-12 | Maximum hops for any message |
| ROUTE_REFRESH_INTERVAL | 300s | 120-600s | Route table refresh period |
| DUPLICATE_CACHE_SIZE | 200 | 100-500 | Number of recent message IDs cached |
| DUPLICATE_CACHE_LIFETIME | 600s | 300-900s | How long to remember message IDs |
| MESSAGE_QUEUE_SIZE | 50 | 20-100 | Max messages buffered per node |
| MOBILE_BEACON_INTERVAL | 10s | 5-30s | Mobile relay beacon period |
| ROUTE_DISCOVERY_TIMEOUT | 5s | 3-10s | Wait time for route replies |
| W1_RSSI | 0.30 | 0.1-0.5 | Route score weight for signal |
| W2_BATTERY | 0.30 | 0.1-0.5 | Route score weight for battery |
| W3_HOPS | 0.20 | 0.1-0.4 | Route score weight for hop count |
| W4_RELIABILITY | 0.20 | 0.1-0.4 | Route score weight for history |

---

## 14. Interoperability with LoRaWAN

### 14.1 Gateway Integration
The Command Gateway supports BOTH:
- **Custom SHLM mesh protocol** (for receiving multi-hop mesh traffic)
- **Standard LoRaWAN** (for forwarding to LoRaWAN network server if available)

### 14.2 Protocol Translation at Gateway
```
SHLM Mesh Packet → Gateway → LoRaWAN Network Server (if uplink available)
                           → Local Dashboard (always)
                           → Satellite Uplink (if available)
```

### 14.3 LoRaWAN Compatibility Features
- SHLM uses LoRa PHY layer (same modulation)
- Packet format includes LoRaWAN-compatible header option
- Gateway can operate as standard LoRaWAN gateway simultaneously
- Device addresses can be mapped to LoRaWAN DevEUI format

---

## 15. Performance Targets

| Scenario | PDR Target | Latency Target | Recovery Target |
|----------|-----------|----------------|-----------------|
| Normal (0% failure) | >97% | <3s | N/A |
| Mild (10% failure) | >95% | <5s | <30s |
| Moderate (20% failure) | >93% | <10s | <45s |
| Severe (30% failure) | >88% | <30s | <60s |
| Critical (50% failure) | >80% | <60s | <120s |
| Isolated (no path) | >80% via mobile | <30 min | N/A (DTN) |
