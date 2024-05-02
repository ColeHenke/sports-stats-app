import logging
from django.shortcuts import render
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo

# Configuring logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_player_position(player_id):
    """Retrieve the position of a player."""
    try:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        player_details = player_info.get_data_frames()[0]
        position = player_details['POSITION'].iloc[0]
        return position if position else 'N/A'
    except Exception as e:
        logger.error(f"Failed to fetch position for player {player_id}: {str(e)}")
        return 'N/A'

def get_active_players():
    """Get active NBA players."""
    # Get active NBA players
    active_players = players.get_active_players()

    # List to store player data
    player_data = []

    # Counter for limiting to 15 players
    count = 0

    # Iterate over each active player
    for player in active_players:
        # Get player career stats
        career = playercareerstats.PlayerCareerStats(player_id=player['id'])
        career_stats = career.get_data_frames()[0]

        # Fetch the player's position using the new function
        position = get_player_position(player['id'])

        # Extract necessary data
        player_stats = {
            'full_name': player['full_name'],
            'position': position,
            'ppg': career_stats.iloc[0]['PTS'] / career_stats.iloc[0]['GP'], # Points per game
            'rpg': career_stats.iloc[0]['REB'] / career_stats.iloc[0]['GP'], # Rebounds per game
            'apg': career_stats.iloc[0]['AST'] / career_stats.iloc[0]['GP']  # Assists per game
        }

        # Append player data to list
        player_data.append(player_stats)

        # Increment counter
        count += 1

        # Break loop if 15 players have been collected
        if count == 10:
            break

    return player_data

def index(request):
    """Render index page."""
    # Get player data
    players_data = get_active_players()

    return render(request, 'index.html', {'players': players_data})