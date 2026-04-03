# Discord Auto Messenger

An automated messaging tool for Discord.

## Features
- Automated message sending to multiple channels
- Rate limit handling and cooldown management
- GUI and CLI interfaces
- Secure configuration management

## Installation
1. Download the latest release
2. Ensure dependencies are installed: `pip install -r requirements.txt`
3. Run `python3 src/main.py` to launch the GUI

## First-time setup (config)
- When launched, the app creates `config.json` from `src/config_template.json` if missing.
- Open `config.json` and set your Discord token and target IDs like:
```json
{
  "token": "YOUR_DISCORD_TOKEN_HERE",
  "targets": [{"type": "channel", "id": "123456789012345678"}],
  "user_agent": "Mozilla/5.0 ...",
  "delay": 15,
  "cycle_sleep": 300,
  "theme": "arc"
}
```
- Save and rerun the app.

## Security Note
This tool is for educational purposes only. Use responsibly.
