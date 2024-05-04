import logging
from django.shortcuts import render, redirect, HttpResponse
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .utils import get_player_by_name_variants
import json
from nba_api.live.nba.endpoints import scoreboard




# Login Function 
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'You have successfully logged in {request.user.username}...')
            return redirect('index')
        else:
            # Check if the user exists to provide a specific error message
            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                messages.error(request, 'Invalid password. Please try again.')
            else:
                messages.error(request, 'Invalid username. Please try again.')
            return render(request, 'login.html', {'username': username})

    # Show the login page for GET requests
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the username already exists to prevent duplication
        if User.objects.filter(username=username).exists():
            messages.warning(request, 'This username has already been taken.')
            return redirect('register')

        # Create new user if username is unique
        user = User.objects.create_user(username=username, password=password)
        user.save()
        login(request, user)  # Log in the newly registered user
        messages.success(request, 'Registration successful!')
        return redirect('index')

    return render(request, 'register.html')


    return render(request, 'register.html', {})

def logout_user(request):
    username = request.user.username
    logout(request)
    messages.success(request, f'You have been logged out, {username}.')
    return redirect('login_user')

file_path = "stats/data.json"
num_sorts_by_position = 0
num_positions = 5
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
    if num_sorts_by_position % num_positions == 0:
        for value in data['data']:
            if value['player']['position'] == 'C':
                sorted_players.append(value)
    elif num_sorts_by_position % num_positions == 1:
        for value in data['data']:
            if value['player']['position'] == 'F':
                sorted_players.append(value)
    elif num_sorts_by_position % num_positions == 2:
        for value in data['data']:
            if value['player']['position'] == 'G':
                sorted_players.append(value)
    elif num_sorts_by_position % num_positions == 4:
        for value in data['data']:
            if value['player']['position'] == 'F-G':
                sorted_players.append(value)
    else:
        for value in data['data']:
            if value['player']['position'] == 'F-C':
                sorted_players.append(value)
    num_sorts_by_position += 1
    return sorted_players

def get_players(sort_option, efficiency_sort):
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
        efficiency = ((player['pts'] * player['reb']) / (player['turnover'] + 100))
        player_stats = {
            'full_name': player['player']['first_name'] + ' ' + player['player']['last_name'],
            'position': player['player']['position'],
            'pts': player['pts'],
            'reb': player['reb'],
            'turnover': player['turnover'],
            'efficiency': efficiency,
            'rank': index
        }
        result_data.append(player_stats)

    if efficiency_sort:
        print('This works')
        result_data = sorted(result_data, key=lambda x: x['efficiency'], reverse=True)
        for index, player in enumerate(result_data, start=1):
            player['rank'] = index
    return result_data



def fetch_live_and_upcoming_scores():
    try:
        # Initialize the scoreboard
        games = scoreboard.ScoreBoard()
        
        # Fetching the live scoreboard as a dictionary
        games_data = games.get_dict()
        
        # Simplifying the data extraction process
        games_list = []
        for game in games_data['scoreboard']['games']:
            # Check if the game is live or upcoming by checking if scores are present
            if game['homeTeam']['score'] == 0 and game['awayTeam']['score'] == 0:
                game_status = "Upcoming"
            else:
                game_status = "Live"

            game_info = {
                'home_team': f"{game['homeTeam']['teamCity']} {game['homeTeam']['teamName']}",
                'away_team': f"{game['awayTeam']['teamCity']} {game['awayTeam']['teamName']}",
                'home_score': game['homeTeam']['score'],
                'away_score': game['awayTeam']['score'],
                'status': game['gameStatusText'], 
                'series_text': game.get('seriesText', 'N/A'), 
                'game_status': game_status  
            }
            games_list.append(game_info)
        return games_list
        
    except Exception as e:
        print(f"Failed to fetch NBA scores: {e}")
        return None





@login_required(login_url=login_user)
def index(request):
    game_data = fetch_live_and_upcoming_scores() or None
    """Render index page."""
    # Get player data
    if request.method == 'POST':
        action_value = request.POST.get('button')
        if action_value == 'by_efficiency':
            players_data = get_players(3, True)
        elif action_value == 'by_rebounds':
            players_data = get_players(3, False)
        elif action_value == 'by_points':
            players_data = get_players(2, False)
        elif action_value == 'by_position':
            players_data = get_players(1, False)
    elif request.method == 'GET':
        players_data = None

    # players_data = get_players(2, False)
    return render(request, 'index.html', {'players': players_data, 'game_data': game_data})


from django.http import JsonResponse

def fetch_scores(request):
    game_data = fetch_live_and_upcoming_scores()
    if game_data:
        data = {'games': game_data}
    else:
        data = {'games': []}  # Send empty list if no data available
    return JsonResponse(data)



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


#
    

if __name__=="__main__":
    debug=True