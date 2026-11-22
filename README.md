# PC Monitor Bot

A Telegram bot that watches the online/offline status of your computers through an HTTP status API and notifies you when something changes. Designed for home labs and Unraid.

[![Support on Ko-fi](https://img.shields.io/badge/Ko--fi-support-ff5e5b?logo=ko-fi&logoColor=white)](https://ko-fi.com/fahrentech)

## Features

- 🔄 Periodic status checks with a configurable interval
- 📱 Telegram notification when a computer goes online or offline (with response time)
- 📊 `/status` and `/info` commands
- 🔐 Only one authorized Telegram user can use the bot
- 🐳 Docker image, example Gitea Actions workflow and deploy script for Unraid

## How it works

The bot polls `GET {API_URL}/api/status/{computer_id}` with the `X-API-Key` header and expects JSON like:

```json
{ "name": "Desktop", "status": "online", "response_time": 1.42 }
```

`status` is `online`, `offline` or any other value (shown as an error). You can back this with any small service that pings your machines.

## Quick start

```bash
git clone https://github.com/Rip-07/pc-monitor-bot.git
cd pc-monitor-bot
cp .env.example .env   # fill in your values
docker compose up -d --build
```

## Configuration

| Variable | Description |
| --- | --- |
| `BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `API_URL` | Base URL of your status API |
| `API_KEY` | Key sent in the `X-API-Key` header |
| `CHAT_ID` | Chat that receives notifications |
| `AUTHORIZED_USER_ID` | Telegram user ID allowed to use commands |
| `COMPUTERS` | Comma-separated computer IDs, default `main_pc` |
| `CHECK_INTERVAL` | Check interval in seconds, default `60` |

Never commit your `.env` — it is already in `.gitignore`.

## Deploy on Unraid with Gitea Actions

`.gitea/workflows/deploy.yml` builds the image on a runner with Docker access and calls `deploy/deploy-unraid.sh`. Add `BOT_TOKEN`, `API_URL`, `API_KEY`, `CHAT_ID`, `AUTHORIZED_USER_ID`, `CHECK_INTERVAL` as repository secrets and `COMPUTERS` as a variable.

## Commands

| Command | Description |
| --- | --- |
| `/start` | Help |
| `/status` | Current status of all computers |
| `/info` | Bot settings |

## License

MIT — see [LICENSE](LICENSE). If this saves you time, you can [buy me a coffee on Ko-fi](https://ko-fi.com/fahrentech) ☕
