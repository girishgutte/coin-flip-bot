import discord
from discord.ext import commands, tasks
import logging
import os
from datetime import datetime
import asyncio
import re

from config import *
from captcha_services import get_service_instance

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Enabled captcha services: {', '.join(ENABLED_SERVICES)}")
    logger.info(f"Watching channel ID: {CHANNEL_ID}")

@bot.command(name="start")
async def start_game(ctx):
    """Start the coin flip game"""
    if game_state.is_running:
        await ctx.send("❌ Game already running!")
        return
    
    game_state.is_running = True
    logger.info("Game started!")
    await ctx.send(f"✅ Game started! Initial bet: {game_state.current_bet}")
    
    await play_game()

@bot.command(name="stop")
async def stop_game(ctx):
    """Stop the coin flip game"""
    if not game_state.is_running:
        await ctx.send("❌ Game not running!")
        return
    
    game_state.is_running = False
    stats = game_state.get_stats()
    logger.info(f"Game stopped! Final stats: {stats}")
    
    embed = discord.Embed(title="Game Stopped", color=discord.Color.red())
    embed.add_field(name="Total Games", value=stats["total_games"])
    embed.add_field(name="Wins", value=stats["wins"])
    embed.add_field(name="Losses", value=stats["losses"])
    embed.add_field(name="Win Rate", value=f"{stats['win_rate']:.2f}%")
    embed.add_field(name="Current Bet", value=stats["current_bet"])
    
    await ctx.send(embed=embed)

@bot.command(name="stats")
async def show_stats(ctx):
    """Show current game statistics"""
    stats = game_state.get_stats()
    
    embed = discord.Embed(title="Game Statistics", color=discord.Color.blue())
    embed.add_field(name="Current Bet", value=stats["current_bet"])
    embed.add_field(name="Total Games", value=stats["total_games"])
    embed.add_field(name="Wins", value=stats["wins"])
    embed.add_field(name="Losses", value=stats["losses"])
    embed.add_field(name="Win Rate", value=f"{stats['win_rate']:.2f}%")
    embed.add_field(name="Status", value="🟢 Running" if game_state.is_running else "🔴 Stopped")
    
    await ctx.send(embed=embed)

async def play_game():
    """Main game loop"""
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        logger.error(f"Channel {CHANNEL_ID} not found!")
        return
    
    while game_state.is_running:
        try:
            # Send coin flip command
            await send_command(channel)
            
            # Wait for result
            result = await read_result(channel)
            
            if result:
                game_state.last_result = result
                game_state.last_timestamp = datetime.now()
                
                if WIN_KEYWORD.lower() in result.lower():
                    game_state.on_win()
                elif LOSS_KEYWORD.lower() in result.lower():
                    game_state.on_loss()
            
            await asyncio.sleep(COMMAND_WAIT_TIME)
        
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
            await asyncio.sleep(COMMAND_WAIT_TIME)

async def send_command(channel):
    """Send the coin flip command"""
    command_text = f"{COMMAND} {game_state.current_bet}"
    logger.info(f"Sending command: {command_text}")
    
    try:
        await channel.send(command_text)
    except Exception as e:
        logger.error(f"Failed to send command: {e}")

async def read_result(channel, timeout: int = MESSAGE_WAIT_TIMEOUT) -> str:
    """Read the owo bot's result message"""
    
    def check(message):
        # Check if message is from owo bot and contains result keywords
        return (message.author.name.lower() == "owo" and 
                (WIN_KEYWORD.lower() in message.content.lower() or 
                 LOSS_KEYWORD.lower() in message.content.lower() or
                 any(kw in message.content.lower() for kw in CAPTCHA_KEYWORDS)))
    
    try:
        message = await bot.wait_for('message', check=check, timeout=timeout)
        logger.info(f"Received message: {message.content}")
        
        # Check for captcha
        if detect_captcha(message.content):
            logger.warning("Captcha detected in message!")
            await handle_captcha(channel, message)
        
        return message.content
    
    except asyncio.TimeoutError:
        logger.warning(f"No response from owo bot within {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Error reading result: {e}")
        return None

def detect_captcha(message_content: str) -> bool:
    """Detect if message contains captcha challenge"""
    content_lower = message_content.lower()
    
    for keyword in CAPTCHA_KEYWORDS:
        if keyword in content_lower:
            return True
    
    return False

async def handle_captcha(channel, message) -> bool:
    """Handle captcha solving using available services"""
    logger.info(f"Attempting to solve captcha using services: {ENABLED_SERVICES}")
    
    if not ENABLED_SERVICES:
        logger.error("No captcha services configured!")
        return False
    
    # Extract captcha data from message (this depends on the captcha format)
    captcha_data = extract_captcha_data(message)
    
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
                logger.info(f"✅ Captcha solved with {service_name}!")
                await channel.send(solution)
                return True
            
        except Exception as e:
            logger.error(f"Error with {service_name}: {e}")
            continue
    
    logger.error("Failed to solve captcha with all services")
    return False

def extract_captcha_data(message) -> dict:
    """Extract captcha data from Discord message
    
    This needs to be customized based on what captcha format is being used.
    For now, returning a generic reCAPTCHA v2 structure.
    """
    
    # This is a placeholder - you'll need to customize based on actual captcha format
    # Looking for patterns like site keys, URLs, etc. in the message
    
    captcha_data = {
        "type": "NoCaptchaTaskProxyless",  # or appropriate type
        "websiteURL": "https://discord.com",  # Replace with actual URL if found
        "websiteKey": extract_sitekey(message.content)
    }
    
    return captcha_data

def extract_sitekey(content: str) -> str:
    """Try to extract sitekey from message content using regex patterns"""
    
    # Common patterns for sitekeys
    patterns = [
        r'sitekey["\']?\s*[:=]\s*["\']([^"\']+ )["\']',
        r'["\']([a-zA-Z0-9_-]{40})["\']',  # Common sitekey length
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    
    return "unknown_sitekey"

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

def main():
    """Main entry point"""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not found in .env file!")
        return
    
    if not CHANNEL_ID or CHANNEL_ID == 0:
        logger.error("CHANNEL_ID not found in .env file!")
        return
    
    logger.info("Starting Discord Coin Flip Bot...")
    logger.info(f"Configured services: {ENABLED_SERVICES}")
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
