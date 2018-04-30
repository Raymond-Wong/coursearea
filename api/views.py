# -*- coding: utf-8 -*-
'''基础python模块'''
import logging
'''django模块'''
from django.http import HttpResponse
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
'''自定义模块'''
import coursearea.utils
from coursearea.utils import Response
from coursearea.decorator import *
from coursearea.models import Course, Collect, Visit, Audition
import utils
from coursearea.settings import APPID, APPSECRET

'''获取首页banner列表
'''
@handler
@get_only
def get_banner_list(request):
  courses = Course.objects.filter(is_banner=True)
  start = coursearea.utils.parse_arg(request.GET, 'start', '0', int)
  end = coursearea.utils.parse_arg(request.GET, 'end', courses.count(), int)
  courses = courses[start:end]
  banner_list = []
  for course in courses:
    banner_list.append(dict(course_id=course.id, cover_url=course.info.cover_url))
  return HttpResponse(Response(data=dict(bannerList=banner_list)).to_json(), content_type="application/json")

'''获取首页精选课程列表
'''
@handler
@get_only
@identify
def get_selected_list(request, user):
  courses = Course.objects.filter(is_selected=True)
  start = coursearea.utils.parse_arg(request.GET, 'start', '0', int)
  end = coursearea.utils.parse_arg(request.GET, 'end', courses.count(), int)
  courses = courses[start:end]
  selected_list = []
  for course in courses:
    data = dict(course_id=course.id, cover_url=course.info.cover_url, title=course.info.name, abstract=course.info.desc)
    data['collected'] = True if Collect.objects.filter(user=user, course=course).count() > 0 else False
    selected_list.append(data)
  return HttpResponse(Response(data=dict(selected_list=selected_list)).to_json(), content_type='application/json')

@handler
@get_only
@identify
def get_course_detail(request, user):
  course_id = coursearea.utils.parse_arg(request.GET, 'course_id', None, int, lambda x:Course.objects.filter(id=x).count() > 0)
  course = dict()
  course_obj = Course.objects.get(id=course_id)
  course['id'] = course_obj.id
  course['info'] = dict(name=course_obj.info.name, description=course_obj.info.desc, price=course_obj.info.price,
                        term_length=course_obj.series.term_length, status=course_obj.info.status, cover_url=course_obj.info.cover_url,
                        teacher=dict(name=course_obj.info.teacher.name, avatar=course_obj.info.teacher.avatar, introduce=course_obj.info.teacher.desc))
  course['group'] = course_obj.group
  visit = Visit.objects.filter(user=user, course=course_obj)
  if visit.count() <= 0:
    invited_by = coursearea.utils.parse_arg(request.GET, 'invited_by', None, None, lambda x:x is None or User.objects.filter(id=x).count() > 0)
    invited_by = invited_by if invited_by is None else User.objects.get(id=invited_by)
    visit = Visit(user=user, course=course_obj, invited_by=invited_by)
    visit.save()
  else:
    visit = visit[0]
  course['friends'] = dict(unlock=visit.unlock, list=[], series=dict(id=course_obj.series.id, cover_url=course_obj.series.cover_url))
  friends = utils.get_friends(user)
  for friend in friends:
    course['friends']['list'].append(dict(nickname=friend.nickname, avatar=friend.avatar))
  course['recommend'] = []
  for c in course_obj.recommend_courses.all():
    crs = dict(id=c.id, title=c.info.name, cover_url=c.info.cover_url)
    course['recommend'].append(crs) 
  course['comments'] = []
  for cmt in course_obj.comment_set.all():
    comment = dict(user_id=cmt.user.id, avatar=cmt.user.avatar, name=cmt.user.nickname, content=cmt.content, create_time=cmt.create_time)
    course['comments'].append(comment)
  return HttpResponse(Response(data=dict(course=course)).to_json(), content_type='application/json')

'''获取收听列表
'''
@handler
@get_only
@identify
def get_audition_list(request, user):
  audition_list = Audition.objects.filter(user=user)
  start = coursearea.utils.parse_arg(request.GET, 'start', '0', int)
  end = coursearea.utils.parse_arg(request.GET, 'end', audition_list.count(), int)
  audition_list = audition_list[start:end].values_list('course__id', 'course__info__cover_url', 'course__info__name', 'create_time').annotate(comments_num=Count('course__comment'))
  resp = []
  keys = ['course_id', 'cover_url', 'title', 'create_time', 'comments_num']
  for aud in audition_list:
    audition = dict()
    for kidx, key in enumerate(keys):
      audition[key] = aud[kidx]
    resp.append(audition)
  return HttpResponse(Response(data=dict(listen_records=resp)).to_json(), content_type="application/json")

'''更新用户会话标识
'''
@csrf_exempt
@handler
@post_only
def wechat_user_login(request):
  logging.info(request.POST.get('js_code'))
  code = coursearea.utils.parse_arg(request.POST, 'code', None, str, None)
  nickname = coursearea.utils.parse_arg(request.POST, 'nickname', None, str, None)
  gender = coursearea.utils.parse_arg(request.POST, 'gender', 1, int, lambda x:x in [0, 1, 2])
  city = coursearea.utils.parse_arg(request.POST, 'city', '', str, None)
  province = coursearea.utils.parse_arg(request.POST, 'province', '', str, None)
  country = coursearea.utils.parse_arg(request.POST, 'country', '', str, None)
  avatar = coursearea.utils.parse_arg(request.POST, 'avatarUrl', '', str, None)
  language = coursearea.utils.parse_arg(request.POST, 'language', 'zh_CN', str, None)
  # 更新登录状态
  status, resp = coursearea.utils.send_request('api.weixin.qq.com', 
    '/sns/jscode2session', 'GET', toLoad=True,
    params=dict(appid=APPID, secret=APPSECRET, js_code=code, grant_type='authorization_code'))
  if not status:
    return HttpResponse(Response(code=1, msg='更新用户会话标识失败').to_json(), content_type='application/json')
  openid = resp['openid']
  session_key = resp['session_key']
  user = User.objects.filter(openid=openid)
  if user.count() > 0:
    user = user[0]
  else:
    user = User(openid=openid)
  user.session_key = session_key
  user.credential = coursearea.utils.md5(json.dumps(dict(openid=openid, session_key=session_key)))
  user.nickname = nickname
  user.gender = gender
  user.city = city
  user.province = province
  user.country = country
  user.avatar = avatar
  user.language = language
  user.save()
  return HttpResponse(Response(data=user.credential).to_json(), content_type='application/json')

'''获取用户详细信息
'''
@handler
@get_only
@identify
def get_user_info(request, user):
  return HttpResponse(Response(data=user).to_json(), content_type='application/json')

'''用户收藏课程
'''
@csrf_exempt
@handler
@post_only
@identify
def do_collect(request, user):
  course = coursearea.utils.parse_arg(request.POST, 'course_id', None, long, lambda x:Course.objects.filter(id=x).count() > 0)
  course = Course.objects.get(id=course)
  collect = Collect.objects.filter(user=user, course=course)
  if collect.count() > 0:
    return HttpResponse(Response(code=1, msg='不能重复收藏同一课程').to_json(), content_type='application/json')
  Collect(user=user, course=course).save()
  return HttpResponse(Response().to_json(), content_type='application/json')

'''用户发表评论
'''
@csrf_exempt
@handler
@post_only
@identify
def post_comment(request, user):
  course = coursearea.utils.parse_arg(request.POST, 'course_id', None, long, lambda x:Course.objects.filter(id=x).count() > 0)
  comment = coursearea.utils.parse_arg(request.POST, 'comment', None, str, None)
  course = Course.objects.get(id=course)
  Comment(course=course, user=user, comment=comment).save()
  return HttpResponse(Response().to_json(), content_type='application/json')

'''用户访问课程
'''
@csrf_exempt
@handler
@post_only
@identify
def do_visit(request, user):
  course = coursearea.utils.parse_arg(request.POST, 'course_id', None, long, lambda x:Course.objects.filter(id=x).count() > 0)
  course = Course.objects.get(id=course)
  invited_by = coursearea.utils.parse_arg(request.POST, 'invited_by', None, long, None)
  invited_by = User.objects.filter(id=invited_by)
  if invited_by.count() > 0:
    invited_by = invited_by[0]
  else:
    invited_by = None
  visit = Visit.objects.filter(course=course, user=user)
  if visit.count() > 0:
    visit = visit[0]
  else:
    visit = Visit(user=user, course=course)
  visit.invited_by = invited_by
  visit.save()
  # 判断发出邀请用户是否已经满足解锁系列条件
  if invited_by is not None and \
     invited_by.invite_visit_set.filter(unlock=True).count() >= course.series.unlock_num and \
     Subscribe.objects.filter(user=user, series=course.series).count() == 0:
    Subscribe(user=user, series=series).save()
  return HttpResponse(Response().to_json(), content_type='application/json')

'''用户试听课程
'''
@csrf_exempt
@handler
@post_only
@identify
def do_listen(request, user):
  course = coursearea.utils.parse_arg(request.POST, 'course_id', None, long, lambda x:Course.objects.filter(id=x).count() > 0)
  course = Course.objects.get(id=course)
  Audition(user=user, course=course).save()
  return HttpResponse(Response().to_json(), content_type='application/json')

'''获取邀请链接
'''
@csrf_exempt
@handler
@get_only
@identify
@accessible
def get_invite_code(request, user, token):
  course = coursearea.utils.parse_arg(request.GET, 'course_id', None, long, lambda x:Course.objects.filter(id=x).count() > 0)
  course = Course.objects.get(id=course)
  page = coursearea.utils.parse_arg(request.GET, 'page', None, str, None)
  width = coursearea.utils.parse_arg(request.GET, 'width', 48, int, None)
  auto_color = coursearea.utils.parse_arg(request.GET, 'auto_color', False, bool, None)
  line_color = coursearea.utils.parse_arg(request.GET, 'line_color', dict(r=0, g=0, b=0), dict, None)
  scene = json.dumps(dict(user=user.id, course=course.id, scene='course_invite'))
  params = dict(scene=scene, page=page, width=width, auto_color=auto_color, line_color=line_color)
  visit = Visit.objects.get(user=user, course=course)
  if visit.invite_url is None:
    status, resp = coursearea.send_request('api.weixin.qq.com', '/wxa/getwxacodeunlimit?access_token=%s' % token, 'POST', 
                                           port=443, params=params, toLoad=True)
    if not status:
      return HttpResponse(Response(code=1, msg='获取邀请链接失败').to_json(), content_type='application/json')
    visit.invite_url = resp['url']
    visit.save()
  resp = dict(qrcode_url=visit.invite_url)
  return HttpResponse(Response(data=resp).to_json(), content_type='application/json')

'''获取邀请样式
'''
@csrf_exempt
@handler
@get_only
def get_invite_style(request):
  course = coursearea.utils.parse_arg(request.GET, 'course_id', None, long, lambda x:Course.objects.filter(id=x).count() > 0)
  course = Course.objects.get(id=course)
  return HttpResponse(Response(data=course.style).to_json(), content_type='application/json')





