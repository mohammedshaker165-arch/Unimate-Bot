# UniMate Assistant Bot

A Telegram bot that gives students access to course materials by academic level, semester, course, material type, and file number. Administrators can upload and register materials through the bot.

## Features

- Course navigation for Levels 1, 2, and 3
- Lecture, practical, and question materials
- Telegram document delivery and stored external links
- WhatsApp community links and external resources
- Admin-only material upload workflow
- MySQL-backed material catalog

## Technologies

- Python 3.10+
- aiogram 3
- aiomysql
- MySQL or a compatible managed MySQL service

## Project Structure

```text
.
├── main.py           # Bot entry point and handlers
├── BD.code2.sql      # Database schema and sample insert
├── requirements.txt  # Python dependencies
├── .env.example      # Configuration template
├── .gitignore        # Files excluded from Git
└── README.md
```

## Local Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and replace every placeholder with your own values. The bot automatically loads this local `.env` file. On a hosting platform, configure the same variables in the service's environment settings instead.

   PowerShell example:

   ```powershell
   $env:BOT_TOKEN = "your_token"
   $env:ADMIN_IDS = "your_telegram_id"
   $env:DB_HOST = "127.0.0.1"
   $env:DB_USER = "unimate_bot"
   $env:DB_PASS = "your_database_password"
   $env:DB_NAME = "unimate_assitant_materials"
   ```

4. Create the database and table using `BD.code2.sql`. The sample insert is optional.

5. Start the bot:

   ```powershell
   python main.py
   ```

## Database

The bot requires a reachable MySQL database. Run `BD.code2.sql` with a MySQL user that can create the database and table, or create them through your provider. Set `DB_HOST`, `DB_USER`, `DB_PASS`, and `DB_NAME` to match that database.

## Deployment

For Railway, Render, or a similar worker service:

1. Push the project to a private or public GitHub repository.
2. Create a worker/background service from the repository.
3. Add the variables from `.env.example` in the provider's environment settings. Never commit `.env` or real credentials.
4. Provision MySQL and run `BD.code2.sql` once.
5. Set the start command to:

   ```text
   python main.py
   ```

The bot uses long polling, so deploy it as a worker/background service rather than a web service unless the platform specifically supports always-on worker processes. Only one running instance should use the bot token at a time.

## GitHub Security

The bot token and database password must be rotated if they were ever committed to a repository or shared publicly. Do not place credentials in source code, README files, SQL sample data, or screenshots.
