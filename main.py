# ============================================================
# DOT DISCORD BOT - coollol.py
# ============================================================
import os
import asyncio
import time
import sqlite3
import json
from datetime import datetime

from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

# ============================================================
# BOT SETUP
# ============================================================
import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=";", intents=intents)

# ============================================================
# CONFIG
# ============================================================
MEMBER_COUNT_CHANNEL = 1425200856944345218
VERIFICATION_CHANNEL = 1411669470040031282
WELCOME_CHANNEL = 1411676037154340874
AFK_ROLES = [1411694640951853208, 1411694617715281963, 1411694510429438053, 1411694596911796234]

SIDEBAR_COLOR = 0xf9ce4c
WELCOME_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475698142061006889/welcomedot.png?ex=699e6e7e&is=699d1cfe&hm=29990ae9a8ebf06a9a27f9b9cf874a1014c35303d207c99adf94496f3c7e4193&"
FOOTER_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475698084817408220/footerisrp_1.png?ex=699e6e70&is=699d1cf0&hm=53dec095fb33d98d05e4bcff6ffa0224b2cb66fe6f38b9181254ef286cc4e1ef&"

# ============================================================
# DATABASE SETUP
# ============================================================
conn = sqlite3.connect('afk.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS afk (
    user_id INTEGER PRIMARY KEY,
    reason TEXT,
    start_time INTEGER,
    pings TEXT DEFAULT '[]'
)''')
conn.commit()

def get_afk(user_id):
    c.execute("SELECT * FROM afk WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        return {"reason": result[1], "start_time": result[2], "pings": json.loads(result[3])}
    return None

def set_afk(user_id, reason):
    c.execute("INSERT OR REPLACE INTO afk (user_id, reason, start_time, pings) VALUES (?, ?, ?, '[]')", (user_id, reason, int(time.time())))
    conn.commit()

def remove_afk(user_id):
    c.execute("DELETE FROM afk WHERE user_id = ?", (user_id,))
    conn.commit()

def add_ping(user_id, pinger_id, message_content, channel_id, message_id):
    current = get_afk(user_id)
    if current:
        pings = current["pings"]
        pings.append({
            "pinger_id": pinger_id, 
            "message": message_content, 
            "time": int(time.time()),
            "channel_id": channel_id,
            "message_id": message_id
        })
        pings = pings[-50:]
        c.execute("UPDATE afk SET pings = ? WHERE user_id = ?", (json.dumps(pings), user_id))
        conn.commit()

def can_use_afk(member):
    return any(role.id in AFK_ROLES for role in member.roles)

# ============================================================
# MEMBER COUNT UPDATE (Every 5 minutes)
# ============================================================
async def update_member_count():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            channel = bot.get_channel(MEMBER_COUNT_CHANNEL)
            if channel and channel.guild:
                count = len([m for m in channel.guild.members if not m.bot])
                await channel.edit(name=f"Members: {count}")
        except Exception as e:
            print(f"Error updating member count: {e}")
        await asyncio.sleep(300)

# ============================================================
# VERIFICATION MESSAGE (Every 12 hours)
# ============================================================
async def send_verification_message():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            channel = bot.get_channel(VERIFICATION_CHANNEL)
            if channel:
                await channel.send("> <@&1467239847444877332> Make sure to click **Verify with Bloxlink** for proper DOT access.")
        except Exception as e:
            print(f"Error sending verification: {e}")
        await asyncio.sleep(43200)

# ============================================================
# WELCOME EMBED
# ============================================================
@bot.event
async def on_member_join(member):
    if member.bot:
        return
    
    channel = bot.get_channel(WELCOME_CHANNEL)
    if not channel:
        return
    
    # Image Embed 1
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=WELCOME_IMAGE)
    
    # Text Embed 2
    embed2 = nextcord.Embed(
        description=f"# Welcome to President Roleplay Community・Department of Transportation.\n\n"
                   f"Hello {member.display_name}\n\n"
                   f"**Welcome to PRPC・Department of Transportation!**\n"
                   f"> - DOT primarily focuses on enhancing the convoy organization mechanics of Presidential Roleplay.\n"
                   f"> - We also engage in political and security affairs with the Mayor, ensuring that his safety and protection is prevalent.\n\n"
                   f"# Review our __key__ channels:\n\n"
                   f"> - Ensure proper Roblox OAuthentication in <#1411669470040031282>.\n"
                   f"> - Read more about the logistics and contributions of DOT in <#1411679034068176927>.\n"
                   f"> - You must follow the ⁠<#1411675000892690505>, which also include PRPC's community regulations.\n"
                   f"> - Want to apply? Head on over to ⁠<#1411677337346379859>.\n"
                   f"> - Need further assistance with anything. Contact <#1411677021976920074> or make <#1467242635482628278>.\n"
                   f"> - Lastly, you are able to configure your pings/mentions in ⁠<#1411684343495266375>.\n\n"
                   f"# __Additional Information__\n"
                   f"Note: The Department of Transportation is primarily ran by MasterGato567 [Director Gato], kalokmanklm [Assistant Director Ka Lok], and Mys1icX [Assistant Director Pyra]. Please refrain from contacting them, unless absolutely necessarily, and follow the chain of command of online individuals, by contacting a Technician, then Operator, then Engineer, then Manager.\n\n"
                   f"Thank you so much for joining the Department of Transportation, and we hope you have a fun roleplay experience and friendly communication environment.",
        color=SIDEBAR_COLOR
    )
    
    # Image Embed 3
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    await channel.send(content=member.mention, embeds=[embed1, embed2, embed3])

# ============================================================
# AFK SYSTEM
# ============================================================
@bot.slash_command(name="afk", description="Set AFK status")
async def afk(interaction: nextcord.Interaction, reason: str = "AFK"):
    if not can_use_afk(interaction.user):
        await interaction.response.send_message("This command is only permissable for usage by a DOT Rookie Operator+.", ephemeral=True)
        return
    
    set_afk(interaction.user.id, reason)
    
    # Try to update nickname
    try:
        old_nick = interaction.user.display_name
        if not old_nick.startswith("[AFK]"):
            try:
                await interaction.user.edit(nick=f"[AFK] {old_nick}")
            except nextcord.Forbidden:
                await interaction.user.send("I am unable to update your nickname due to your highest role being above my role. You are AFK though.")
    except Exception:
        pass
    
    # Embed 1
    embed1 = nextcord.Embed(
        description=f"{interaction.user.mention}, you are now away from keyboard [AFK]. Anyone who mentions you will be notified of your status.",
        color=SIDEBAR_COLOR
    )
    
    # Embed 2 (Footer)
    embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed2.set_image(url=FOOTER_IMAGE)
    
    await interaction.response.send_message(embeds=[embed1, embed2])

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Check if author is AFK
    afk_data = get_afk(message.author.id)
    if afk_data:
        remove_afk(message.author.id)
        
        # Calculate time away
        elapsed = int(time.time()) - afk_data["start_time"]
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        
        pings = afk_data["pings"]
        
        # Build ping info
        ping_text = ""
        if pings:
            for ping in pings[-5:]:
                pinger = message.guild.get_member(ping["pinger_id"])
                pinger_name = pinger.name if pinger else "Unknown"
                channel = bot.get_channel(ping["channel_id"])
                channel_mention = f"#{channel.name}" if channel else "Unknown"
                msg_link = f"https://discord.com/channels/{message.guild.id}/{ping['channel_id']}/{ping['message_id']}"
                
                ping_text += f"\n`Who?` {pinger_name}\n`What?` {ping['message']}\n`When?` <t:{ping['time']}:F>\n`Where?` [{channel_mention}]({msg_link})\n"
        
        # Embed 1 - Welcome back
        embed1 = nextcord.Embed(
            description=f"**You are now back online! Here is a summary while you were AFK for {hours} hours, {minutes} minutes, and {seconds} seconds!**\n{ping_text}",
            color=SIDEBAR_COLOR
        )
        
        # Embed 2 - Footer
        embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
        embed2.set_image(url=FOOTER_IMAGE)
        
        await message.channel.send(embeds=[embed1, embed2], delete_after=30)
    
    # Check for mentions of AFK users
    for mention in message.mentions:
        afk_info = get_afk(mention.id)
        if afk_info:
            add_ping(mention.id, message.author.id, message.content, message.channel.id, message.id)
            
            elapsed = int(time.time()) - afk_info["start_time"]
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            
            embed = nextcord.Embed(
                description=f"**{mention.name}** is currently AFK: **{afk_info['reason']}**\nAway for: **{hours}h {minutes}m**",
                color=SIDEBAR_COLOR
            )
            embed.set_image(url=FOOTER_IMAGE)
            
            await message.reply(embed=embed, delete_after=20)
    
    await bot.process_commands(message)

# ============================================================
# ON READY
# ============================================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(update_member_count())
    bot.loop.create_task(send_verification_message())

# ============================================================
# RUN BOT
# ============================================================
bot.run(os.environ.get("DISCORD_TOKEN"))

