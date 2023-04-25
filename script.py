import os
import discord
from discord.ext import commands
import aiohttp
import sqlite3
import random
from config import RE_TOKEN, DEV_ID, DEV_TOKEN, DEVMODE, SNCF_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

async def fetch_train_info(train_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/journeys?from={train_id}", headers={"Authorization": SNCF_API_KEY}) as response:
            return await response.json()

async def fetch_train_id(departure_station, arrival_station):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/journeys?from={departure_station}&to={arrival_station}", headers={"Authorization": SNCF_API_KEY}) as response:
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

        
async def fetch_test():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.sncf.com/v1/coverage/sncf/journeys?from=admin:7444extern&to=admin:120965extern&datetime=20170123T140151", headers={"Authorization": SNCF_API_KEY}) as response:
            return await response.json()

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté avec succès !")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {synced} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

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
            for chunk in trains_chunks:
                trains_list = "\n".join([f"{train_id.split(':')[0]} - {train_name} | Départ : {departure_station} ({departure_time}) | Arrivée : {arrival_station} ({arrival_time})" for train_id, train_name, departure_station, arrival_station, departure_time, arrival_time in chunk])
                await ctx.response.send_message(f"🚆 Liste des trains en circulation :\n{trains_list}")
        else:
            await ctx.response.send_message("⚠️ Aucun train en circulation actuellement.")
    except KeyError:
        await ctx.response.send_message("⚠️ Erreur lors de la récupération des trains. Veuillez réessayer.")


@bot.tree.command(name="test")
async def test(ctx):
    await ctx.response.send_message(await fetch_test())

bot.run(RE_TOKEN)