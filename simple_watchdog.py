#!/usr/bin/env python
"""
Simple File Watchdog
Monitors continuous_fills.csv and runs net_position_monitor and lifo_pnl_monitor in parallel.
"""

import os
import time
import json
import csv
import subprocess
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from lifo_pnl_monitor import process_lifo_once
from net_position_monitor import run_net_position_once
from Optimizer.Sumo_Curve.trade_state_monitor import run_trade_state_once
from Optimizer.Sumo_Curve.risk_stream import run_risk_once
from Optimizer.Sumo_Curve.generate_risk_html import generate_html_once
from config import CONTINUOUS_FILLS_CSV, WATCHDOG_STATE_JSON, LIFO_STREAMING_CSV


class SimpleHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = 0
        self.debounce_time = 2.0  # 2 second debounce
        self.watch_file = CONTINUOUS_FILLS_CSV
        self.state_file = WATCHDOG_STATE_JSON
        self.last_row = None
        
    def get_last_row_from_csv(self):
        """Get the last row from continuous_fills.csv."""
        if not os.path.exists(self.watch_file):
            return None
            
        try:
            with open(self.watch_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows[-1] if rows else None
        except Exception as e:
            print(f"⚠️ Error reading CSV: {e}")
            return None
    
    def load_state(self):
        """Load last processed row from state file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_row = state.get('last_row')
                    print(f"📋 Loaded state: {len(self.last_row) if self.last_row else 0} fields")
            except Exception as e:
                print(f"⚠️ Error loading state: {e}")
                self.last_row = None
        else:
            self.last_row = None
    
    def save_state(self):
        """Save current last row to state file."""
        current_last_row = self.get_last_row_from_csv()
        if current_last_row:
            try:
                state = {'last_row': current_last_row}
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                self.last_row = current_last_row
                print(f"💾 Saved state: {len(current_last_row)} fields")
            except Exception as e:
                print(f"⚠️ Error saving state: {e}")
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only watch continuous_fills.csv
        if not event.src_path.endswith('continuous_fills.csv'):
            return
            
        # Debounce
        current_time = time.time()
        if current_time - self.last_modified < self.debounce_time:
            return
            
        self.last_modified = current_time
        print(f"📁 File changed: {event.src_path}")
        
        # Check if there are new rows
        if self.check_for_new_rows():
            print("🆕 New rows detected!")
            # Run both monitors in parallel
            self.run_monitors_parallel()
            # Update state after processing
            self.save_state()
    
    def check_for_new_rows(self):
        """Check if there are new rows since last processed."""
        current_last_row = self.get_last_row_from_csv()
        
        if not current_last_row:
            return False
            
        # If no previous state, just record current
        if not self.last_row:
            return False
        
        # Compare unique identifier fields - ALL must match for same row
        key_fields = ['OrderId', 'TimeStamp']
        for field in key_fields:
            if field in current_last_row and field in self.last_row:
                if current_last_row[field] != self.last_row[field]:
                    return True  # Different row = new data
            else:
                return True  # Missing field = different structure = new data
        
        # All key fields match = same row = no new data
        return False
    
    def check_for_missed_changes(self):
        """Check if file has new rows while watchdog was stopped."""
        if self.check_for_new_rows():
            current_last_row = self.get_last_row_from_csv()
            print(f"📁 Detected missed changes while watchdog was stopped!")
            print(f"   Last processed: {self.last_row.get('Date', 'N/A')} {self.last_row.get('Time', 'N/A')}")
            print(f"   Current last: {current_last_row.get('Date', 'N/A')} {current_last_row.get('Time', 'N/A')}")
            return True
        
        return False
    

    def run_monitors_parallel(self):
        """Run monitors with direct function calls - much faster."""
        
        def lifo_chain():
            print("�� Running LIFO...")
            process_lifo_once(CONTINUOUS_FILLS_CSV, LIFO_STREAMING_CSV)
            print("✅ LIFO completed")
            
        def net_position_chain():
            print("🔄 Running net_position...")
            run_net_position_once()
            print("✅ net_position completed")
            
            print("🔄 Running trade_state...")
            run_trade_state_once()
            print("✅ trade_state completed")

            print("🔄 Running risk_stream...")
            run_risk_once()
            print("✅ risk_stream completed")

            print("🔄 Running HTML generation...")
            generate_html_once()
            print("✅ HTML generation completed")

        t_lifo = threading.Thread(target=lifo_chain)
        t_net = threading.Thread(target=net_position_chain)

        t_lifo.start()
        t_net.start()

def main():
    # Setup observer
    event_handler = SimpleHandler()
    observer = Observer()
    observer.schedule(event_handler, "data/output/ladder", recursive=False)
    
    print("🔍 Starting Simple Watchdog...")
    print("📁 Watching: data/output/ladder/continuous_fills.csv")
    print("Press Ctrl+C to stop")
    
    # Load previous state
    event_handler.load_state()

    if event_handler.last_row is None:
        current_last_row = event_handler.get_last_row_from_csv()
        if current_last_row:
            event_handler.save_state()
            print("📋 Initialized state with current last row")
        
    # Check for missed changes on startup
    if event_handler.check_for_missed_changes():
        print("🔄 Processing missed changes...")
        event_handler.run_monitors_parallel()
        event_handler.save_state()
    
    observer.start()
    
    try:
        # Keep alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Stopping...")
    finally:
        observer.stop()
        observer.join()
        print("✅ Stopped")

if __name__ == "__main__":
    main() 