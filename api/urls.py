# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
  url(r'home/getBannerList$', views.get_banner_list, name=u'首页banner轮播获取'),
  url(r'home/getSelectedList$', views.get_selected_list, name=u'首页精选内容获取'),
  url(r'user/getAuditionList$', views.get_audition_list, name=u'获取试听列表'),
  url(r'user/login$', views.wechat_user_login, name=u'用户登录'),
  url(r'user/getUserInfo$', views.get_user_info, name=u'获取用户信息'),
  url(r'course/getCourseDetail$', views.get_course_detail, name=u'获取课程详情'),
  url(r'course/doCollect$', views.do_collect, name=u'收藏课程'),
  url(r'course/postComment$', views.post_comment, name=u'发布评论'),
  url(r'course/doVisit$', views.do_visit, name=u'访问课程'),
  url(r'course/doListen$', views.do_listen, name=u'试听课程'),
  url(r'course/getInviteCode$', views.get_invite_code, name=u'获取邀请二维码'),
  url(r'course/getInviteStyle$', views.get_invite_style, name=u'获取邀请卡样式'),
)