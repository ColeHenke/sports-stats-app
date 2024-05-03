from http.client import HTTPResponse
import logging
from django.shortcuts import render
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo

import json

# Configuring logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


file_path = 'stats\data.json'
num_sorts_by_position = 0
data = None

def load_data():
    global data
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("The file was not found:", file_path)
    except json.JSONDecodeError:
        print("Failed to decode JSON from the file:", file_path)

def get_players_by_position():
    """Retrieve the position of a players."""
    global num_sorts_by_position
    sorted_players = []
    if num_sorts_by_position % 3 == 0:
        for value in data['data']:
            if value['player']['position'] == 'C':
                sorted_players.append(value)
    elif num_sorts_by_position % 3 == 1:
        for value in data['data']:
            if value['player']['position'] == 'F':
                sorted_players.append(value)
    else:
        for value in data['data']:
            if value['player']['position'] == 'G':
                sorted_players.append(value)
    num_sorts_by_position += 1
    return sorted_players

def get_players_by_points():
    sorted_players = sorted(data['data'], key=lambda x: x['pts'], reverse=True)
    return sorted_players

def get_players_by_rebounds():
    sorted_players = sorted(data['data'], key=lambda x: x['reb'], reverse=True)
    return sorted_players

def get_players_by_rank():
    sorted_players = sorted(data['data'], key=lambda x: ((x['pts'] * x['reb']) / (x['turnover'] + 1)), reverse=True)
    return sorted_players

def get_players(sort_option):
    """Get active NBA players."""

    load_data()

    # Get NBA player list
    player_data = []

    if sort_option == 1:
        player_data = get_players_by_position()
    elif sort_option == 2:
        player_data = get_players_by_points()
    elif sort_option == 3:
        player_data == get_players_by_rebounds()
    else:
        player_data = get_players_by_rank()
            
    # Iterate over each active player
    for index, player in enumerate(player_data, start=1):
        # Extract necessary data
        player_stats = {
            'full_name': player['player']['first_name'] + ' ' +  player['player']['last_name'],
            'position': player['player']['position'],
            'pts': player['pts'],
            'reb': player['reb'],
            'rank': index
        }
        #print(player['player']['first_name'])
        # Append player data to list
        player_data.append(player_stats)

    return player_data

def index(request):
    """Render index page."""
    # Get player data
    players_data = get_players(1)

    return render(request, 'index.html', {'players': players_data})


def search_by_player_last_name(player_last_name):
    player = players.find_players_by_last_name(player_last_name)
    return player

def search(request):
    """Player search page"""

    search_results = {}
    if request.method == 'POST':
        input_value = request.POST.get('player_last_name')
        search_results = search_by_player_last_name(input_value)
        logging.info(search_results)

        f = open("demofile2.txt", "a")
        f.write("Now the file has more content!")
        f.close()
    return render(request, 'stats/search.html', {'search_results': search_results})