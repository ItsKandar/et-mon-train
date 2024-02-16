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

class Pages(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Precedent', style=discord.ButtonStyle.grey)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Page precedente', ephemeral=True)
        self.value = False
        self.stop()

    @discord.ui.button(label='Suivant', style=discord.ButtonStyle.green)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Page suivante', ephemeral=True)
        self.value = True
        self.stop()

bot = Bot()

async def fetch_train_info(train_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/journeys?from={train_id}", headers={"Authorization": SNCF_API_KEY}) as response:
            return await response.json()

async def fetch_train_id(departure_station, arrival_station):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/journeys?from={departure_station}&to={arrival_station}", headers={"Authorization": SNCF_API_KEY}) as response:
            return await response.json()

async def fetch_all_stations():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/stop_areas?", headers={"Authorization": SNCF_API_KEY}) as response: 
            return await response.json()

async def fetch_stations_by_city(city):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/areas?type=stop_area&q={city}", headers={"Authorization": SNCF_API_KEY}) as response:
            return await response.json()
        
async def fetch_all_trains():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/vehicle_journeys?start_page=0", headers={"Authorization": SNCF_API_KEY}) as response:
            data = await response.json()
            vehicle_journeys = data.get("vehicle_journeys", [])
            for journey in vehicle_journeys:
                departure_stop = journey["stop_times"][0]
                arrival_stop = journey["stop_times"][-1]
                journey["departure_station"] = departure_stop["stop_point"]["name"]
                journey["arrival_station"] = arrival_stop["stop_point"]["name"]
                journey["departure_time"] = departure_stop["arrival_time"]
                journey["arrival_time"] = arrival_stop["departure_time"]
            return data
        
async def fetch_info_by_id(area_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/stop_areas/{area_id}", headers={"Authorization": SNCF_API_KEY}) as response:
            return await response.json()
        
async def change_page(ctx, trains_chunks, page):
    view = Pages()
    trains_list = "\n".join([f"{train_id.split(':')[0]} - {train_name} | Départ : {departure_station} ({departure_time}) | Arrivée : {arrival_station} ({arrival_time})" for train_id, train_name, departure_station, arrival_station, departure_time, arrival_time in trains_chunks[page]])
    message = await ctx.response.send_message(f"🚆 Liste des trains en circulation (Page {page + 1}/{len(trains_chunks)}):\n{trains_list}", view=view)
    await view.wait()
    if view.value is None:
        print("Timeout")
    elif view.value:
        page+=1
    elif not view.value:
        page-=1
    else:
        print("Cancelled")

    await discord.Interaction.response.edit_message(content=f"🚆 Liste des trains en circulation (Page {page + 1}/{len(trains_chunks)}):\n{trains_list}")
        
async def fetch_test():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/stop_areas/stop_area%3ASNCF%3A87171009/departures?", headers={"Authorization": SNCF_API_KEY}) as response:
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

@bot.tree.command(name="info")
async def info(ctx, train_id: str): 
    train_info = await fetch_train_info(train_id)
    try:
        train_status = train_info["disruptions"][0]["status"]
        train_delay = train_info["disruptions"][0]["impacted_objects"][0]["impacted_stops"][0]["amended_arrival_time"]
        train_platform = train_info["disruptions"][0]["impacted_objects"][0]["impacted_stops"][0]["commercial_track"]

        if train_status == "DELAYED":
            await ctx.response.send_message(f"🚆 Le train {train_id} est en retard. Il arrivera à {train_delay}.")
        else:
            await ctx.response.send_message(f"🚆 Le train {train_id} est à l'heure.")

        if train_platform:
            await ctx.response.send_message(f"🛤️ La voie annoncée pour le train {train_id} est la voie {train_platform}.")
        else:
            await ctx.response.send_message(f"🛤️ La voie pour le train {train_id} n'est pas encore annoncée.")

    except KeyError:
        await ctx.response.send_message("⚠️ Train introuvable. Veuillez vérifier l'identifiant du train.")

@bot.tree.command(name='getcoveragebyid')
async def getcoveragebyid(ctx, station: str):
    train_info = await fetch_info_by_id(station)
    await ctx.response.send_message(train_info)

@bot.tree.command(name="getid")
async def get_train_id(ctx, departure_station: str, arrival_station: str):
    train_info = await fetch_train_id(departure_station, arrival_station)
    try:
        train_id = train_info["journeys"][0]["sections"][0]["id"]
        await ctx.response.send_message(f"🚆 L'ID du train entre {departure_station} et {arrival_station} est : {train_id}")
    except KeyError:
        await ctx.response.send_message("⚠️ Train introuvable. Veuillez vérifier les gares de départ et d'arrivée.")

@bot.tree.command(name="getstations")
async def get_stations(ctx, city: str):
    stations_data = await fetch_stations_by_city(city)
    try:
        stations = [station["name"] for station in stations_data["stop_areas"]]
        if stations:
            stations_list = "\n".join(stations)
            await ctx.response.send_message(f"🚉 Les gares de {city} sont :\n{stations_list}")
        else:
            await ctx.response.send_message(f"⚠️ Aucune gare trouvée pour la ville {city}.")
    except KeyError:
        await ctx.response.send_message("⚠️ Erreur lors de la récupération des gares. Veuillez réessayer.")

@bot.tree.command(name="getalltrains")
async def get_all_trains(ctx):
    trains_data = await fetch_all_trains()
    try:
        trains = [(train["id"].replace("vehicle_journey:SNCF:", ""), train["name"], train["departure_station"], train["arrival_station"], train["departure_time"], train["arrival_time"]) for train in trains_data["vehicle_journeys"]]
        
        if trains:
            trains_chunks = [trains[i:i + 10] for i in range(0, len(trains), 10)]
            await change_page(ctx, trains_chunks, 0)
        else:
            await ctx.response.send_message("⚠️ Aucun train en circulation actuellement.")
    except KeyError:
        await ctx.response.send_message("⚠️ Erreur lors de la récupération des trains. Veuillez réessayer.")

@bot.tree.command(name="getallstations")
async def get_all_stations(ctx):
    await ctx.response.send_message(await fetch_all_stations())

@bot.tree.command(name="test")
async def test(ctx):
    await ctx.response.send_message(await fetch_test())

# Commandes admin
@bot.tree.command(name="stop")
@commands.is_owner()
async def stop(ctx):
    await ctx.response.send_message("🛑 Arrêt du bot...")
    await bot.close()

bot.run(RE_TOKEN)