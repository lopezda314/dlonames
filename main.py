import pkg_resources
import uuid
import os
from flask import Flask, abort, render_template, request, url_for, redirect
from flask_cors import CORS, cross_origin
from flask_jsglue import JSGlue
from flask_socketio import SocketIO, send, emit
from random import randint

path = '/static/words.txt'
filepath = pkg_resources.resource_filename(__name__, path)
with open(filepath) as f:
    all_words = f.readlines()
    all_words = [x.strip() for x in all_words] 

NUMBER_WORDS = len(all_words)

app = Flask(__name__)
CORS(app)
jsglue = JSGlue(app)
socketio = SocketIO(app)
app.debug = True

MAX_GAMES = 50
games = {}

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/')
def redirect_to_home():
    return redirect(url_for('home'))

@app.route('/lobby/', methods=['GET', 'POST'])
def lobby():
    global games
    if len(games) > 50:
        # Only allow MAX_GAMES games before resetting to avoid memory leak.
        games = {}
    query_params = {}
    query_params_kv = bytes.decode(request.query_string).split('&')
    for query_param in query_params_kv:
        if not query_param:
            continue
        query_params[query_param.split('=')[0]] = query_param.split('=')[1]
    if 'player' in query_params:
        return render_template('lobby.html', current_player=query_params['player'], gameId=query_params['gameId'], players=games[query_params['gameId']]['players'])
    maybe_gameId = ''
    if len(query_params) > 0:
        maybe_gameId = query_params['gameId']
    if 'gameId' not in request.form and not maybe_gameId:
        gameId = createNewgameId()
        games[gameId] = {}
        if 'name' in request.form:
            games[gameId]['players'] = [request.form['name']]
            return render_template('lobby.html',
                        current_player=request.form['name'],
                        gameId=gameId,
                        players=games[gameId]['players'])
        if 'players' in games[gameId]:
            return render_template('lobby.html', current_player='', gameId=gameId, players=games[gameId]['players'])
        else:
            games[gameId]['players'] = []
            return render_template('lobby.html', current_player='', gameId=gameId, players=games[gameId]['players'])
    elif 'gameId' in request.form:
        gameId = request.form['gameId']
        if gameId not in games:
            abort(404)
        if 'players' in games[gameId]:
            games[gameId]['players'].append(request.form['name']) 
        else:
            games[gameId]['players'] = [request.form['name']]
        return render_template('lobby.html',
                 current_player=request.form['name'],
                 gameId=gameId,
                 players=games[gameId]['players'])
    else:
        gameId = maybe_gameId
        if gameId not in games:
            abort(404)
        return render_template('lobby.html',
                 current_player='',
                 gameId=gameId,
                 players=games[gameId]['players'])


@app.route('/game/', methods=['GET', 'POST'])
def game():
    global games
    query_params = {}
    query_params_kv = bytes.decode(request.query_string).split('&')
    for query_param in query_params_kv:
        query_params[query_param.split('=')[0]] = query_param.split('=')[1]
    if ('redTeam' not in query_params or 'blueTeam' not in query_params or 'blueCodeMaster'
        not in query_params or 'redCodeMaster' not in query_params or 'gameId' not in 
        query_params or 'currentPlayer' not in query_params):
        abort(500)
    if query_params['gameId'] not in games:
        games[query_params['gameId']] = {}
    if 'first' not in games[query_params['gameId']]:
        games[query_params['gameId']]['first'] = getWhichTeamGoesFirst()
    if 'words' not in games[query_params['gameId']]:
        games[query_params['gameId']]['words'] = getWordsForBoard()
    if 'indices' not in games[query_params['gameId']]:
        games[query_params['gameId']]['indices'] = getIndicesForBoard()    
    if 'word' in games[query_params['gameId']]:
        if 'guesses' in games[query_params['gameId']]:
            if 'team' in games[query_params['gameId']]:
                return render_template('game.html', gameId=query_params['gameId'], words=games[query_params['gameId']]['words'],
                    indices=games[query_params['gameId']]['indices'], first=games[query_params['gameId']]['first'], blueTeam=query_params['blueTeam'],
                    redTeam=query_params['redTeam'], blueCodeMaster=query_params['blueCodeMaster'],
                    redCodeMaster=query_params['redCodeMaster'], currentPlayer=query_params['currentPlayer'], word=games[query_params['gameId']]['word'],
                    numGuesses=games[query_params['gameId']]['numGuesses'], guesses=games[query_params['gameId']]['guesses'], team=games[query_params['gameId']]['team'],
                    initialNumGuesses=games[query_params['gameId']]['initialNumGuesses'], previousWords=games[query_params['gameId']]['previousWords'])
            else:
                return render_template('game.html', gameId=query_params['gameId'], words=games[query_params['gameId']]['words'],
                            indices=games[query_params['gameId']]['indices'], first=games[query_params['gameId']]['first'], blueTeam=query_params['blueTeam'],
                            redTeam=query_params['redTeam'], blueCodeMaster=query_params['blueCodeMaster'],
                            redCodeMaster=query_params['redCodeMaster'], currentPlayer=query_params['currentPlayer'], word=games[query_params['gameId']]['word'],
                            numGuesses=games[query_params['gameId']]['numGuesses'], guesses=games[query_params['gameId']]['guesses'],
                            initialNumGuesses=games[query_params['gameId']]['initialNumGuesses'], previousWords=games[query_params['gameId']]['previousWords'])                
        else:
            if 'team' in games[query_params['gameId']]:
                return render_template('game.html', gameId=query_params['gameId'], words=games[query_params['gameId']]['words'],
                    indices=games[query_params['gameId']]['indices'], first=games[query_params['gameId']]['first'], blueTeam=query_params['blueTeam'],
                    redTeam=query_params['redTeam'], blueCodeMaster=query_params['blueCodeMaster'],
                    redCodeMaster=query_params['redCodeMaster'], currentPlayer=query_params['currentPlayer'], word=games[query_params['gameId']]['word'],
                    numGuesses=games[query_params['gameId']]['numGuesses'], initialNumGuesses=games[query_params['gameId']]['initialNumGuesses'],
                    previousWords=games[query_params['gameId']]['previousWords'], team=games[query_params['gameId']]['team'])
            else:
                return render_template('game.html', gameId=query_params['gameId'], words=games[query_params['gameId']]['words'],
                    indices=games[query_params['gameId']]['indices'], first=games[query_params['gameId']]['first'], blueTeam=query_params['blueTeam'],
                    redTeam=query_params['redTeam'], blueCodeMaster=query_params['blueCodeMaster'],
                    redCodeMaster=query_params['redCodeMaster'], currentPlayer=query_params['currentPlayer'], word=games[query_params['gameId']]['word'],
                    numGuesses=games[query_params['gameId']]['numGuesses'], initialNumGuesses=games[query_params['gameId']]['initialNumGuesses'],
                    previousWords=games[query_params['gameId']]['previousWords'])
    else:
        return render_template('game.html', gameId=query_params['gameId'], words=games[query_params['gameId']]['words'],
            indices=games[query_params['gameId']]['indices'], first=games[query_params['gameId']]['first'], blueTeam=query_params['blueTeam'],
            redTeam=query_params['redTeam'], blueCodeMaster=query_params['blueCodeMaster'],
            redCodeMaster=query_params['redCodeMaster'], currentPlayer=query_params['currentPlayer'])


def createNewgameId():
    return str(uuid.uuid4())[:4]

def getWordsForBoard():
    game_words = []
    used_words = set()
    while len(game_words) < 25:
        maybeNextIndex = randint(0, NUMBER_WORDS - 1)
        if all_words[maybeNextIndex] not in used_words:
            game_words.append(all_words[maybeNextIndex].upper())
            used_words.add(all_words[maybeNextIndex])
    return game_words

def getIndicesForBoard():
    indices = []
    used_indices = set()
    while len(indices) < 19:
        maybeNextIndex = randint(1, 25)
        if maybeNextIndex not in used_indices:
            indices.append(maybeNextIndex)
            used_indices.add(maybeNextIndex)
    return indices

def getWhichTeamGoesFirst():
    return 'Blue' if randint(0, 1) == 0 else 'Red'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app)

from flask_socketio import send, emit, join_room

@socketio.on('join')
def on_join(data):
    join_room(data['room'])

@socketio.on('client_connected')
def handle_client_connect_event(json):
    if 'isFromDirectLink' in json:
        if json['isFromDirectLink']:
            games[json['room']]['players'].append(json['data'])
    emit('new_client', json, broadcast=True)

@socketio.on('start_game')
def handle_start_game_event(json):
    emit('game_started', json, broadcast=True)

@socketio.on('new_word')
def handle_new_word_event(json):
    global games
    if 'previousWords' not in games[json['room']]:
        games[json['room']]['previousWords'] = { json['newWord'] : json['numberForNewWord']-1 }
    else:
        games[json['room']]['previousWords'][json['newWord']] = json['numberForNewWord']-1
    games[json['room']]['word'] = json['newWord']
    games[json['room']]['numGuesses'] = json['numberForNewWord']
    games[json['room']]['initialNumGuesses'] = json['numberForNewWord']-1
    emit('display_new_word', json, broadcast=True)

@socketio.on('new_guess')
def handle_new_guess_event(json):
    global games
    if 'guesses' not in games[json['room']]:
        games[json['room']]['guesses'] = [str(json['guess'])]
    else:
        games[json['room']]['guesses'].append(json['guess'])
    emit('display_results_of_new_guess', json, broadcast=True)
    if json['isSwap']:
        handle_switch_teams_event(json)
    else:
        games[json['room']]['numGuesses'] = games[json['room']]['numGuesses'] - 1        


@socketio.on('switch_teams')
def handle_switch_teams_event(json):
    global games
    if 'word' in games[json['room']]:
        # Changing this means you have to change some client side code (isWaitingForCodemaster)
        games[json['room']]['word'] = 'Waiting! (not a clue :))'
        games[json['room']]['numGuesses'] = 0
        games[json['room']]['initialNumGuesses'] = 0
    if ('team' in games[json['room']]):
        games[json['room']]['team'] = 'Blue' if games[json['room']]['team'] == 'Red' else 'Red'
    else:
        games[json['room']]['team'] = 'Blue' if games[json['room']]['first'] == 'Red' else 'Red'
    emit('should_switch_teams', json, broadcast=True)
