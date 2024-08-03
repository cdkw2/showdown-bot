import discord
from discord import app_commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio

intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.tree.command()
async def stats(interaction: discord.Interaction, player: str, category: str):
    await interaction.response.defer()
    
    url = f'https://pokemonshowdown.com/users/{player}'
    
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

client.run('') # bot token
