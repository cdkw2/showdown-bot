import discord
from discord import app_commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import csv
from datetime import datetime
import os
import json

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
        self.last_known_stats = {}
        self.stats_folder = 'player_stats'
        self.config_file = 'bot_config.json'
        
        if not os.path.exists(self.stats_folder):
            os.makedirs(self.stats_folder)

        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.tracked_players = config.get('tracked_players', {})
                self.update_interval = config.get('update_interval', 300)
        else:
            self.tracked_players = {}
            self.update_interval = 300

    def save_config(self):
        config = {
            'tracked_players': self.tracked_players,
            'update_interval': self.update_interval
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    async def setup_hook(self):
        await self.tree.sync()
        self.bg_task = self.loop.create_task(self.track_players())
        self.load_last_known_stats()

    async def track_players(self):
        await self.wait_until_ready()
        while not self.is_closed():
            for player in self.tracked_players:
                await self.update_player_stats(player)
            await asyncio.sleep(self.update_interval)

    async def update_player_stats(self, player):
        stats = await self.fetch_all_stats(player)
        if stats:
            for category, category_stats in stats.items():
                if self.has_stats_changed(player, category, category_stats):
                    self.save_stats_to_csv(player, category, category_stats)
                    self.update_last_known_stats(player, category, category_stats)

    async def fetch_all_stats(self, player):
        url = f'https://pokemonshowdown.com/users/{player}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        rows = soup.find_all('tr')
                        stats = {}
                        for row in rows:
                            cols = row.find_all('td')
                            if cols:
                                category = cols[0].text.strip()
                                stats[category] = {
                                    'elo': cols[1].text.strip() if len(cols) > 1 else 'N/A',
                                    'gxe': cols[2].text.strip() if len(cols) > 2 else 'N/A',
                                    'glicko': cols[3].text.strip() if len(cols) > 3 else 'N/A',
                                    'w': cols[4].text.strip() if len(cols) > 4 else 'N/A',
                                    'l': cols[5].text.strip() if len(cols) > 5 else 'N/A',
                                }
                        return stats
        except Exception as e:
            print(f"Error fetching stats for {player}: {e}")
        return None

    def has_stats_changed(self, player, category, new_stats):
        if player not in self.last_known_stats:
            self.last_known_stats[player] = {}
        if category not in self.last_known_stats[player]:
            return True
        old_stats = self.last_known_stats[player][category]
        return any(old_stats.get(key) != new_stats.get(key) for key in new_stats)

    def update_last_known_stats(self, player, category, stats):
        if player not in self.last_known_stats:
            self.last_known_stats[player] = {}
        self.last_known_stats[player][category] = stats.copy()

    def save_stats_to_csv(self, player, category, stats):
        filename = os.path.join(self.stats_folder, f"{player}_{category}_stats.csv")
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

    def load_last_known_stats(self):
        filename = os.path.join(self.stats_folder, 'last_known_stats.json')
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                self.last_known_stats = json.load(f)

    async def close(self):
        self.save_config()
        filename = os.path.join(self.stats_folder, 'last_known_stats.json')
        with open(filename, 'w') as f:
            json.dump(self.last_known_stats, f)
        await super().close()

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.tree.command()
async def stats(interaction: discord.Interaction, player: str):
    """Fetch and display current stats for a player in all categories."""
    await interaction.response.defer()

    stats = await client.fetch_all_stats(player)
    if stats:
        await send_stats_messages(interaction, player, stats)
    else:
        await interaction.followup.send(f"Couldn't fetch stats for {player}. The user might not exist.")

async def send_stats_messages(interaction, player, stats):
    messages = []
    current_message = f"Stats for {player}:\n\n"

    for category, category_stats in stats.items():
        category_text = f"{category}:\n"
        category_text += f"Elo: {category_stats['elo']}\n"
        category_text += f"GXE: {category_stats['gxe']}\n"
        category_text += f"Glicko-1: {category_stats['glicko']}\n"
        category_text += f"W/L: {category_stats['w']}/{category_stats['l']}\n\n"

        if len(current_message) + len(category_text) > 1900:
            messages.append(current_message)
            current_message = category_text
        else:
            current_message += category_text

    if current_message:
        messages.append(current_message)

    for i, message in enumerate(messages):
        if i == 0:
            await interaction.followup.send(message)
        else:
            await interaction.followup.send(message)

@client.tree.command()
async def track(interaction: discord.Interaction, player: str):
    """Start tracking a player's stats in all categories."""
    await interaction.response.defer()

    if player in client.tracked_players:
        await interaction.followup.send(f"{player} is already being tracked.")
        return

    stats = await client.fetch_all_stats(player)
    if stats:
        client.tracked_players[player] = True
        client.save_config()
        for category, category_stats in stats.items():
            client.save_stats_to_csv(player, category, category_stats)
            client.update_last_known_stats(player, category, category_stats)
        await interaction.followup.send(f"Now tracking {player} in all categories. Initial stats have been recorded.")
    else:
        await interaction.followup.send(f"Couldn't fetch stats for {player}. Please check the player name.")

@client.tree.command()
async def untrack(interaction: discord.Interaction, player: str):
    """Stop tracking a player's stats."""
    if player in client.tracked_players:
        del client.tracked_players[player]
        client.save_config() 
        await interaction.response.send_message(f"Stopped tracking {player}.")
    else:
        await interaction.response.send_message(f"{player} is not currently being tracked.")

@client.tree.command()
async def list_tracked(interaction: discord.Interaction):
    """List all currently tracked players."""
    if client.tracked_players:
        tracked_list = "\n".join(client.tracked_players.keys())
        await interaction.response.send_message(f"Currently tracked players:\n{tracked_list}")
    else:
        await interaction.response.send_message("No players are currently being tracked.")

@client.tree.command()
async def set_update_interval(interaction: discord.Interaction, minutes: int):
    """Set the update interval for tracking (in minutes)."""
    if minutes < 1:
        await interaction.response.send_message("Update interval must be at least 1 minute.")
        return
    
    client.update_interval = minutes * 60
    client.save_config()
    await interaction.response.send_message(f"Update interval set to {minutes} minutes.")

client.run(get_bot_token())
