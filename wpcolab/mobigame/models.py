from django.db import models
from django.core.validators import MinValueValidator


class Level(models.Model):
    """Round of play. Higher levels are more difficult."""
    levelno = models.IntegerField(primary_key=True,
                                validators=[MinValueValidator(1)])

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


class Game(models.Model):
    """A model of game state."""
    complete = models.BooleanField()
    level = models.ForeignKey(Level, null=True)

    @classmethod
    def current_game(cls):
        """Return the currently active (incomplete) game or create one."""
        uncompleted = list(cls.objects.filter(complete=False).order_by('pk'))
        if not uncompleted:
            uncompleted = [cls.objects.create(complete=False, level=None)]
        return uncompleted[0]

    def used_colours(self):
        """Return colours already used by players in the game."""
        return set([p.colour for p in self.player_set.all()])

    def unused_colours(self):
        """Return colours still available for use in the game."""
        return set(Player.COLOUR_STYLES.keys()) - self.used_colours()


class Player(models.Model):
    COLOURS = [
        ("blue", "Blue", "colorBarBlue"),
        ("red", "Red", "colorBarRed"),
        ("green", "Green", "colorBarGreen"),
        ("pink", "Pink", "colorBarPink"),
        ]

    COLOUR_STYLES = dict((colour, style) for colour, _desc, style in COLOURS)
    COLOUR_DISPLAY = dict((colour, desc) for colour, desc, _style in COLOURS)
    COLOUR_CHOICES = COLOUR_DISPLAY.items()

    first_name = models.CharField(max_length=80)
    colour = models.CharField(max_length=10, choices=COLOUR_CHOICES)
    game = models.ForeignKey(Game)
