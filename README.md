
# Showdown Bot

A Discord bot to keep track of Pokémon Showdown progress and stats.

## Features

 - [x] Track multiple players stats over time
 - [x] Automatically update tracked players' stats at configurable intervals
 - [x] Store player stats in CSV files for data analysis
 - [x] Discord slash command
 - [ ] Graph tracking

## Commands

- `/stats <player> <category>`: Fetch and display current stats for a player in a specific category
- `/track <player> <category>`: Start tracking a player's stats in a specific category
- `/untrack <player>`: Stop tracking a player's stats
- `/list_tracked`: Display a list of all currently tracked players
- `/set_update_interval <minutes>`: Set the interval for automatic stat updates

Sample command: `/stats cdkw2 gen9randombattle`

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
- Stats for tracked players are stored in CSV files named `<player>_<category>_stats.csv` in the same directory as the script.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This bot is not officially affiliated with Pokémon Showdown. Use it responsibly and in accordance with Pokémon Showdown's terms of service.
