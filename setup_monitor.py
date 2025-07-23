#!/usr/bin/env python3
"""
Setup script for Flight Price Monitor
Creates cron jobs and system services for automated monitoring
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def get_script_dir():
    """
    Return the absolute path to the directory containing this script.
    """
    return Path(__file__).parent.absolute()

def create_cron_job(interval_minutes=60):
    """
    Creates a cron job that periodically runs the flight monitor script at a specified interval.
    
    Parameters:
        interval_minutes (int): The interval in minutes between each execution of the monitor script. Defaults to 60.
    """
    script_dir = get_script_dir()
    monitor_script = script_dir / "flight_monitor.py"
    
    # Create cron command
    cron_command = f"*/{interval_minutes} * * * * cd {script_dir} && /usr/bin/python3 {monitor_script} --once >> flight_monitor_cron.log 2>&1"
    
    # Add to crontab
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        # Check if our job already exists
        if str(monitor_script) in current_crontab:
            print("⚠️  Cron job already exists. Skipping.")
            return
        
        # Add new job
        new_crontab = current_crontab + "\n" + cron_command + "\n"
        
        # Write back to crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print(f"✅ Cron job created successfully!")
            print(f"   Command: {cron_command}")
            print(f"   Interval: Every {interval_minutes} minutes")
        else:
            print("❌ Failed to create cron job")
            
    except Exception as e:
        print(f"❌ Error creating cron job: {str(e)}")

def remove_cron_job():
    """
    Removes the cron job associated with the flight monitor script from the user's crontab.
    
    If no relevant cron job is found, the function completes without error.
    """
    script_dir = get_script_dir()
    monitor_script = script_dir / "flight_monitor.py"
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("No crontab found")
            return
            
        current_crontab = result.stdout
        
        # Remove lines containing our script
        lines = current_crontab.split('\n')
        new_lines = [line for line in lines if str(monitor_script) not in line]
        new_crontab = '\n'.join(new_lines)
        
        # Write back to crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Cron job removed successfully!")
        else:
            print("❌ Failed to remove cron job")
            
    except Exception as e:
        print(f"❌ Error removing cron job: {str(e)}")

def test_monitor():
    """
    Runs the flight monitor script once to verify its functionality, displaying output and reporting success or failure.
    """
    script_dir = get_script_dir()
    monitor_script = script_dir / "flight_monitor.py"
    
    print("🧪 Testing flight monitor...")
    try:
        result = subprocess.run([
            sys.executable, str(monitor_script), "--once"
        ], cwd=script_dir, capture_output=True, text=True, timeout=300)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ Monitor test completed successfully!")
        else:
            print(f"❌ Monitor test failed with return code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("❌ Monitor test timed out (5 minutes)")
    except Exception as e:
        print(f"❌ Error testing monitor: {str(e)}")

def show_status():
    """
    Displays the current status of the flight monitor setup, including configuration file presence, monitored flights, cron job activity, and log file existence and size.
    """
    script_dir = get_script_dir()
    
    print("📊 Flight Monitor Status")
    print("=" * 30)
    
    # Check config file
    config_file = script_dir / "flight_config.json"
    if config_file.exists():
        print("✅ Configuration file exists")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                active_flights = [f for f in config['flights'] if f['monitoring']['enabled']]
                print(f"📋 {len(active_flights)} flights being monitored")
                
                for flight in active_flights:
                    last_checked = flight['monitoring'].get('last_checked', 'Never')
                    print(f"   • {flight['description']} - Last checked: {last_checked}")
                    
        except Exception as e:
            print(f"❌ Error reading config: {str(e)}")
    else:
        print("❌ Configuration file not found")
    
    # Check cron job
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0 and "flight_monitor.py" in result.stdout:
            print("✅ Cron job is active")
        else:
            print("❌ No cron job found")
    except:
        print("❌ Cannot check cron job status")
    
    # Check log files
    log_files = [
        script_dir / "flight_monitor.log",
        script_dir / "flight_monitor_cron.log"
    ]
    
    for log_file in log_files:
        if log_file.exists():
            size = log_file.stat().st_size
            print(f"📄 {log_file.name} exists ({size} bytes)")
        else:
            print(f"📄 {log_file.name} not found")

def main():
    """
    Parses command-line arguments and dispatches setup actions for the Flight Price Monitor.
    
    Depending on the provided arguments, this function installs or removes the cron job, tests the monitor script, or displays the current setup status. If no recognized arguments are given, it prints usage instructions.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Flight Monitor Setup')
    parser.add_argument('--install', action='store_true', help='Install cron job')
    parser.add_argument('--uninstall', action='store_true', help='Remove cron job')
    parser.add_argument('--test', action='store_true', help='Test the monitor')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in minutes')
    
    args = parser.parse_args()
    
    if args.install:
        create_cron_job(args.interval)
    elif args.uninstall:
        remove_cron_job()
    elif args.test:
        test_monitor()
    elif args.status:
        show_status()
    else:
        print("Flight Monitor Setup")
        print("=" * 20)
        print("Usage:")
        print("  python3 setup_monitor.py --install     # Install cron job")
        print("  python3 setup_monitor.py --uninstall   # Remove cron job")
        print("  python3 setup_monitor.py --test        # Test monitor")
        print("  python3 setup_monitor.py --status      # Show status")
        print("  python3 setup_monitor.py --interval 30 # Set 30-minute interval")

if __name__ == "__main__":
    main()