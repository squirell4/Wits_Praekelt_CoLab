"""Mobi game views."""

from django.shortcuts import redirect, render
from django.forms import ModelForm

from mobigame.models import Game, Player


class LoginForm(ModelForm):
    class Meta:
        model = Player
        fields = ('first_name', 'colour')

    def clean(self):
        super(LoginForm, self).clean()
        if self.colour not in self.game.unused_colours:
            raise ValueError("Colour already taken, sorry. :(")


def index(request):
    game = Game.current_game()
    if game.player_set.count() < 4:
        return redirect('login')
    redirect('gamefull')


def login(request):
    game = Game.current_game()
    if game.player_set.count() >= 4:
        return redirect('gamefull')

    if request.method == 'POST':
        player = Player(game=game)
        login_form = LoginForm(request.POST, instance=player)
        if login_form.is_valid():
            player = login_form.save()
            if game.player_set.count() >= 4:
                return redirect('getready')
            return redirect('findafriend')
    else:
        login_form = LoginForm()

    unused_colours = sorted(list(game.unused_colours()))
    context = {
        'first_colour_style': Player.COLOUR_STYLES[unused_colours[0]],
        'login_form': login_form,
        }
    return render(request, 'login.html', context)


def signout(request):
    login_form = LoginForm()

    context = {
        'login_form': login_form,
        }
    return render(request, 'signout.html', context)


def gamefull(request):
    context = {}
    return render(request, 'gamefull.html', context)


def findafriend(request):
    context = {}
    return render(request, 'findafriend.html', context)


def getready(request):
    context = {}
    return render(request, 'getready.html', context)
