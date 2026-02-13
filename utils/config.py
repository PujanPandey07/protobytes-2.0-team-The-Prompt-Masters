"""
SADRN Configuration Constants

This module contains all configuration parameters for the
Software-Defined Adaptive Disaster Response Network.
"""

# =============================================================================
# NETWORK CONFIGURATION
# =============================================================================

# IP Subnets for different segments
GATEWAY_A_SUBNET = "10.0.1.0/24"  # Flood monitoring
GATEWAY_B_SUBNET = "10.0.2.0/24"  # Earthquake monitoring  
GATEWAY_C_SUBNET = "10.0.3.0/24"  # Fire monitoring
DISPLAY_SUBNET = "10.0.100.0/24"  # Display server

# Gateway IPs (interface facing sensors)
GATEWAY_A_IP = "10.0.1.1"
GATEWAY_B_IP = "10.0.2.1"
GATEWAY_C_IP = "10.0.3.1"

# Display server IP
DISPLAY_SERVER_IP = "10.0.100.1"
DISPLAY_SERVER_PORT = 8080

# Gateway ports (for receiving sensor data)
GATEWAY_A_PORT = 5001
GATEWAY_B_PORT = 5002
GATEWAY_C_PORT = 5003

# =============================================================================
# PRIORITY LEVELS
# =============================================================================

PRIORITY_NORMAL = 1
PRIORITY_HIGH = 2
PRIORITY_CRITICAL = 3  # Reserved for earthquake

PRIORITY_NAMES = {
    1: "NORMAL",
    2: "HIGH",
    3: "CRITICAL"
}

# =============================================================================
# SENSOR THRESHOLDS
# =============================================================================

# Flood sensors (Gateway A)
WATER_LEVEL_NORMAL_MAX = 50      # cm
WATER_LEVEL_EMERGENCY = 80      # cm
RAINFALL_NORMAL_MAX = 20        # mm/hr
RAINFALL_EMERGENCY = 50         # mm/hr

# Earthquake sensors (Gateway B) - Always treated as high priority
VIBRATION_NORMAL_MAX = 2.0      # g (gravitational acceleration)
VIBRATION_EMERGENCY = 4.0       # g
TILT_NORMAL_MAX = 5             # degrees
TILT_EMERGENCY = 15             # degrees

# Fire sensors (Gateway C)
TEMPERATURE_NORMAL_MAX = 35     # Celsius
TEMPERATURE_EMERGENCY = 60      # Celsius
SMOKE_NORMAL_MAX = 100          # ppm
SMOKE_EMERGENCY = 300           # ppm

# =============================================================================
# SENSOR TIMING
# =============================================================================

SENSOR_INTERVAL = 3.0           # Seconds between readings
SPIKE_PROBABILITY = 0.15        # 15% chance of abnormal spike
EMERGENCY_DURATION = 2          # Number of consecutive emergency readings

# =============================================================================
# GATEWAY CONFIGURATION
# =============================================================================

# Gateway types and their priorities (base priority)
GATEWAY_TYPES = {
    "flood": PRIORITY_NORMAL,
    "earthquake": PRIORITY_CRITICAL,  # Always critical
    "fire": PRIORITY_NORMAL
}

# Aggregation window (seconds)
AGGREGATION_WINDOW = 1.0

# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================

# Alarm triggers
ALARM_MULTI_GATEWAY_THRESHOLD = 2  # Alarm if >= 2 gateways report emergencies
ALARM_DISPLAY_DURATION = 5         # Seconds to show alarm

# Console colors for display (ANSI)
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
