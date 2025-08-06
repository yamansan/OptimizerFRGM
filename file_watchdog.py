#!/usr/bin/env python
"""
File Watchdog Script for Trading System
Monitors data/output/ladder/continuous_fills.csv for changes and triggers downstream processing.
Provides event-driven alternative to polling-based monitoring.
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# Default configuration
DEFAULT_CONFIG = {
    "watch_file": "data/output/ladder/continuous_fills.csv",
    "commands": [
        {
            "name": "net_position_monitor", 
            "command": ["python", "net_position_monitor.py", "--run-once"],
            "enabled": True
        },
        {
            "name": "lifo_pnl_monitor",
            "command": ["python", "lifo_pnl_monitor.py", "--run-once"],
            "enabled": True
        }
    ],
    "debounce_seconds": 1.0,
    "log_level": "INFO"
}

class ContinuousFillsHandler(FileSystemEventHandler):
    """Event handler for continuous_fills.csv modifications."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        super().__init__()
        self.config = config
        self.logger = logger
        self.last_triggered = {}  # Track last trigger time per command for debouncing
        self.watch_file = Path(config["watch_file"]).resolve()
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        # Check if the modified file is our target
        modified_path = Path(event.src_path).resolve()
        if modified_path != self.watch_file:
            return
            
        self.logger.info(f"📁 Detected modification: {event.src_path}")
        self._trigger_commands()
    
    def _trigger_commands(self):
        """Trigger configured downstream commands with debouncing."""
        current_time = time.time()
        debounce_seconds = self.config.get("debounce_seconds", 2.0)
        
        for cmd_config in self.config.get("commands", []):
            if not cmd_config.get("enabled", True):
                continue
                
            cmd_name = cmd_config.get("name", "unknown")
            
            # Check debouncing
            last_run = self.last_triggered.get(cmd_name, 0)
            if current_time - last_run < debounce_seconds:
                self.logger.debug(f"⏳ Debouncing {cmd_name} (last run {current_time - last_run:.1f}s ago)")
                continue
            
            # Execute command
            self._execute_command(cmd_config)
            self.last_triggered[cmd_name] = current_time
    
    def _execute_command(self, cmd_config: Dict[str, Any]):
        """Execute a downstream command."""
        cmd_name = cmd_config.get("name", "unknown")
        command = cmd_config.get("command", [])
        
        if not command:
            self.logger.warning(f"⚠️ No command specified for {cmd_name}")
            return
            
        try:
            self.logger.info(f"🚀 Triggering: {cmd_name}")
            self.logger.debug(f"Command: {' '.join(command)}")
            
            # Execute command with timeout
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ {cmd_name} completed successfully")
                if result.stdout.strip():
                    self.logger.debug(f"Output: {result.stdout.strip()}")
            else:
                self.logger.error(f"❌ {cmd_name} failed with code {result.returncode}")
                if result.stderr.strip():
                    self.logger.error(f"Error: {result.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ {cmd_name} timed out after 30 seconds")
        except Exception as e:
            self.logger.error(f"💥 Error executing {cmd_name}: {e}")

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("file_watchdog")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from JSON file or use defaults."""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"📋 Loaded configuration from {config_file}")
            return config
        except Exception as e:
            print(f"⚠️ Error loading config file {config_file}: {e}")
            print("Using default configuration")
    else:
        print(f"📋 Config file {config_file} not found, using defaults")
    
    return DEFAULT_CONFIG.copy()

def save_default_config(config_file: str):
    """Save default configuration to file."""
    try:
        with open(config_file, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"💾 Default configuration saved to {config_file}")
    except Exception as e:
        print(f"❌ Error saving config file: {e}")

def main():
    """Main watchdog function."""
    parser = argparse.ArgumentParser(description='File Watchdog for Trading System')
    parser.add_argument('--config', default='watchdog_config.json',
                       help='Configuration file path')
    parser.add_argument('--save-default-config', action='store_true',
                       help='Save default configuration and exit')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Save default config if requested
    if args.save_default_config:
        save_default_config(args.config)
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Override log level from command line
    if args.log_level:
        config['log_level'] = args.log_level
    
    # Setup logging
    logger = setup_logging(config.get('log_level', 'INFO'))
    
    # Validate watch file
    watch_file = Path(config['watch_file'])
    if not watch_file.exists():
        logger.warning(f"⚠️ Watch file does not exist: {watch_file}")
        logger.info("Watchdog will start monitoring once the file is created")
    
    # Setup file system watcher
    event_handler = ContinuousFillsHandler(config, logger)
    observer = Observer()
    
    # Watch the directory containing the file
    watch_dir = watch_file.parent
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    
    # Start monitoring
    logger.info("🔍 Starting File Watchdog...")
    logger.info(f"📁 Watching: {watch_file}")
    logger.info(f"📂 Directory: {watch_dir}")
    logger.info(f"🔧 Commands: {len(config.get('commands', []))} configured")
    logger.info("Press Ctrl+C to stop")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested...")
    finally:
        observer.stop()
        observer.join()
        logger.info("✅ Watchdog stopped")

if __name__ == "__main__":
    main() 