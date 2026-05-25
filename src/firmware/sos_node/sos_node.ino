/*
 * SHLM SOS Node Firmware
 * =======================
 * ESP32 + SX1276 LoRa SOS Device
 * 
 * This device allows users to send emergency SOS messages
 * via LoRa mesh network during disasters.
 * 
 * Hardware:
 *   - ESP32 DevKit or TTGO LoRa32
 *   - SX1276 LoRa module (868/915 MHz)
 *   - SOS button (GPIO input, active LOW)
 *   - 4x option buttons (emergency type selection)
 *   - LED (green) for ACK indication
 *   - Buzzer for audio feedback
 *   - Optional: GPS module (UART)
 * 
 * Libraries Required:
 *   - RadioLib (https://github.com/jgromes/RadioLib)
 *   - ArduinoJson (for packet serialization)
 *   - TinyGPS++ (if GPS module attached)
 * 
 * Pin Configuration (TTGO LoRa32 V2.1):
 *   LoRa: SCK=5, MISO=19, MOSI=27, CS=18, RST=23, DIO0=26
 *   SOS Button: GPIO 0 (built-in BOOT button for testing)
 *   Option Buttons: GPIO 12, 13, 14, 15
 *   LED: GPIO 25
 *   Buzzer: GPIO 32
 *   GPS TX: GPIO 34 (input only)
 * 
 * Author: [Your Name]
 * Date: 2026
 * License: MIT
 */

#include <SPI.h>
#include <RadioLib.h>
#include <ArduinoJson.h>

// ============================================================
// PIN DEFINITIONS (adjust for your board)
// ============================================================
#define LORA_SCK    5
#define LORA_MISO   19
#define LORA_MOSI   27
#define LORA_CS     18
#define LORA_RST    23
#define LORA_DIO0   26

#define PIN_SOS_BUTTON    0    // Main SOS button (hold 3 sec)
#define PIN_BTN_TRAPPED   12   // Option: People trapped
#define PIN_BTN_BOAT      13   // Option: Boat needed
#define PIN_BTN_MEDICAL   14   // Option: Medical emergency
#define PIN_BTN_FOOD      15   // Option: Food/Water needed

#define PIN_LED_GREEN     25   // ACK received indicator
#define PIN_BUZZER        32   // Audio feedback

// ============================================================
// PROTOCOL CONSTANTS
// ============================================================
#define NODE_TYPE_SOS       0x01
#define ZONE_ID             0x03  // TGH-Zone-3
#define NODE_SEQUENCE       14    // This node's sequence number

#define PACKET_TYPE_SOS     0x01
#define PACKET_TYPE_HB      0x02
#define PACKET_TYPE_ACK     0x07

#define PRIORITY_CRITICAL   0x01
#define PRIORITY_HIGH       0x02
#define PRIORITY_MEDIUM     0x03

#define EMERGENCY_TRAPPED       0x01
#define EMERGENCY_BOAT          0x02
#define EMERGENCY_MEDICAL       0x03
#define EMERGENCY_FOOD          0x04
#define EMERGENCY_TRAPPED_BOAT  0x05

#define SOS_HOLD_TIME_MS    3000  // 3 second hold to trigger SOS
#define MAX_RETRIES         12
#define ACK_TIMEOUT_MS      30000 // 30 seconds for ACK

// Retry intervals (milliseconds)
const uint32_t RETRY_INTERVALS[] = {0, 30000, 60000, 180000, 300000};
#define NUM_RETRY_INTERVALS 5

// ============================================================
// LORA CONFIGURATION
// ============================================================
#define LORA_FREQUENCY    868.0   // MHz (adjust for region)
#define LORA_BANDWIDTH    125.0   // kHz
#define LORA_SF           9       // Spreading Factor
#define LORA_CR           5       // Coding Rate (4/5)
#define LORA_TX_POWER     14      // dBm
#define LORA_PREAMBLE     8       // symbols
#define LORA_SYNC_WORD    0x34    // Private network sync word

// ============================================================
// GLOBAL VARIABLES
// ============================================================
SX1276 radio = new Module(LORA_CS, LORA_DIO0, LORA_RST, -1);

// Node identity
uint8_t nodeAddress[4] = {NODE_TYPE_SOS, ZONE_ID, 0x00, NODE_SEQUENCE};
char nodeIdStr[16] = "SOS-TGH-014";

// SOS state
bool sosTriggered = false;
uint8_t emergencyType = 0;
uint16_t messageSequence = 0;
uint8_t retryCount = 0;
bool ackReceived = false;
unsigned long lastSendTime = 0;
unsigned long sosButtonPressStart = 0;

// Message tracking
enum MessageState {
  MSG_IDLE,
  MSG_CREATED,
  MSG_SENT,
  MSG_WAITING_ACK,
  MSG_RETRYING,
  MSG_DELIVERED
};
MessageState currentMsgState = MSG_IDLE;

// Battery
float batteryPercent = 100.0;


// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n[SHLM] SOS Node Starting..."));
  Serial.print(F("[SHLM] Node ID: "));
  Serial.println(nodeIdStr);

  // Initialize pins
  pinMode(PIN_SOS_BUTTON, INPUT_PULLUP);
  pinMode(PIN_BTN_TRAPPED, INPUT_PULLUP);
  pinMode(PIN_BTN_BOAT, INPUT_PULLUP);
  pinMode(PIN_BTN_MEDICAL, INPUT_PULLUP);
  pinMode(PIN_BTN_FOOD, INPUT_PULLUP);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  // Initialize LoRa
  Serial.print(F("[LORA] Initializing... "));
  int state = radio.begin(
    LORA_FREQUENCY,
    LORA_BANDWIDTH,
    LORA_SF,
    LORA_CR,
    LORA_SYNC_WORD,
    LORA_TX_POWER,
    LORA_PREAMBLE
  );

  if (state == RADIOLIB_ERR_NONE) {
    Serial.println(F("OK!"));
  } else {
    Serial.print(F("FAILED! Code: "));
    Serial.println(state);
    // Blink LED rapidly to indicate error
    while (true) {
      digitalWrite(PIN_LED_GREEN, !digitalRead(PIN_LED_GREEN));
      delay(100);
    }
  }

  // Read battery level
  batteryPercent = readBatteryPercent();
  Serial.print(F("[BATT] Level: "));
  Serial.print(batteryPercent);
  Serial.println(F("%"));

  // Startup beep
  beep(100, 1);
  Serial.println(F("[SHLM] Ready. Press SOS button (3 sec hold) for emergency."));
}

// ============================================================
// MAIN LOOP
// ============================================================
void loop() {
  // Check SOS button
  checkSOSButton();

  // Handle message state machine
  handleMessageState();

  // Listen for incoming ACK
  listenForACK();

  // Periodic battery check
  static unsigned long lastBattCheck = 0;
  if (millis() - lastBattCheck > 60000) {
    batteryPercent = readBatteryPercent();
    lastBattCheck = millis();
  }

  delay(10); // Small delay to prevent watchdog issues
}

// ============================================================
// SOS BUTTON HANDLING
// ============================================================
void checkSOSButton() {
  if (currentMsgState != MSG_IDLE && currentMsgState != MSG_DELIVERED) {
    return; // Already processing an SOS
  }

  if (digitalRead(PIN_SOS_BUTTON) == LOW) {
    if (sosButtonPressStart == 0) {
      sosButtonPressStart = millis();
    }
    // Check if held for required duration
    if (millis() - sosButtonPressStart >= SOS_HOLD_TIME_MS) {
      triggerSOS();
      sosButtonPressStart = 0;
    }
  } else {
    sosButtonPressStart = 0;
  }
}

void triggerSOS() {
  Serial.println(F("\n[SOS] *** EMERGENCY TRIGGERED ***"));
  beep(500, 3); // 3 long beeps

  // Determine emergency type from option buttons
  emergencyType = classifyEmergency();
  Serial.print(F("[SOS] Emergency Type: 0x"));
  Serial.println(emergencyType, HEX);

  // Create message
  messageSequence++;
  retryCount = 0;
  ackReceived = false;
  currentMsgState = MSG_CREATED;

  // Send immediately
  sendSOSPacket();
}

uint8_t classifyEmergency() {
  // Priority Agent: classify based on button combination
  bool trapped = (digitalRead(PIN_BTN_TRAPPED) == LOW);
  bool boat = (digitalRead(PIN_BTN_BOAT) == LOW);
  bool medical = (digitalRead(PIN_BTN_MEDICAL) == LOW);
  bool food = (digitalRead(PIN_BTN_FOOD) == LOW);

  if (trapped && boat) return EMERGENCY_TRAPPED_BOAT;
  if (trapped) return EMERGENCY_TRAPPED;
  if (medical) return EMERGENCY_MEDICAL;
  if (boat) return EMERGENCY_BOAT;
  if (food) return EMERGENCY_FOOD;
  return EMERGENCY_TRAPPED; // Default: people trapped
}


// ============================================================
// PACKET CONSTRUCTION & TRANSMISSION
// ============================================================
void sendSOSPacket() {
  // Build SHLM packet
  uint8_t packet[47]; // Total SOS packet size
  int idx = 0;

  // Header (5 bytes)
  packet[idx++] = 0x11;  // Version=1, Type=SOS
  packet[idx++] = (PRIORITY_CRITICAL << 5) | 8; // Priority=CRITICAL, TTL=8
  packet[idx++] = 0x01;  // HopCount=0, Flags=ACK_REQ
  packet[idx++] = (messageSequence >> 8) & 0xFF;
  packet[idx++] = messageSequence & 0xFF;

  // Source address (4 bytes)
  memcpy(&packet[idx], nodeAddress, 4);
  idx += 4;

  // Destination address (4 bytes) - Gateway broadcast
  packet[idx++] = 0x05; // Gateway type
  packet[idx++] = 0x00;
  packet[idx++] = 0x00;
  packet[idx++] = 0x01; // GW-01

  // Payload - Message ID (10 bytes)
  memcpy(&packet[idx], nodeAddress, 4); idx += 4;
  uint32_t timestamp = millis() / 1000; // Simplified timestamp
  memcpy(&packet[idx], &timestamp, 4); idx += 4;
  packet[idx++] = (messageSequence >> 8) & 0xFF;
  packet[idx++] = messageSequence & 0xFF;

  // Emergency type
  packet[idx++] = emergencyType;
  // Zone
  packet[idx++] = ZONE_ID;
  // Battery
  packet[idx++] = (uint8_t)batteryPercent;
  // Location source (PRE_REGISTERED)
  packet[idx++] = 0x03;

  // GPS lat/lon (pre-registered, zeros for now)
  float lat = 25.08f;  // Pre-registered latitude
  float lon = 91.12f;  // Pre-registered longitude
  memcpy(&packet[idx], &lat, 4); idx += 4;
  memcpy(&packet[idx], &lon, 4); idx += 4;

  // Timestamp
  memcpy(&packet[idx], &timestamp, 4); idx += 4;
  // People count (unknown)
  packet[idx++] = 0x00;
  // Retry count
  packet[idx++] = retryCount;
  // Reserved
  packet[idx++] = 0x00;
  packet[idx++] = 0x00;
  packet[idx++] = 0x00;
  packet[idx++] = 0x00;

  // Transmit
  Serial.print(F("[LORA] Sending SOS (attempt "));
  Serial.print(retryCount + 1);
  Serial.println(F(")..."));

  int state = radio.transmit(packet, idx);

  if (state == RADIOLIB_ERR_NONE) {
    Serial.println(F("[LORA] TX success!"));
    currentMsgState = MSG_WAITING_ACK;
    lastSendTime = millis();
    beep(50, 1); // Short beep = sent
  } else {
    Serial.print(F("[LORA] TX failed! Code: "));
    Serial.println(state);
    currentMsgState = MSG_RETRYING;
  }
}

// ============================================================
// MESSAGE STATE MACHINE
// ============================================================
void handleMessageState() {
  switch (currentMsgState) {
    case MSG_IDLE:
    case MSG_DELIVERED:
      break;

    case MSG_WAITING_ACK:
      if (ackReceived) {
        currentMsgState = MSG_DELIVERED;
        onACKReceived();
      } else if (millis() - lastSendTime > ACK_TIMEOUT_MS) {
        currentMsgState = MSG_RETRYING;
      }
      break;

    case MSG_RETRYING:
      retryCount++;
      if (retryCount >= MAX_RETRIES) {
        Serial.println(F("[SOS] Max retries reached. Storing for mobile relay."));
        currentMsgState = MSG_IDLE; // Will be picked up by mobile relay
        beep(1000, 1); // Long beep = failed
      } else {
        // Calculate retry delay
        int intervalIdx = min(retryCount, NUM_RETRY_INTERVALS - 1);
        uint32_t retryDelay = RETRY_INTERVALS[intervalIdx];
        if (millis() - lastSendTime >= retryDelay) {
          sendSOSPacket();
        }
      }
      break;

    default:
      break;
  }
}

// ============================================================
// ACK LISTENING
// ============================================================
void listenForACK() {
  if (currentMsgState != MSG_WAITING_ACK) return;

  // Try to receive (non-blocking)
  uint8_t rxBuffer[64];
  int state = radio.receive(rxBuffer, 64);

  if (state == RADIOLIB_ERR_NONE) {
    // Check if it's an ACK for us
    if (rxBuffer[0] == 0x17 || rxBuffer[0] == 0x18 || rxBuffer[0] == 0x19) {
      // ACK type packet - verify destination matches us
      if (memcmp(&rxBuffer[9], nodeAddress, 4) == 0) {
        ackReceived = true;
        Serial.println(F("[ACK] Received acknowledgment!"));
      }
    }
  }
}

void onACKReceived() {
  Serial.println(F("[SOS] *** RESCUE NOTIFIED ***"));
  // Visual feedback: green LED blink pattern
  for (int i = 0; i < 5; i++) {
    digitalWrite(PIN_LED_GREEN, HIGH);
    delay(200);
    digitalWrite(PIN_LED_GREEN, LOW);
    delay(200);
  }
  // Buzzer pattern: rescue notified
  beep(100, 3);
  delay(300);
  beep(300, 1);
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================
void beep(int durationMs, int count) {
  for (int i = 0; i < count; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    delay(durationMs);
    digitalWrite(PIN_BUZZER, LOW);
    if (i < count - 1) delay(durationMs);
  }
}

float readBatteryPercent() {
  // Read ADC for battery voltage (voltage divider on GPIO 35)
  // Adjust calibration for your hardware
  int adcValue = analogRead(35);
  float voltage = adcValue * (3.3 / 4095.0) * 2.0; // 2x for voltage divider
  // Map 3.0V-4.2V to 0-100%
  float percent = (voltage - 3.0) / (4.2 - 3.0) * 100.0;
  return constrain(percent, 0.0, 100.0);
}
