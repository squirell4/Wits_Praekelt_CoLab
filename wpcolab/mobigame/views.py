"""Mobi game views."""

from django.shortcuts import redirect, render
from django.forms import ModelForm
from django.core.exceptions import ValidationError

from mobigame.models import Game, Player


class LoginForm(ModelForm):
    class Meta:
        model = Player
        fields = ('first_name', 'colour')

    def clean(self):
        super(LoginForm, self).clean()
        if (self.cleaned_data['colour'] not in
            self.instance.game.unused_colours()):
            raise ValidationError("Colour already taken, sorry. :(")
        return self.cleaned_data


def first_colour_style(game=None):
    """Retrieve the style of the first available colour."""
    if game is None:
        game = Game.current_game()
    unused_colours = sorted(list(game.unused_colours()))
    return Player.COLOUR_STYLES[unused_colours[0]]


def index(request):
    game = Game.current_game()
    if not game.full():
        return redirect('mobigame:login')
    redirect('mobigame:gamefull')


def login(request):
    game = Game.current_game()
    if game.full():
        return redirect('mobigame:gamefull')

    if request.method == 'POST':
        player = Player(game=game)
        login_form = LoginForm(request.POST, instance=player)
        if login_form.is_valid():
            player = login_form.save()
            request.session['player'] = player
            if game.full():
                return redirect('mobigame:getready')
            return redirect('mobigame:findafriend')
    else:
        login_form = LoginForm()

    context = {
        'first_colour_style': first_colour_style(game),
        'login_form': login_form,
        }
    return render(request, 'login.html', context)


def signout(request):
    player = request.session.get('player')
    if player is not None:
        player.delete()

    login_form = LoginForm()
    context = {
        'first_colour_style': first_colour_style(),
        'login_form': login_form,
        }
    return render(request, 'signout.html', context)


def gamefull(request):
    context = {}
    return render(request, 'gamefull.html', context)
    # TODO: implement


def findafriend(request):
    player = request.session.get('player')
    if player is None:
        redirect('mobigame:login')
    game = Game.current_game()
    if game.full():
        return redirect('mobigame:getready')
    context = {
        'player': player,
        }
    return render(request, 'findafriend.html', context)


def getready(request):
    player = request.session.get('player')
    if player is None:
        redirect('mobigame:login')
    context = {
        'player': player,
        }
    return render(request, 'getready.html', context)


def play(request):
    player = request.session.get('player')
    if player is None:
        redirect('mobigame:login')
    game = Game.current_game()
    question = game.question()
    [answer1, answer2] = question.answer_set.all()
    context = {
        'game': game,
        'player': player,
        'question': question,
        'answer1': answer1,
        'answer2': answer2,
        }
    return render(request, 'play.html', context)
