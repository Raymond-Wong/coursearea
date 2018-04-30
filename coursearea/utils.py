# -*- coding: utf-8 -*-
'''基础python模块'''
import json
from datetime import datetime, date
import httplib
import urllib
import hashlib
import logging
'''django模块'''
import django.db.models
from django.core import serializers
'''自定义模块'''
from coursearea.settings import APPID, APPSECRET
from coursearea.models import Access_Token

'''基础响应类
'''
class Response:
  def __init__(self, code=0, msg="success", data=None):
    self.code = code
    self.msg = msg
    self.data = data

  def to_json(self):
    resp = dict()
    resp['code'] = self.code
    resp['msg'] = self.msg
    resp['data'] = self.data
    return json.dumps(resp, ensure_ascii=False, cls=Json_Encoder)

'''让json能够处理日期，时间，模型对象，模型列表
'''
class Json_Encoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, datetime):
      return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, date):
      return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, django.db.models.query.QuerySet):
      return serializers.serialize('json', obj)
    elif isinstance(obj, django.db.models.Model):
      return json.dumps(dict([(attr, getattr(obj, attr)) for attr in [f.name for f in obj._meta.fields]]), ensure_ascii=False, cls=Json_Encoder)
    else:
      return json.JSONEncoder.default(self, obj)

'''从请求中获取参数
如果参数类型不正确，则尝试强制转换类型
如果强制转换失败，则抛出错误参数错误
'''
def parse_arg(args, name, default, _type=None, _filter=None):
  value = args.get(name, default)
  if _type is not None:
    # 尝试强制转换
    try:
      value = _type(value)
    except Exception as e:
      raise InvalidArgError(u'参数类型错误！参数（%s）需要符合类型（%s）' % (name, _type))
  # 尝试过滤
  if _filter is None:
    return value
  # 如果过滤不触发异常且返回True，则认为符合过滤条件
  # 否则触发无效参数异常
  try:
    if _filter(value):
      return value
  except Exception as e:
    print e
    pass
  raise InvalidArgError(u'无效参数（%s）' % name)

'''错误参数异常
'''
class InvalidArgError(Exception):
  def __init__(self, message):
    self.message = message
  def __str__(self):
    return repr(self.message)

'''发送http请求
'''
def send_request(host, path, method, port=443, params={}, toLoad=True):
  logging.info('send request:\t[host:%s][path:%s][params:%s]' % (host, path, params))
  client = httplib.HTTPSConnection(host, port)
  if method == 'GET':
    path = '?'.join([path, urllib.urlencode(params)])
    client.request(method, path)
  else:
    client.request(method, path, json.dumps(params, ensure_ascii=False).encode('utf8'))
    # client.request(method, path, urllib.urlencode(params))
  res = client.getresponse()
  if not res.status == 200:
    return False, res.status
  resStr = res.read()
  logging.info('get response:\t%s' % resStr)
  if toLoad:
    resDict = json.loads(resStr, encoding="utf-8")
    if 'errcode' in resDict.keys() and resDict['errcode'] != 0:
      return False, resDict
    return True, resDict
  return True, resStr

'''获取字符串的md5加密形式
'''
def md5(string):
  encoder = hashlib.md5()
  encoder.update(string)
  return encoder.hexdigest()

'''更新数据库中的access token
'''
def update_token():
  params = {
    'grant_type': 'client_credential',
    'appid': APPID,
    'secret': APPSECRET
  }
  host = 'api.weixin.qq.com'
  path = '/cgi-bin/token'
  method = 'GET'
 
  res = send_request(host, path, method, params=params)
  if not res[0] or res[1].get('errcode'):
    return False
  token = res[1].get('access_token')
  starttime = datetime.now()
  expires_in = timedelta(seconds=int(res[1].get('expires_in')))
  endtime = starttime + expires_in
  token_record = Access_Token.objects.order_by('-start_time')
  if len(token_record) > 0:
    token_record = token_record[0]
  else:
    token_record = Access_Token()
  token_record.token = token
  token_record.end_time = endtime
  token_record.save()
  logging.debug('更新数据库中的access token: %s' % token_record.token)
  return token_record

'''获取或创建对象
'''
def get_or_create(obj, target, default):
  try:
    return target(obj)
  except:
    pass
  return default