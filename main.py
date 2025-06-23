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
    "*Quintin peers out the window, watching the sky.*",
    "*Quintin wipes down the bar with a rag that’s seen better days.*",
    "*Quintin carefully counts coins behind the bar.*",
    "*Quintin rearranges bottles on the shelf by height, then by colour.*",
    "*Quintin steps outside and brings in a small crate of root vegetables.*",
    "*Quintin adjusts the crooked painting of a griffon behind the counter.*",
    "*Quintin scoops out a ladle of stew and tastes it with a frown.*",
    "*Quintin mends a torn apron with quick, practiced stitches.*",
    "*Quintin dusts the old adventurers' trophies on the mantle.*",
    "*Quintin checks the cellar trapdoor, then locks it again.*",
    "*Quintin adds a log to the fireplace, sending up a small cloud of embers.*",
    "*Quintin cleans a tankard with a practiced swirl and stack.*",
    "*Quintin leans over a scroll, tracing something with his finger.*",
    "*Quintin oils the hinges on the front door — they still creak.*",
    "*Quintin sets out fresh candles on each table.*",
    "*Quintin flips through a dusty recipe book behind the counter.*",
    "*Quintin polishes the Lucky Griffon’s brass sign above the hearth.*",
    "*Quintin checks the herb bundle hanging over the kitchen door.*",
    "*Quintin waters a wilting potted plant in the windowsill.*",
    "*Quintin untangles a ball of string with growing frustration.*",
    "*Quintin taps a barrel twice and listens, judging its fullness.*",
    "*Quintin straightens a stack of mismatched coasters.*",
    "*Quintin folds a stack of clean rags and sets them neatly aside.*",
    "*Quintin brushes away cobwebs from a high corner with a broom.*",
    "*Quintin scratches a note in the tavern ledger and underlines it twice.*",
    "*Quintin peeks into a small locked box under the counter, then locks it again.*",
    "*Quintin sweeps a corner of the room that somehow always gathers dust.*",
    "*Quintin wipes soot off the chimney flue.*",
    "*Quintin stretches his back with a quiet grunt and rolls his shoulders.*",
    "*Quintin neatly folds a lost scarf and places it on the cloak rack.*",
    "*Quintin feeds a stray cat skulking under one of the tables.*",
    "*Quintin locks the front door, then unlocks it again and checks the latch.*",
    "*Quintin flicks a speck of dust off a glass and inspects it closely.*",
    "*Quintin carefully stacks firewood beside the hearth.*",
    "*Quintin wipes a ring of condensation off a table.*",
    "*Quintin scribbles a tally onto a notched board above the bar.*",
    "*Quintin lifts a floorboard and peers underneath, just briefly.*",
    "*Quintin adjusts the curtains to let in a sliver of moonlight.*",
    "*Quintin places a faded wanted poster behind the bar.*",
    "*Quintin wraps a cracked mug in cloth and places it on a shelf.*",
    "*Quintin drops a few herbs into the simmering stew pot.*",
    "*Quintin flips a coin through his fingers absently.*",
    "*Quintin rubs a hand over an old burn mark on the bar.*",
    "*Quintin presses his ear to the wall, then shakes his head.*",
    "*Quintin opens a window briefly, sniffs the air, then shuts it tight.*",
    "*Quintin lights a lantern, then lowers its flame to a soft glow.*"
]

@scheduler.scheduled_job("interval", minutes=60)
async def tavern_ambience():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(random.choice(status_messages))

# 🔹 On Ready
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=YOUR_GUILD_ID)

        # Clear both global and guild commands
        await bot.tree.clear_commands()
        await bot.tree.clear_commands(guild=guild)

        # Re-register only the intended ones
        await bot.tree.sync(guild=guild)  # Use only guild sync for faster updates

        print(f"🍻 Quintin is ready. Synced slash commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")


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

from bs4 import BeautifulSoup  # Make sure this is in your imports

@bot.tree.command(name="who", description="Ask Quintin about someone from the world.")
async def who(interaction: discord.Interaction, name: str):
    if interaction.channel.id != DISCORD_CHANNEL_ID:
        await interaction.response.send_message(
            "Quintin raises an eyebrow. 'Only regulars get to ask about folks, friend.'",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        name_key = name.lower()
        if name_key in LORE_INDEX:
            url = LORE_INDEX[name_key]
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                content_text = soup.get_text(separator="\n").strip()
                paragraphs = [p.strip() for p in content_text.split("\n") if len(p.strip()) > 50]

                if not paragraphs:
                    lore = f"Quintin flips through the ledger. 'Strange, nothing here on {name.title()}.'"
                else:
                    snippet = "\n\n".join(random.sample(paragraphs, min(2, len(paragraphs))))
                    lore = f"**About {name.title()}**\n{snippet[:2000]}"
            else:
                lore = f"Quintin frowns. 'Trouble finding the records for {name.title()} – the ledger gave me a {response.status_code} error.'"
        else:
            lore = f"Quintin scratches his beard. 'Can’t say I know much about {name.title()}, but the name rings a bell…'"

        await interaction.followup.send(lore)

    except Exception as e:
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Quintin dropped the ledger: `{e}`")


@bot.tree.command(name="rumour", description="Quintin shares a whispered rumour from the tavern.")
async def rumour(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        # Pick a random topic from your lore index
        topic = random.choice(list(LORE_INDEX.keys()))
        lore = fetch_lore_from_index(topic)

        if lore.startswith("("):  # handle fetch issues
            lore = "No real knowledge survives on this, only whispers and lies."

        # Generate a rumour using OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Quintin, a wise and slightly gruff barkeep of the Lucky Griffon tavern in Alexandria. "
                        "You speak in dry humour, always staying in character. A customer has asked for a whispered rumour. "
                        "Based on the lore I give you, invent a rumour that sounds half-believable, dramatic, or eerie. "
                        "Make it short (1–2 sentences), and make sure it feels tied to Sordia Vignti's world."
                    )
                },
                {"role": "user", "content": f"Lore about {topic}:\n{lore}\n\nWhat’s the rumour?"}
            ]
        )

        rumour_text = response.choices[0].message.content.strip()

        await interaction.followup.send(f"*Quintin leans in and murmurs:*\n> {rumour_text}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        await interaction.followup.send("❌ Quintin burned the stew trying to remember that rumour.")

import random

@bot.tree.command(name="investigate", description="Ask Quintin to dig into a rumour or mystery.")
async def investigate(interaction: discord.Interaction, topic: str):
    if interaction.channel.id != DISCORD_CHANNEL_ID:
        await interaction.response.send_message(
            "Quintin leans in and mutters, 'Can't go spreading suspicions outside the tavern.'",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    # Roll a d20 to determine investigation quality
    roll = random.randint(1, 20)

    # Try to identify known lore
    topic_guess = next((word for word in topic.lower().split() if word in LORE_INDEX), "")
    lore = fetch_lore_from_index(topic_guess) if topic_guess else ""

    # Vary the tone based on the roll
    if roll == 1:
        clue_intro = "Quintin stares blankly. 'I asked around... but everyone gave me the runaround.'"
    elif roll <= 5:
        clue_intro = f"Quintin scratches his head. 'Found something odd about *{topic}*, but it might be just drunk talk...'"
    elif roll <= 10:
        clue_intro = f"Quintin slides a note across the bar. 'Bit of gossip about *{topic}*—could be worth a sniff.'"
    elif roll <= 15:
        clue_intro = f"Quintin leans in, eyes narrowing. 'Turns out *{topic}* has more to it than I thought...'"
    elif roll < 20:
        clue_intro = f"Quintin grins. 'A friend owed me a favour. Here's what I dug up on *{topic}*.'"
    else:
        clue_intro = f"Quintin wipes his hands and speaks low. 'I risked a lot pulling this thread on *{topic}*—listen closely.'"

    # Prompt for GPT response
    prompt = (
        f"You are Quintin, a barkeep informant. You just rolled a {roll} on a D&D-style investigation check.\n"
        f"The topic was: '{topic}'.\n"
        f"{'Known info:\n' + lore if lore else 'You don’t know much directly, but whispers abound.'}\n"
        f"Respond with a flavourful rumour, lead, or clue based on the roll result."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Quintin, barkeep of the Lucky Griffon. You're dry, witty, and know more than you let on."},
                {"role": "user", "content": prompt}
            ]
        )
        clue = response.choices[0].message.content
        await interaction.followup.send(f"🎲 *Quintin rolled a {roll} on his investigation.*\n{clue_intro}\n\n{clue}")
    except Exception as e:
        await interaction.followup.send(f"Quintin groans. 'Something went wrong with my digging: `{e}`'")

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

    # Expanded menu
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

    await interaction.followup.send(reply)

@bot.tree.command(name="gossip", description="Quintin shares some juicy, fresh tavern gossip.")
async def gossip(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
        
        prompt = (
            "You are Quintin, the barkeep of the Lucky Griffon in Alexandria. "
            "In a warm, whispery tone, share a rumour you've heard from your patrons. "
            "It should sound like juicy tavern gossip, mysterious or mildly absurd, and relate to the world of Sordia Vignti — "
            "including Kalteo, Alexandria, Big Tony, Zargathax, Ellette, Graxen, Qwimby, Steve Emberfoot, kyo, orlan, or any known figures or places from that world. "
            "Keep it under 2 sentences, and deliver it as if you're leaning in conspiratorially."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )

        rumour = response.choices[0].message.content.strip()
        await interaction.followup.send(f"*Quintin leans in and whispers:*\n> {rumour}")

    except Exception as e:
        await interaction.followup.send(f"❌ Quintin spilled the stew instead of gossiping: `{e}`")

@bot.tree.command(name="compliment", description="Quintin gives someone a heartfelt (or odd) compliment.")
async def compliment(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer()
    prompt = (
        f"You're Quintin, the barkeep of the Lucky Griffon in Alexandria. "
        f"You're warm, witty, and charming. Give a unique and funny compliment to the adventurer {user.name}. "
        f"Use old-timey, tavern-style flair, like something you'd say while pouring a drink."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        reply = response.choices[0].message.content
        await interaction.followup.send(f"{user.mention} {reply}")
    except Exception as e:
        await interaction.followup.send(f"❌ Quintin dropped the bottle: `{e}`")


@bot.tree.command(name="insult", description="Quintin roasts someone, barkeep-style.")
async def insult(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer()
    prompt = (
        f"You're Quintin, the barkeep of the Lucky Griffon in Alexandria. "
        f"You're sarcastic but never cruel. Roast the adventurer {user.name} with dry wit, "
        f"like a grumpy tavern keeper who's seen too much. Keep it humorous and lighthearted."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        reply = response.choices[0].message.content
        await interaction.followup.send(f"{user.mention} {reply}")
    except Exception as e:
        await interaction.followup.send(f"❌ Quintin choked on his own sass: `{e}`")


# 🔹 Run the bot
bot.run(DISCORD_TOKEN)
