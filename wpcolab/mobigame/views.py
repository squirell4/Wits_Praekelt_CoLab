"""Mobi game views."""

from django.shortcuts import redirect, render
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from mobigame.models import Game, Player


# Forms

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


# View decorators

def game_in_progress(view):
    def wrapper(request):
        game = Game.current_game()
        player = request.session.get('player')
        if player is None:
            return redirect('mobigame:login')
        if player not in game.player_set:
            del request.session['player']
            return redirect('mobigame:login')
        game.touch()
        return view(game, player, request)
    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


def plain_text(f):
    def wrapper(request):
        text = f(request)
        return HttpResponse(text, mimetype="text/plain")
    return wrapper


# Views

def index(request):
    return redirect('mobigame:login')


def login(request):
    game = Game.current_game()

    if request.method == 'POST':
        player = Player(game=game)
        login_form = LoginForm(request.POST, instance=player)
        if login_form.is_valid():
            player = login_form.save()
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


@game_in_progress
def play(game, player, request):
    # TODO: handler submit
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


# play.html
# madeit.html
# return render(request, 'findafriend.html', context)
# return render(request, 'getready.html', context)
# return render(request, 'eliminated.html', context)
# return render(request, 'winner.html', context)


ELIMINATION_MSGS = [
    'The tribe has spoken!',
    'You are the weakest link...',
    'K.O.',
    ]


WINNING_MSG = {
    'blue': "That flashing blue light aint the Cops -- It's You!",
    'red': "Red is Dynamite! Go set off some fireworks!",
    'green': "You're a mean green maths machine! Look at You!",
    'pink': "You've Proved Pink is not for Sissies!",
    }


@plain_text
def api_v1(request):
    game = Game.current_game()
    if game.level is None:
        return "0"
    elif game.level.levelno == 1:
        return "1234"
    return "5"
