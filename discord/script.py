import os
import discord
from discord.ext import commands
import aiohttp
import sqlite3
import random
from config import RE_TOKEN, DEV_ID, DEV_TOKEN, DEVMODE, SNCF_API_KEY

conn = sqlite3.connect("et-mon-train.db")
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS servers (server_id INTEGER PRIMARY KEY, prefix TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, wins INTEGER)")

# Fonction qui verifie si une colonne existe dans une table
def column_exists(cursor, table_name, column_name):
    cursor.execute("PRAGMA table_info({})".format(table_name))
    columns = cursor.fetchall()
    for column in columns:
        if column[1] == column_name:
            return True
    return False

if not column_exists(c, "servers", "channel_id"):
    c.execute("ALTER TABLE servers ADD COLUMN channel_id INTEGER")

if not column_exists(c, "users", "user_id"):
    c.execute("ALTER TABLE users ADD COLUMN user_id INTEGER")

# Initialisation du bot
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

bot = Bot()

async def fetch_test(test_request):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{test_request}", headers={"Authorization": SNCF_API_KEY}) as response:
            return await response.json()

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté avec succès !")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {synced} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    await bot.change_presence(activity=discord.Game(name='ET MON TRAIN ?!'))

@bot.tree.command(name="test")
async def test(ctx, test_request: str):
    await ctx.response.send_message(await fetch_test(test_request))

# Commandes admin
@bot.tree.command(name="stop")
@commands.is_owner()
async def stop(ctx):
    await ctx.response.send_message("🛑 Arrêt du bot...")
    await bot.close()

bot.run(RE_TOKEN)