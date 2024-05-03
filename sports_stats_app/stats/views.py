import logging
from django.shortcuts import render, redirect, HttpResponse
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .utils import get_player_by_name_variants


# Login Function 
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            # Display appropriate error messages for invalid credentials
            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                messages.error(request, 'Invalid password. Please try again.')
            else:
                messages.error(request, 'Invalid username. Please try again.')
            return render(request, 'login.html')

    # Show the login page for GET requests
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        # get the username and password
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # check if th username and password is valid then try to create new account 
            user = User.objects.create_user(username=username, password=password)
        except:
            messages.warning(request, 'This Username has already been taken.')
            return redirect('register')
        # user.is_superuser = True
        user.save()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('index')

    return render(request, 'register.html', {})


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

# def index(request):
#     """Render index page."""
#     # pass
# #     # Get player data
#     players_data = get_active_players()
#     # players_data = []
#     return render(request, 'index.html', {'players': players_data})

import logging
import json
from django.shortcuts import render
from nba_api.stats.static import players
from django.http import HttpResponse

# Configuring logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# file_path = 'stats\data.json'
file_path = "stats/data.json"
num_sorts_by_position = 2
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
    """Retrieve the position of players."""
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

def get_players(sort_option):
    """Get active NBA players."""
    player_data = []
    load_data()

    if sort_option == 1:
        player_data = get_players_by_position()
    elif sort_option == 2:
        player_data = sorted(data['data'], key=lambda x: x['pts'], reverse=True)
    elif sort_option == 3:
        player_data = sorted(data['data'], key=lambda x: x['reb'], reverse=True)

    # Eliminate duplicates using a set for unique keys
    seen = set()
    unique_players = []
    for player in player_data:
        # Define a tuple of properties that makes each record unique
        identifier = (player['player']['first_name'] + ' ' + player['player']['last_name'], player['player']['position'])
        if identifier not in seen:
            seen.add(identifier)
            unique_players.append(player)

    # Iterate over each active player
    result_data = []
    for index, player in enumerate(unique_players, start=1):
        player_stats = {
            'full_name': player['player']['first_name'] + ' ' + player['player']['last_name'],
            'position': player['player']['position'],
            'pts': player['pts'],
            'reb': player['reb'],
            'turnover': player['turnover'],
            'rank': index
        }
        result_data.append(player_stats)

    return result_data

@login_required(login_url=login_user)
def index(request):
    """Render index page."""
    # Get player data
    players_data = get_players(1)
    if request.method == 'POST':
        if 'button' in request.POST:
            action_value = request.POST['button']
            if action_value == 'by_name':
                get_players(3)
                return HttpResponse("Button 1 was clicked.")
            elif action_value == 'by_points':
                get_players(2)
                return HttpResponse("Button 2 was clicked.")
            elif action_value == 'by_position':
                get_players(1)

    # print(players_data)
    return render(request, 'index.html', {'players': players_data})



@login_required(login_url=login_user)
def search(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        search_result = get_player_by_name_variants(username)  # Replace with your actual data fetching logic

        # Normalize the data to ensure all entries are list of dicts
        if isinstance(search_result, dict):
            search_results = [search_result]  # Convert a single dict to a list of one dict
        elif isinstance(search_result, list):
            search_results = search_result
        else:
            search_results = []

        # Ensure each dictionary has a flattened structure for easy access in the template
        normalized_results = []
        for result in search_results:
            # Flatten the team data if available
            team_name = result.get('team', {}).get('full_name', 'N/A')  # Default to 'N/A' if no team info
            normalized_result = {
                'id': result.get('id', 'N/A'),
                'first_name': result.get('first_name', 'N/A'),
                'last_name': result.get('last_name', 'N/A'),
                'position': result.get('position', 'N/A'),
                'height': result.get('height', 'N/A'),
                'weight': result.get('weight', 'N/A'),
                'jersey_number': result.get('jersey_number', 'N/A'),
                'college': result.get('college', 'N/A'),
                'country': result.get('country', 'N/A'),
                'draft_year': result.get('draft_year', 'N/A'),
                'draft_round': result.get('draft_round', 'N/A'),
                'draft_number': result.get('draft_number', 'N/A'),
                'team_name': result.get('team').get('name')
            }
            normalized_results.append(normalized_result)

        return render(request, 'stats/player_result.html', {'search_results': normalized_results})
    else:
        # For a GET request, just render the search page without any data
        return render(request, 'stats/search.html', {'search_results': []})




def logout_user(request):
    logout(request)
    return redirect('login_user')

    

if __name__=="__main__":
    debug=True