from mobigame import views

from django.conf.urls.defaults import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^^$', views.index, name='index'),
    url(r'^login/', views.login, name='login'),
    url(r'^colour/', views.select_colour, name='select_colour'),
    url(r'^play/', views.play, name='play'),
    )
