"""
CLI Command Handler
"""
import argparse
import sys
from typing import List
from auto_messenger.core.config import ConfigManager
from auto_messenger.core.sender import MessageSender
from auto_messenger.core.logger import get_logger
from auto_messenger.utils.helpers import load_messages


class CLIHandler:
    """Handles CLI commands"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.logger = get_logger()
        self.sender = MessageSender(self.config)
    
    def handle_commands(self):
        """Parse and execute CLI commands"""
        parser = argparse.ArgumentParser(description="Discord Auto Messenger")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Start command
        start_parser = subparsers.add_parser("start", help="Start sending messages")
        start_parser.add_argument("--dry-run", action="store_true", help="Preview only, don't actually send")
        
        # Config commands
        config_parser = subparsers.add_parser("config", help="Manage configuration")
        config_subparsers = config_parser.add_subparsers(dest="config_action")
        
        set_token = config_subparsers.add_parser("set-token", help="Set Discord token")
        set_token.add_argument("token", help="Discord token")
        
        show_config = config_subparsers.add_parser("show", help="Show current configuration")
        
        # Target commands
        target_parser = subparsers.add_parser("target", help="Manage targets")
        target_subparsers = target_parser.add_subparsers(dest="target_action")
        
        add_target = target_subparsers.add_parser("add", help="Add a target")
        add_target.add_argument("type", choices=["channel", "dm"], help="Target type")
        add_target.add_argument("id", help="Target ID")
        
        remove_target = target_subparsers.add_parser("remove", help="Remove a target")
        remove_target.add_argument("index", type=int, help="Target index (use 'list' to see indices)")
        
        list_targets = target_subparsers.add_parser("list", help="List all targets")
        
        # Parse arguments
        args = parser.parse_args()
        
        if args.command == "start":
            self._start_sending(args.dry_run)
        elif args.command == "config":
            self._handle_config(args)
        elif args.command == "target":
            self._handle_targets(args)
        else:
            parser.print_help()
    
    def _start_sending(self, dry_run: bool = False):
        """Start sending messages"""
        self.logger.info("Starting message sending (CLI mode)")
        
        if not self.config.get("token") or not self.config.get("targets"):
            self.logger.error("Token or targets not configured!")
            return
            
        messages = load_messages()
        if not messages:
            self.logger.error("No messages found in messages.txt!")
            return
            
        delay = self.config.get("delay", 15)
        success_count = 0
        total_count = 0
        
        try:
            for item in messages:
                for target in self.config.get("targets", []):
                    name = self.sender.fetch_channel_name(target["id"])
                    success = self.sender.send_message(target["id"], name, item, dry_run)
                    total_count += 1
                    if success:
                        success_count += 1
                    # Respect rate limits
                    import time
                    time.sleep(delay)
                    
            self.logger.success(f"Completed! {success_count}/{total_count} messages sent successfully")
        except KeyboardInterrupt:
            self.logger.info("Sending interrupted by user")
    
    def _handle_config(self, args):
        """Handle config subcommands"""
        if args.config_action == "set-token":
            self.config["token"] = args.token
            self.config_manager.save_config(self.config)
            self.logger.success("Token updated successfully")
        elif args.config_action == "show":
            print("Current Configuration:")
            for key, value in self.config.items():
                if key != "token":  # Don't show token
                    print(f"  {key}: {value}")
