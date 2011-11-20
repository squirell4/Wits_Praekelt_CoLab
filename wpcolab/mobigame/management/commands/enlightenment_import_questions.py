"""Command for importing questions and answers."""

import sys
import re

from django.core.management.base import BaseCommand
from optparse import make_option

from wpcolab.mobigame.models import Level, Question, Answer


class ParserError(Exception):
    """Error parsing a question file."""


class FileParser(object):

    LEVEL_RE = re.compile(r'^Level\s+(?P<level>\d+)\s+$')
    QUESTION_RE = re.compile(r'^\d+\.\)(?P<question>.*)$')
    ANSWER_RE = re.compile(r'[AB](?P<correct>\*?)\:(?P<answer>.*)$')

    def __init__(self):
        self.current_level = None
        self.current_question = None
        self.lineno = 0
        self.levels = []
        self.questions = []
        self.answers = []
        self.regex_handlers = [
            ('level', self.handle_level, self.LEVEL_RE),
            ('question', self.handle_question, self.QUESTION_RE),
            ('answer', self.handle_answer, self.ANSWER_RE),
            ]

    def raise_error(self, msg):
        raise ParserError(u"%s [line %d: %r]" % (msg, self.lineno, self.line))

    def feed(self, line):
        self.lineno += 1
        self.line = line
        if not line.strip():
            return
        for _name, handler, regex in self.regex_handlers:
            match = regex.match(line)
            if match is not None:
                handler(match)
                return
        self.raise_error(u"Bad line")

    def handle_level(self, match):
        levelno = int(match.group('level'))
        if levelno < 1:
            self.raise_error(u"Invalid level number %d" % levelno)
        self.current_level, _ = Level.objects.get_or_create(levelno=levelno)
        self.current_question = None
        self.levels.append(self.current_level)

    def handle_question(self, match):
        question = match.group('question').strip()
        if self.current_level is None:
            self.raise_error(u"Question outside of level")
        self.current_question = Question(text=question,
                                         level=self.current_level)
        self.questions.append((self.current_question, []))

    def handle_answer(self, match):
        answer = match.group('answer').strip()
        correct = bool(match.group('correct'))
        if self.current_question is None:
            self.raise_error(u"Answer outside of question")
        answer = Answer(text=answer, correct=correct,
                        question=self.current_question)
        self.questions[-1][1].append(answer)

    def print_summary(self):
        print "Summary:"
        print "  Levels:", len(self.levels)
        print "  Questions:", len(self.questions)

    def print_results(self):
        print "Levels:"
        for level in self.levels:
            print " ", level.levelno
        print "Questions:"
        for question, answers in self.questions:
            print " ", question.text
            for answer in answers:
                print "   %s" % ('*' if answer.correct else ''), answer.text

    def check(self):
        for question, answers in self.questions:
            if len(answers) != 2:
                raise ParserError("There must be two answers for question %r" %
                                  question)
            correct_answers = [a for a in answers if a.correct]
            if len(correct_answers) != 1:
                raise ParserError("There must be exactly one correct answer"
                                  " for question %r" % question)

    def save(self):
        for level in self.levels:
            level.save()
        for question, answers in self.questions:
            question.save()
            for answer in answers:
                answer.save()


class Command(BaseCommand):
    help = "Import questions and answers from a text file."

    option_list = BaseCommand.option_list + (
        make_option('--filename', dest='filename', default='', type='str',
                        help='Text file to read'),
        make_option('--verbose', dest='verbose', action="store_true",
                    default=False),
    )

    def handle(self, *args, **options):
        filename = options['filename']
        if not filename:
            sys.exit('Please provide --filename')
        verbose = options.get('verbose')

        print 'Importing questions from %s' % filename
        parser = FileParser()
        with open(filename, "rb") as qfile:
            for line in qfile:
                line = line.decode("utf8")
                parser.feed(line)

        if verbose:
            parser.print_results()

        parser.print_summary()

        print 'Checking imports ...'
        parser.check()

        print 'Saving questions, answers and levels ...'
        parser.save()

        print 'Done'
