import requests
import json
import logging
import os
from datetime import datetime
import asyncio
import time
import re
from typing import Optional, Dict, Any

from config import *
from captcha_services import get_service_instance

# Setup logging with UTF-8 encoding to prevent encoding errors
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Detect token type
def detect_token_type(token: str) -> str:
    """Detect the type of Discord token"""
    if not token or len(token) < 10:
        return "invalid"
    
    dot_count = token.count('.')
    
    # Bot token: has 2 dots (format: ID.base64.secret)
    if dot_count == 2:
        return "bot"
    
    # User token: no dots, long string
    if dot_count == 0 and len(token) > 50:
        return "user"
    
    # Webhook: 1 dot
    if dot_count == 1:
        return "webhook"
    
    return "unknown"

# Game State
class GameState:
    def __init__(self):
        self.current_bet = INITIAL_BET
        self.total_games = 0
        self.wins = 0
        self.losses = 0
        self.is_running = False
        self.last_result = None
        self.last_timestamp = None
    
    def on_win(self):
        self.wins += 1
        self.total_games += 1
        self.current_bet = INITIAL_BET
        logger.info(f"WIN! Bet reset to {INITIAL_BET}. Stats: {self.wins}W - {self.losses}L")
    
    def on_loss(self):
        self.losses += 1
        self.total_games += 1
        self.current_bet *= BET_MULTIPLIER
        logger.warning(f"LOSS! Bet doubled to {self.current_bet}. Stats: {self.wins}W - {self.losses}L")
    
    def get_stats(self):
        win_rate = (self.wins / self.total_games * 100) if self.total_games > 0 else 0
        return {
            "current_bet": self.current_bet,
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": win_rate
        }

game_state = GameState()

# Discord API Handler - Works with ALL token types
class DiscordClient:
    def __init__(self, token: str):
        self.token = token
        self.token_type = detect_token_type(token)
        self.base_url = "https://discord.com/api/v10"
        self.user_id = None
        self.username = None
        self.last_message_id = None
        
        # Set authorization header based on token type
        if self.token_type == "bot":
            self.auth_header = f"Bot {token}"
        elif self.token_type == "user":
            self.auth_header = token
        elif self.token_type == "webhook":
            self.auth_header = f"Bot {token}"
        else:
            self.auth_header = token
        
        logger.info(f"Initialized Discord client with token type: {self.token_type}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (coin-flip-bot)"
        }
    
    def verify_token(self) -> bool:
        """Verify token is valid by checking current user"""
        try:
            response = requests.get(
                f"{self.base_url}/users/@me",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("id")
                self.username = data.get("username")
                logger.info(f"Token verified! Logged in as {self.username}#{data.get('discriminator', '0')}")
                return True
            else:
                logger.error(f"Token verification failed! Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False
    
    def send_message(self, channel_id: int, content: str) -> bool:
        """Send a message to a channel"""
        try:
            payload = {"content": content}
            response = requests.post(
                f"{self.base_url}/channels/{channel_id}/messages",
                headers=self.get_headers(),
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Message sent: {content}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def get_messages(self, channel_id: int, limit: int = 10) -> list:
        """Get recent messages from a channel"""
        try:
            response = requests.get(
                f"{self.base_url}/channels/{channel_id}/messages",
                headers=self.get_headers(),
                params={"limit": limit},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get messages: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def wait_for_owo_response(self, channel_id: int, timeout: int = MESSAGE_WAIT_TIMEOUT) -> Optional[str]:
        """Wait for owo bot response"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                messages = self.get_messages(channel_id, limit=5)
                
                for message in messages:
                    # Check if message is from owo bot
                    author = message.get("author", {})
                    if author.get("username", "").lower() == "owo":
                        content = message.get("content", "").lower()
                        
                        # Check for result keywords
                        if WIN_KEYWORD.lower() in content or LOSS_KEYWORD.lower() in content:
                            logger.info(f"Received owo response: {message.get('content')}")
                            return message.get("content")
                        
                        # Check for captcha
                        for keyword in CAPTCHA_KEYWORDS:
                            if keyword in content:
                                logger.warning(f"Captcha detected in message!")
                                return message.get("content")
                
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error waiting for response: {e}")
                time.sleep(1)
        
        logger.warning(f"No response from owo bot within {timeout} seconds")
        return None

# Initialize client
client = None

def detect_captcha(message_content: str) -> bool:
    """Detect if message contains captcha challenge"""
    content_lower = message_content.lower()
    
    for keyword in CAPTCHA_KEYWORDS:
        if keyword in content_lower:
            return True
    
    return False

async def handle_captcha(channel_id: int, message_content: str) -> bool:
    """Handle captcha solving using available services"""
    logger.info(f"Attempting to solve captcha using services: {ENABLED_SERVICES}")
    
    if not ENABLED_SERVICES:
        logger.error("No captcha services configured!")
        return False
    
    # Extract captcha data from message
    captcha_data = extract_captcha_data(message_content)
    
    if not captcha_data:
        logger.error("Could not extract captcha data from message")
        return False
    
    # Try each service in priority order
    for service_name in ENABLED_SERVICES:
        try:
            logger.info(f"Trying {service_name}...")
            service_config = CAPTCHA_SERVICES[service_name]
            
            service = get_service_instance(service_name, service_config)
            if not service:
                continue
            
            solution = service.solve(captcha_data)
            
            if solution:
                logger.info(f"Captcha solved with {service_name}!")
                client.send_message(channel_id, solution)
                return True
            
        except Exception as e:
            logger.error(f"Error with {service_name}: {e}")
            continue
    
    logger.error("Failed to solve captcha with all services")
    return False

def extract_captcha_data(message_content: str) -> dict:
    """Extract captcha data from Discord message"""
    
    captcha_data = {
        "type": "NoCaptchaTaskProxyless",
        "websiteURL": "https://discord.com",
        "websiteKey": extract_sitekey(message_content)
    }
    
    return captcha_data

def extract_sitekey(content: str) -> str:
    """Try to extract sitekey from message content using regex patterns"""
    
    patterns = [
        r'sitekey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        r'["\']([a-zA-Z0-9_-]{40})["\']',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    
    return "unknown_sitekey"

async def play_game(channel_id: int):
    """Main game loop"""
    logger.info("Starting game loop...")
    
    while game_state.is_running:
        try:
            # Send coin flip command
            command_text = f"{COMMAND} {game_state.current_bet}"
            logger.info(f"Sending command: {command_text}")
            client.send_message(channel_id, command_text)
            
            # Wait for result
            result = client.wait_for_owo_response(channel_id)
            
            if result:
                game_state.last_result = result
                game_state.last_timestamp = datetime.now()
                
                # Check for captcha
                if detect_captcha(result):
                    await handle_captcha(channel_id, result)
                
                # Check for result
                if WIN_KEYWORD.lower() in result.lower():
                    game_state.on_win()
                elif LOSS_KEYWORD.lower() in result.lower():
                    game_state.on_loss()
            
            await asyncio.sleep(COMMAND_WAIT_TIME)
        
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
            await asyncio.sleep(COMMAND_WAIT_TIME)

def print_stats():
    """Print game statistics"""
    stats = game_state.get_stats()
    print("\n" + "="*50)
    print("GAME STATISTICS")
    print("="*50)
    print(f"Current Bet: {stats['current_bet']}")
    print(f"Total Games: {stats['total_games']}")
    print(f"Wins: {stats['wins']}")
    print(f"Losses: {stats['losses']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Status: {'Running' if game_state.is_running else 'Stopped'}")
    print("="*50 + "\n")

def main():
    """Main entry point"""
    global client
    
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not found in .env file!")
        return
    
    if not CHANNEL_ID or CHANNEL_ID == 0:
        logger.error("CHANNEL_ID not found in .env file!")
        return
    
    token_type = detect_token_type(DISCORD_TOKEN)
    logger.info(f"Starting Discord Coin Flip Bot...")
    logger.info(f"Token type detected: {token_type}")
    logger.info(f"Configured services: {ENABLED_SERVICES}")
    
    if token_type == "invalid":
        logger.error("Invalid token format!")
        return
    
    if token_type == "unknown":
        logger.warning("Unknown token format, attempting to use it anyway...")
    
    # Initialize client
    client = DiscordClient(DISCORD_TOKEN)
    
    # Verify token
    if not client.verify_token():
        logger.error("Failed to verify token!")
        logger.error("Make sure your token is correct and not expired.")
        logger.error("Go to https://discord.com/developers/applications and reset your token.")
        return
    
    # Start game loop
    game_state.is_running = True
    logger.info("Bot started! Press Ctrl+C to stop")
    
    try:
        # Run async game loop
        asyncio.run(play_game(CHANNEL_ID))
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        game_state.is_running = False
        print_stats()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        game_state.is_running = False

if __name__ == "__main__":
    main()
