# Disk Health Monitor

A Python script to monitor disk health on Red Hat Linux systems using SMART data and system logs, with email alerting.

## Features

- Checks SMART health status of all disks using `smartctl`
- Parses system logs or journalctl for disk-related errors
- Sends email alerts if any disk issues are detected

## Requirements

- Python 3.x
- `smartmontools` installed (`sudo yum install smartmontools`)
- SMTP server credentials for sending email
- Run with root privileges for full access

## Installation

1. Clone this repository
2. Copy `config_example.py` to `config.py` and update with your settings
3. Run the script:

```bash
sudo python3 disk_health_monitor.py
