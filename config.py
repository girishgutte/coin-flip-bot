import os
from dotenv import load_dotenv

load_dotenv()

# Discord Settings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

# Coin Flip Settings
INITIAL_BET = 400
BET_MULTIPLIER = 2  # Double on loss
WIN_KEYWORD = "heads"
LOSS_KEYWORD = "tails"

# Captcha Services Configuration
CAPTCHA_SERVICES = {
    "capsolver": {
        "enabled": bool(os.getenv("CAPSOLVER_API_KEY")),
        "api_key": os.getenv("CAPSOLVER_API_KEY", ""),
        "timeout": 30,
        "priority": 1
    },
    "2captcha": {
        "enabled": bool(os.getenv("2CAPTCHA_API_KEY")),
        "api_key": os.getenv("2CAPTCHA_API_KEY", ""),
        "timeout": 60,
        "priority": 2
    },
    "nopecha": {
        "enabled": bool(os.getenv("NOPECHA_API_KEY")),
        "api_key": os.getenv("NOPECHA_API_KEY", ""),
        "timeout": 30,
        "priority": 3
    },
    "anticaptcha": {
        "enabled": bool(os.getenv("ANTICAPTCHA_API_KEY")),
        "api_key": os.getenv("ANTICAPTCHA_API_KEY", ""),
        "timeout": 30,
        "priority": 4
    },
    "deathbycaptcha": {
        "enabled": bool(os.getenv("DEATHBYCAPTCHA_USER") and os.getenv("DEATHBYCAPTCHA_PASS")),
        "username": os.getenv("DEATHBYCAPTCHA_USER", ""),
        "password": os.getenv("DEATHBYCAPTCHA_PASS", ""),
        "timeout": 60,
        "priority": 5
    }
}

# Get enabled services sorted by priority
ENABLED_SERVICES = sorted(
    [s for s, config in CAPTCHA_SERVICES.items() if config["enabled"]],
    key=lambda x: CAPTCHA_SERVICES[x]["priority"]
)

# Captcha Detection
CAPTCHA_KEYWORDS = [
    "captcha",
    "verify",
    "human check",
    "recaptcha",
    "hcaptcha",
    "challenge"
]

# Logging
LOG_FILE = "bot.log"
LOG_LEVEL = "INFO"

# Retry Settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Message Reading
MESSAGE_WAIT_TIMEOUT = 10  # seconds to wait for bot response
POLL_INTERVAL = 2  # seconds between checking for messages

# Command Settings
COMMAND = "owo cf"
COMMAND_WAIT_TIME = 5  # seconds to wait after sending command
