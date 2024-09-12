import discord
from discord import app_commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import csv
from datetime import datetime
import os

def get_bot_token():
    with open('token.txt', 'r') as file:
        return file.read().strip()

intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tracked_players = {}
        self.update_interval = 300

    async def setup_hook(self):
        await self.tree.sync()
        self.bg_task = self.loop.create_task(self.track_players())

    async def track_players(self):
        await self.wait_until_ready()
        while not self.is_closed():
            for player, data in self.tracked_players.items():
                await self.update_player_stats(player, data['category'])
            await asyncio.sleep(self.update_interval)

    async def update_player_stats(self, player, category):
        stats = await self.fetch_stats(player, category)
        if stats:
            self.save_stats_to_csv(player, category, stats)

    async def fetch_stats(self, player, category):
        url = f'https://pokemonshowdown.com/users/{player}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        rows = soup.find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if cols and cols[0].text.strip().lower() == category.lower():
                                return {
                                    'elo': cols[1].text.strip() if len(cols) > 1 else 'N/A',
                                    'gxe': cols[2].text.strip() if len(cols) > 2 else 'N/A',
                                    'glicko': cols[3].text.strip() if len(cols) > 3 else 'N/A',
                                    'w': cols[4].text.strip() if len(cols) > 4 else 'N/A',
                                    'l': cols[5].text.strip() if len(cols) > 5 else 'N/A',
                                }
        except Exception as e:
            print(f"Error fetching stats for {player}: {e}")
        return None

    def save_stats_to_csv(self, player, category, stats):
        filename = f"{player}_{category}_stats.csv"
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'elo', 'gxe', 'glicko', 'w', 'l']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'elo': stats['elo'],
                'gxe': stats['gxe'],
                'glicko': stats['glicko'],
                'w': stats['w'],
                'l': stats['l']
            })

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.tree.command()
async def stats(interaction: discord.Interaction, player: str, category: str):
    """Fetch and display current stats for a player in a specific category."""
    await interaction.response.defer()

    url = f'https://pokemonshowdown.com/users/{player}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    rows = soup.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if cols and cols[0].text.strip().lower() == category.lower():
                            response_message = f"Stats for {player} in {category}:\n"

                            def safe_get(index, default="N/A"):
                                return cols[index].text.strip() if index < len(cols) else default

                            response_message += f"Elo: {safe_get(1)}\n"

                            gxe = safe_get(2)
                            if gxe == "N/A":
                                gxe = safe_get(3, "N/A (more games needed)")
                            response_message += f"GXE: {gxe}\n"

                            glicko = safe_get(3)
                            if glicko != "N/A":
                                response_message += f"Glicko-1: {glicko}\n"

                            w = safe_get(4)
                            l = safe_get(5)
                            if w != "N/A" and l != "N/A":
                                response_message += f"W/L: {w}/{l}"

                            await interaction.followup.send(response_message)
                            return

                    await interaction.followup.send(f"Couldn't find stats for {player} in {category}.")
                else:
                    await interaction.followup.send(f"Couldn't fetch stats for {player}. The user might not exist.")
    except aiohttp.ClientError as e:
        print(f"HTTP request failed: {e}")
        await interaction.followup.send("An error occurred while fetching the stats.")
    except Exception as e:
        print(f"An error occurred: {e}")
        await interaction.followup.send("An unexpected error occurred.")

@client.tree.command()
async def track(interaction: discord.Interaction, player: str, category: str):
    """Start tracking a player's stats in a specific category."""
    await interaction.response.defer()

    if player in client.tracked_players:
        await interaction.followup.send(f"{player} is already being tracked.")
        return

    stats = await client.fetch_stats(player, category)
    if stats:
        client.tracked_players[player] = {'category': category}
        client.save_stats_to_csv(player, category, stats)
        await interaction.followup.send(f"Now tracking {player} in {category}. Initial stats have been recorded.")
    else:
        await interaction.followup.send(f"Couldn't fetch stats for {player} in {category}. Please check the player name and category.")

@client.tree.command()
async def untrack(interaction: discord.Interaction, player: str):
    """Stop tracking a player's stats."""
    if player in client.tracked_players:
        del client.tracked_players[player]
        await interaction.response.send_message(f"Stopped tracking {player}.")
    else:
        await interaction.response.send_message(f"{player} is not currently being tracked.")

@client.tree.command()
async def list_tracked(interaction: discord.Interaction):
    """List all currently tracked players."""
    if client.tracked_players:
        tracked_list = "\n".join([f"{player} ({data['category']})" for player, data in client.tracked_players.items()])
        await interaction.response.send_message(f"Currently tracked players:\n{tracked_list}")
    else:
        await interaction.response.send_message("No players are currently being tracked.")

@client.tree.command()
async def set_update_interval(interaction: discord.Interaction, minutes: int):
    """Set the update interval for tracking (in minutes)."""
    if minutes < 1:
        await interaction.response.send_message("Update interval must be at least 1 minute.")
        return
    
    client.update_interval = minutes * 60  # Convert to seconds
    await interaction.response.send_message(f"Update interval set to {minutes} minutes.")

client.run(get_bot_token())
