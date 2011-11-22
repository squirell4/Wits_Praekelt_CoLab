import datetime
import json
import copy

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

    MAX_AGE = datetime.timedelta(seconds=120)

    complete = models.BooleanField()
    last_access = models.DateTimeField(auto_now=True)
    state = models.TextField(blank=True)
    winner = models.ForeignKey(Player, null=True)

    def __unicode__(self):
        return u"Game %s (complete: %s)" % (self.pk, self.complete)

    @classmethod
    def current_game(cls, create=True):
        """Return the currently active (incomplete) game or create one."""
        uncompleted = list(cls.objects.filter(complete=False)\
                           .order_by('last_access').all())
        now = datetime.datetime.now()
        # expire old games
        for game in uncompleted[:-1]:
            game.complete = True
            game.save()
        if uncompleted:
            current = uncompleted[-1]
            if now - current.last_access > cls.MAX_AGE:
                current.complete = True
                current.save()
            else:
                return current
        if not create:
            return None
        return cls.objects.create(complete=False, last_access=now)

    @classmethod
    def last_game(cls):
        """Return the most recent game, completed or not."""
        games = cls.objects.filter().order_by('-last_access')
        last_game = list(games[:1])
        if last_game:
            print last_game[0].last_access
            return last_game[0]
        return None

    @classmethod
    def previous_winners(cls, limit=10):
        previous_winner_pks = list(cls.objects.filter(winner__isnull=False)\
                                .order_by('-last_access')\
                                .values_list('winner', flat=True)\
                                .distinct()[:limit])
        previous_winners = [Player.objects.get(pk=pk)
                            for pk in previous_winner_pks]
        return previous_winners

    def get_state(self):
        return GameState(self)


class GameState(object):

    LAST_LEVEL = 3
    NUM_PLAYERS = 4
    ROUND_LIMITS = {
        1: 3,  # at most 3 go through from round 1
        2: 2,  # at most 2 go through from round 2
        }
    GAME_STATE_START = {
        'players': {},
        # players that successfully answered all rounds
        'winners': [],
        # players that have been eliminated
        'eliminated': [],
        }
    PLAYER_STATE_START = {
        'level': 0,  # last level answered
        'questions': {},  # level -> question_pk, answer_pk
        }

    def __init__(self, game):
        self.game = game
        if game.state:
            self.data = json.loads(game.state)
        else:
            self.data = copy.deepcopy(self.GAME_STATE_START)

    def __getitem__(self, name):
        return self.data[name]

    def __setitem__(self, name, value):
        self.data[name] = value

    def _pk(self, obj):
        return str(obj.pk)

    def save(self):
        self.game.state = json.dumps(self.data)
        self.game.complete = len(self['eliminated']) == self.NUM_PLAYERS
        if self.data['winners']:
            player_pk = int(self.data['winners'][0])
            winner = Player.objects.get(pk=player_pk)
            self.game.winner = winner
        else:
            self.game.winner = None
        self.game.save()

    def colour_used(self, colour):
        pks = [int(pk) for pk in self['players']]
        used_colours = set(Player.objects.filter(pk__in=pks)\
                                         .values_list('colour', flat=True))
        return colour in used_colours

    def add_player(self, player):
        defaults = copy.deepcopy(self.PLAYER_STATE_START)
        player_pk = self._pk(player)
        self['players'].setdefault(player_pk, defaults)

    def full(self):
        """Whether a full set of players have logged in."""
        return len(self['players']) == self.NUM_PLAYERS

    def player_exists(self, player):
        player_pk = self._pk(player)
        return player_pk in self['players']

    def eliminate_player(self, player):
        """Remove player from game."""
        player_pk = self._pk(player)
        if player_pk not in self['eliminated']:
            self['eliminated'].append(player_pk)

    def eliminated(self, player):
        """Whether player is still in the game."""
        player_pk = self._pk(player)
        return player_pk in self['eliminated']

    def second(self, player):
        return self['winners'][1:2] == [self._pk(player)]

    def winner(self, player):
        return self['winners'][0:1] == [self._pk(player)]

    def answer(self, player, answer_pk):
        """Answer for the current question."""
        player_state = self['players'][self._pk(player)]
        questions = player_state['questions']
        level_no = player_state['level']
        level_key = str(level_no)
        if level_key not in questions:
            return
        question_pk, existing_answer_pk = questions[level_key]
        if existing_answer_pk is not None:
            return

        answer = Answer.objects.get(pk=answer_pk)
        if answer.question.pk != question_pk:
            return

        questions[level_key] = [question_pk, answer_pk]
        player_state['level'] = min(level_no + 1, self.LAST_LEVEL)
        if not answer.correct:
            self.eliminate_player(player)
        elif level_no == self.LAST_LEVEL:
            self['winners'].append(self._pk(player))
            self.eliminate_player(player)
        elif level_no in self.ROUND_LIMITS:
            limit = self.ROUND_LIMITS[level_no]
            if self.players_at_level(level_no + 1) >= limit:
                self.eliminate_player(player)

    def current_question(self, player):
        """Return the question for the current level, creating one
        if needed."""
        player_state = self['players'][self._pk(player)]
        questions = player_state['questions']
        level_no = player_state['level']
        level_key = str(level_no)
        if level_key in questions:
            question_pk, _answer_pk = questions[level_key]
            question = Question.objects.get(pk=question_pk)
        else:
            level = Level.objects.get(levelno=level_no)
            question = level.random_question()
            questions[level_key] = [question.pk, None]
        return question

    def players_at_level(self, level_no):
        all_levels = [p['level'] for k, p in self['players'].items()
                      if k not in self['eliminated']]
        return len([level for level in all_levels if level == level_no])

    def players_synced(self):
        return (self.players_at_level(self.level_no()) ==
                (self.NUM_PLAYERS - len(self['eliminated'])))

    def player_ahead(self, player):
        player_level = self['players'][self._pk(player)]['level']
        all_levels = [p['level'] for p in self['players'].values()
                      if p not in self['eliminated']]
        return any(player_level > level for level in all_levels)

    def seen_ready(self, player):
        self['players'][self._pk(player)]['level'] = 1

    def level_no(self):
        """Current round. Zero if round 1 hasn't started."""
        all_levels = [p['level'] for k, p in self['players'].items()
                      if k not in self['eliminated']]
        if not all_levels:
            return 0
        return min(all_levels)

    def player_level(self, player):
        player_pk = self._pk(player)
        return self['players'][player_pk]['level']

    API_V1_ORDER = ["blue", "red", "green", "pink"]
    API_V1_ELIMINATED = "abcd"
    API_V1_LEVELS = ["1234", "5678", "9xyz"]
    API_V1_WINNER = "mnop"

    def api_v1_state(self):
        # handle non-full game
        if not self.full():
            api_values = []
            for player_pk in self['players']:
                player = Player.objects.get(pk=int(player_pk))
                player_idx = self.API_V1_ORDER.index(player.colour)
                api_values.append(self.API_V1_LEVELS[0][player_idx])
                if not api_values:
                    return "0"
                return "".join(api_values)

        api_values = []
        level = self.level_no()
        players_synced = self.players_synced()
        if players_synced:
            level = max(level - 1, 0)
        for player_pk, player_state in self['players'].items():
            player = Player.objects.get(pk=int(player_pk))
            player_idx = self.API_V1_ORDER.index(player.colour)
            if self.winner(player):
                api_values.append(self.API_V1_WINNER[player_idx])
                continue
            if player_pk in self['eliminated']:
                api_values.append(self.API_V1_ELIMINATED[player_idx])
                continue
            player_level = player_state['level']
            player_lit = (player_level > level)
            print level, player_level, player_lit
            if player_lit and level < len(self.API_V1_LEVELS):
                api_values.append(self.API_V1_LEVELS[level][player_idx])

        if not api_values:
            return "0"
        return "".join(sorted(api_values))
