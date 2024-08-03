import discord
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    channel = client.get_channel() #channel id here
    
    while True:
        await channel.send("This is a message sent every 5 seconds!")
        await asyncio.sleep(5)

client.run('') # token here
