import os
import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

import json
import requests
import random
from keep_alive import keep_alive
from apscheduler.schedulers.asyncio import AsyncIOScheduler

keep_alive()

# Load the lore index once at startup
with open("lore_index.json", "r") as file:
    LORE_INDEX = json.load(file)

def fetch_lore_from_index(topic: str) -> str:
    try:
        topic = topic.lower()
        if topic in LORE_INDEX:
            url = LORE_INDEX[topic]
            response = requests.get(url)
            if response.status_code == 200:
                return response.text.strip()[:2000]  # Limit to avoid token overflow
            else:
                return f"(Couldn't load {topic} lore: {response.status_code})"
        else:
            return f"(No entry found for '{topic}' in the lore index.)"
    except Exception as e:
        return f"(Error fetching lore: {e})"

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_CHANNEL_ID = 1385397409550565566  # Locked to this channel only

# Initialise OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

scheduler = AsyncIOScheduler()

status_messages = [
    "*Quintin quietly sweeps the tavern floor, whistling a forgotten tune.*",
    "*Quintin refills a mug, inspecting the stew pot with a suspicious eye.*",
    "*Quintin flips through a dusty ledger, muttering about old adventuring tabs.*",
    "*Quintin polishes the bar with care, humming softly.*",
    "*Quintin lights a candle in the corner, glancing at the empty table by the fire.*",
    "*A stool creaks. Quintin frowns. He starts to repair the stool*",
    "*Quintin sharpens a blade behind the bar, just in case.*",
    "*Quintin tacks a new rumour to the noticeboard.*",
    "*Quintin peers out the window, watching the sky*"
]

@scheduler.scheduled_job("interval", minutes=30)
async def tavern_ambience():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(random.choice(status_messages))

@bot.event
async def on_ready():
    try:
        scheduler.start()
        synced = await bot.tree.sync()
        print(f"\U0001f954 Quintin is behind the bar. Synced {len(synced)} commands. Logged in as {bot.user}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@bot.tree.command(name="askquintin", description="Ask Quintin, the barkeep, anything.")
async def askquintin(interaction: discord.Interaction, prompt: str):
    try:
        # Restrict usage to only the allowed channel
        if interaction.channel.id != DISCORD_CHANNEL_ID:
            await interaction.response.send_message(
                "Quintin wipes his hands and says, 'We only talk shop at the bar, friend.'",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        topic_guess = ""
        for word in prompt.lower().split():
            if word in LORE_INDEX:
                topic_guess = word
                break

        lore = ""
        if topic_guess:
            lore = fetch_lore_from_index(topic_guess)
            if lore.startswith("("):  # Error or not found
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

bot.run(DISCORD_TOKEN)
