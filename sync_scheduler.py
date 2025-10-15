#!/usr/bin/env python3
"""
Scheduler to run sync_data.py every 30 minutes
"""
import time
import subprocess
import sys
from datetime import datetime

def run_sync():
    """Run the sync_data.py script"""
    try:
        print(f"🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting data sync...")
        
        # Run sync_data.py
        result = subprocess.run([sys.executable, 'sync_data.py'], 
                              capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print(f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data sync completed successfully")
            if result.stdout:
                print("Output:", result.stdout)
        else:
            print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data sync failed with return code {result.returncode}")
            if result.stderr:
                print("Error:", result.stderr)
    
    except subprocess.TimeoutExpired:
        print(f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data sync timed out after 30 minutes")
    except Exception as e:
        print(f"💥 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error running sync: {e}")

def main():
    """Main scheduler loop"""
    print("🚀 Starting Homeflix Data Sync Scheduler")
    print("📅 Will run sync_data.py every 30 minutes")
    
    # Run sync immediately on startup
    run_sync()
    
    # Schedule to run every 30 minutes (1800 seconds)
    interval = 30 * 60  # 30 minutes in seconds
    
    while True:
        print(f"😴 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for 30 minutes...")
        time.sleep(interval)
        run_sync()

if __name__ == "__main__":
    main()
