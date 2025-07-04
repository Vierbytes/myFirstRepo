"""
Secure Configuration Management for YouTube Agent
Handles API keys, credentials, and sensitive data with encryption
"""

import os
import json
import keyring
import base64
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

@dataclass
class YouTubeConfig:
    """YouTube API configuration"""
    api_key: str = ""
    client_id: str = ""
    client_secret: str = ""
    channel_id: str = ""
    category_id: str = "20"  # Gaming category

@dataclass
class EmailConfig:
    """Email configuration for notifications"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""  # App password, not regular password
    notification_email: str = ""

@dataclass
class AIConfig:
    """AI service configuration"""
    openai_api_key: str = ""
    model: str = "gpt-4"
    max_tokens: int = 1200
    temperature: float = 0.7

@dataclass
class MediaConfig:
    """Media service configuration"""
    unsplash_api_key: str = ""
    pixabay_api_key: str = ""
    elevenlabs_api_key: str = ""

@dataclass
class ScheduleConfig:
    """Upload schedule configuration"""
    upload_times: list = None
    timezone: str = "UTC"
    enabled: bool = True
    
    def __post_init__(self):
        if self.upload_times is None:
            self.upload_times = ["09:00", "12:00", "16:00", "20:00"]

@dataclass
class SecurityConfig:
    """Security and privacy settings"""
    encrypt_config: bool = True
    use_keyring: bool = True
    log_level: str = "INFO"
    backup_credentials: bool = True
    session_timeout: int = 3600  # 1 hour

class SecureConfigManager:
    """Secure configuration manager with encryption and keyring support"""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".youtube_agent"
        self.config_dir.mkdir(exist_ok=True, mode=0o700)  # Secure permissions
        
        self.config_file = self.config_dir / "config.json"
        self.encrypted_config_file = self.config_dir / "config.enc"
        self.key_file = self.config_dir / "key.key"
        
        self.logger = logging.getLogger(__name__)
        self.cipher_suite = None
        
        # Configuration objects
        self.youtube = YouTubeConfig()
        self.email = EmailConfig()
        self.ai = AIConfig()
        self.media = MediaConfig()
        self.schedule = ScheduleConfig()
        self.security = SecurityConfig()
        
        self._load_or_create_config()
    
    def _generate_key_from_password(self, password: str) -> bytes:
        """Generate encryption key from password"""
        password_bytes = password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'youtube_agent_salt',  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def _setup_encryption(self) -> bool:
        """Setup encryption system"""
        try:
            if self.key_file.exists():
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                self.cipher_suite = Fernet(key)
                return True
            else:
                # Create new encryption setup
                print("Setting up encryption for YouTube Agent...")
                password = getpass.getpass("Enter a master password for encryption: ")
                confirm_password = getpass.getpass("Confirm password: ")
                
                if password != confirm_password:
                    print("Passwords don't match!")
                    return False
                
                key = self._generate_key_from_password(password)
                self.cipher_suite = Fernet(key)
                
                # Save key securely
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                self.key_file.chmod(0o600)  # Owner read/write only
                
                print("Encryption setup complete!")
                return True
                
        except Exception as e:
            self.logger.error(f"Encryption setup failed: {e}")
            return False
    
    def _load_or_create_config(self):
        """Load existing config or create new one"""
        try:
            if self.security.encrypt_config and self._setup_encryption():
                self._load_encrypted_config()
            elif self.config_file.exists():
                self._load_plain_config()
            else:
                self._create_initial_config()
                
        except Exception as e:
            self.logger.error(f"Config loading failed: {e}")
            self._create_initial_config()
    
    def _load_encrypted_config(self):
        """Load encrypted configuration"""
        if not self.encrypted_config_file.exists():
            self._create_initial_config()
            return
        
        try:
            with open(self.encrypted_config_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            config_dict = json.loads(decrypted_data.decode())
            
            self._populate_from_dict(config_dict)
            self.logger.info("Encrypted config loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load encrypted config: {e}")
            self._create_initial_config()
    
    def _load_plain_config(self):
        """Load plain text configuration"""
        try:
            with open(self.config_file, 'r') as f:
                config_dict = json.load(f)
            
            self._populate_from_dict(config_dict)
            self.logger.info("Plain config loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load plain config: {e}")
            self._create_initial_config()
    
    def _populate_from_dict(self, config_dict: Dict[str, Any]):
        """Populate configuration objects from dictionary"""
        if 'youtube' in config_dict:
            self.youtube = YouTubeConfig(**config_dict['youtube'])
        if 'email' in config_dict:
            self.email = EmailConfig(**config_dict['email'])
        if 'ai' in config_dict:
            self.ai = AIConfig(**config_dict['ai'])
        if 'media' in config_dict:
            self.media = MediaConfig(**config_dict['media'])
        if 'schedule' in config_dict:
            self.schedule = ScheduleConfig(**config_dict['schedule'])
        if 'security' in config_dict:
            self.security = SecurityConfig(**config_dict['security'])
    
    def _create_initial_config(self):
        """Create initial configuration with empty values"""
        self.logger.info("Creating initial configuration...")
        
        config_dict = {
            'youtube': asdict(self.youtube),
            'email': asdict(self.email),
            'ai': asdict(self.ai),
            'media': asdict(self.media),
            'schedule': asdict(self.schedule),
            'security': asdict(self.security)
        }
        
        # Save empty config
        self.save_config()
        
        print(f"\nInitial configuration created at: {self.config_dir}")
        print("Please update the configuration with your API keys and settings.")
        print("Use the setup wizard or edit manually.\n")
    
    def save_config(self):
        """Save configuration to file"""
        config_dict = {
            'youtube': asdict(self.youtube),
            'email': asdict(self.email),
            'ai': asdict(self.ai),
            'media': asdict(self.media),
            'schedule': asdict(self.schedule),
            'security': asdict(self.security)
        }
        
        try:
            if self.security.encrypt_config and self.cipher_suite:
                self._save_encrypted_config(config_dict)
            else:
                self._save_plain_config(config_dict)
                
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
    
    def _save_encrypted_config(self, config_dict: Dict[str, Any]):
        """Save encrypted configuration"""
        json_data = json.dumps(config_dict, indent=2)
        encrypted_data = self.cipher_suite.encrypt(json_data.encode())
        
        with open(self.encrypted_config_file, 'wb') as f:
            f.write(encrypted_data)
        self.encrypted_config_file.chmod(0o600)
    
    def _save_plain_config(self, config_dict: Dict[str, Any]):
        """Save plain text configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        self.config_file.chmod(0o600)
    
    def setup_wizard(self):
        """Interactive setup wizard for configuration"""
        print("\n🤖 YouTube Agent Configuration Wizard")
        print("=" * 50)
        
        # YouTube API setup
        print("\n📺 YouTube API Configuration")
        self.youtube.api_key = self._get_secure_input("YouTube API Key", self.youtube.api_key)
        self.youtube.client_id = self._get_secure_input("YouTube Client ID", self.youtube.client_id)
        self.youtube.client_secret = self._get_secure_input("YouTube Client Secret", self.youtube.client_secret, True)
        self.youtube.channel_id = self._get_secure_input("YouTube Channel ID", self.youtube.channel_id)
        
        # Email configuration
        print("\n📧 Email Configuration")
        self.email.username = self._get_secure_input("Gmail Username", self.email.username)
        self.email.password = self._get_secure_input("Gmail App Password", self.email.password, True)
        self.email.notification_email = self._get_secure_input("Notification Email", self.email.notification_email)
        
        # AI configuration
        print("\n🤖 AI Configuration")
        self.ai.openai_api_key = self._get_secure_input("OpenAI API Key", self.ai.openai_api_key, True)
        
        # Media services (optional)
        print("\n🎨 Media Services (Optional)")
        use_media = input("Do you want to configure media services for images/videos? (y/N): ").lower().startswith('y')
        if use_media:
            self.media.unsplash_api_key = self._get_secure_input("Unsplash API Key", self.media.unsplash_api_key, True)
            self.media.pixabay_api_key = self._get_secure_input("Pixabay API Key", self.media.pixabay_api_key, True)
        
        # Schedule configuration
        print("\n⏰ Upload Schedule")
        current_times = ", ".join(self.schedule.upload_times)
        new_times = input(f"Upload times ({current_times}): ").strip()
        if new_times:
            self.schedule.upload_times = [time.strip() for time in new_times.split(',')]
        
        # Save configuration
        self.save_config()
        
        # Store sensitive data in keyring if enabled
        if self.security.use_keyring:
            self._store_in_keyring()
        
        print("\n✅ Configuration completed successfully!")
        print(f"Configuration saved to: {self.config_dir}")
    
    def _get_secure_input(self, prompt: str, current_value: str = "", hide_input: bool = False) -> str:
        """Get secure input from user"""
        display_value = "***" if current_value and hide_input else current_value
        full_prompt = f"{prompt} ({display_value}): " if current_value else f"{prompt}: "
        
        if hide_input:
            new_value = getpass.getpass(full_prompt)
        else:
            new_value = input(full_prompt)
        
        return new_value.strip() if new_value.strip() else current_value
    
    def _store_in_keyring(self):
        """Store sensitive credentials in system keyring"""
        try:
            service_name = "youtube_agent"
            
            # Store API keys
            if self.youtube.api_key:
                keyring.set_password(service_name, "youtube_api_key", self.youtube.api_key)
            if self.youtube.client_secret:
                keyring.set_password(service_name, "youtube_client_secret", self.youtube.client_secret)
            if self.email.password:
                keyring.set_password(service_name, "email_password", self.email.password)
            if self.ai.openai_api_key:
                keyring.set_password(service_name, "openai_api_key", self.ai.openai_api_key)
            
            self.logger.info("Credentials stored in system keyring")
            
        except Exception as e:
            self.logger.warning(f"Failed to store credentials in keyring: {e}")
    
    def load_from_keyring(self):
        """Load credentials from system keyring"""
        try:
            service_name = "youtube_agent"
            
            # Load API keys from keyring
            youtube_api_key = keyring.get_password(service_name, "youtube_api_key")
            if youtube_api_key:
                self.youtube.api_key = youtube_api_key
            
            youtube_client_secret = keyring.get_password(service_name, "youtube_client_secret")
            if youtube_client_secret:
                self.youtube.client_secret = youtube_client_secret
            
            email_password = keyring.get_password(service_name, "email_password")
            if email_password:
                self.email.password = email_password
            
            openai_api_key = keyring.get_password(service_name, "openai_api_key")
            if openai_api_key:
                self.ai.openai_api_key = openai_api_key
            
            self.logger.info("Credentials loaded from system keyring")
            
        except Exception as e:
            self.logger.warning(f"Failed to load credentials from keyring: {e}")
    
    def load_from_environment(self):
        """Load configuration from environment variables"""
        # YouTube configuration
        self.youtube.api_key = os.getenv('YOUTUBE_API_KEY', self.youtube.api_key)
        self.youtube.client_id = os.getenv('YOUTUBE_CLIENT_ID', self.youtube.client_id)
        self.youtube.client_secret = os.getenv('YOUTUBE_CLIENT_SECRET', self.youtube.client_secret)
        self.youtube.channel_id = os.getenv('YOUTUBE_CHANNEL_ID', self.youtube.channel_id)
        
        # Email configuration
        self.email.username = os.getenv('EMAIL_USERNAME', self.email.username)
        self.email.password = os.getenv('EMAIL_PASSWORD', self.email.password)
        self.email.notification_email = os.getenv('NOTIFICATION_EMAIL', self.email.notification_email)
        
        # AI configuration
        self.ai.openai_api_key = os.getenv('OPENAI_API_KEY', self.ai.openai_api_key)
        
        # Media configuration
        self.media.unsplash_api_key = os.getenv('UNSPLASH_API_KEY', self.media.unsplash_api_key)
        self.media.pixabay_api_key = os.getenv('PIXABAY_API_KEY', self.media.pixabay_api_key)
        
        self.logger.info("Configuration loaded from environment variables")
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration completeness"""
        validation_results = {
            'youtube_api_key': bool(self.youtube.api_key),
            'youtube_client_id': bool(self.youtube.client_id),
            'youtube_client_secret': bool(self.youtube.client_secret),
            'email_configured': bool(self.email.username and self.email.password),
            'openai_configured': bool(self.ai.openai_api_key),
            'schedule_configured': bool(self.schedule.upload_times)
        }
        
        return validation_results
    
    def get_missing_config(self) -> List[str]:
        """Get list of missing configuration items"""
        validation = self.validate_config()
        missing = [key for key, is_valid in validation.items() if not is_valid]
        return missing
    
    def backup_config(self, backup_path: str = None):
        """Create a backup of the configuration"""
        if not backup_path:
            backup_path = self.config_dir / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            config_dict = {
                'youtube': asdict(self.youtube),
                'email': asdict(self.email),
                'ai': asdict(self.ai),
                'media': asdict(self.media),
                'schedule': asdict(self.schedule),
                'security': asdict(self.security)
            }
            
            # Remove sensitive data from backup
            config_dict['youtube']['api_key'] = '***'
            config_dict['youtube']['client_secret'] = '***'
            config_dict['email']['password'] = '***'
            config_dict['ai']['openai_api_key'] = '***'
            
            with open(backup_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            self.logger.info(f"Configuration backup created: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")

# CLI interface for configuration management
def main():
    """CLI interface for configuration management"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="YouTube Agent Configuration Manager")
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--backup', action='store_true', help='Create configuration backup')
    parser.add_argument('--config-dir', type=str, help='Configuration directory path')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize config manager
    config_manager = SecureConfigManager(args.config_dir)
    
    if args.setup:
        config_manager.setup_wizard()
    elif args.validate:
        validation = config_manager.validate_config()
        missing = config_manager.get_missing_config()
        
        print("\n📊 Configuration Validation Results:")
        print("=" * 40)
        
        for key, is_valid in validation.items():
            status = "✅" if is_valid else "❌"
            print(f"{status} {key}: {'Valid' if is_valid else 'Missing/Invalid'}")
        
        if missing:
            print(f"\n⚠️  Missing configuration: {', '.join(missing)}")
            print("Run with --setup to configure missing items.")
        else:
            print("\n🎉 All configuration items are valid!")
    
    elif args.backup:
        config_manager.backup_config()
        print("Configuration backup created successfully!")
    
    else:
        print("YouTube Agent Configuration Manager")
        print("Use --setup to run the configuration wizard")
        print("Use --validate to check configuration completeness")
        print("Use --backup to create a configuration backup")

if __name__ == "__main__":
    main()