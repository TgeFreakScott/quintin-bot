import os
import json
import random
import requests
import discord
from discord import File, app_commands
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from keep_alive import keep_alive

# 🔹 Keep the bot alive with a ping server
keep_alive()

# 🔹 Load lore index from local file
with open("lore_index.json", "r") as file:
    LORE_INDEX = json.load(file)

def fetch_lore_from_index(topic: str) -> str:
    try:
        topic = topic.lower()
        if topic in LORE_INDEX:
            url = LORE_INDEX[topic]
            response = requests.get(url)
            if response.status_code == 200:
                return response.text.strip()[:2000]
            else:
                return f"(Couldn't load {topic} lore: {response.status_code})"
        else:
            return f"(No entry found for '{topic}' in the lore index.)"
    except Exception as e:
        return f"(Error fetching lore: {e})"

# 🔹 Load tokens and secrets
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_CHANNEL_ID = 1385397409550565566
GUILD_ID = 1383828857827758151  # Your server ID

client = OpenAI(api_key=OPENAI_API_KEY)

# 🔹 Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

# 🔹 Idle tavern chatter
status_messages = [
    "*Quintin quietly sweeps the tavern floor, whistling a forgotten tune.*",
    "*Quintin refills a mug, inspecting the stew pot with a suspicious eye.*",
    "*Quintin flips through a dusty ledger, muttering about old adventuring tabs.*",
    "*Quintin polishes the bar with care, humming softly.*",
    "*Quintin lights a candle in the corner, glancing at the empty table by the fire.*",
    "*A stool creaks. Quintin frowns. He starts to repair the stool.*",
    "*Quintin sharpens a blade behind the bar, just in case.*",
    "*Quintin tacks a new rumour to the noticeboard.*",
    "*Quintin peers out the window, watching the sky.*"
]

@scheduler.scheduled_job("interval", minutes=30)
async def tavern_ambience():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(random.choice(status_messages))

# 🔹 On Ready
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)  # Optional: copy global to guild
        await bot.tree.sync(guild=guild)
        scheduler.start()
        print(f"🍻 Quintin is behind the bar. Synced to guild {GUILD_ID}.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# 🔹 Ask Quintin
@bot.tree.command(name="askquintin", description="Ask Quintin, the barkeep, anything.", guild=discord.Object(id=GUILD_ID))
async def askquintin(interaction: discord.Interaction, prompt: str):
    try:
        if interaction.channel.id != DISCORD_CHANNEL_ID:
            await interaction.response.send_message(
                "Quintin wipes his hands and says, 'We only talk shop at the bar, friend.'",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        topic_guess = next((word for word in prompt.lower().split() if word in LORE_INDEX), "")
        lore = fetch_lore_from_index(topic_guess) if topic_guess else ""

        if lore.startswith("("):
            lore = (
                f"Rumour has it, no one really knows the full story of {topic_guess.capitalize()}, "
                f"but the tavern regulars whisper they once did something truly legendary..."
            )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Quintin, the barkeep of the Lucky Griffon in Alexandria. "
                        "You speak with dry humour and warmth, and never break character. "
                        "You serve stew, gossip, and wisdom to adventurers.\n\n"
                        f"Here is what you know about {topic_guess or 'this matter'}:\n{lore}"
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message.content
        await interaction.followup.send(reply)

    except Exception as e:
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Quintin dropped his mug: `{e}`")

# 🔹 Sing command
@bot.tree.command(name="sing", description="Ask Quintin to sing a tavern song.", guild=discord.Object(id=GUILD_ID))
async def sing(interaction: discord.Interaction):
    if interaction.channel.id != DISCORD_CHANNEL_ID:
        await interaction.response.send_message(
            "Quintin grumbles, 'I only sing in the tavern, friend.'",
            ephemeral=True
        )
        return

    song_folder = "assets"
    song_files = [f for f in os.listdir(song_folder) if f.endswith((".mp3", ".wav"))]

    if not song_files:
        await interaction.response.send_message(
            "Quintin scratches his head. 'No songs left in the book tonight, friend.'"
        )
        return

    chosen_song = random.choice(song_files)
    file_path = os.path.join(song_folder, chosen_song)
    song_title = os.path.splitext(chosen_song)[0].replace("_", " ").title()

    await interaction.response.send_message(
        content=f"*Quintin clears his throat and begins to sing:* 🎵 **{song_title}**",
        file=File(file_path)
    )

# 🔹 List Commands
@bot.tree.command(name="listcommands", description="Lists all registered commands.", guild=discord.Object(id=GUILD_ID))
async def list_commands(interaction: discord.Interaction):
    cmds = [cmd.name for cmd in bot.tree.get_commands(guild=discord.Object(id=GUILD_ID))]
    await interaction.response.send_message(f"Registered commands: {', '.join(cmds)}")

# 🔹 Run the bot
bot.run(DISCORD_TOKEN)
