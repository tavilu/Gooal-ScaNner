Gooal Scanner - TotalFootball (RapidAPI) integration
---------------------------------------------------
Files included:
- app.py
- services/totalfootball_service.py
- services/telegram_service.py
- templates/index.html
- requirements.txt, Procfile, README.md

Setup on Render:
1) Create project and push these files to GitHub repo connected to Render.
2) In Render dashboard, set Environment Variables:
   - RAPIDAPI_KEY (your X-RapidAPI-Key)
   - RAPIDAPI_HOST (usually totalfootball-api.p.rapidapi.com)
   - TELEGRAM_BOT_TOKEN (your bot token)
   - CHAT_ID (your Telegram chat id)
3) Deploy. The polling background task runs automatically and sends Telegram messages when rules match.
Notes:
- Adjust parsing in services/totalfootball_service.py if your provider returns a different JSON shape.
- Tune polling interval and alert rules as needed.
