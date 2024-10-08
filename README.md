# Showdown Bot

A Discord bot to keep track of Pokémon Showdown progress and stats.

## Features

 - [x] Track multiple players stats over time
 - [x] Automatically update tracked players' stats at configurable intervals
 - [x] Store player stats in CSV files for data analysis
 - [x] Discord slash commands
 - [x] Persist tracked players and update interval between bot restarts
 - [ ] Graph tracking

## Commands

- `/stats <player>`: Fetch and display current stats for a player in all categories
- `/track <player>`: Start tracking a player's stats in all categories
- `/untrack <player>`: Stop tracking a player's stats
- `/list_tracked`: Display a list of all currently tracked players
- `/set_update_interval <minutes>`: Set the interval for automatic stat updates

Sample command: `/stats cdkw2`

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/cdkw2/showdown-bot
   cd showdown-bot
   ```

2. Install the required dependencies:
   ```
   pip install discord.py aiohttp beautifulsoup4
   ```

3. Create a `token.txt` file in the project directory and paste your Discord bot token into it.

4. Run the bot:
   ```
   python showdown.py
   ```

## Configuration

- The default update interval for tracked players is 5 minutes. You can change this using the `/set_update_interval` command.
- Stats for tracked players are stored in CSV files named `<player>_<category>_stats.csv` in the `player_stats` folder.
- The bot configuration (tracked players and update interval) is stored in `bot_config.json` and persists between bot restarts.
- Player stats are stored in CSV files in a `player_stats` folder, with separate files for each player and category.
- The bot configuration is stored in `bot_config.json` in the main directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or shoot me a dm on discord.

## Disclaimer

This bot is not officially affiliated with Pokémon Showdown. Use it responsibly and in accordance with Pokémon Showdown's terms of service.
