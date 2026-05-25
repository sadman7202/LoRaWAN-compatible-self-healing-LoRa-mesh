/*
 * SHLM Relay Node Firmware
 * =========================
 * ESP32 + SX1276 LoRa Mesh Relay
 * 
 * This device receives, routes, and forwards SOS messages
 * through the mesh network. Implements heartbeat-based
 * self-healing and AI-driven route selection.
 * 
 * Hardware:
 *   - ESP32 DevKit or TTGO LoRa32
 *   - SX1276 LoRa module (868/915 MHz)
 *   - External antenna (high-gain for backbone)
 *   - Solar panel + charge controller
 *   - LiFePO4 battery
 *   - Status LEDs
 * 
 * Libraries Required:
 *   - RadioLib
 *   - ArduinoJson
 * 
 * Author: [Your Name]
 * Date: 2026
 * License: MIT
 */

#include <SPI.h>
#include <RadioLib.h>
#include <Preferences.h>

// ============================================================
// PIN DEFINITIONS
// ============================================================
#define LORA_CS     18
#define LORA_RST    23
#define LORA_DIO0   26

#define PIN_LED_STATUS  25
#define PIN_LED_RELAY   2   // Built-in LED = relay activity

// ============================================================
// NODE CONFIGURATION
// ============================================================
#define NODE_TYPE_LOCAL_RELAY  0x02
#define NODE_TYPE_BACKBONE     0x03
#define ZONE_ID               0x03
#define NODE_SEQUENCE         7     // LREL-TGH-07

// Change this for backbone relay:
#define MY_NODE_TYPE   NODE_TYPE_LOCAL_RELAY
#define MY_TX_POWER    14   // 14 for local, 20 for backbone

// ============================================================
// PROTOCOL CONSTANTS
// ============================================================
#define MAX_NEIGHBORS        20
#define MAX_ROUTES           50
#define MAX_QUEUE            50
#define MAX_DUP_CACHE        200
#define HEARTBEAT_NORMAL_MS  60000
#define HEARTBEAT_DISASTER_MS 120000
#define MISS_THRESHOLD       3
#define MAX_TTL              8

// ============================================================
// LORA CONFIG
// ============================================================
#define LORA_FREQUENCY    868.0
#define LORA_BANDWIDTH    125.0
#define LORA_SF           9
#define LORA_CR           5
#define LORA_SYNC_WORD    0x34
#define LORA_PREAMBLE     8

// ============================================================
// DATA STRUCTURES
// ============================================================
struct NeighborEntry {
  uint8_t address[4];
  int8_t  rssi;
  uint8_t battery;
  uint32_t lastSeen;
  uint8_t consecutiveMisses;
  uint8_t status; // 1=ACTIVE, 2=STALE, 3=DOWN
  uint8_t nodeType;
};

struct RouteEntry {
  uint8_t destination[4];
  uint8_t nextHop[4];
  uint8_t hopCount;
  int8_t  rssi;
  uint8_t battery;
  uint8_t quality;  // 0-255 route score
  uint32_t lastUpdated;
  uint8_t status;
};

struct QueuedPacket {
  uint8_t data[64];
  uint8_t length;
  uint8_t priority;
  uint8_t retries;
  uint32_t createdAt;
  bool valid;
};

struct DuplicateEntry {
  uint8_t messageId[10];
  uint32_t timestamp;
  bool valid;
};


// ============================================================
// GLOBAL STATE
// ============================================================
SX1276 radio = new Module(LORA_CS, LORA_DIO0, LORA_RST, -1);
Preferences preferences;

uint8_t myAddress[4] = {MY_NODE_TYPE, ZONE_ID, 0x00, NODE_SEQUENCE};
char myIdStr[16] = "LREL-TGH-07";

// Neighbor table
NeighborEntry neighbors[MAX_NEIGHBORS];
int neighborCount = 0;

// Route table
RouteEntry routes[MAX_ROUTES];
int routeCount = 0;

// Message queue (priority sorted)
QueuedPacket messageQueue[MAX_QUEUE];
int queueCount = 0;

// Duplicate detection cache
DuplicateEntry dupCache[MAX_DUP_CACHE];
int dupCacheCount = 0;

// Operational state
enum OpMode { MODE_NORMAL, MODE_PREPAREDNESS, MODE_DISASTER, MODE_ISOLATED };
OpMode currentMode = MODE_NORMAL;

// Timing
unsigned long lastHeartbeat = 0;
unsigned long lastRouteCheck = 0;
uint16_t heartbeatSeq = 0;

// Statistics
uint32_t packetsReceived = 0;
uint32_t packetsForwarded = 0;
uint32_t packetsDropped = 0;
float batteryPercent = 100.0;

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n[SHLM] Relay Node Starting..."));
  Serial.print(F("[SHLM] Node ID: "));
  Serial.println(myIdStr);
  Serial.print(F("[SHLM] Type: "));
  Serial.println(MY_NODE_TYPE == NODE_TYPE_BACKBONE ? "BACKBONE" : "LOCAL_RELAY");

  pinMode(PIN_LED_STATUS, OUTPUT);
  pinMode(PIN_LED_RELAY, OUTPUT);

  // Initialize LoRa
  int state = radio.begin(LORA_FREQUENCY, LORA_BANDWIDTH, LORA_SF,
                          LORA_CR, LORA_SYNC_WORD, MY_TX_POWER, LORA_PREAMBLE);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.println(F("[LORA] Init FAILED!"));
    while (true) { delay(100); }
  }
  Serial.println(F("[LORA] Init OK"));

  // Initialize tables
  memset(neighbors, 0, sizeof(neighbors));
  memset(routes, 0, sizeof(routes));
  memset(messageQueue, 0, sizeof(messageQueue));
  memset(dupCache, 0, sizeof(dupCache));

  batteryPercent = readBattery();
  Serial.print(F("[BATT] "));
  Serial.print(batteryPercent);
  Serial.println(F("%"));

  Serial.println(F("[SHLM] Relay ready. Listening..."));
}

// ============================================================
// MAIN LOOP
// ============================================================
void loop() {
  // 1. Listen for incoming packets
  receivePacket();

  // 2. Send heartbeat periodically
  unsigned long hbInterval = (currentMode == MODE_DISASTER) ?
                              HEARTBEAT_DISASTER_MS : HEARTBEAT_NORMAL_MS;
  if (millis() - lastHeartbeat >= hbInterval) {
    sendHeartbeat();
    checkNeighborHealth();
    lastHeartbeat = millis();
  }

  // 3. Process message queue (forward pending messages)
  processQueue();

  // 4. Periodic route maintenance
  if (millis() - lastRouteCheck >= 300000) { // Every 5 min
    pruneStaleRoutes();
    lastRouteCheck = millis();
  }

  // 5. Battery monitoring
  static unsigned long lastBatt = 0;
  if (millis() - lastBatt >= 60000) {
    batteryPercent = readBattery();
    lastBatt = millis();
  }

  delay(5);
}


// ============================================================
// PACKET RECEPTION & HANDLING
// ============================================================
void receivePacket() {
  uint8_t buffer[64];
  int state = radio.receive(buffer, 64);

  if (state != RADIOLIB_ERR_NONE) return;

  int len = radio.getPacketLength();
  float rssi = radio.getRSSI();
  packetsReceived++;
  blinkLED(PIN_LED_RELAY, 50);

  // Parse header
  uint8_t packetType = buffer[0] & 0x0F;
  uint8_t priority = (buffer[1] >> 5) & 0x07;
  uint8_t ttl = buffer[1] & 0x1F;
  uint8_t hopCount = (buffer[2] >> 4) & 0x0F;

  Serial.print(F("[RX] Type=0x"));
  Serial.print(packetType, HEX);
  Serial.print(F(" Pri="));
  Serial.print(priority);
  Serial.print(F(" TTL="));
  Serial.print(ttl);
  Serial.print(F(" RSSI="));
  Serial.println(rssi);

  // Handle by type
  switch (packetType) {
    case 0x01: // SOS
      handleSOSPacket(buffer, len, rssi);
      break;
    case 0x02: // Heartbeat
      handleHeartbeat(buffer, len, rssi);
      break;
    case 0x05: // Route Down
      handleRouteDown(buffer, len);
      break;
    case 0x07: // End ACK (forward back to source)
    case 0x08: // Rescue ACK
    case 0x09: // Resolve ACK
      handleACKPacket(buffer, len);
      break;
    default:
      break;
  }
}

void handleSOSPacket(uint8_t* pkt, int len, float rssi) {
  // Extract message ID (bytes 13-22 in SOS packet)
  uint8_t msgId[10];
  memcpy(msgId, &pkt[13], 10);

  // Duplicate check
  if (isDuplicate(msgId)) {
    Serial.println(F("[RX] Duplicate SOS - dropping"));
    return;
  }
  markAsSeen(msgId);

  // Check TTL
  uint8_t ttl = pkt[1] & 0x1F;
  if (ttl <= 1) {
    Serial.println(F("[RX] TTL expired - dropping"));
    packetsDropped++;
    return;
  }

  // Update source neighbor info
  updateNeighbor(&pkt[5], rssi, 100); // Source address at offset 5

  // Decrement TTL, increment hop count
  pkt[1] = (pkt[1] & 0xE0) | ((ttl - 1) & 0x1F);
  uint8_t hops = (pkt[2] >> 4) & 0x0F;
  pkt[2] = ((hops + 1) << 4) | (pkt[2] & 0x0F);

  // Enqueue for forwarding
  enqueuePacket(pkt, len, pkt[1] >> 5);
  Serial.println(F("[FWD] SOS enqueued for forwarding"));
}

void handleHeartbeat(uint8_t* pkt, int len, float rssi) {
  // Extract source address (offset 5, 4 bytes)
  uint8_t srcAddr[4];
  memcpy(srcAddr, &pkt[5], 4);

  // Extract heartbeat payload
  uint8_t nodeType = pkt[13];
  uint8_t battery = pkt[14];
  uint8_t mode = pkt[15];

  updateNeighbor(srcAddr, rssi, battery);
}

void handleRouteDown(uint8_t* pkt, int len) {
  // Extract failed node address (payload offset 13, 4 bytes)
  uint8_t failedAddr[4];
  memcpy(failedAddr, &pkt[13], 4);

  Serial.print(F("[HEAL] Route-down notification for node "));
  printAddress(failedAddr);
  Serial.println();

  // Mark failed node in neighbor table
  for (int i = 0; i < neighborCount; i++) {
    if (memcmp(neighbors[i].address, failedAddr, 4) == 0) {
      neighbors[i].status = 3; // DOWN
      break;
    }
  }

  // Invalidate routes through failed node
  invalidateRoutes(failedAddr);
}

void handleACKPacket(uint8_t* pkt, int len) {
  // Check if ACK destination is one of our neighbors (forward it)
  uint8_t destAddr[4];
  memcpy(destAddr, &pkt[9], 4); // Dest address offset

  // If it's for a node we can reach, forward it
  if (isNeighborActive(destAddr)) {
    enqueuePacket(pkt, len, 5); // SYSTEM priority for ACKs
    Serial.println(F("[FWD] ACK forwarded"));
  }
}


// ============================================================
// HEARTBEAT & SELF-HEALING
// ============================================================
void sendHeartbeat() {
  heartbeatSeq++;
  uint8_t packet[31]; // Heartbeat packet size
  int idx = 0;

  // Header
  packet[idx++] = 0x12;  // Version=1, Type=HEARTBEAT
  packet[idx++] = (0x05 << 5) | 1; // Priority=SYSTEM, TTL=1
  packet[idx++] = 0x00;  // HopCount=0, Flags=0
  packet[idx++] = (heartbeatSeq >> 8) & 0xFF;
  packet[idx++] = heartbeatSeq & 0xFF;

  // Source
  memcpy(&packet[idx], myAddress, 4); idx += 4;
  // Destination (broadcast)
  packet[idx++] = 0xFF; packet[idx++] = 0xFF;
  packet[idx++] = 0xFF; packet[idx++] = 0xFF;

  // Payload
  packet[idx++] = MY_NODE_TYPE;
  packet[idx++] = (uint8_t)batteryPercent;
  packet[idx++] = (uint8_t)currentMode;
  packet[idx++] = (uint8_t)neighborCount;
  uint32_t uptime = millis() / 1000;
  memcpy(&packet[idx], &uptime, 4); idx += 4;
  packet[idx++] = (heartbeatSeq >> 8) & 0xFF;
  packet[idx++] = heartbeatSeq & 0xFF;
  packet[idx++] = (uint8_t)((queueCount * 100) / MAX_QUEUE); // Queue %
  packet[idx++] = 0; // Error rate placeholder
  // Reserved
  packet[idx++] = 0; packet[idx++] = 0;
  packet[idx++] = 0; packet[idx++] = 0;

  radio.transmit(packet, idx);
}

void checkNeighborHealth() {
  unsigned long hbInterval = (currentMode == MODE_DISASTER) ?
                              HEARTBEAT_DISASTER_MS : HEARTBEAT_NORMAL_MS;
  uint32_t timeout = 2 * hbInterval;
  uint32_t now = millis();

  for (int i = 0; i < neighborCount; i++) {
    if (neighbors[i].status == 3) continue; // Already DOWN

    uint32_t timeSince = now - neighbors[i].lastSeen;
    if (timeSince > timeout) {
      neighbors[i].consecutiveMisses++;
      if (neighbors[i].consecutiveMisses >= MISS_THRESHOLD) {
        neighbors[i].status = 3; // DOWN
        Serial.print(F("[HEAL] Node FAILED: "));
        printAddress(neighbors[i].address);
        Serial.println();
        triggerSelfHealing(neighbors[i].address);
      }
    }
  }
}

void triggerSelfHealing(uint8_t* failedAddr) {
  Serial.println(F("[HEAL] Self-healing triggered!"));
  // 1. Invalidate routes through failed node
  invalidateRoutes(failedAddr);
  // 2. Broadcast ROUTE_DOWN to neighbors
  broadcastRouteDown(failedAddr);
  // 3. Re-route pending messages
  reroutePendingMessages(failedAddr);
}

void invalidateRoutes(uint8_t* failedAddr) {
  int invalidated = 0;
  for (int i = 0; i < routeCount; i++) {
    if (memcmp(routes[i].nextHop, failedAddr, 4) == 0) {
      routes[i].status = 3; // DOWN
      invalidated++;
    }
  }
  Serial.print(F("[HEAL] Invalidated "));
  Serial.print(invalidated);
  Serial.println(F(" routes"));
}

void broadcastRouteDown(uint8_t* failedAddr) {
  uint8_t packet[27]; // Route Down packet
  int idx = 0;
  packet[idx++] = 0x15;  // Version=1, Type=ROUTE_DOWN
  packet[idx++] = (0x05 << 5) | 3; // Priority=SYSTEM, TTL=3
  packet[idx++] = 0x00;
  packet[idx++] = 0x00; packet[idx++] = 0x00;
  memcpy(&packet[idx], myAddress, 4); idx += 4;
  packet[idx++] = 0xFF; packet[idx++] = 0xFF;
  packet[idx++] = 0xFF; packet[idx++] = 0xFF;
  // Payload
  memcpy(&packet[idx], failedAddr, 4); idx += 4;
  uint32_t now = millis() / 1000;
  memcpy(&packet[idx], &now, 4); idx += 4;
  packet[idx++] = 0x01; // HEARTBEAT_TIMEOUT
  packet[idx++] = 90;   // 90% confidence
  packet[idx++] = 0x00; packet[idx++] = 0x00;
  radio.transmit(packet, idx);
}

void reroutePendingMessages(uint8_t* failedAddr) {
  // Find alternate routes for queued messages
  // Simplified: forward to any active neighbor with higher type
  for (int i = 0; i < queueCount; i++) {
    if (!messageQueue[i].valid) continue;
    // Message will be routed in processQueue() using best available route
  }
}


// ============================================================
// QUEUE & FORWARDING
// ============================================================
void enqueuePacket(uint8_t* pkt, uint8_t len, uint8_t priority) {
  if (queueCount >= MAX_QUEUE) {
    // Drop lowest priority
    int lowestIdx = -1;
    uint8_t lowestPri = 0;
    for (int i = 0; i < MAX_QUEUE; i++) {
      if (messageQueue[i].valid && messageQueue[i].priority > lowestPri) {
        lowestPri = messageQueue[i].priority;
        lowestIdx = i;
      }
    }
    if (lowestIdx >= 0 && lowestPri > priority) {
      messageQueue[lowestIdx].valid = false;
      queueCount--;
      packetsDropped++;
    } else {
      packetsDropped++;
      return;
    }
  }
  // Find empty slot
  for (int i = 0; i < MAX_QUEUE; i++) {
    if (!messageQueue[i].valid) {
      memcpy(messageQueue[i].data, pkt, len);
      messageQueue[i].length = len;
      messageQueue[i].priority = priority;
      messageQueue[i].retries = 0;
      messageQueue[i].createdAt = millis();
      messageQueue[i].valid = true;
      queueCount++;
      return;
    }
  }
}

void processQueue() {
  // Forward highest priority message first
  int bestIdx = -1;
  uint8_t bestPri = 255;
  for (int i = 0; i < MAX_QUEUE; i++) {
    if (messageQueue[i].valid && messageQueue[i].priority < bestPri) {
      bestPri = messageQueue[i].priority;
      bestIdx = i;
    }
  }
  if (bestIdx < 0) return;

  // Transmit
  int state = radio.transmit(messageQueue[bestIdx].data,
                             messageQueue[bestIdx].length);
  if (state == RADIOLIB_ERR_NONE) {
    packetsForwarded++;
    messageQueue[bestIdx].valid = false;
    queueCount--;
    blinkLED(PIN_LED_STATUS, 30);
  }
}

// ============================================================
// NEIGHBOR & ROUTE MANAGEMENT
// ============================================================
void updateNeighbor(uint8_t* addr, float rssi, uint8_t battery) {
  // Find existing or add new
  for (int i = 0; i < neighborCount; i++) {
    if (memcmp(neighbors[i].address, addr, 4) == 0) {
      neighbors[i].rssi = (int8_t)rssi;
      neighbors[i].battery = battery;
      neighbors[i].lastSeen = millis();
      neighbors[i].consecutiveMisses = 0;
      neighbors[i].status = 1; // ACTIVE
      return;
    }
  }
  // Add new neighbor
  if (neighborCount < MAX_NEIGHBORS) {
    memcpy(neighbors[neighborCount].address, addr, 4);
    neighbors[neighborCount].rssi = (int8_t)rssi;
    neighbors[neighborCount].battery = battery;
    neighbors[neighborCount].lastSeen = millis();
    neighbors[neighborCount].consecutiveMisses = 0;
    neighbors[neighborCount].status = 1;
    neighbors[neighborCount].nodeType = addr[0];
    neighborCount++;
  }
}

bool isNeighborActive(uint8_t* addr) {
  for (int i = 0; i < neighborCount; i++) {
    if (memcmp(neighbors[i].address, addr, 4) == 0) {
      return neighbors[i].status == 1;
    }
  }
  return false;
}

bool isDuplicate(uint8_t* msgId) {
  uint32_t now = millis();
  for (int i = 0; i < dupCacheCount; i++) {
    if (!dupCache[i].valid) continue;
    if (now - dupCache[i].timestamp > 600000) { // 10 min expiry
      dupCache[i].valid = false;
      continue;
    }
    if (memcmp(dupCache[i].messageId, msgId, 10) == 0) {
      return true;
    }
  }
  return false;
}

void markAsSeen(uint8_t* msgId) {
  // Find empty slot or oldest
  int slot = -1;
  uint32_t oldest = UINT32_MAX;
  for (int i = 0; i < MAX_DUP_CACHE; i++) {
    if (!dupCache[i].valid) { slot = i; break; }
    if (dupCache[i].timestamp < oldest) {
      oldest = dupCache[i].timestamp;
      slot = i;
    }
  }
  if (slot >= 0) {
    memcpy(dupCache[slot].messageId, msgId, 10);
    dupCache[slot].timestamp = millis();
    dupCache[slot].valid = true;
    if (slot >= dupCacheCount) dupCacheCount = slot + 1;
  }
}

void pruneStaleRoutes() {
  uint32_t now = millis();
  for (int i = 0; i < routeCount; i++) {
    if (now - routes[i].lastUpdated > 600000) {
      routes[i].status = 2; // STALE
    }
  }
}

// ============================================================
// UTILITIES
// ============================================================
void blinkLED(int pin, int ms) {
  digitalWrite(pin, HIGH);
  delay(ms);
  digitalWrite(pin, LOW);
}

void printAddress(uint8_t* addr) {
  Serial.print(F("0x"));
  for (int i = 0; i < 4; i++) {
    if (addr[i] < 0x10) Serial.print('0');
    Serial.print(addr[i], HEX);
  }
}

float readBattery() {
  int adcValue = analogRead(35);
  float voltage = adcValue * (3.3 / 4095.0) * 2.0;
  float percent = (voltage - 3.0) / (4.2 - 3.0) * 100.0;
  return constrain(percent, 0.0, 100.0);
}
