# Discord Coin Flip Bot - Multi-Service Captcha Support

An automated Discord bot that plays coin flip games, handles captchas with multiple solving services, and manages betting progression.

## Features

- 🎲 **Automated Coin Flip Gaming** - Sends `owo cf 400` command and tracks bets
- 📊 **Smart Betting Logic** - Doubles bet on loss, resets to 400 on win
- 📖 **Message Reading** - Monitors channel for owo bot results (heads/tails)
- 🔐 **Multi-Service Captcha Solving** - Supports CapSolver, 2Captcha, NopeCHA, AntiCaptcha, DeathByCaptcha, and more
- 🔑 **Token Configuration** - Easy setup with Discord bot token and captcha API keys
- 🚀 **24/7 Ready** - Run locally or on a server for continuous operation
- ⚡ **Fallback Support** - Automatically switches to next service if one fails

## Supported Captcha Services

1. **CapSolver** - Fast, reliable, modern API
2. **2Captcha** - Wide support, affordable
3. **NopeCHA** - Specialized in modern captchas
4. **AntiCaptcha** - High accuracy, excellent support
5. **DeathByCaptcha** - Budget-friendly option
6. **More services can be added easily**

## Requirements

- Python 3.8+
- discord.py
- requests
- python-dotenv

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file:
```env
DISCORD_TOKEN=your_discord_bot_token_here
CHANNEL_ID=your_discord_channel_id

# Add any captcha services you use
CAPSOLVER_API_KEY=your_capsolver_key
2CAPTCHA_API_KEY=your_2captcha_key
NOPECHA_API_KEY=your_nopecha_key
ANTICAPTCHA_API_KEY=your_anticaptcha_key
DEATHBYCAPTCHA_USER=your_dbc_username
DEATHBYCAPTCHA_PASS=your_dbc_password
```

### 3. Run the Bot
```bash
python bot.py
```

## Discord Commands

- `!start` - Start the coin flip game
- `!stop` - Stop the game and show stats
- `!stats` - Show current game statistics

## How It Works

1. Bot sends `owo cf {current_bet}` command
2. Waits for owo bot's result message
3. If result contains "tails" → loss detected → doubles bet
4. If result contains "heads" → win detected → resets bet to 400
5. If captcha detected → automatically tries enabled services in priority order
6. Solves captcha and proceeds
7. Repeats until stopped

## Captcha Service Endpoints

### CapSolver
- Create Task: `POST https://api.capsolver.com/createTask`
- Get Result: `POST https://api.capsolver.com/getTaskResult`
- Balance: `POST https://api.capsolver.com/getBalance`

### 2Captcha
- Submit: `POST/GET https://2captcha.com/in.php`
- Get Result: `GET https://2captcha.com/res.php`
- Balance: `GET https://2captcha.com/res.php?action=getbalance`

### NopeCHA
- Solve: `POST https://api.nopecha.com/api/v1/solve`
- Get Solution: `GET https://api.nopecha.com/api/v1/get_solution`

### AntiCaptcha
- Create Task: `POST https://api.anticaptcha.com/createTask`
- Get Result: `POST https://api.anticaptcha.com/getTaskResult`
- Balance: `POST https://api.anticaptcha.com/getBalance`

### DeathByCaptcha
- Upload: `POST https://deathbycaptcha.com/api/captcha`
- Get Result: `GET https://deathbycaptcha.com/api/captcha/{captcha_id}`
- Auth: HTTP Basic Authentication (username:password)

## Configuration

Edit `config.py` to customize:
- Starting bet amount (default: 400)
- Bet multiplier on loss (default: 2x)
- Channel to monitor
- Captcha service priority order
- Timeout settings
- Retry attempts

## Logging

All activities are logged to `bot.log` including:
- Bet amounts and results
- Captcha detection and solving attempts
- Service fallback switches
- Errors and exceptions

View logs:
```bash
tail -f bot.log
```

## Deployment for 24/7 Running

See [SETUP.md](SETUP.md) for detailed deployment guides:
- Local machine setup
- Heroku deployment (free)
- AWS EC2 setup
- DigitalOcean droplet
- VPS with systemd

## Troubleshooting

**Bot not responding?**
- Verify DISCORD_TOKEN is correct
- Check CHANNEL_ID is valid
- Ensure bot has message permissions

**Captcha not solving?**
- Check API keys are valid
- Verify account has balance/credits
- Check logs: `grep -i captcha bot.log`
- Try different services

**Messages not being read?**
- Verify bot has "Read Message History" permission
- Check owo bot username matches
- Verify message detection keywords

## Support

- CapSolver: https://docs.capsolver.com/guide/api/
- 2Captcha: https://2captcha.com/api-docs
- NopeCHA: https://nopecha.com/docs/api
- AntiCaptcha: https://anti-captcha.com/apidoc
- DeathByCaptcha: https://www.deathbycaptcha.com/user/api

## Security

⚠️ **IMPORTANT**: Never commit `.env` file!
- Use `.env.example` as template
- Add `.env` to `.gitignore` (already done)
- Keep API keys secret
- Use different test keys before production

## License

MIT
