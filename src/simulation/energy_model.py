"""
Energy Model - Battery Consumption Simulation
==============================================
Models energy consumption for different node types and operational
states in the SHLM network. Based on real ESP32 + SX1276 datasheet
values for realistic simulation.

References:
- ESP32 datasheet: Active ~240mA, Light sleep ~0.8mA, Deep sleep ~10uA
- SX1276 datasheet: Tx@14dBm ~120mA, Tx@20dBm ~150mA, Rx ~12mA, Sleep ~0.2uA
- Solar panel: 10-20W, ~5V output, 6 hours effective per day

Author: [Your Name]
Date: 2026
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict


class NodePowerState(Enum):
    """Power states for nodes."""
    ACTIVE_TX = auto()       # Transmitting LoRa packet
    ACTIVE_RX = auto()       # Receiving/listening
    ACTIVE_PROCESS = auto()  # MCU processing (no radio)
    IDLE_LISTEN = auto()     # Low-power listening (CAD mode)
    SLEEP = auto()           # Deep sleep between heartbeats
    OFF = auto()             # Node powered off / dead


@dataclass
class BatterySpec:
    """Battery specification."""
    capacity_mah: float      # Total capacity in mAh
    voltage_nominal: float   # Nominal voltage (V)
    voltage_min: float       # Minimum operating voltage
    self_discharge_pct_day: float  # Self-discharge % per day

    @property
    def capacity_wh(self) -> float:
        return self.capacity_mah * self.voltage_nominal / 1000.0

    @property
    def capacity_joules(self) -> float:
        return self.capacity_wh * 3600.0



# ============================================================
# HARDWARE CURRENT PROFILES (from datasheets)
# ============================================================

# ESP32 current consumption (mA)
ESP32_CURRENT = {
    'active': 240.0,       # CPU active, WiFi off
    'modem_sleep': 20.0,   # CPU active, radio off
    'light_sleep': 0.8,    # CPU paused, RTC on
    'deep_sleep': 0.01,    # Only RTC, ~10 uA
}

# SX1276 LoRa transceiver current (mA)
SX1276_CURRENT = {
    'tx_14dbm': 120.0,    # Transmit at 14 dBm
    'tx_17dbm': 130.0,    # Transmit at 17 dBm
    'tx_20dbm': 150.0,    # Transmit at 20 dBm (max)
    'rx_continuous': 12.0, # Continuous receive
    'rx_cad': 12.0,       # Channel Activity Detection
    'standby': 1.6,       # Standby (oscillator on)
    'sleep': 0.0002,      # Sleep mode (~0.2 uA)
}

# Combined system current for each power state (mA)
SYSTEM_CURRENT = {
    NodePowerState.ACTIVE_TX: ESP32_CURRENT['active'] + SX1276_CURRENT['tx_14dbm'],
    NodePowerState.ACTIVE_RX: ESP32_CURRENT['modem_sleep'] + SX1276_CURRENT['rx_continuous'],
    NodePowerState.ACTIVE_PROCESS: ESP32_CURRENT['active'] + SX1276_CURRENT['standby'],
    NodePowerState.IDLE_LISTEN: ESP32_CURRENT['light_sleep'] + SX1276_CURRENT['rx_cad'],
    NodePowerState.SLEEP: ESP32_CURRENT['deep_sleep'] + SX1276_CURRENT['sleep'],
    NodePowerState.OFF: 0.0,
}

# Typical battery specs per node type
BATTERY_SPECS = {
    'SOS_DEVICE': BatterySpec(
        capacity_mah=3000,    # Single 18650 cell
        voltage_nominal=3.7,
        voltage_min=3.0,
        self_discharge_pct_day=0.1
    ),
    'LOCAL_RELAY': BatterySpec(
        capacity_mah=10000,   # 2-3x 18650 or LiFePO4
        voltage_nominal=3.7,
        voltage_min=3.0,
        self_discharge_pct_day=0.05
    ),
    'BACKBONE_RELAY': BatterySpec(
        capacity_mah=20000,   # Large LiFePO4 pack
        voltage_nominal=3.2,
        voltage_min=2.5,
        self_discharge_pct_day=0.03
    ),
    'MOBILE_RELAY': BatterySpec(
        capacity_mah=10000,
        voltage_nominal=3.7,
        voltage_min=3.0,
        self_discharge_pct_day=0.05
    ),
    'GATEWAY': BatterySpec(
        capacity_mah=50000,   # Large battery + IPS
        voltage_nominal=12.0,
        voltage_min=10.0,
        self_discharge_pct_day=0.02
    ),
}

# Solar recharge rates (mA average, accounting for 6h effective sun)
SOLAR_RECHARGE = {
    'SOS_DEVICE': 50.0,       # Small solar cell (0.5W effective avg)
    'LOCAL_RELAY': 200.0,     # 10W panel, ~6h/day = avg 200mA
    'BACKBONE_RELAY': 400.0,  # 20W panel
    'MOBILE_RELAY': 0.0,      # No solar (battery/boat power only)
    'GATEWAY': 800.0,         # 40W panel + IPS backup
}



# ============================================================
# ENERGY MODEL CLASS
# ============================================================

class EnergyModel:
    """
    Models energy consumption and battery life for a network node.
    
    Tracks cumulative energy usage across different operational states
    and provides estimated remaining lifetime.
    """

    def __init__(self, node_type):
        """
        Initialize energy model for a specific node type.
        
        Args:
            node_type: NodeType enum value
        """
        self.node_type_name = node_type.name
        self.battery = BATTERY_SPECS.get(node_type.name,
                                          BATTERY_SPECS['LOCAL_RELAY'])
        self.solar_rate_ma = SOLAR_RECHARGE.get(node_type.name, 0.0)

        # Current state
        self.current_state = NodePowerState.IDLE_LISTEN
        self.remaining_mah = self.battery.capacity_mah
        self.total_consumed_mah = 0.0

        # Timing (for energy calculation)
        self.last_state_change_time = 0.0
        self.is_daytime = True  # Solar available

        # Per-operation costs (pre-calculated for simulation speed)
        self._calculate_operation_costs()

        # Statistics
        self.tx_count = 0
        self.rx_count = 0
        self.total_tx_time_s = 0.0
        self.total_rx_time_s = 0.0
        self.total_sleep_time_s = 0.0

    def _calculate_operation_costs(self):
        """Pre-calculate energy costs for common operations."""
        # Packet transmission time depends on SF and packet size
        # SF9, BW125, 47 bytes payload → ~200ms airtime
        # SF12, BW125, 47 bytes payload → ~1500ms airtime
        self.tx_time_s = 0.2  # ~200ms for SF9 (typical relay)
        self.rx_time_s = 0.1  # ~100ms to receive and process

        # Energy per TX (mAh) = current_mA * time_s / 3600
        tx_current = SYSTEM_CURRENT[NodePowerState.ACTIVE_TX]
        self.tx_cost_mah = tx_current * self.tx_time_s / 3600.0

        rx_current = SYSTEM_CURRENT[NodePowerState.ACTIVE_RX]
        self.rx_cost_mah = rx_current * self.rx_time_s / 3600.0

        # Heartbeat cost (TX one packet)
        self.heartbeat_cost_mah = self.tx_cost_mah

        # Idle listening cost per second
        idle_current = SYSTEM_CURRENT[NodePowerState.IDLE_LISTEN]
        self.idle_cost_per_second_mah = idle_current / 3600.0

        # Sleep cost per second
        sleep_current = SYSTEM_CURRENT[NodePowerState.SLEEP]
        self.sleep_cost_per_second_mah = sleep_current / 3600.0

    @property
    def battery_percent(self) -> float:
        """Current battery percentage."""
        return max(0.0, (self.remaining_mah / self.battery.capacity_mah) * 100.0)

    @property
    def is_alive(self) -> bool:
        """Check if node has enough power to operate."""
        return self.remaining_mah > 0

    @property
    def tx_cost(self) -> float:
        """Cost of one TX in battery percentage."""
        return (self.tx_cost_mah / self.battery.capacity_mah) * 100.0

    @property
    def heartbeat_cost(self) -> float:
        """Cost of one heartbeat in battery percentage."""
        return (self.heartbeat_cost_mah / self.battery.capacity_mah) * 100.0

    def consume_tx(self, current_battery_pct: float) -> float:
        """
        Consume energy for one packet transmission.
        Returns new battery percentage.
        """
        self.remaining_mah -= self.tx_cost_mah
        self.total_consumed_mah += self.tx_cost_mah
        self.tx_count += 1
        self.total_tx_time_s += self.tx_time_s
        return self.battery_percent

    def consume_rx(self) -> float:
        """Consume energy for one packet reception."""
        self.remaining_mah -= self.rx_cost_mah
        self.total_consumed_mah += self.rx_cost_mah
        self.rx_count += 1
        self.total_rx_time_s += self.rx_time_s
        return self.battery_percent

    def consume_idle(self, duration_s: float) -> float:
        """Consume energy for idle listening period."""
        cost = self.idle_cost_per_second_mah * duration_s
        self.remaining_mah -= cost
        self.total_consumed_mah += cost
        return self.battery_percent

    def consume_sleep(self, duration_s: float) -> float:
        """Consume energy during sleep period."""
        cost = self.sleep_cost_per_second_mah * duration_s
        self.remaining_mah -= cost
        self.total_consumed_mah += cost
        self.total_sleep_time_s += duration_s
        return self.battery_percent

    def apply_solar_recharge(self, duration_s: float) -> float:
        """Apply solar recharge for given duration (daytime only)."""
        if self.solar_rate_ma > 0 and self.is_daytime:
            recharge = self.solar_rate_ma * duration_s / 3600.0
            self.remaining_mah = min(
                self.battery.capacity_mah,
                self.remaining_mah + recharge
            )
        return self.battery_percent

    def estimate_lifetime_hours(self, heartbeat_interval_s: float,
                                 avg_tx_per_hour: float = 2.0,
                                 duty_cycle: float = 0.01) -> float:
        """
        Estimate remaining operational lifetime in hours.
        
        Args:
            heartbeat_interval_s: Seconds between heartbeats
            avg_tx_per_hour: Average data transmissions per hour
            duty_cycle: Fraction of time in active listen (0.0-1.0)
        """
        # Hourly consumption breakdown
        heartbeats_per_hour = 3600.0 / heartbeat_interval_s
        hb_cost_hourly = heartbeats_per_hour * self.heartbeat_cost_mah
        tx_cost_hourly = avg_tx_per_hour * self.tx_cost_mah
        listen_cost_hourly = (duty_cycle * 3600.0 * self.idle_cost_per_second_mah)
        sleep_cost_hourly = ((1 - duty_cycle) * 3600.0 * self.sleep_cost_per_second_mah)

        total_hourly_mah = (hb_cost_hourly + tx_cost_hourly +
                            listen_cost_hourly + sleep_cost_hourly)

        # Account for solar (average over 24h: 6h sun, 18h dark)
        solar_hourly = self.solar_rate_ma * (6.0 / 24.0)
        net_hourly = total_hourly_mah - solar_hourly

        if net_hourly <= 0:
            return float('inf')  # Solar sustains indefinitely

        return self.remaining_mah / net_hourly

    def get_stats(self) -> dict:
        """Return energy statistics."""
        return {
            'node_type': self.node_type_name,
            'battery_capacity_mah': self.battery.capacity_mah,
            'remaining_mah': self.remaining_mah,
            'battery_percent': self.battery_percent,
            'total_consumed_mah': self.total_consumed_mah,
            'tx_count': self.tx_count,
            'rx_count': self.rx_count,
            'total_tx_time_s': self.total_tx_time_s,
            'solar_rate_ma': self.solar_rate_ma,
        }


# ============================================================
# DEMO / TEST
# ============================================================

if __name__ == '__main__':
    from enum import Enum, auto

    class NodeType(Enum):
        SOS_DEVICE = 1
        LOCAL_RELAY = 2
        BACKBONE_RELAY = 3
        MOBILE_RELAY = 4
        GATEWAY = 5

    print("=" * 60)
    print("ENERGY MODEL DEMONSTRATION")
    print("=" * 60)

    for nt in NodeType:
        model = EnergyModel(nt)
        lifetime_normal = model.estimate_lifetime_hours(
            heartbeat_interval_s=60, avg_tx_per_hour=2, duty_cycle=0.01)
        lifetime_disaster = model.estimate_lifetime_hours(
            heartbeat_interval_s=120, avg_tx_per_hour=10, duty_cycle=0.05)

        print(f"\n{nt.name}:")
        print(f"  Battery: {model.battery.capacity_mah} mAh")
        print(f"  Solar: {model.solar_rate_ma} mA avg")
        print(f"  TX cost: {model.tx_cost:.4f}% per packet")
        print(f"  HB cost: {model.heartbeat_cost:.4f}% per heartbeat")
        print(f"  Lifetime (normal mode): {lifetime_normal:.1f} hours")
        print(f"  Lifetime (disaster mode): {lifetime_disaster:.1f} hours")

    # Simulate 72 hours of disaster operation for a relay
    print("\n" + "=" * 60)
    print("72-HOUR DISASTER SIMULATION (Local Relay)")
    print("=" * 60)
    relay_model = EnergyModel(NodeType.LOCAL_RELAY)
    time_hours = 0
    while time_hours < 72 and relay_model.is_alive:
        # Each hour: heartbeats + some data TX + idle
        heartbeats = 3600 / 120  # Disaster mode: every 120s
        for _ in range(int(heartbeats)):
            relay_model.consume_tx(relay_model.battery_percent)
        # ~10 data packets forwarded per hour
        for _ in range(10):
            relay_model.consume_tx(relay_model.battery_percent)
            relay_model.consume_rx()
        # Rest of time: idle listen (5% duty cycle)
        relay_model.consume_idle(3600 * 0.05)
        relay_model.consume_sleep(3600 * 0.95)
        # Solar (if daytime, assume 12h day)
        if time_hours % 24 < 12:
            relay_model.apply_solar_recharge(3600)
        time_hours += 1

        if time_hours % 12 == 0:
            print(f"  T+{time_hours:3d}h: Battery={relay_model.battery_percent:.1f}%")

    print(f"\n  Final: Battery={relay_model.battery_percent:.1f}% after {time_hours}h")
    print(f"  Status: {'ALIVE' if relay_model.is_alive else 'DEAD'}")
