# 🧩 TODO List

## ✅ Completed Features
- [x] **Network Agent Implementation**
  - Intelligent automation system for network diagnostics
  - Smart task recommendations and analysis
  - Automated health checks, performance monitoring, and diagnostics
  - Custom task builder with async execution

## System & Data Collection
- [ ] **Add `dmesg -T` polling**
  - Implement periodic polling of `dmesg` with timestamps for live kernel event updates.
  - *Could be integrated into Network Agent as a monitoring task*

- [ ] **Add data export of graph data**
  - Support exporting performance and monitoring graphs as CSV or JSON.
  - *Network Agent already supports task result export*

## Graph Enhancements
- [ ] **Add statistics on graph data**
  - Compute and display **min**, **max**, **mean**, and **median** for captured graph metrics.

- [ ] **Add auto-update of graph in GUI**
  - Refresh graphs automatically based on a **user-selected interval (seconds)**.

- [ ] **Add removal of graphs and interrupt handling**
  - Allow users to remove specific graphs and **terminate worker threads** tied to a specific interface.

## Features & Commands
- [ ] **Add more commands**
  - Currently only `ethtool` is implemented. Extend support for more network-related commands.
  - *Network Agent supports multiple commands: ethtool, mlxconfig, mlxlink, ipmitool*

- [ ] **Add full info dump tab**
  - Create a new **INFO tab** displaying all known interface/module/NIC details.
  - *Network Agent provides comprehensive diagnostics and can be extended for info dumps*

## Network Agent Enhancements
- [ ] **Machine Learning Integration**
  - Learn from historical task results to improve recommendations
  - Predictive analysis for potential network issues

- [ ] **Scheduled Tasks**
  - Cron-like scheduling for regular diagnostic tasks
  - Automated monitoring with configurable intervals

- [ ] **Alert System**
  - Proactive notifications for critical network issues
  - Integration with external alerting systems

- [ ] **Report Generation**
  - Automated diagnostic reports in PDF/HTML format
  - Historical trend analysis and recommendations
