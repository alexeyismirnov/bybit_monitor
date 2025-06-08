import asyncio
import re
import logging
import os
import base64
import tempfile
from datetime import datetime
from telethon import TelegramClient, events
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TelegramChannelMonitor:
    def __init__(self):
        # Load credentials from environment variables
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone_number = os.getenv('TELEGRAM_PHONE')
        self.bot_token = os.getenv('BOT_TOKEN')
        self.target_channel_id = os.getenv('TARGET_CHANNEL_ID')
        self.session_data = os.getenv('TELEGRAM_SESSION_DATA')  # Base64 encoded session
        
        # Validate required environment variables
        required_vars = [
            'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE',
            'BOT_TOKEN', 'TARGET_CHANNEL_ID', 'TELEGRAM_SESSION_DATA'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        
        # Monitoring settings
        self.source_channels = ['@Bybit_Announcements', '@varlamov_news']
        self.client = None
        
        # Filtering keywords
        self.filter_keywords = [
            'New', 'Listing', 'Perpetual', 'Contract'
        ]
        
        self.client = None
        self.session_file_path = None
        
        self.sent_messages = set()
        logger.info("✅ TelegramChannelMonitor initialized with session data")

    def create_session_file(self):
        """Create session file from base64 encoded data"""
        try:
            # Decode base64 session data
            session_bytes = base64.b64decode(self.session_data)
            
            # Create temporary session file
            temp_dir = tempfile.gettempdir()
            self.session_file_path = os.path.join(temp_dir, 'railway_session')
            
            # Write session data to file
            with open(f"{self.session_file_path}.session", 'wb') as f:
                f.write(session_bytes)
            
            logger.info("✅ Session file created from environment data")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create session file: {e}")
            return False

    async def initialize_client(self):
        """Initialize Telethon client with pre-authenticated session"""
        try:
            # Create session file from environment variable
            if not self.create_session_file():
                raise Exception("Failed to create session file")
            
            # Initialize client with session file
            self.client = TelegramClient(
                self.session_file_path, 
                self.api_id, 
                self.api_hash,
                device_model="Railway Server",
                system_version="Linux",
                app_version="1.0"
            )
            
            # Connect without interactive authentication
            await self.client.connect()
            
            # Verify authentication
            if not await self.client.is_user_authorized():
                raise Exception("Session is not authorized - please re-create session locally")
            
            # Get user info to confirm connection
            me = await self.client.get_me()
            logger.info(f"✅ Authenticated as: {me.first_name} {me.last_name or ''}")
            logger.info("✅ Telethon client initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Client initialization failed: {e}")
            return False

    def cleanup_session_file(self):
        """Clean up temporary session file"""
        try:
            if self.session_file_path and os.path.exists(f"{self.session_file_path}.session"):
                os.remove(f"{self.session_file_path}.session")
                logger.info("🧹 Temporary session file cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Could not clean up session file: {e}")

    def send_to_bot_channel(self, message_text, original_message_id=None):
        """Send message to your private channel using bot API"""
        bot_api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        formatted_message = f"""
🚨 **Bybit Alert** 🚨

{message_text}

📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
🔗 Source: Bybit Official Channel
{'🆔 Message ID: ' + str(original_message_id) if original_message_id else ''}
🤖 Railway Deployment
        """.strip()
        
        payload = {
            'chat_id': self.target_channel_id,
            'text': formatted_message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(bot_api_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Message sent successfully to channel")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending message to bot: {e}")
            return False

    def should_forward_message(self, message_text):
        """Check if message matches filtering criteria"""
        if not message_text or len(message_text.strip()) < 20:
            return False
        
        return True
        message_lower = message_text.lower()
        return any(keyword.lower() in message_lower for keyword in self.filter_keywords)

    async def setup_channel_monitoring(self):
        """Set up message monitoring for specified channels"""
        monitored_entities = []
        
        for channel_username in self.source_channels:
            try:
                entity = await self.client.get_entity(channel_username)
                monitored_entities.append(entity)
                logger.info(f"✅ Connected to channel: {entity.title}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to {channel_username}: {e}")
        
        if not monitored_entities:
            logger.error("❌ No channels could be monitored. Exiting.")
            return False
        
        @self.client.on(events.NewMessage(chats=monitored_entities))
        async def message_handler(event):
            await self.handle_new_message(event)
        
        logger.info(f"🎯 Monitoring {len(monitored_entities)} channels for updates...")
        return True

    async def handle_new_message(self, event):
        """Handle incoming messages from monitored channels"""
        try:
            message = event.message
            message_text = message.text or message.raw_text or ""
            message_hash = f"{event.chat_id}_{message.id}"
            
            if message_hash in self.sent_messages:
                return
            
            if self.should_forward_message(message_text):
                logger.info(f"📨 New matching message: {message_text[:100]}...")
                
                success = self.send_to_bot_channel(message_text, message.id)
                if success:
                    self.sent_messages.add(message_hash)
                    
                    if len(self.sent_messages) > 1000:
                        self.sent_messages = set(list(self.sent_messages)[500:])
                        
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")

    async def start_monitoring(self):
        """Start the monitoring process"""
        try:
            logger.info("🚀 Starting Telegram Bybit Monitor on Railway...")
            
            # Initialize client with pre-authenticated session
            if not await self.initialize_client():
                raise Exception("Failed to initialize Telegram client")
            
            # Test bot connection
            test_message = "🤖 Bybit Monitor Started on Railway!\n\n✅ Pre-authenticated session loaded\n🎯 Monitoring channels for updates..."
            if not self.send_to_bot_channel(test_message):
                logger.error("❌ Bot connection test failed")
                return
            
            if not await self.setup_channel_monitoring():
                return
            
            logger.info("✅ Monitoring started successfully on Railway!")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            raise e
        finally:
            if self.client:
                await self.client.disconnect()
            self.cleanup_session_file()

async def main():
    """Main function for Railway deployment"""
    try:
        monitor = TelegramChannelMonitor()
        await monitor.start_monitoring()
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        exit(1)

if __name__ == '__main__':
    asyncio.run(main())