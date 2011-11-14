"""Mobi game views."""

from django.shortcuts import render_to_response
from django.template import RequestContext


def index(request):
    return render_to_response('index.html',
                              context_instance=RequestContext(request))


def login(request):
    return render_to_response('login.html',
                              context_instance=RequestContext(request))


def select_colour(request):
    pass


def play(request):
    pass
