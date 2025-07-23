#!/usr/bin/env python3
import subprocess
import re
import smtplib
from email.message import EmailMessage

# === Configuration ===
# Copy config_example.py to config.py and edit your settings there
try:
    import config
except ImportError:
    print("Please create a config.py file based on config_example.py")
    exit(1)

def get_disks():
    """Return a list of disk device names, e.g., ['/dev/sda', '/dev/sdb']"""
    try:
        result = subprocess.run(['lsblk', '-dn', '-o', 'NAME,TYPE'], capture_output=True, text=True)
        disks = []
        for line in result.stdout.strip().split('\n'):
            name, typ = line.split()
            if typ == 'disk':
                disks.append(f"/dev/{name}")
        return disks
    except Exception as e:
        print(f"Error getting disks: {e}")
        return []

def check_smart_status(disk):
    """Run smartctl to check SMART health status of a disk"""
    try:
        result = subprocess.run(['smartctl', '-H', disk], capture_output=True, text=True)
        output = result.stdout
        match = re.search(r'SMART overall-health self-assessment test result: (\w+)', output)
        if match:
            return match.group(1)
        else:
            return "UNKNOWN"
    except Exception as e:
        print(f"Error checking SMART status for {disk}: {e}")
        return "ERROR"

def parse_log_for_errors():
    """Parse system logs or journalctl for disk-related errors"""
    errors = []
    try:
        if config.LOG_FILE:
            with open(config.LOG_FILE, 'r') as f:
                logs = f.readlines()
        else:
            # Use journalctl if no log file is configured
            result = subprocess.run(['journalctl', '-k', '--since', '1 hour ago'], capture_output=True, text=True)
            logs = result.stdout.splitlines()
        
        error_keywords = ['I/O error', 'ata_error', 'fail', 'error', 'unresponsive', 'offline', 'faulty']
        for line in logs:
            if any(keyword.lower() in line.lower() for keyword in error_keywords):
                errors.append(line.strip())
    except Exception as e:
        print(f"Error parsing logs: {e}")
    return errors

def send_email(subject, body):
    """Send alert email"""
    try:
        msg = EmailMessage()
        msg['From'] = config.EMAIL_FROM
        msg['To'] = config.EMAIL_TO
        msg['Subject'] = subject
        msg.set_content(body)

        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(msg)
        print("Alert email sent.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    disks = get_disks()
    if not disks:
        print("No disks found.")
        return

    failed_disks = []
    for disk in disks:
        status = check_smart_status(disk)
        print(f"{disk}: SMART status = {status}")
        if status.lower() != 'passed':
            failed_disks.append(disk)

    log_errors = parse_log_for_errors()
    if log_errors:
        print("\nDisk-related errors found in system logs:")
        for err in log_errors:
            print(err)

    if failed_disks or log_errors:
        subject = "Disk Health Alert on Red Hat System"
        body = "The following disk issues were detected:\n\n"
        if failed_disks:
            body += "Failed or failing disks (SMART):\n"
            for fdisk in failed_disks:
                body += f" - {fdisk}\n"
            body += "\n"
        if log_errors:
            body += "Disk-related errors from system logs:\n"
            for err in log_errors:
                body += f" - {err}\n"
        send_email(subject, body)
    else:
        print("\nAll disks passed SMART checks and no disk errors found in logs.")

if __name__ == "__main__":
    main()
