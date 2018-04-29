# -*- coding: utf-8 -*-
'''基础python模块'''
import logging
from datetime import datetime, timedelta
import time
from os import environ
import json
'''django模块'''
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
'''自定义模块'''
import coursearea.utils
from coursearea.utils import Response
from coursearea.decorator import *
from coursearea.models import *
from coursearea.settings import ADMIN_CONFIG

'''路由转发
'''
@handler
@get_only
@admin
def index(request):
  pass

'''上传图片
'''
@csrf_exempt
@handler
@post_only
@admin
def upload_image(request):
  image = request.FILES['image']
  image._name = '%s_%s' % (str(int(time.time())), image._name)
  image = Image(url=image)
  image.save()
  # 获取完整的图片url
  url = image.__dict__.get('url')
  remote = environ.get("APP_NAME", "")
  remote_media_path = "http://%s-images.stor.sinaapp.com/" % remote
  base_url = remote_media_path if remote else "/media/"
  url = base_url + url
  return HttpResponse(Response(data=url).to_json(), content_type='application/json')

'''管理员登录状态
'''
class ADMIN_STATUS:
  logined = 0
  logouted = -1
  locked = -2
  failed = -3
'''登录记录类
'''
class Login_Record:
  def __init__(self, status):
    self.status = status
    self.time = datetime.now()

'''登录处理函数
'''
@csrf_exempt
@handler
@post_only
def login(request):
  if not request.session.has_key('admin'):
    request.session['admin'] = []
  # 判断当前是否已经是登录状态
  if len(request.session['admin']) > 0 and request.session['admin'][-1].status == ADMIN_STATUS.logined:
    return HttpResponse(Response(code=4, msg=u'不允许重复登录').to_json(), content_type='application/json')
  print len(request.session['admin'])
  # 判断是否被锁定
  now = datetime.now()
  if len(request.session['admin']) > 0 and\
     request.session['admin'][-1].status == ADMIN_STATUS.locked and\
     (now - request.session['admin'][-1].time).total_seconds() < ADMIN_CONFIG['retry_freq'][2]:
    unlocked_time = request.session['admin'][-1].time + timedelta(seconds=ADMIN_CONFIG['retry_freq'][2])
    unlocked_time = unlocked_time.strftime('%Y-%m-%d %H:%M')
    return HttpResponse(Response(code=1, msg=u'登录失败次数超过限制，请于%s后重新尝试' % unlocked_time).to_json(), content_type='application/json')
  # 判断账号密码是否正确
  account = coursearea.utils.parse_arg(request.POST, 'account', None, str, None)
  passwd = coursearea.utils.parse_arg(request.POST, 'passwd', None, str, None)
  if account == coursearea.utils.md5(ADMIN_CONFIG['account']) and\
     passwd == coursearea.utils.md5(ADMIN_CONFIG['passwd']):
    request.session['admin'] = [Login_Record(ADMIN_STATUS.logined)]
    return HttpResponse(Response(msg=u'登录成功').to_json(), content_type='application/json')
  # 如果账号或者密码错误，判断是否要上锁
  if len(filter(lambda x:x.status == ADMIN_STATUS.failed and (now - x.time).total_seconds() < ADMIN_CONFIG['retry_freq'][0], request.session['admin'])) >= ADMIN_CONFIG['retry_freq'][1] - 1:
    request.session['admin'] = [Login_Record(ADMIN_STATUS.locked)]
    unlocked_time = request.session['admin'][-1].time + timedelta(seconds=ADMIN_CONFIG['retry_freq'][2])
    unlocked_time = unlocked_time.strftime('%Y-%m-%d %H:%M')
    return HttpResponse(Response(code=2, msg=u'登录失败次数超过限制，请于%s后重新尝试！' % unlocked_time).to_json(), content_type='application/json')
  request.session['admin'].append(Login_Record(ADMIN_STATUS.failed))
  request.session['test'] = datetime.now()
  return HttpResponse(Response(code=3, msg=u'登录失败').to_json(), content_type='application/json')

'''管理员登出处理函数
'''
@csrf_exempt
@handler
@post_only
@admin
def logout(request):
  request.session['admin'] = []
  return HttpResponse(Response(msg='登出成功').to_json(), content_type='application/json')

'''获取系列列表
'''
@handler
@get_only
@admin
def get_series_list(request):
  series_obj = Series.objects.all()
  series_list = []
  for series in series_obj:
    series_list.append(dict(id=series.id, name=series.name, cover_url=series.cover_url, create_time=series.create_time))
  return HttpResponse(Response(data=series_list).to_json(), content_type='application/json')

'''获取系列详情
'''
@handler
@get_only
@admin
def get_series_detail(request):
  series_id = coursearea.utils.parse_arg(request.GET, 'series_id', None, long, lambda x:Series.objects.filter(id=x).count() > 0)
  series = Series.objects.get(id=series_id)
  return HttpResponse(Response(data=series).to_json(), content_type='application/json')

'''获取课程列表
'''
@handler
@get_only
@admin
def get_course_list(request):
  series_id = coursearea.utils.parse_arg(request.GET, 'series_id', None, None, lambda x:(x is None or Series.objects.filter(id=x).count() > 0))
  if series_id == None:
    courses_obj = Course.objects.all()
  else:
    courses_obj = Series.objects.get(id=series_id).course_set
  course_list = []
  for course in courses_obj.all():
    course_list.append(dict(id=course.id, info=dict(name=course.info.name, desc=course.info.desc, cover_url=course.info.cover_url)))
  return HttpResponse(Response(data=course_list).to_json(), content_type='application/json')

'''获取课程详情
'''
@handler
@get_only
@admin
def get_course_detail(request):
  course_id = coursearea.utils.parse_arg(request.GET, 'course_id', None, long, lambda x:Course.objects.filter(id=x).count() > 0)
  course_obj = Course.objects.get(id=course_id)
  course = dict()
  course['info'] = dict(name=course_obj.info.name, desc=course_obj.info.desc, price=course_obj.info.price, status=course_obj.info.status,
                        cover_url=course_obj.info.cover_url, teacher=dict(name=course_obj.info.teacher.name, avatar=course_obj.info.teacher.avatar, desc=course_obj.info.teacher.desc))
  course['group'] = dict(name=course_obj.group.name, avatar=course_obj.group.avatar, desc=course_obj.group.desc, link=course_obj.group.link)
  course['series'] = dict(id=course_obj.series.id, name=course_obj.series.name, term_length=course_obj.series.term_length, cover_url=course_obj.series.cover_url)
  course['is_selected'] = course_obj.is_selected
  course['is_banner'] = course_obj.is_banner
  course['recommend_courses'] = []
  for c in course_obj.recommend_courses.all():
    course['recommend_courses'].append(dict(id=c.id, info=dict(name=c.info.name, desc=c.info.desc)))
  course['create_time'] = course_obj.create_time
  course['is_released'] = course_obj.is_released
  return HttpResponse(Response(data=course).to_json(), content_type='application/json')

'''获取评论列表
'''
@handler
@get_only
@admin
def get_comment_list(request):
  comments_obj = Comment.objects.all()
  user_id = coursearea.utils.parse_arg(request.GET, 'user_id', None, None, lambda x:(x is None or User.objects.filter(id=x).count() > 0))
  if user_id is not None:
    comments_obj = comments_obj.filter(user=User.objects.get(id=user_id))
  course_id = coursearea.utils.parse_arg(request.GET, 'course_id', None, None, lambda x:(x is None or Course.objects.filter(id=course_id).count() > 0))
  if course_id is not None:
    comments_obj = comments_obj.filter(course=Course.objects.get(id=course_id))
  comment_list = []
  for comment in comments_obj:
    comment_list.append(dict(id=comment.id, create_time=comment.create_time, course=comment.course.id, user=comment.user.id, content=comment.content))
  return HttpResponse(Response(data=comment_list).to_json(), content_type='application/json')

'''设置系列详情
'''
@csrf_exempt
@handler
@post_only
@admin
def set_series_detail(request):
  series_id = coursearea.utils.parse_arg(request.POST, 'series_id', None, None, lambda x:(x is None or Series.objects.filter(id=x).count() > 0))
  if series_id is not None:
    series = Series.objects.get(id=series_id)
  else:
    series = Series()
  series.name = coursearea.utils.parse_arg(request.POST, 'name', series.name, unicode, None)
  series.term_length = coursearea.utils.parse_arg(request.POST, 'term_length', series.term_length, int, None)
  series.cover_url = coursearea.utils.parse_arg(request.POST, 'cover_url', series.cover_url, str, None)
  series.save()
  return HttpResponse(Response().to_json(), content_type='application/json')

'''设置课程详情
'''
@csrf_exempt
@handler
@post_only
@admin
def set_course_detail(request):
  # 获取或创建课程
  course_id = coursearea.utils.parse_arg(request.POST, 'course_id', None, None, lambda x:(x is None or Course.objects.filter(id=x).count() > 0))
  if course_id is None:
    MODE = 'create'
    course = Course()
  else:
    MODE = 'edit'
    course = Course.objects.get(id=course_id)
  # 设置课程基本信息
  info = coursearea.utils.parse_arg(request.POST, 'info', None, None, lambda x:((x is None and MODE == 'edit') or isinstance(json.loads(x), dict)))
  if info is not None:
    info = json.loads(info)
    info_obj = coursearea.utils.get_or_create(course, lambda x:x.info, Course_Info())
    info_obj.name = info['name'] if info.has_key('name') else info_obj.name
    info_obj.desc = info['desc'] if info.has_key('desc') else info_obj.desc
    info_obj.price = info['price'] if info.has_key('price') else info_obj.price
    info_obj.status = info['status'] if info.has_key('status') else info_obj.status
    info_obj.cover_url = info['cover_url'] if info.has_key('cover_url') else info_obj.cover_url
    info_obj.resource = info['resource'] if info.has_key('resource') else info_obj.resource
    teacher_obj = coursearea.utils.get_or_create(info_obj, lambda x:x.teacher, Teacher())
    if info.has_key('teacher') and isinstance(info['teacher'], dict):
      teacher_obj.name = info['teacher']['name'] if info['teacher'].has_key('name') else teacher_obj.name
      teacher_obj.avatar = info['teacher']['avatar'] if info['teacher'].has_key('avatar') else teacher_obj.avatar
      teacher_obj.desc = info['teacher']['desc'] if info['teacher'].has_key('desc') else teacher_obj.desc
      teacher_obj.save()
      info_obj.teacher = teacher_obj
    info_obj.save()
    course.info = info_obj
  # 设置组
  group = coursearea.utils.parse_arg(request.POST, 'group', None, None, lambda x:((x is None and MODE == 'edit') or isinstance(json.loads(x), dict)))
  if group is not None:
    group = json.loads(group)
    group_obj = coursearea.utils.get_or_create(course, lambda x:x.group, Group())
    group_obj.name = group['name'] if group.has_key('name') else group_obj.name
    group_obj.desc = group['desc'] if group.has_key('desc') else group_obj.desc
    group_obj.avatar = group['avatar'] if group.has_key('avatar') else group_obj.avatar
    group_obj.link = group['link'] if group.has_key('link') else group_obj.link
    group_obj.save()
    course.group = group_obj
  # 设置系列，是否精选，是否banner
  series_id = coursearea.utils.parse_arg(request.POST, 'series_id', None, long, lambda x:Series.objects.filter(id=x).count() > 0)
  series = Series.objects.get(id=series_id)
  course.series = series
  course.is_selected = coursearea.utils.parse_arg(request.POST, 'is_selected', course.is_selected, bool, None)
  course.is_banner = coursearea.utils.parse_arg(request.POST, 'is_banner', course.is_banner, bool, None)
  # 设置推荐课程
  recommend_courses = coursearea.utils.parse_arg(request.POST, 'recommend_courses', None, None, lambda x:((x is None and MODE == 'edit') or isinstance(json.loads(x), list)))
  if recommend_courses is not None:
    recommend_courses = json.loads(recommend_courses)
    try:
      course.recommend_courses.clear()
    except:
      'this is a new course or this course has never recommended any courses'
    recommend_courses = filter(lambda x:Course.objects.filter(id=x).count() > 0, recommend_courses)
    recommend_courses = Course.objects.filter(id__in=recommend_courses)
    for obj in recommend_courses:
      course.recommend_courses.add(obj)
  # 设置是否发布
  course.is_released = coursearea.utils.parse_arg(request.POST, 'is_released', course.is_released, bool, None)
  # 设置海报样式
  style = coursearea.utils.parse_arg(request.POST, 'style', None, None, lambda x:((x is None and MODE == 'edit') or isinstance(json.loads(x), dict)))
  if style is not None:
    style = json.loads(style)
    style_obj = coursearea.utils.get_or_create(course, lambda x:x.style, Course_Style())
    style_obj.name_x = style['name_x'] if style.has_key('name_x') else style_obj.name_x
    style_obj.name_y = style['name_y'] if style.has_key('name_y') else style_obj.name_y
    style_obj.font_size = style['font_size'] if style.has_key('font_size') else style_obj.font_size
    style_obj.qrcode_x = style['qrcode_x'] if style.has_key('qrcode_x') else style_obj.qrcode_x
    style_obj.qrcode_y = style['qrcode_y'] if style.has_key('qrcode_y') else style_obj.qrcode_y
    style_obj.qrcode_size = style['qrcode_size'] if style.has_key('qrcode_size') else style_obj.qrcode_size
    style_obj.bg = style['bg'] if style.has_key('bg') else style_obj.bg
    style_obj.save()
    course.style = style_obj
  course.save()
  return HttpResponse(Response().to_json(), content_type='application/json')