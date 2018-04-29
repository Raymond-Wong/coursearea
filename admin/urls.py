# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
  url(r'index', views.index, name=u'页面路由转发给前端'),
  url(r'api/image/upload', views.upload_image, name=u'上传图片')
  url(r'api/user/login', views.login, name=u'管理员登录')
  url(r'api/user/logout', views.logout, name=u'管理员登出')
  url(r'api/series/getSeriesList', views.get_series_list, name=u'获取系列列表')
  url(r'api/series/getSeriesDetail', views.get_series_detail, name=u'获取系列详情')
  url(r'api/series/setSeriesDetail', views.set_series_detail, name=u'设置系列详情')
  url(r'api/course/getCourseList', views.get_course_list, name=u'获取课程列表')
  url(r'api/course/getCourseDetail', views.get_course_detail, name=u'获取课程详情')
  url(r'api/course/setCourseDetail', views.set_course_detail, name=u'设置课程详情')
  url(r'api/comment/getCommentList', views.get_comment_list, name=u'获取评论列表')
)