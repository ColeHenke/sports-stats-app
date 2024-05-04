from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .utils import get_player_by_name_variants
import json
from django.shortcuts import render


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

# file_path = 'stats\data.json'
file_path = "stats/data.json"
num_sorts_by_position = 0
num_positions = 5
data = None

def load_data():
    global data
    try:
        print('This code is being hit')
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

@login_required(login_url=login_user)
def index(request):
    """Render index page."""
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
    return render(request, 'index.html', {'players': players_data})



@login_required(login_url=login_user)
def search(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        search_result = get_player_by_name_variants(username)

        # Normalize the data to ensure all entries are list of dicts
        if isinstance(search_result, dict):
            search_results = [search_result] 
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