"""Mobi game views."""

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from mobigame.models import Game, Player


def index(request):
    game = Game.current_game()
    if len(game.player_set.all()) < 4:
        return redirect('login')
    redirect('gamefull')


def login(request):
    game = Game.current_game()
    if len(game.player_set.all()) >= 4:
        return redirect('gamefull')
    unused_colours = sorted(list(game.unused_colours()))
    colour_options = [(colour, Player.COLOUR_DISPLAY[colour])
                      for colour in unused_colours]
    context = RequestContext(request, {
        'first_colour_style': Player.COLOUR_STYLES[unused_colours[0]],
        'colour_options': colour_options,
        })
    return render_to_response('login.html',
                              context_instance=context)


def signout(request):
    pass


def gamefull(request):
    pass


def findafriend(request):
    pass


def getready(request):
    pass
