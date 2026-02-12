# Team Information
---
Amrit Kandel - amritkandel062@gmail.com - Amritkandel49
Prasish Timalsina - prasishabde@gmail.com - prasish_17
Saroj Nagarkoti - ntsaroj156@gmail.com - ntjoras22

# SADRN - Software-Defined Adaptive Disaster Response Network

A comprehensive demonstration of Software-Defined Networking (SDN) and Software-Defined Wireless Sensor Networks (SDWSN) for disaster response applications.

## Overview

SADRN demonstrates how SDN technology can revolutionize disaster response networks by providing:
- **Centralized Control**: Single SDN controller manages all network routing decisions
- **Dynamic Path Computation**: Shortest path routing using Dijkstra algorithm
- **Automatic Failover**: Instant rerouting when switches/links fail
- **Priority-Based Routing**: Emergency traffic gets higher priority
- **Real-Time Monitoring**: Live visualization of packet flows through network

## Architecture

```
                     ┌─────────────────────────────────────┐
                     │        SDN Controller (Ryu)         │
                     │  - Topology Discovery               │
                     │  - Shortest Path Routing            │
                     │  - Flow Rule Installation           │
                     │  - REST API (port 8080)             │
                     └────────────────┬────────────────────┘
                                      │ OpenFlow 1.3
     ┌────────────────────────────────┼────────────────────────────────┐
     │                                │                                │
┌────┴────┐                     ┌─────┴─────┐                    ┌─────┴─────┐
│   S1    │◄───────────────────►│    S2     │◄──────────────────►│    S3     │
│ (Core)  │◄────────────────────┤  (Core)   ├───────────────────►│  (Core)   │
└────┬────┘                     └─────┬─────┘                    └─────┬─────┘
     │                                │                                │
     │    ┌───────────────────────────┼───────────────────────────┐    │
     │    │                           │                           │    │
┌────┴────┴───┐               ┌───────┴───────┐               ┌───┴────┴────┐
│     S4      │               │      S5       │               │      S6     │
│ (Flood Zone)│               │  (EQ Zone)    │               │ (Fire Zone) │
└──────┬──────┘               └───────┬───────┘               └──────┬──────┘
       │                              │                              │
   ┌───┴───┐                      ┌───┴───┐                      ┌───┴───┐
   │ GW-A  │                      │ GW-B  │                      │ GW-C  │
   │10.0.0.1│                     │10.0.0.2│                     │10.0.0.3│
   └───┬───┘                      └───┬───┘                      └───┬───┘
       │                              │                              │
   ┌───┴───┐                      ┌───┴───┐                      ┌───┴───┐
   │Sensors│                      │Sensors│                      │Sensors│
   │Water  │                      │Seismic│                      │ Temp  │
   │Rain   │                      │ Tilt  │                      │ Smoke │
   └───────┘                      └───────┘                      └───────┘

                              ┌─────────────┐
                              │   Display   │
                              │  Server     │
                              │ 10.0.0.100  │
                              └─────────────┘
```

# Techical Stack
Frontend: React, Vite
Backend: Flask
Other Technology: Mininet, NetworkX