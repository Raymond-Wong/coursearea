# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
  url(r'^api', include('api.urls')),
  url(r'^admin', include('admin.urls')),
)
