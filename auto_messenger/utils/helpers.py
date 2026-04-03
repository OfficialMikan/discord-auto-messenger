"""
Utility Functions
"""
import json
import re
from typing import List, Dict, Any


def validate_discord_id(discord_id: str) -> bool:
    """
    Validate Discord ID format (17-20 digits)
    
    Args:
        discord_id: String to validate
        
    Returns:
        bool: True if valid Discord ID
    """
    return bool(re.match(r'^\d{17,20}$', discord_id))


def load_messages(messages_file: str = "messages.txt") -> List[Dict[str, Any]]:
    """Load messages from file"""
    try:
        with open(messages_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        blocks = [block.strip() for block in content.split("\n\n") if block.strip()]
        messages = []
        for i, block in enumerate(blocks):
            print(f"DEBUG: Block {i}: '{block}'")  # Debug line
            if block.startswith("{") and block.endswith("}"):
                try:
                    messages.append({"type": "embed", "data": json.loads(block)})
                except:
                    messages.append({"type": "text", "data": block})
            else:
                messages.append({"type": "text", "data": block})
        print(f"DEBUG: Loaded {len(messages)} messages")  # Debug line
        return messages
    except Exception as e:
        print(f"Error loading messages: {e}")
        return []



def format_time(seconds: float) -> str:
    """
    Format seconds into human-readable time
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"
