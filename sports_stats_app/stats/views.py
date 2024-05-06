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
from .models import PlayerSearchHistory




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





class PlayerStatsLoader:
    def __init__(self, file_path="stats/data.json"):
        self.file_path = file_path
        self.data = self.load_data()
        self.num_sorts_by_position = 0
        self.num_positions = 5

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"The file was not found: {self.file_path}")
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from the file: {self.file_path}")
        return None

    def get_players_by_position(self):
        position_map = {0: 'C', 1: 'F', 2: 'G', 3: 'F-G', 4: 'F-C'}
        current_position = self.num_sorts_by_position % self.num_positions
        sorted_players = [value for value in self.data['data'] if value['player']['position'] == position_map[current_position]]
        self.num_sorts_by_position += 1
        return sorted_players

    def get_players(self, sort_option):
        if not self.data:
            return []
        if sort_option == 1:
            player_data = self.get_players_by_position()
        else:
            key = 'pts' if sort_option == 2 else 'reb'
            player_data = sorted(self.data['data'], key=lambda x: x[key], reverse=True)

        seen = set()
        unique_players = []
        for player in player_data:
            identifier = (player['player']['first_name'] + ' ' + player['player']['last_name'], player['player']['position'])
            if identifier not in seen:
                seen.add(identifier)
                unique_players.append(player)

        return unique_players

    def calculate_efficiency(self, players, efficiency_sort=False):
        result_data = [{
            'first_name':  player['player']['first_name'],
            'full_name': player['player']['first_name'] + ' ' + player['player']['last_name'],
            'position': player['player']['position'],
            'pts': player['pts'],
            'reb': player['reb'],
            'turnover': player['turnover'],
            'efficiency': (player['pts'] * player['reb']) / (player['turnover'] + 100)
        } for player in players]

        if efficiency_sort:
            result_data.sort(key=lambda x: x['efficiency'], reverse=True)

        for index, player in enumerate(result_data, start=1):
            player['rank'] = index

        return result_data

# # test Cases
# file_path = "stats/data.json"
# psl = PlayerStatsLoader(file_path)
# players = psl.get_players(1)
# players_stats = psl.calculate_efficiency(players, efficiency_sort=True)



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




# Assuming `login_user` is a path to the login view
@login_required(login_url='login_user')  # Corrected the login_url parameter to be a string path
def index(request):
    game_data = fetch_live_and_upcoming_scores() or None
    psl = PlayerStatsLoader("stats/data.json")  # Load player stats using the class
    players_data = []

    if request.method == 'POST':
        action_value = request.POST.get('button')
        if action_value == 'by_efficiency':
            raw_players = psl.get_players(3)
            players_data = psl.calculate_efficiency(raw_players, efficiency_sort=True)
        elif action_value == 'by_rebounds':
            raw_players = psl.get_players(3)
            players_data = psl.calculate_efficiency(raw_players, efficiency_sort=False)
        elif action_value == 'by_points':
            raw_players = psl.get_players(2)
            players_data = psl.calculate_efficiency(raw_players, efficiency_sort=False)
        elif action_value == 'by_position':
            raw_players = psl.get_players(1)
            players_data = psl.calculate_efficiency(raw_players, efficiency_sort=False)
        return render(request, 'index.html', {'players': players_data, 'game_data': game_data})

    elif request.method == 'GET':
        raw_players = psl.get_players(3)
        players_data = psl.calculate_efficiency(raw_players, efficiency_sort=True)

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
        search_results = get_player_by_name_variants(username)

        # Ensure search_results is a list of dictionaries
        if isinstance(search_results, dict):
            search_results = [search_results]  # Convert a single dict to a list of one dict
        elif not isinstance(search_results, list):
            search_results = []

        # Save only the first player if there are multiple search results
        if search_results:
            first_result = search_results[0]

            # Save search history for the current user
            user = request.user
            PlayerSearchHistory.objects.create(
                user=user,
                player_id=first_result.get('id', 'N/A'),
                first_name=first_result.get('first_name', 'N/A'),
                last_name=first_result.get('last_name', 'N/A'),
                position=first_result.get('position', 'N/A'),
                height=first_result.get('height', 'N/A'),
                weight=first_result.get('weight', 'N/A'),
                jersey_number=first_result.get('jersey_number', 'N/A'),
                college=first_result.get('college', 'N/A'),
                country=first_result.get('country', 'N/A'),
                draft_year=first_result.get('draft_year', 'N/A'),
                draft_round=first_result.get('draft_round', 'N/A'),
                draft_number=first_result.get('draft_number', 'N/A'),
                team=first_result.get('team').get('name', 'N/A')
            )

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
        # For a GET request, just render the search page with the search history data
        user = request.user
        search_history = PlayerSearchHistory.objects.filter(user=user).order_by('-search_timestamp')
        return render(request, 'stats/search.html', {'search_history': search_history})
        # return render(request, 'stats/search.html', {'search_results': []})


import requests
from django.shortcuts import render

# Define the API key and the base URL
api_key = 'a16ac370-e80f-4615-a9c6-36346f9cb961'
base_url = 'https://api.balldontlie.io/v1'

# Set up headers with your API key
headers = {
    'Authorization': api_key
}

# Function to search for players by name with multiple attempts
def get_player_by_name_variants(first_name):
    name_variants = [
        f'{first_name}',
        f'{first_name.lower()}',
        f'{first_name.upper()}',
        f'{first_name.capitalize()}'
    ]
    for name in name_variants:
        params = {'search': name}
        response = requests.get(f'{base_url}/players', headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data']  # Return the first player that matches the name
    return None

def search_selected_player(request, first_name):
    # Search for the player by name
    players = get_player_by_name_variants(first_name)

    # Render the players in an HTML template
    return render(request, 'stats/player_result.html', {'search_results': players})





if __name__=="__main__":
    debug=True
