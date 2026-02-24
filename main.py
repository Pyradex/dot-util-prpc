# ============================================================
# DOT DISCORD BOT - coollol.py
# ============================================================
import os
import asyncio
import time
import sqlite3
import json

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

bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

# ============================================================
# CONFIG
# ============================================================
MEMBER_COUNT_CHANNEL = 1425200856944345218
VERIFICATION_CHANNEL = 1411669470040031282
WELCOME_CHANNEL = 1411676037154340874
APPLICATION_CHANNEL = 1411677337346379859
DEPLOYMENT_CHANNEL = 1467622434395000993

AFK_ROLES = [1411694640951853208, 1411694617715281963, 1411694510429438053, 1411694596911796234]
VERIFICATION_ROLE = 1467239847444877332

# Role IDs for commands
SAY_ROLES = [1411694510429438053, 1411694596911796234]
PURGE_ROLES = [1411694596911796234, 1411694510429438053]
DMROLE_ROLES = [1411694596911796234]
DMUSER_ROLES = [1411694596911796234, 1411694510429438053, 1411694617715281963, 1411694640951853208]
DEPLOYMENT_PING_ROLE = 1411695097170624512
DEPLOYMENT_ROLES = [1411694596911796234, 1411694510429438053]

SIDEBAR_COLOR = 0xf9ce4c
WELCOME_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475698142061006889/welcomedot.png?ex=699e6e7e&is=699d1cfe&hm=29990ae9a8ebf06a9a27f9b9cf874a1014c35303d207c99adf94496f3c7e4193&"
FOOTER_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475698084817408220/footerisrp_1.png?ex=699e6e70&is=699d1cf0&hm=53dec095fb33d98d05e4bcff6ffa0224b2cb66fe6f38b9181254ef286cc4e1ef&"
HELP_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475708680304594944/bot_utils_dot.png?ex=699e784e&is=699d26ce&hm=547f72dad68ad0023cb575f10725ff244058722e648d41a96b694a175dc3818f&"
DEPLOYMENT_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475711782525079712/deploywdot.png?ex=699e7b32&is=699d29b2&hm=3fa79c8d76c0fc9551b22b338e36c7004920faed960e4284bb28c46a4ed82c43&"

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

def can_use_say(member):
    return any(role.id in SAY_ROLES for role in member.roles)

def can_use_purge(member):
    return any(role.id in PURGE_ROLES for role in member.roles)

def can_use_dmrole(member):
    return any(role.id in DMROLE_ROLES for role in member.roles)

def can_use_dmuser(member):
    return any(role.id in DMUSER_ROLES for role in member.roles)

def can_use_deployment(member):
    return any(role.id in DEPLOYMENT_ROLES for role in member.roles)

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
last_verification_message_id = None

async def send_verification_message():
    global last_verification_message_id
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            channel = bot.get_channel(VERIFICATION_CHANNEL)
            if channel:
                if last_verification_message_id:
                    try:
                        old_msg = await channel.fetch_message(last_verification_message_id)
                        await old_msg.delete()
                    except:
                        pass
                msg = await channel.send(f"> <@&{VERIFICATION_ROLE}> Make sure to click **Verify with Bloxlink** for proper DOT access.")
                last_verification_message_id = msg.id
        except Exception as e:
            print(f"Error sending verification: {e}")
        await asyncio.sleep(43200)

# ============================================================
# APPLICATION STATUS MESSAGE (One time on startup)
# ============================================================
async def send_application_message():
    await bot.wait_until_ready()
    try:
        channel = bot.get_channel(APPLICATION_CHANNEL)
        if channel:
            await channel.send("## <:DOT_PRPC:1467614174740877436> `Status: Available to Applicants ✅`")
    except Exception as e:
        print(f"Error sending application message: {e}")

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def create_dm_embed(message_content, sender):
    embed1 = nextcord.Embed(description=message_content, color=SIDEBAR_COLOR)
    embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed2.set_image(url=FOOTER_IMAGE)
    return [embed1, embed2]

def create_help_embeds(prefix: str):
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=HELP_IMAGE)
    
    commands_list = ""
    if prefix == ">":
        commands_list = """`Command:` >say
`Definition:` Deletes your message and sends the specified content as the bot. Used for announcements or responding as the bot.
`Permissions:` Management & Directive Roles (1411694510429438053, 1411694596911796234)

`Command:` >afk
`Definition:` Sets your status as Away From Keyboard. Adds [AFK] prefix to your nickname and notifies others when they ping you.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` >purge
`Definition:` Deletes a specified number of messages from the current channel (1-100).
`Permissions:` Management & Directive Roles (1411694596911796234, 1411694510429438053)

`Command:` >dmrole
`Definition:` Sends a direct message to all members with a specific role.
`Permissions:` Directive Role (1411694596911796234)

`Command:` >dmuser
`Definition:` Sends a direct message to a specific user by their ID.
`Permissions:` Directive & Management Roles

`Command:` >deployment
`Definition:` Initiates a DOT deployment session with organized instructions for participants.
`Permissions:` Management & Directive Roles (1411694596911796234, 1411694510429438053)

`Command:` >help
`Definition:` Shows this help message with all available commands and their descriptions.
`Permissions:` Everyone"""
    else:
        commands_list = """`Command:` /say
`Definition:` Deletes your message and sends the specified content as the bot. Used for announcements or responding as the bot.
`Permissions:` Management & Directive Roles (1411694510429438053, 1411694596911796234)

`Command:` /afk
`Definition:` Sets your status as Away From Keyboard. Adds [AFK] prefix to your nickname and notifies others when they ping you.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /purge
`Definition:` Deletes a specified number of messages from the current channel (1-100).
`Permissions:` Management & Directive Roles (1411694596911796234, 1411694510429438053)

`Command:` /dmrole
`Definition:` Sends a direct message to all members with a specific role.
`Permissions:` Directive Role (1411694596911796234)

`Command:` /dmuser
`Definition:` Sends a direct message to a specific user by their ID.
`Permissions:` Directive & Management Roles

`Command:` /deployment
`Definition:` Initiates a DOT deployment session with organized instructions for participants.
`Permissions:` Management & Directive Roles (1411694596911796234, 1411694510429438053)

`Command:` /help
`Definition:` Shows this help message with all available commands and their descriptions.
`Permissions:` Everyone"""
    
    embed2 = nextcord.Embed(
        title=f"# <:DOT_PRPC:1467614174740877436>・__{prefix}help・Utilities Documentation__",
        description=commands_list,
        color=SIDEBAR_COLOR
    )
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    return [embed1, embed2, embed3]

# ============================================================
# ON MESSAGE
# ============================================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # ===== SAY COMMAND =====
    if message.content.startswith(">say ") and can_use_say(message.author):
        content = message.content[5:].strip()
        try:
            await message.delete()
        except:
            pass
        await message.channel.send(content)
        return
    
    # ===== VERIFICATION CHANNEL AUTO-DELETE =====
    if message.channel.id == VERIFICATION_CHANNEL:
        if "https://discord.com/channels/" not in message.content:
            try:
                await message.delete()
            except:
                pass
    
    # ===== AFK SYSTEM =====
    afk_data = get_afk(message.author.id)
    if afk_data:
        remove_afk(message.author.id)
        
        elapsed = int(time.time()) - afk_data["start_time"]
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        
        pings = afk_data["pings"]
        ping_count = len(pings)
        
        # Build welcome back message
        if ping_count == 0:
            # No pings
            description = f"Welcome back, {message.author.display_name}. You are now available.\n> Duration of AFK: **{hours} hours, {minutes} minutes, and {seconds} seconds.**\n> You were not pinged, while you were AFK."
            delete_after = None  # Don't delete if no pings
        else:
            # Has pings
            ping_text = ""
            for ping in pings[-5:]:
                pinger = message.guild.get_member(ping["pinger_id"])
                pinger_name = pinger.name if pinger else "Unknown"
                channel = bot.get_channel(ping["channel_id"])
                channel_mention = f"#{channel.name}" if channel else "Unknown"
                msg_link = f"https://discord.com/channels/{message.guild.id}/{ping['channel_id']}/{ping['message_id']}"
                
                ping_text += f"\n`Who?` {pinger_name}\n`What?` {ping['message']}\n`When?` <t:{ping['time']}:F>\n`Where?` [{channel_mention}]({msg_link})\n"
            
            description = f"Welcome back, {message.author.display_name}. You are now available.\n> Duration of AFK: **{hours} hours, {minutes} minutes, and {seconds} seconds.**\n> Below lists a summary of the DOT community members that had mentioned you, while you were AFK.{ping_text}"
            # Delete after 30 seconds if 3+ pings
            delete_after = 30 if ping_count >= 3 else None
        
        embed1 = nextcord.Embed(description=description, color=SIDEBAR_COLOR)
        embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
        embed2.set_image(url=FOOTER_IMAGE)
        
        await message.channel.send(embeds=[embed1, embed2], delete_after=delete_after)
    
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
# WELCOME EMBED
# ============================================================
@bot.event
async def on_member_join(member):
    if member.bot:
        return
    
    channel = bot.get_channel(WELCOME_CHANNEL)
    if not channel:
        return
    
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=WELCOME_IMAGE)
    
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
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    await channel.send(content=member.mention, embeds=[embed1, embed2, embed3])

# ============================================================
# SLASH COMMANDS
# ============================================================

@bot.slash_command(name="help", description="Show help documentation")
async def help_slash(interaction: nextcord.Interaction):
    embeds = create_help_embeds("/")
    await interaction.response.send_message(embeds=embeds)

@bot.slash_command(name="afk", description="Set AFK status")
async def afk(interaction: nextcord.Interaction, reason: str = "AFK"):
    if not can_use_afk(interaction.user):
        await interaction.response.send_message("This command is only permissable for usage by a DOT Rookie Operator+.", ephemeral=True)
        return
    
    set_afk(interaction.user.id, reason)
    
    try:
        old_nick = interaction.user.display_name
        if not old_nick.startswith("[AFK]"):
            try:
                await interaction.user.edit(nick=f"[AFK] {old_nick}")
            except nextcord.Forbidden:
                await interaction.user.send("I am unable to update your nickname due to your highest role being above my role. You are AFK though.")
    except Exception:
        pass
    
    embed1 = nextcord.Embed(
        description=f"{interaction.user.mention}, you are now away from keyboard [AFK]. Anyone who mentions you will be notified of your status.",
        color=SIDEBAR_COLOR
    )
    embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed2.set_image(url=FOOTER_IMAGE)
    
    await interaction.response.send_message(embeds=[embed1, embed2])

@bot.slash_command(name="say", description="Send a message as the bot")
async def say_slash(interaction: nextcord.Interaction, message: str):
    if not can_use_say(interaction.user):
        await interaction.response.send_message("The command `/say` is only permissable to Management and Directive members.", ephemeral=True)
        return
    
    await interaction.response.send_message(message)

@bot.slash_command(name="purge", description="Purge messages in channel")
async def purge_slash(interaction: nextcord.Interaction, amount: int):
    if not can_use_purge(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
        return
    
    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)

@bot.slash_command(name="dmrole", description="DM all users with a specific role")
async def dmrole_slash(interaction: nextcord.Interaction, role_id: str, message: str):
    if not can_use_dmrole(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        role_id = int(role_id)
    except ValueError:
        await interaction.response.send_message("Invalid role ID.", ephemeral=True)
        return
    
    role = interaction.guild.get_role(role_id)
    if not role:
        await interaction.response.send_message("Role not found.", ephemeral=True)
        return
    
    embeds = create_dm_embed(message, interaction.user)
    success = 0
    failed = 0
    
    for member in role.members:
        try:
            await member.send(embeds=embeds)
            success += 1
        except:
            failed += 1
    
    await interaction.response.send_message(f"Message sent to {success} members. Failed: {failed}", ephemeral=True)

@bot.slash_command(name="dmuser", description="DM a specific user")
async def dmuser_slash(interaction: nextcord.Interaction, user_id: str, message: str):
    if not can_use_dmuser(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        user_id = int(user_id)
    except ValueError:
        await interaction.response.send_message("Invalid user ID.", ephemeral=True)
        return
    
    user = await bot.fetch_user(user_id)
    if not user:
        await interaction.response.send_message("User not found.", ephemeral=True)
        return
    
    embeds = create_dm_embed(message, interaction.user)
    
    try:
        await user.send(embeds=embeds)
        await interaction.response.send_message(f"Message sent to {user.name}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Failed to send message: {e}", ephemeral=True)

@bot.slash_command(name="deployment", description="Initiate a DOT deployment session")
async def deployment_slash(interaction: nextcord.Interaction, initial_roleplay: str = "Normal"):
    if not can_use_deployment(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    channel = bot.get_channel(DEPLOYMENT_CHANNEL)
    if not channel:
        await interaction.response.send_message("Deployment channel not found.", ephemeral=True)
        return
    
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=DEPLOYMENT_IMAGE)
    
    embed2 = nextcord.Embed(
        description=f"# A DOT Deployment is being initiated!\n\n"
                   f"> - Host: {interaction.user.mention}\n"
                   f"> - Initial Roleplay: **{initial_roleplay}**\n"
                   f"> - Location: DOT Building\n\n"
                   f"Welcome to another session.\n"
                   f"> - In elections, be sure that cars are organized neatly behind the staff vehicle with the assistance of person-pushing and tools.\n"
                   f"> - Refuel Staff + Convoy Vehicles.\n"
                   f"> - Fix Broken Tires from Weaponry or Spike Strips/Tool Abuse\n"
                   f"> - Report Tool Abusers to PRPC Staff.\n"
                   f"> - Before the president moves, make sure a DOT Unit **sets up** a proper entrance and parking system to ensure good coordination. This will help you receive a promotion.\n"
                   f"> - High-Ranks observe Technicians and Operators for promotions and good, efficient conduct.\n"
                   f"> - Suggestions based on observations will be passed on for SHR to implement new policies/changes to the procedures of DOT personnel.",
        color=SIDEBAR_COLOR
    )
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    await channel.send(content=f"<@&{DEPLOYMENT_PING_ROLE}>", embeds=[embed1, embed2, embed3])
    await interaction.response.send_message("Deployment message sent!", ephemeral=True)

# ============================================================
# PREFIX COMMANDS
# ============================================================

@bot.command(name="help")
async def help_prefix(ctx):
    embeds = create_help_embeds(">")
    await ctx.send(embeds=embeds)

@bot.command(name="afk")
async def afk_prefix(ctx, *, reason="AFK"):
    if not can_use_afk(ctx.author):
        await ctx.send("This command is only permissable for usage by a DOT Rookie Operator+.")
        return
    
    set_afk(ctx.author.id, reason)
    
    try:
        old_nick = ctx.author.display_name
        if not old_nick.startswith("[AFK]"):
            try:
                await ctx.author.edit(nick=f"[AFK] {old_nick}")
            except nextcord.Forbidden:
                await ctx.author.send("I am unable to update your nickname due to your highest role being above my role. You are AFK though.")
    except Exception:
        pass
    
    embed1 = nextcord.Embed(
        description=f"{ctx.author.mention}, you are now away from keyboard [AFK]. Anyone who mentions you will be notified of your status.",
        color=SIDEBAR_COLOR
    )
    embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed2.set_image(url=FOOTER_IMAGE)
    
    await ctx.send(embeds=[embed1, embed2])

@bot.command(name="purge")
async def purge_prefix(ctx, amount: int):
    if not can_use_purge(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    if amount < 1 or amount > 100:
        await ctx.send("Amount must be between 1 and 100.")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="dmrole")
async def dmrole_prefix(ctx, role_id: int, *, message: str):
    if not can_use_dmrole(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Role not found.")
        return
    
    embeds = create_dm_embed(message, ctx.author)
    success = 0
    failed = 0
    
    for member in role.members:
        try:
            await member.send(embeds=embeds)
            success += 1
        except:
            failed += 1
    
    await ctx.send(f"Message sent to {success} members. Failed: {failed}", delete_after=10)

@bot.command(name="dmuser")
async def dmuser_prefix(ctx, user_id: int, *, message: str):
    if not can_use_dmuser(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    user = await bot.fetch_user(user_id)
    if not user:
        await ctx.send("User not found.")
        return
    
    embeds = create_dm_embed(message, ctx.author)
    
    try:
        await user.send(embeds=embeds)
        await ctx.send(f"Message sent to {user.name}.", delete_after=10)
    except Exception as e:
        await ctx.send(f"Failed to send message: {e}")

@bot.command(name="deployment")
async def deployment_prefix(ctx, *, initial_roleplay="Normal"):
    if not can_use_deployment(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    channel = bot.get_channel(DEPLOYMENT_CHANNEL)
    if not channel:
        await ctx.send("Deployment channel not found.")
        return
    
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=DEPLOYMENT_IMAGE)
    
    embed2 = nextcord.Embed(
        description=f"# A DOT Deployment is being initiated!\n\n"
                   f"> - Host: {ctx.author.mention}\n"
                   f"> - Initial Roleplay: **{initial_roleplay}**\n"
                   f"> - Location: DOT Building\n\n"
                   f"Welcome to another session.\n"
                   f"> - In elections, be sure that cars are organized neatly behind the staff vehicle with the assistance of person-pushing and tools.\n"
                   f"> - Refuel Staff + Convoy Vehicles.\n"
                   f"> - Fix Broken Tires from Weaponry or Spike Strips/Tool Abuse\n"
                   f"> - Report Tool Abusers to PRPC Staff.\n"
                   f"> - Before the president moves, make sure a DOT Unit **sets up** a proper entrance and parking system to ensure good coordination. This will help you receive a promotion.\n"
                   f"> - High-Ranks observe Technicians and Operators for promotions and good, efficient conduct.\n"
                   f"> - Suggestions based on observations will be passed on for SHR to implement new policies/changes to the procedures of DOT personnel.",
        color=SIDEBAR_COLOR
    )
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    await channel.send(content=f"<@&{DEPLOYMENT_PING_ROLE}>", embeds=[embed1, embed2, embed3])
    await ctx.send("Deployment message sent!", delete_after=10)

# ============================================================
# ON READY
# ============================================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        await bot.sync_all_application_commands()
        print("Slash commands synced!")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    bot.loop.create_task(update_member_count())
    bot.loop.create_task(send_verification_message())
    bot.loop.create_task(send_application_message())

# ============================================================
# RUN BOT
# ============================================================
bot.run(os.environ.get("DISCORD_TOKEN"))

