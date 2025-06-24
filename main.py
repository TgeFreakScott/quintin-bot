import os
import json
import random
import asyncio
import requests
import discord
from discord import File, app_commands
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from keep_alive import keep_alive
from bs4 import BeautifulSoup

keep_alive()

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

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_CHANNEL_ID = 1385397409550565566
GUILD_ID = 1383828857827758151

client = OpenAI(api_key=OPENAI_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

# Helper to send followup, handling rate limits
async def safe_followup_send(interaction, *args, **kwargs):
    try:
        await interaction.followup.send(*args, **kwargs)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print("Discord: Rate limited (429). Not sending followup.")
        else:
            print("Discord API error:", e)
    except Exception as e:
        print("Other send error:", e)

# Helper for OpenAI with anti-spam delay
async def get_quintin_reply(messages):
    try:
        await asyncio.sleep(1.5)  # Slow down to avoid OpenAI spam
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print("OpenAI error:", e)
        return "Quintin mutters, 'Sorry, I can't recall that right now.'"

# ------------- Commands ----------------

@bot.tree.command(name="askquintin", description="Ask Quintin, the barkeep, anything.", guild=discord.Object(id=GUILD_ID))
async def askquintin(interaction: discord.Interaction, prompt: str):
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

    reply = await get_quintin_reply([
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
    ])
    await safe_followup_send(interaction, reply)

# --- Other Commands ---

@bot.tree.command(name="menu", description="Order food or drinks from the Lucky Griffon.")
@app_commands.describe(item="What would you like to order?")
async def menu(interaction: discord.Interaction, item: str):
    if interaction.channel.id != DISCORD_CHANNEL_ID:
        await interaction.response.send_message(
            "Quintin raises an eyebrow. 'We don’t serve out on the street, friend.'",
            ephemeral=True
        )
        return

    await interaction.response.defer()
    food_menu = {
        "stew": "*A bubbling cauldron of meat and vegetables, always hot, always slightly mysterious.*",
        "bread": "*Thick-sliced, fresh from the oven. Served with herbed butter and a smirk.*",
        "cheese": "*Aged and sharp, with a rind tough enough to stop a dagger.*",
        "meat pie": "*Savory and flaky, with fillings that change daily (but are always tasty).*",
        "roast boar": "*Crispy skin, juicy meat, and a glaze of apples and ale.*",
        "fish chowder": "*Creamy and rich, with a hint of sea salt and stories.*",
        "dragon sausage": "*Spicy. Real dragon? Probably not. You want some or not?*",
        "mushroom risotto": "*Cooked with wild mushrooms from the Moonwood. Slightly magical.*",
        "owlbear ribs": "*Smoky, tender, and probably illegal. Comes with napkins.*",
        "tavern platter": "*A bit of everything. For the indecisive or the drunk.*"
    }
    drink_menu = {
        "ale": "*Foamy and dark, brewed right here. One mug is plenty. Two is... ambitious.*",
        "wine": "*A red so dry it might judge you for ordering it.*",
        "mead": "*Sticky, golden, and makes your teeth feel warm.*",
        "water": "*Cold and clean. Quintin still raises an eyebrow.*",
        "mulled cider": "*Spiced with cinnamon, clove, and subtle hints of regret.*",
        "dwarven stout": "*Strong enough to floor a Goliath. Served in small cups for safety.*",
        "elven nectar": "*Light, floral, and makes you think of forests you'll never see.*",
        "firewhiskey": "*Burns like betrayal. Goes down smooth.*",
        "ghost grog": "*Chilled by spirits. Literally.*",
        "wyrmshot": "*A tiny vial of something green. Glows. Quintin won't tell you what's in it.*"
    }
    item_lower = item.lower()
    if item_lower in food_menu:
        reply = f"🍽️ Quintin nods and serves you **{item.title()}**.\n{food_menu[item_lower]}"
    elif item_lower in drink_menu:
        reply = f"🍺 Quintin pours you a glass of **{item.title()}**.\n{drink_menu[item_lower]}"
    elif item_lower in ("secret", "mystery", "special"):
        reply = (
            "*Quintin leans in, lowers his voice.*\n"
            "'You want the *special*, eh? Alright. One [REDACTED] stew, on the house. Just don’t ask what’s in it.'"
        )
    else:
        reply = (
            f"Quintin blinks. 'Sorry friend, we don't serve *{item}*. Try something from the menu below.'\n\n"
            f"**🍴 Food Available:** {', '.join(food_menu.keys())}\n"
            f"**🍻 Drinks Available:** {', '.join(drink_menu.keys())}\n"
            f"_(Try ordering 'secret' if you're feeling lucky...)_"
        )
    await safe_followup_send(interaction, reply)

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
        await safe_followup_send(interaction, "Quintin scratches his head. 'No songs left in the book tonight, friend.'")
        return
    chosen_song = random.choice(song_files)
    file_path = os.path.join(song_folder, chosen_song)
    song_title = os.path.splitext(chosen_song)[0].replace("_", " ").title()
    await safe_followup_send(interaction, content=f"*Quintin clears his throat and begins to sing:* 🎵 **{song_title}**", file=File(file_path))

# --- On Ready and Bot Run ---

@bot.event
async def on_ready():
    print(f"Bot online as {bot.user} in guild(s):", [g.name for g in bot.guilds])
    print("Loaded GUILD_ID:", GUILD_ID, type(GUILD_ID))
    print("Use /sync in Discord if you don't see slash commands!")

bot.run(DISCORD_TOKEN)
