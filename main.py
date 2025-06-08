import asyncio
import re
import logging
import os
from datetime import datetime
from telethon import TelegramClient, events
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output for Railway logs
    ]
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
        
        # Validate required environment variables
        required_vars = [
            'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE',
            'BOT_TOKEN', 'TARGET_CHANNEL_ID'
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
        
        # Anti-spam tracking
        self.sent_messages = set()
        
        logger.info("✅ TelegramChannelMonitor initialized with environment variables")

    async def initialize_client(self):
        """Initialize and authenticate Telethon client"""
        # Use Railway's ephemeral storage for session
        session_name = '/tmp/monitoring_session'
        
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone_number)
        logger.info("✅ Telethon client initialized and authenticated")

    def send_to_bot_channel(self, message_text, original_message_id=None):
        """Send message to your private channel using bot API"""
        bot_api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        formatted_message = f"""
🚨 **Bybit Alert** 🚨

{message_text}

📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
🔗 Source: Bybit Official Channel
{'🆔 Message ID: ' + str(original_message_id) if original_message_id else ''}
🤖 Deployed on Railway
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
        return all(keyword.lower() in message_lower for keyword in self.filter_keywords)

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
                    
                    # Prevent memory bloat
                    if len(self.sent_messages) > 1000:
                        self.sent_messages = set(list(self.sent_messages)[500:])
                        
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")

    async def start_monitoring(self):
        """Start the monitoring process"""
        try:
            logger.info("🚀 Starting Telegram Bybit Monitor on Railway...")
            
            await self.initialize_client()
            
            # Test bot connection
            test_message = "🤖 Bybit Monitor Started on Railway!\n\nMonitoring channels for updates..."
            if not self.send_to_bot_channel(test_message):
                logger.error("❌ Bot connection test failed")
                return
            
            if not await self.setup_channel_monitoring():
                return
            
            logger.info("✅ Monitoring started successfully on Railway!")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            # Railway will restart the service automatically
            raise e
        finally:
            if self.client:
                await self.client.disconnect()

async def main():
    """Main function for Railway deployment"""
    try:
        monitor = TelegramChannelMonitor()
        await monitor.start_monitoring()
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        # Exit with error code so Railway can restart
        exit(1)

if __name__ == '__main__':
    asyncio.run(main())