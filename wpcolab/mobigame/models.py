import datetime
import json

from django.db import models
from django.core.validators import MinValueValidator


class Level(models.Model):
    """Round of play. Higher levels are more difficult."""
    levelno = models.IntegerField(validators=[MinValueValidator(1)])

    def __unicode__(self):
        return u"Level %d" % self.levelno

    def random_question(self):
        return self.question_set.order_by('?')[0]


class Question(models.Model):
    text = models.TextField()
    level = models.ForeignKey(Level)

    def __unicode__(self):
        return u"%s (%s)" % (self.text, self.level)


class Answer(models.Model):
    text = models.TextField()
    correct = models.BooleanField()
    question = models.ForeignKey(Question)

    def __unicode__(self):
        return u"%s (%s)" % (self.text,
                             "correct" if self.correct else "incorrect")


class Player(models.Model):
    COLOURS = [
        ("blue", "Blue", "colorBarBlue"),
        ("red", "Red", "colorBarRed"),
        ("green", "Green", "colorBarGreen"),
        ("pink", "Pink", "colorBarPink"),
        ]

    NO_PLAYER_STYLE = "colorBarNoPlayer"

    COLOUR_STYLES = dict((colour, style) for colour, _desc, style in COLOURS)
    COLOUR_DISPLAY = dict((colour, desc) for colour, desc, _style in COLOURS)
    COLOUR_CHOICES = COLOUR_DISPLAY.items()

    first_name = models.CharField(max_length=80)
    colour = models.CharField(max_length=10, choices=COLOUR_CHOICES)

    def __unicode__(self):
        return u"Player %s (%s, %s)" % (self.pk, self.first_name, self.colour)

    def colour_style(self):
        return self.COLOUR_STYLES[self.colour]


class Game(models.Model):
    """A model of game state."""

    MAX_AGE = datetime.timedelta(seconds=60)

    complete = models.BooleanField()
    last_access = models.DateTimeField(auto_now=True)
    state = models.TextField()
    winner = models.ForeignKey(Player, null=True)

    def __unicode__(self):
        return u"Game %s (complete: %s)" % (self.pk, self.complete)

    @classmethod
    def current_game(cls):
        """Return the currently active (incomplete) game or create one."""
        uncompleted = list(cls.objects.filter(complete=False)\
                           .order_by('last_access').all())
        now = datetime.datetime.now()
        # expire old games
        for game in uncompleted[:-1]:
            game.completed = True
            game.save()
        if uncompleted:
            current = uncompleted[-1]
            if now - current.last_access > cls.MAX_AGE:
                current.completed = True
                current.save()
            else:
                return current
        return cls.objects.create(complete=False, last_access=now)

    def get_state(self):
        return GameState(self)


class GameState(object):

    PLAYER_STATE_START = {
        'sync': None,  # last sync level
        'eliminated': False,  # still in game
        'questions': {},
        }

    def __init__(self, game):
        self.game = game
        self.data = json.loads(game.state)
        self.setdefaults()

    def setdefaults(self):
        self.data.setdefault('players', {})
        self.data.setdefault('level', 0)

    def __getitem__(self, name):
        return self.data[name]

    def __setitem__(self, name, value):
        self.data[name] = value

    def _pk(self, obj):
        return str(obj.pk)

    def save(self):
        self.game.state = json.dumps(self.data)
        self.game.save()

    def add_player(self, player):
        defaults = self.PLAYER_STATE_START.copy()
        player_pk = self._pk(player)
        self['players'].setdefault(player_pk, defaults)

    def full(self):
        """Whether a full set of players have logged in."""
        return len(self['players']) == 4

    def player_exists(self, player):
        player_pk = self._pk(player)
        return player_pk in self['players']

    def eliminate_player(self, player):
        """Remove player from game."""
        player_pk = self._pk(player)
        self['players'][player_pk]['eliminated'] = True

    def eliminated(self, player):
        """Whether player is still in the game."""
        player_pk = self._pk(player)
        return self['players'][player_pk]['eliminated']

    def second(self, player):
        pass

    def winner(self, player):
        pass

    def answer(self, player, answer_pk):
        """Answer for the current question."""
        player_state = self['players'][self._pk(player)]
        questions = player_state['questions']
        level_key = str(self['level'])
        if level_key not in questions:
            return
        question_pk, existing_answer_pk = questions[level_key]
        if existing_answer_pk is not None:
            return

        answer = Answer.objects.get(pk=answer_pk)
        if answer.question.pk != question_pk:
            return

        questions[level_key] = [question_pk, answer_pk]
        if not answer.correct:
            self.eliminated(player)

    def current_question(self, player):
        """Return the question for the current level, creating one
        if needed."""
        player_state = self['players'][self._pk(player)]
        questions = player_state['questions']
        level_no = self['level']
        level_key = str(level_no)
        if level_key in questions:
            question_pk, _answer_pk = questions[level_key]
            question = Question.objects.get(pk=question_pk)
        else:
            level = Level.objects.get(levelno=level_no)
            question = level.random_question()
            questions[level_key] = [question.pk, None]
        return question

    def level_no(self):
        """Current round. None if round 1 hasn't started."""
        return self['level']

    def sync_player(self, player):
        """Sync player at current level. Once all players
        have synced, the level increased."""
        level = self['level']
        player_state = self['players'][self._pk(player)]
        if player_state['sync'] != level:
            player_state['sync'] = level
            if self.players_synced():
                self['level'] = min(level + 1, 3)

    def players_synced(self):
        player_syncs = [p['sync'] for p in self['players'].values()]
        level = self['level']
        return all(sync == level for sync in player_syncs)
