# SHLM Packet Format Specification

## Version: 1.0 (Research Draft)

---

## 1. General Packet Structure

All SHLM packets follow this common frame format:

```
┌──────────┬──────────┬──────────┬──────────┬─────────┬──────────┐
│ Preamble │  Header  │  Source  │   Dest   │ Payload │   CRC    │
│  (LoRa)  │  (5B)    │  (4B)    │  (4B)    │ (var)   │  (2B)    │
└──────────┴──────────┴──────────┴──────────┴─────────┴──────────┘
```

### Total overhead: 15 bytes (Header + Source + Dest + CRC)
### Max payload: 51 bytes (SF12) to 222 bytes (SF7)
### Effective payload: 36-207 bytes depending on SF

---

## 2. Header Format (5 bytes)

```
Byte 0: [Protocol Version (4 bits) | Packet Type (4 bits)]
Byte 1: [Priority (3 bits) | TTL (5 bits)]
Byte 2: [Hop Count (4 bits) | Flags (4 bits)]
Byte 3-4: [Sequence Number (16 bits)]
```

### 2.1 Protocol Version (4 bits)
- `0x01` = SHLM v1.0

### 2.2 Packet Types (4 bits)

| Value | Type | Description |
|-------|------|-------------|
| 0x01 | SOS | Emergency message from end device |
| 0x02 | HEARTBEAT | Periodic keepalive |
| 0x03 | ROUTE_REQUEST | Route discovery request |
| 0x04 | ROUTE_REPLY | Route discovery response |
| 0x05 | ROUTE_DOWN | Route failure notification |
| 0x06 | HOP_ACK | Single-hop acknowledgment |
| 0x07 | END_ACK | End-to-end acknowledgment |
| 0x08 | RESCUE_ACK | Rescue assigned notification |
| 0x09 | RESOLVE_ACK | Incident resolved notification |
| 0x0A | MOBILE_BEACON | Mobile relay presence broadcast |
| 0x0B | TRANSFER_REQ | DTN transfer request |
| 0x0C | TRANSFER_ACC | DTN transfer accept |
| 0x0D | TRANSFER_DONE | DTN transfer complete |
| 0x0E | MODE_CHANGE | Operational mode change broadcast |
| 0x0F | RESERVED | Future use |



### 2.3 Priority (3 bits)

| Value | Level | Use |
|-------|-------|-----|
| 0x01 | CRITICAL | Life-threatening emergency |
| 0x02 | HIGH | Urgent assistance needed |
| 0x03 | MEDIUM | Important but not life-threatening |
| 0x04 | LOW | Status updates |
| 0x05 | SYSTEM | Protocol control messages |

### 2.4 TTL (5 bits)
- Range: 0-31
- Default: 8
- Decremented at each hop
- Packet dropped when TTL = 0

### 2.5 Flags (4 bits)

| Bit | Flag | Meaning |
|-----|------|---------|
| 0 | ACK_REQ | Acknowledgment requested |
| 1 | FRAG | Fragmented packet (not first) |
| 2 | LAST_FRAG | Last fragment |
| 3 | ENCRYPTED | Payload is encrypted |

---

## 3. SOS Packet (Type 0x01)

The primary emergency message sent by SOS devices.

```
Header (5B) + Source (4B) + Dest (4B) + SOS Payload + CRC (2B)
```

### SOS Payload Format (32 bytes)

```
Byte 0-9:   Message ID (10 bytes)
              [Source Addr (4B) + Timestamp (4B) + Sequence (2B)]
Byte 10:    Emergency Type (1 byte)
Byte 11:    Zone ID (1 byte)
Byte 12:    Battery Level (1 byte, 0-100%)
Byte 13:    Location Source (1 byte)
Byte 14-17: Latitude (4 bytes, float32) — if GPS available
Byte 18-21: Longitude (4 bytes, float32) — if GPS available
Byte 22-25: Timestamp (4 bytes, Unix epoch)
Byte 26:    People Count Estimate (1 byte, 0=unknown)
Byte 27:    Retry Count (1 byte)
Byte 28-31: Reserved (4 bytes, for future use)
```

### 3.1 Emergency Types (Byte 10)

| Value | Type | Description |
|-------|------|-------------|
| 0x01 | PEOPLE_TRAPPED | People stranded/trapped |
| 0x02 | BOAT_NEEDED | Water rescue required |
| 0x03 | MEDICAL | Medical emergency |
| 0x04 | FOOD_WATER | Food/water needed |
| 0x05 | TRAPPED_AND_BOAT | Combination: trapped + boat |
| 0x06 | MEDICAL_AND_BOAT | Medical + boat needed |
| 0x07 | CHILDREN_ELDERLY | Vulnerable population |
| 0x08 | BUILDING_COLLAPSE | Structural emergency |
| 0x09 | GENERAL_SOS | Unspecified emergency |
| 0xFF | TEST | Test message (non-emergency) |

### 3.2 Location Source (Byte 13)

| Value | Source | Accuracy |
|-------|--------|----------|
| 0x01 | GPS_LIVE | Real-time GPS fix |
| 0x02 | GPS_LAST | Last known GPS position |
| 0x03 | PRE_REGISTERED | Pre-deployed node location |
| 0x04 | UNKNOWN | No location available |



---

## 4. Heartbeat Packet (Type 0x02)

Periodic keepalive broadcast by all routing nodes.

### Heartbeat Payload (16 bytes)

```
Byte 0:     Node Type (1 byte)
Byte 1:     Battery Level (1 byte, 0-100%)
Byte 2:     Operational Mode (1 byte)
Byte 3:     Neighbor Count (1 byte)
Byte 4-7:   Uptime (4 bytes, seconds since boot)
Byte 8-9:   Heartbeat Sequence (2 bytes)
Byte 10:    Queue Occupancy (1 byte, 0-100%)
Byte 11:    Error Rate (1 byte, 0-100%)
Byte 12-15: Reserved (4 bytes)
```

### 4.1 Operational Mode (Byte 2)

| Value | Mode |
|-------|------|
| 0x01 | NORMAL |
| 0x02 | PREPAREDNESS |
| 0x03 | DISASTER |
| 0x04 | ISOLATED |
| 0x05 | LOW_BATTERY |
| 0x06 | MAINTENANCE |

---

## 5. Route Request Packet (Type 0x03)

Broadcast when a node needs to discover a route.

### Route Request Payload (14 bytes)

```
Byte 0-3:   Target Destination (4 bytes)
Byte 4-7:   Request ID (4 bytes, unique per request)
Byte 8-11:  Timestamp (4 bytes)
Byte 12:    Max Hops Allowed (1 byte)
Byte 13:    Request Flags (1 byte)
```

### Request Flags (Byte 13)

| Bit | Flag | Meaning |
|-----|------|---------|
| 0 | URGENT | High-priority route needed |
| 1 | AVOID_LOW_BATT | Exclude nodes below 20% battery |
| 2 | PREFER_BACKBONE | Prefer backbone relay path |
| 3-7 | RESERVED | Future use |

---

## 6. Route Reply Packet (Type 0x04)

Unicast response to a route request.

### Route Reply Payload (variable, max 40 bytes)

```
Byte 0-3:   Request ID (4 bytes, matches the request)
Byte 4:     Path Length (1 byte, number of hops)
Byte 5:     Aggregate RSSI (1 byte, normalized 0-255)
Byte 6:     Min Battery on Path (1 byte, 0-100%)
Byte 7:     Route Quality Score (1 byte, 0-255)
Byte 8+:    Path Nodes (4 bytes each, up to 8 nodes = 32 bytes)
```

---

## 7. Route Down Packet (Type 0x05)

Broadcast when a node failure is detected.

### Route Down Payload (12 bytes)

```
Byte 0-3:   Failed Node Address (4 bytes)
Byte 4-7:   Detection Timestamp (4 bytes)
Byte 8:     Failure Type (1 byte)
Byte 9:     Reporter Confidence (1 byte, 0-100%)
Byte 10-11: Affected Route Count (2 bytes)
```

### Failure Type (Byte 8)

| Value | Type |
|-------|------|
| 0x01 | HEARTBEAT_TIMEOUT | No heartbeat received |
| 0x02 | TX_FAILURE | Transmission to node failed |
| 0x03 | BATTERY_DEAD | Last known battery was critical |
| 0x04 | MANUAL_REPORT | Operator marked as down |



---

## 8. ACK Packets (Types 0x06-0x09)

### 8.1 Hop ACK Payload (6 bytes)

```
Byte 0-3:   Original Message ID fragment (first 4 bytes)
Byte 4:     ACK Status (1 byte)
Byte 5:     Receiver Queue Space (1 byte, 0-100%)
```

### 8.2 End ACK / Rescue ACK / Resolve ACK Payload (16 bytes)

```
Byte 0-9:   Original Message ID (10 bytes, full)
Byte 10:    ACK Type (1 byte: END=0x01, RESCUE=0x02, RESOLVE=0x03)
Byte 11-14: Gateway Timestamp (4 bytes)
Byte 15:    Incident Status Code (1 byte)
```

### Incident Status Codes (Byte 15)

| Value | Status |
|-------|--------|
| 0x01 | RECEIVED | Gateway received SOS |
| 0x02 | PROCESSING | Being reviewed by operator |
| 0x03 | ASSIGNED | Rescue team assigned |
| 0x04 | EN_ROUTE | Rescue team en route |
| 0x05 | ON_SCENE | Rescue team at location |
| 0x06 | RESOLVED | Incident closed |

---

## 9. Mobile Relay Beacon (Type 0x0A)

### Mobile Beacon Payload (20 bytes)

```
Byte 0:     Relay Type (1 byte: BOAT=0x01, BACKPACK=0x02)
Byte 1-4:   GPS Latitude (4 bytes, float32)
Byte 5-8:   GPS Longitude (4 bytes, float32)
Byte 9:     Battery Level (1 byte, 0-100%)
Byte 10:    Buffer Capacity (1 byte, free slots)
Byte 11:    Messages Carried (1 byte, current count)
Byte 12:    Gateway Reachable (1 byte, 0=No, 1=Yes)
Byte 13:    Speed (1 byte, km/h estimate)
Byte 14-17: Timestamp (4 bytes)
Byte 18-19: Beacon Sequence (2 bytes)
```

---

## 10. Transfer Request (Type 0x0B)

Sent by isolated node to mobile relay.

### Transfer Request Payload (10 bytes)

```
Byte 0:     Message Count (1 byte, how many to send)
Byte 1-2:   Total Bytes (2 bytes)
Byte 3:     Highest Priority (1 byte)
Byte 4:     Battery Level (1 byte)
Byte 5:     Time Since Isolation (1 byte, hours)
Byte 6-9:   Oldest Message Timestamp (4 bytes)
```

---

## 11. Transfer Accept (Type 0x0C)

Sent by mobile relay to isolated node.

### Transfer Accept Payload (4 bytes)

```
Byte 0:     Max Messages Accepted (1 byte)
Byte 1:     Priority Threshold (1 byte, minimum priority accepted)
Byte 2:     Available Buffer (1 byte, slots)
Byte 3:     Transfer Window (1 byte, seconds available for transfer)
```

---

## 12. Mode Change Packet (Type 0x0E)

Broadcast by gateway to change network operational mode.

### Mode Change Payload (8 bytes)

```
Byte 0:     New Mode (1 byte)
Byte 1:     Effective Immediately (1 byte, 0=scheduled, 1=immediate)
Byte 2-5:   Effective Timestamp (4 bytes, if scheduled)
Byte 6:     Heartbeat Interval Override (1 byte, seconds/10)
Byte 7:     Authority Level (1 byte, GATEWAY=0x01, OPERATOR=0x02)
```

---

## 13. Example Packet Encodings

### 13.1 SOS Packet Example (People Trapped + Boat Needed)

```
HEADER:
  Version=1, Type=SOS(0x01)     → 0x11
  Priority=CRITICAL(0x01), TTL=8 → 0x28
  HopCount=0, Flags=ACK_REQ(1)  → 0x01
  Sequence=145                   → 0x00 0x91

SOURCE: SOS-TGH-014             → 0x01 0x03 0x00 0x0E
DEST: GATEWAY-01 (broadcast)    → 0x05 0x00 0x00 0x01

PAYLOAD (SOS):
  MessageID: 0x01030000E + timestamp + seq (10B)
  EmergencyType: TRAPPED_AND_BOAT(0x05)
  ZoneID: 0x03
  Battery: 72 (0x48)
  LocationSource: PRE_REGISTERED(0x03)
  Lat: [4B float, pre-registered]
  Lon: [4B float, pre-registered]
  Timestamp: [4B unix epoch]
  PeopleCount: 0x00 (unknown)
  RetryCount: 0x00
  Reserved: 0x00000000

CRC: [2 bytes CRC-16]

Total packet size: 5 + 4 + 4 + 32 + 2 = 47 bytes
→ Fits within SF12 limit (51 bytes payload)
```

### 13.2 Heartbeat Packet Example

```
HEADER:
  Version=1, Type=HEARTBEAT(0x02) → 0x12
  Priority=SYSTEM(0x05), TTL=1    → 0xA1
  HopCount=0, Flags=0             → 0x00
  Sequence=4521                   → 0x11 0xA9

SOURCE: LREL-TGH-07              → 0x02 0x03 0x00 0x07
DEST: BROADCAST                  → 0xFF 0xFF 0xFF 0xFF

PAYLOAD (Heartbeat):
  NodeType: LOCAL_RELAY(0x02)
  Battery: 85 (0x55)
  Mode: DISASTER(0x03)
  NeighborCount: 4 (0x04)
  Uptime: 86400 seconds (0x00015180)
  HeartbeatSeq: 4521 (0x11A9)
  QueueOccupancy: 20% (0x14)
  ErrorRate: 2% (0x02)
  Reserved: 0x00000000

CRC: [2 bytes]

Total: 5 + 4 + 4 + 16 + 2 = 31 bytes
→ Easily fits in all SF modes
```



---

## 14. Packet Size Summary

| Packet Type | Header | Addresses | Payload | CRC | Total |
|-------------|--------|-----------|---------|-----|-------|
| SOS | 5B | 8B | 32B | 2B | 47B |
| Heartbeat | 5B | 8B | 16B | 2B | 31B |
| Route Request | 5B | 8B | 14B | 2B | 29B |
| Route Reply | 5B | 8B | 8-40B | 2B | 23-55B |
| Route Down | 5B | 8B | 12B | 2B | 27B |
| Hop ACK | 5B | 8B | 6B | 2B | 21B |
| End/Rescue/Resolve ACK | 5B | 8B | 16B | 2B | 31B |
| Mobile Beacon | 5B | 8B | 20B | 2B | 35B |
| Transfer Request | 5B | 8B | 10B | 2B | 25B |
| Transfer Accept | 5B | 8B | 4B | 2B | 19B |
| Mode Change | 5B | 8B | 8B | 2B | 23B |

### SF Compatibility

| SF | Max PHY Payload | Compatible Packets |
|----|-----------------|-------------------|
| SF7 | 222 bytes | All |
| SF8 | 222 bytes | All |
| SF9 | 115 bytes | All |
| SF10 | 51 bytes | All (Route Reply may need fragmentation) |
| SF11 | 51 bytes | All (Route Reply may need fragmentation) |
| SF12 | 51 bytes | All (Route Reply may need fragmentation) |

---

## 15. Error Detection

### CRC-16 (CCITT)
- Polynomial: 0x1021
- Initial value: 0xFFFF
- Computed over: Header + Source + Dest + Payload
- Appended as last 2 bytes (big-endian)

### Validation
```
On receive:
    computed_crc = CRC16(packet[0 : len-2])
    received_crc = packet[len-2 : len]
    if computed_crc != received_crc:
        DROP packet (corrupt)
        increment error_counter
```

---

## 16. Implementation Notes

### 16.1 Byte Order
- All multi-byte fields are **big-endian** (network byte order)
- Exception: GPS float32 uses IEEE 754 format

### 16.2 Timestamp Format
- 4-byte unsigned integer
- Unix epoch (seconds since 1970-01-01 00:00:00 UTC)
- Nodes synchronize time from gateway heartbeats

### 16.3 Message ID Uniqueness
```
MESSAGE_ID = SOURCE_ADDR (4B) || TIMESTAMP (4B) || SEQUENCE (2B)

- Source address ensures uniqueness across nodes
- Timestamp ensures uniqueness across time
- Sequence handles multiple messages in same second
- Combined: globally unique with 10-byte ID
```

### 16.4 Fragmentation (for Route Reply at high SF)
When Route Reply exceeds max payload:
```
Fragment 1: Header(FRAG=1, LAST=0) + Payload[0:max]
Fragment 2: Header(FRAG=1, LAST=1) + Payload[max:end]

Reassembly: by (Source, Sequence) matching
Timeout: 10 seconds for all fragments
```

---

## 17. C Struct Definitions (for firmware implementation)

```c
// Common header
typedef struct __attribute__((packed)) {
    uint8_t  version_type;    // [version:4][type:4]
    uint8_t  priority_ttl;    // [priority:3][ttl:5]
    uint8_t  hops_flags;      // [hop_count:4][flags:4]
    uint16_t sequence;        // Packet sequence number
} SHLMHeader;

// Node address
typedef struct __attribute__((packed)) {
    uint8_t  node_type;
    uint8_t  zone_id;
    uint16_t node_seq;
} SHLMAddress;

// SOS payload
typedef struct __attribute__((packed)) {
    uint8_t  message_id[10];
    uint8_t  emergency_type;
    uint8_t  zone_id;
    uint8_t  battery;
    uint8_t  location_source;
    float    latitude;
    float    longitude;
    uint32_t timestamp;
    uint8_t  people_count;
    uint8_t  retry_count;
    uint8_t  reserved[4];
} SOSPayload;  // 32 bytes

// Heartbeat payload
typedef struct __attribute__((packed)) {
    uint8_t  node_type;
    uint8_t  battery;
    uint8_t  mode;
    uint8_t  neighbor_count;
    uint32_t uptime;
    uint16_t heartbeat_seq;
    uint8_t  queue_occupancy;
    uint8_t  error_rate;
    uint8_t  reserved[4];
} HeartbeatPayload;  // 16 bytes

// Complete packet frame
typedef struct __attribute__((packed)) {
    SHLMHeader  header;       // 5 bytes
    SHLMAddress source;       // 4 bytes
    SHLMAddress destination;  // 4 bytes
    uint8_t     payload[];    // Variable length
    // CRC16 appended after payload
} SHLMPacket;
```
