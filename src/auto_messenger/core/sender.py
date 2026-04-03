"""
Message Sending Core
"""
import json
import time
import random
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from auto_messenger.core.logger import get_logger
from auto_messenger.utils.helpers import validate_discord_id


class MessageSender:
    """Handles sending messages to Discord targets"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": config.get("token", ""),
            "Content-Type": "application/json",
            "User-Agent": config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        })
        self.logger = get_logger()
        self.cooldown_channels = {}  # channel_id -> cooldown_end_time
    
    def is_channel_cooldown(self, channel_id: str) -> bool:
        """Check if channel is in cooldown"""
        if channel_id in self.cooldown_channels:
            if time.time() < self.cooldown_channels[channel_id]:
                return True
            else:
                # Cooldown expired, remove it
                del self.cooldown_channels[channel_id]
        return False
    
    def set_channel_cooldown(self, channel_id: str, seconds: float):
        """Set cooldown for a channel"""
        self.cooldown_channels[channel_id] = time.time() + seconds
    
    def send_message(self, target_id: str, target_name: str, message_item: Dict[str, Any], 
                    dry_run: bool = False, target_type: str = "channel") -> bool:
        """
        Send a message to a Discord target
        """
        # Validate token before sending
        if not self.config.get("token"):
            self.logger.error("No token configured!")
            return False
            
        if not validate_discord_id(target_id):
            self.logger.error(f"Invalid target ID: {target_id}")
            return False
            
        # Handle DM creation if needed
        actual_target_id = target_id
        if target_type == "dm":
            actual_target_id = self._create_dm_channel(target_id)
            if not actual_target_id:
                self.logger.error(f"Failed to create DM channel for user {target_id}")
                return False
        
        url = f"https://discord.com/api/v10/channels/{actual_target_id}/messages"
        
        if message_item["type"] == "embed":
            payload = {"embeds": [message_item["data"]]}
            preview = f"Embed: {message_item['data'].get('title', 'No Title')}"
        else:
            payload = {"content": message_item["data"]}
            # Skip empty messages
            if not message_item["data"] or not message_item["data"].strip():
                self.logger.warning(f"Skipping empty message to {target_name}")
                return True
            preview = (message_item["data"].replace("\n", " \\n ")[:70] + "...") if len(message_item["data"]) > 70 else message_item["data"]
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would send to {target_name}: {preview}")
            return True
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            if response.status_code in (200, 201):
                self.logger.success(f"✓ Sent to {target_name}: {preview}")
                return True
            elif response.status_code == 401:
                self.logger.error(f"UNAUTHORIZED (401) - Check your token validity!")
                self.logger.error("Run validate_token.py to check your token")
                return False
            elif response.status_code == 429:
                retry = response.json().get("retry_after", 5)
                cooldown_time = retry + random.uniform(5, 10)
                self.set_channel_cooldown(target_id, cooldown_time)
                self.logger.warning(f"Rate limited on {target_name} → Cooldown: {cooldown_time:.1f} seconds")
                return True
            elif response.status_code == 403:
                self.logger.error(f"No permission to send to {target_name} (muted/blocked?)")
                self.set_channel_cooldown(target_id, 300)
                return True
            elif response.status_code == 404:
                self.logger.error(f"Channel not found {target_name}")
                return False
            else:
                self.logger.error(f"Failed on {target_name} ({response.status_code}): {response.text[:120]}")
                return False
        except Exception as e:
            self.logger.error(f"Request error on {target_name}: {e}")
            return False

    
    def _create_dm_channel(self, user_id: str) -> Optional[str]:
        """
        Create a DM channel with a user
        
        Args:
            user_id: User ID to create DM with
            
        Returns:
            str: DM channel ID or None if failed
        """
        url = "https://discord.com/api/v10/users/@me/channels"
        payload = {"recipient_id": user_id}
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            if response.status_code in (200, 201):
                data = response.json()
                return data.get("id")
            else:
                self.logger.error(f"Failed to create DM channel for {user_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating DM channel for {user_id}: {e}")
            return None
    
    def fetch_channel_name(self, channel_id: str) -> str:
        """
        Fetch the name of a Discord channel/DM
        
        Args:
            channel_id: Channel/User ID
            
        Returns:
            str: Friendly name of the channel
        """
        if not validate_discord_id(channel_id):
            return "(Invalid ID)"
            
        # Try to get channel info directly first
        url = f"https://discord.com/api/v10/channels/{channel_id}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("name"):
                    return f"#{data['name']}"
                recipients = data.get("recipients", [])
                if recipients:
                    return f"DM with {recipients[0].get('username', 'User')}"
                return "Channel"
            elif resp.status_code == 403:
                return "(No Access)"
            elif resp.status_code == 404:
                # Might be a user ID, try to get user info
                user_url = f"https://discord.com/api/v10/users/{channel_id}"
                try:
                    user_resp = self.session.get(user_url, timeout=10)
                    if user_resp.status_code == 200:
                        user_data = user_resp.json()
                        return f"DM with {user_data.get('username', 'User')}"
                except:
                    pass
                return "(User/Channel Not Found)"
            return f"(Error {resp.status_code})"
        except Exception as e:
            self.logger.error(f"Error fetching channel name for {channel_id}: {e}")
            return "(Failed to fetch name)"
