"""
Run this script LOCALLY to create and encode your Telegram session
This solves the Railway authentication problem by pre-authenticating
"""
import asyncio
import base64
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def create_session():
    """Create authenticated session locally"""
    
    # Your credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH') 
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing credentials in .env file")
        return
    
    print("🔐 Creating Telegram session locally...")
    
    # Create session with local file
    session_name = 'telegram_session'
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        # Connect and authenticate interactively
        await client.start(phone=phone)
        print("✅ Authentication successful!")
        
        # Test connection
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name} {me.last_name or ''}")
        
        # Disconnect to save session
        await client.disconnect()
        
        # Read and encode session file
        session_file = f"{session_name}.session"
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                session_data = f.read()
            
            # Encode to base64 for environment variable storage
            encoded_session = base64.b64encode(session_data).decode('utf-8')
            
            print("\n" + "="*60)
            print("🎯 COPY THIS TO RAILWAY ENVIRONMENT VARIABLES:")
            print("="*60)
            print(f"TELEGRAM_SESSION_DATA={encoded_session}")
            print("="*60)
            print("\n✅ Session created successfully!")
            print("🚀 You can now deploy to Railway without authentication prompts")
            
            # Clean up local session file for security
            os.remove(session_file)
            print("🧹 Local session file cleaned up")
            
        else:
            print("❌ Session file not created")
            
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Make sure you:")
        print("1. Have correct API credentials")
        print("2. Can receive SMS/calls on your phone")
        print("3. Enter the verification code when prompted")

if __name__ == '__main__':
    asyncio.run(create_session())