"""Mobi game views."""

import random

from django.shortcuts import redirect, render
from django.forms import ModelForm
from django.http import HttpResponse

from mobigame.models import Game, Player


# Forms

class LoginForm(ModelForm):
    class Meta:
        model = Player
        fields = ('first_name', 'colour')


# View decorators

def game_in_progress(view):
    def wrapper(request):
        game = Game.current_game()
        gamestate = game.get_state()
        player = request.session.get('player')
        if player is None:
            return redirect('mobigame:login')
        if not gamestate.player_exists(player):
            del request.session['player']
            return redirect('mobigame:login')
        return view(game, gamestate, player, request)
    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


# Views

def index(request):
    return redirect('mobigame:login')


def login(request):
    game = Game.current_game()
    gamestate = game.get_state()

    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            player = login_form.save()
            gamestate.add_player(player)
            gamestate.save()
            request.session['player'] = player
            return redirect('mobigame:play')
    else:
        login_form = LoginForm()

    context = {
        'colour_style': Player.NO_PLAYER_STYLE,
        'login_form': login_form,
        }
    return render(request, 'login.html', context)


def signout(request):
    player = request.session.get('player')
    if player is not None:
        game = Game.current_game()
        gamestate = game.get_state()
        gamestate.eliminate_player(player)
        gamestate.save()
        player.delete()

    login_form = LoginForm()
    context = {
        'colour_style': Player.NO_PLAYER_STYLE,
        'login_form': login_form,
        }
    return render(request, 'signout.html', context)


def scores(request):
    context = {}
    return render(request, 'scores.html', context)


ELIMINATION_MSGS = [
    'The tribe has spoken!',
    'You are the weakest link...',
    'K.O.',
    ]


WINNING_MSGS = {
    'blue': "That flashing blue light aint the Cops -- It's You!",
    'red': "Red is Dynamite! Go set off some fireworks!",
    'green': "You're a mean green maths machine! Look at You!",
    'pink': "You've Proved Pink is not for Sissies!",
    }


@game_in_progress
def play(game, gamestate, player, request):
    context = {
        'game': game,
        'gamestate': gamestate,
        'player': player,
        }

    if request.method == 'POST':
        # answering a question
        answer_pk = request.POST.get('answer')
        answer_pk = int(answer_pk)
        gamestate.answer(player, answer_pk)
        if gamestate.winner(player):
            context['winner_msg'] = \
                WINNING_MSGS[player.colour]
            template = 'winner.html'
        if gamestate.second(player):
            template = 'second.html'
        if gamestate.eliminated(player):
            template = 'eliminated.html'
            context['elimination_msg'] = \
                random.choice(ELIMINATION_MSGS)
        else:
            template = 'madeit.html'
    else:
        if not gamestate.full():
            template = 'findafriend.html'
        elif not gamestate.players_synced():
            gamestate.sync_player(player)
            if gamestate.level_no() is None:
                template = 'getready'
            else:
                template = 'madeit.html'
        else:
            # ask a question!
            template = 'play.html'
            question = gamestate.current_question(player)
            [answer1, answer2] = question.answer_set.all()
            context.update({
                'levelno': gamestate.level_no(),
                'question': question,
                'answer1': answer1,
                'answer2': answer2,
                })

    gamestate.save()
    return render(request, template, context)


# API

def api_v1(request):
    game = Game.current_game()
    gamestate = game.get_state()
    text = gamestate.api_v1_state()
    return HttpResponse(text, mimetype="text/plain")
