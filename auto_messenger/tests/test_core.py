"""
Unit Tests for Core Modules
"""
import unittest
import os
import tempfile
from auto_messenger.utils.helpers import validate_discord_id, load_messages


class TestHelpers(unittest.TestCase):
    """Test utility functions"""
    
    def test_validate_discord_id_valid(self):
        """Test valid Discord IDs"""
        valid_ids = [
            "123456789012345678",  # 18 digits
            "9876543210987654321", # 19 digits
            "12345678901234567890" # 20 digits
        ]
        for discord_id in valid_ids:
            self.assertTrue(validate_discord_id(discord_id))
    
    def test_validate_discord_id_invalid(self):
        """Test invalid Discord IDs"""
        invalid_ids = [
            "12345",           # Too short
            "123456789012345", # 15 digits
            "abc123def456ghi", # Contains letters
            "123456789012345678901" # Too long
        ]
        for discord_id in invalid_ids:
            self.assertFalse(validate_discord_id(discord_id))
    
    def test_load_messages_empty(self):
        """Test loading messages from empty file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_filename = f.name
        
        try:
            messages = load_messages(temp_filename)
            self.assertEqual(messages, [])
        finally:
            os.unlink(temp_filename)
    
    def test_load_messages_text(self):
        """Test loading text messages"""
        content = "Hello World!\n\nSecond message."
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            temp_filename = f.name
        
        try:
            messages = load_messages(temp_filename)
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]["type"], "text")
            self.assertEqual(messages[0]["data"], "Hello World!")
            self.assertEqual(messages[1]["type"], "text")
            self.assertEqual(messages[1]["data"], "Second message.")
        finally:
            os.unlink(temp_filename)


if __name__ == '__main__':
    unittest.main()
