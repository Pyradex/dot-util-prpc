# Standalone bot to keep your main bot alive on hosting platforms
# This bot just stays online to prevent your host from sleeping

import os
import nextcord
from nextcord.ext import commands
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

# Start the web server in a background thread
threading.Thread(target=run_web, daemon=True).start()

# Bot setup
intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=">", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Keep-alive bot is online: {bot.user}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! Keep-alive bot is running.")

# Run the bot - token from environment variable
bot.run(os.getenv("TOKEN"), reconnect=True)

