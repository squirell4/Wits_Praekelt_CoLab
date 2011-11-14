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
