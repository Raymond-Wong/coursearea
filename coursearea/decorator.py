# -*- coding: utf-8 -*-
'''基础python模块'''
import traceback
import logging
from datetime import datetime
from urllib import urlencode
'''django模块'''
from django.http import HttpResponse, Http404, HttpResponseRedirect
'''自定义模块'''
import utils
from models import User, Access_Token

'''所有请求处理器的基装饰器，用于处理未考虑到的异常
'''
def handler(view):
  def inner(request, *args, **kwargs):
    try:
      return view(request, *args, **kwargs)
    except utils.InvalidArgError as e:
      logging.error(u'请求参数错误：' + unicode(e).decode("unicode-escape"))
      return HttpResponse(utils.Response(code=-3, msg='请求参数错误：%s' % e).to_json(), content_type='application/json')
    except Exception as e:
      logging.error('未知错误:\n' + traceback.format_exc())
      return HttpResponse(utils.Response(code=-1, msg='未知错误：%s' % e).to_json(), content_type="application/json")
  return inner

'''用以装饰只接受post请求的处理器，请求方式错误则返回404
'''
def post_only(view):
  def inner(request, *args, **kwargs):
    if request.method.lower() == 'post':
      return view(request, *args, **kwargs)
    else:
      logging.warn('请求方式错误')
      raise Http404
  return inner

'''用以装饰只接受get请求的处理器，请求方式错误则返回404
'''
def get_only(view):
  def inner(request, *args, **kwargs):
    if request.method.lower() == 'get':
      return view(request, *args, **kwargs)
    else:
      logging.warn('请求方式错误')
      raise Http404
  return inner

'''用以确定用户身份
'''
def identify(view):
  def inner(request, *args, **kwargs):
    # return view(request, User.objects.all()[0], *args, **kwargs)
    credential = utils.parse_arg(request.GET, 'credential', None, str, None)
    user = User.objects.filter(credential=credential)
    if user.count() > 0:
      return view(request, user[0], *args, **kwargs)
    return HttpResponse(Response(code=-2, msg='用户未登录').to_json(), content_type='application/json')
  return inner

'''用以获取access token
'''
def accessible(view):
  def inner(request, *args, **kwargs):
    tokens = Access_Token.objects.order_by('-start_time')
    now = datetime.now()
    if len(tokens) == 0 or now > tokens[0].end_time:
      most_recent_token = utils.update_token()
    else:
      most_recent_token = tokens[0]
    return view(request, most_recent_token.token, *args, **kwargs)
  return inner

'''判断是否有管理员权限
'''
def admin(view):
  def inner(request, *args, **kwargs):
    return view(request, *args, **kwargs)
    if request.session.has_key('admin') and (len(request.session['admin']) == 0 or request.session['admin'][-1].status == 0):
      return view(request, *args, **kwargs)
    data = dict(redirect='/admin/index')
    return HttpResponseRedirect('/admin/user/login?' + urlencode(data))
  return inner