# Coin Flip Bot - Setup & Deployment Guide

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/girishgutte/coin-flip-bot.git
cd coin-flip-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Get Your Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and click "Add Bot"
4. Copy the token
5. Under "OAUTH2 > URL Generator", select:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Read Messages/View Channels`, `Read Message History`
6. Use the generated URL to invite bot to your server

### 4. Get Your Channel ID
1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on the channel and select "Copy Channel ID"

### 5. Set Up Captcha Services

Choose one or more services:

**CapSolver** (Recommended)
- Register at https://www.capsolver.com
- Get API key from dashboard

**2Captcha**
- Register at https://2captcha.com
- Get API key from settings

**NopeCHA**
- Register at https://nopecha.com
- Get API key from dashboard

**AntiCaptcha**
- Register at https://anti-captcha.com
- Get API key from account settings

**DeathByCaptcha**
- Register at https://www.deathbycaptcha.com
- Get username and password

### 6. Configure Environment
1. Copy `.env.example` to `.env`
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your values:
   ```env
   DISCORD_TOKEN=your_token_here
   CHANNEL_ID=123456789
   CAPSOLVER_API_KEY=your_capsolver_key
   2CAPTCHA_API_KEY=your_2captcha_key
   # ... other services
   ```

### 7. Run the Bot
```bash
python bot.py
```

## Discord Commands

Once the bot is running:

- `!start` - Start the coin flip game
- `!stop` - Stop the game and show stats
- `!stats` - Show current game statistics

## How to Deploy for 24/7 Running

### Option 1: Local Machine
Keep your computer running and the bot script active.

```bash
# Simple way
python bot.py

# Better way (runs in background)
nohup python bot.py > bot_output.log 2>&1 &
```

### Option 2: Heroku (Easy, Free tier available)

1. Create Heroku account at https://www.heroku.com
2. Install Heroku CLI
3. Create a `Procfile` in repo:
   ```
   worker: python bot.py
   ```
4. Create a `runtime.txt`:
   ```
   python-3.9.18
   ```
5. Deploy:
   ```bash
   heroku login
   heroku create your-app-name
   heroku config:set DISCORD_TOKEN=your_token
   heroku config:set CHANNEL_ID=your_channel_id
   heroku config:set CAPSOLVER_API_KEY=your_key
   # ... set other env vars
   
   git push heroku main
   heroku ps:scale worker=1
   heroku logs --tail
   ```

### Option 3: AWS EC2 (Reliable)

1. Launch EC2 instance (t2.micro free tier, Ubuntu)
2. SSH into instance:
   ```bash
   ssh -i your-key.pem ec2-user@your-instance-ip
   ```
3. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   ```
4. Clone repo and setup:
   ```bash
   git clone https://github.com/girishgutte/coin-flip-bot.git
   cd coin-flip-bot
   pip3 install -r requirements.txt
   cp .env.example .env
   # Edit .env with your keys
   nano .env
   ```
5. Run with systemd (persistent):
   ```bash
   sudo nano /etc/systemd/system/coinflip.service
   ```
   Add:
   ```ini
   [Unit]
   Description=Coin Flip Bot
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/coin-flip-bot
   ExecStart=/usr/bin/python3 /home/ubuntu/coin-flip-bot/bot.py
   Restart=on-failure
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   Then:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable coinflip
   sudo systemctl start coinflip
   sudo systemctl status coinflip
   ```

### Option 4: DigitalOcean (Affordable - $5/month)

1. Create Droplet ($5/month, Ubuntu 22.04)
2. SSH and setup:
   ```bash
   ssh root@your_droplet_ip
   apt-get update
   apt-get install python3 python3-pip git
   ```
3. Clone and configure (same as AWS above)
4. Use systemd for persistence

### Option 5: VPS with Screen/Tmux

```bash
# Install screen
sudo apt-get install screen

# Run bot in background
screen -S coin-flip-bot python bot.py

# Detach: Ctrl+A then D
# Reattach: screen -r coin-flip-bot
# List sessions: screen -ls
```

## Monitoring Logs

Check `bot.log` for activity:

```bash
# View live logs
tail -f bot.log

# View last 50 lines
tail -50 bot.log

# Search for errors
grep ERROR bot.log

# Search for captcha events
grep -i captcha bot.log

# Search for wins/losses
grep "WIN\|LOSS" bot.log
```

## Troubleshooting

### Bot not responding?
- Verify `DISCORD_TOKEN` is correct
- Check `CHANNEL_ID` is valid and correct
- Ensure bot has message permissions in channel
- Check firewall isn't blocking connection

### Captcha not solving?
- Verify all API keys are correct
- Check account has sufficient balance/credits
- Review logs: `grep -i error bot.log`
- Try different services in priority order
- Some services have rate limits - wait and retry

### Messages not being read?
- Verify bot has "Read Message History" permission
- Check owo bot username (currently: "owo")
- Verify message detection keywords in config.py
- Ensure bot is in same channel

### Bot crashes or disconnects?
- Check logs for errors: `tail -f bot.log`
- Verify Discord token hasn't expired
- Check internet connection stability
- Use systemd/screen for auto-restart

## Tips for Production

1. **Monitor Balance**: Regularly check captcha service account balances
2. **Start Small**: Test with initial bet before running 24/7
3. **Use Multiple Services**: Ensures game continues if one fails
4. **Set Bet Limits**: Consider adding max bet to prevent huge losses
5. **Regular Backups**: Back up `bot.log` to track statistics
6. **Error Alerts**: Set up email/webhook alerts for crashes
7. **Update Logs**: Rotate logs to prevent disk full: `logrotate`

## Updating the Bot

```bash
# Pull latest changes
git pull origin main

# Restart bot (if using systemd)
sudo systemctl restart coinflip

# Or if using screen
# Ctrl+C to stop, then: python bot.py
```

## Support & Resources

- Discord.py docs: https://discordpy.readthedocs.io/
- CapSolver: https://docs.capsolver.com/guide/api/
- 2Captcha: https://2captcha.com/api-docs
- NopeCHA: https://nopecha.com/docs/api
- AntiCaptcha: https://anti-captcha.com/apidoc
- DeathByCaptcha: https://www.deathbycaptcha.com/user/api

## Security Best Practices

⚠️ **IMPORTANT**: 
- Never commit `.env` file with real tokens
- Use `.env.example` as template only
- Keep all API keys secret and secure
- Use different test keys before production
- Rotate tokens regularly
- Use strong, unique passwords for services
- Monitor account activity for suspicious access

---

Enjoy your automated coin flip bot! 🎲
