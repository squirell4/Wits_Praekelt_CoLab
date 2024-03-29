from mobigame import views

from django.conf.urls.defaults import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^login/', views.login, name='login'),
    url(r'^signout/', views.signout, name='signout'),
    url(r'^scores/', views.scores, name='scores'),
    url(r'^play/', views.play, name='play'),
    url(r'^api/v1/', views.api_v1, name='apiv1'),
    )
