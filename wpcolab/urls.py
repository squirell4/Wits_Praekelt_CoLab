from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'wpcolab.views.home', name='home'),
    # url(r'^wpcolab/', include('wpcolab.foo.urls')),

    # mobigame
    url(r'^', include('mobigame.urls', namespace='mobigame')),

    # admin site
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
