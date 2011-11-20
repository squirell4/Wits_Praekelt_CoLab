import datetime

from django.db import models
from django.core.validators import MinValueValidator


class Level(models.Model):
    """Round of play. Higher levels are more difficult."""
    levelno = models.IntegerField(validators=[MinValueValidator(1)])

    def __unicode__(self):
        return u"Level %d" % self.levelno


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
    players = models.ManyToManyField(Player)
    last_access = models.DateTimeField()

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

    def touch(self):
        self.last_access = datetime.datetime.now()
        self.save()

    def used_colours(self):
        """Return colours already used by players in the game."""
        return set([p.colour for p in self.players.all()])

    def unused_colours(self):
        """Return colours still available for use in the game."""
        return set(Player.COLOUR_STYLES.keys()) - self.used_colours()

    def full(self):
        return (self.players.count() == 4)


class GameAnswer(models.Model):
    """An answers provided by a player in a game."""
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    question = models.ForeignKey(Question)
    answer = models.ForeignKey(Answer, null=True)
