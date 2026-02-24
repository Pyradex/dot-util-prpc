# ============================================================
# KEEP-ALIVE CODE - Paste this at the TOP of your main.py
# ============================================================
import os
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Start Flask in background thread
threading.Thread(target=run_web, daemon=True).start()

# ============================================================
# YOUR BOT CODE GOES HERE
# ============================================================

# Example bot setup (replace with your actual bot code)
import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Your commands here...

# ============================================================
# AT THE VERY END OF YOUR FILE - Run the bot
# ============================================================
bot.run(os.environ.get("DISCORD_TOKEN"))
