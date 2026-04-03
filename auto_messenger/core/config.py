"""
Configuration Management
"""
import json
import os
from typing import Dict, Any
from cryptography.fernet import Fernet
from auto_messenger.core.logger import get_logger


class ConfigManager:
    """Handles configuration loading/saving with encryption"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.key_file = "key.key"
        self.cipher_suite = None
        self.logger = get_logger()
        self.config = self.load_config()
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption cipher"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, "rb") as key_file:
                    key = key_file.read()
            else:
                key = Fernet.generate_key()
                with open(self.key_file, "wb") as key_file:
                    key_file.write(key)
            return Fernet(key)
        except Exception as e:
            self.logger.error(f"Encryption initialization failed: {e}")
            return None
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt Discord token"""
        if not token or not self.cipher_suite:
            return token  # Return as-is if no encryption available
        try:
            return self.cipher_suite.encrypt(token.encode()).decode()
        except Exception:
            return token  # Return as-is if encryption fails
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt Discord token"""
        if not encrypted_token or not self.cipher_suite:
            return encrypted_token  # Return as-is if no decryption available
        try:
            return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
        except Exception:
            return encrypted_token  # Return as-is if decryption fails
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "token": "",
            "targets": [],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "delay": 15,
            "cycle_sleep": 300,
            "theme": "arc"
        }
        
        # Initialize encryption
        self.cipher_suite = self._initialize_encryption()
        
        if not os.path.exists(self.config_file):
            self.save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Handle both encrypted and non-encrypted tokens
            if "encrypted_token" in config:
                config["token"] = self._decrypt_token(config.pop("encrypted_token"))
            elif "token" in config:
                # If token exists but isn't encrypted, keep it as is for backward compatibility
                pass
            else:
                config["token"] = ""
                    
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                    
            return config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            # Work with a copy to avoid modifying the original
            config_copy = config.copy()
            
            # Encrypt token before saving if encryption is available
            if config_copy.get("token") and self.cipher_suite:
                config_copy["encrypted_token"] = self._encrypt_token(config_copy.pop("token"))
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_copy, f, indent=4)
                
            self.logger.info("Config saved to disk.")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def backup_config(self):
        """Create backup of config file"""
        if os.path.exists(self.config_file):
            backup_path = f"{self.config_file}.bak"
            try:
                import shutil
                shutil.copy2(self.config_file, backup_path)
                self.logger.info(f"Config backed up to {backup_path}")
            except Exception as e:
                self.logger.error(f"Failed to backup config: {e}")
    
    def cleanup_old_logs(self, days: int = 7):
        """Clean up log files older than specified days"""
        log_file = "auto_log.txt"
        if os.path.exists(log_file):
            try:
                import time
                age = time.time() - os.path.getmtime(log_file)
                if age > days * 86400:  # 86400 seconds in a day
                    os.remove(log_file)
                    self.logger.info(f"Old log file cleaned up: {log_file}")
            except Exception as e:
                self.logger.error(f"Failed to cleanup old logs: {e}")


# Make sure the class is accessible when imported
__all__ = ['ConfigManager']
