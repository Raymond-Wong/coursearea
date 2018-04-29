# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile, FieldFile, ImageFile
import sae.storage
from os import environ

'''访问微信服务器的凭证
'''
class Access_Token(models.Model):
  token = models.CharField(max_length=600)
  start_time = models.DateTimeField(auto_now=True)
  end_time = models.DateTimeField()

'''微信用户
'''
GENDER = ((0, u'未知'), (1, u'男性'), (2, u'女性'))
class User(models.Model):
  create_time = models.DateTimeField(auto_now_add=True)
  openid = models.CharField(max_length=200, unique=True)
  session_key = models.CharField(max_length=200)
  credential = models.CharField(max_length=50, unique=True)
  nickname = models.CharField(max_length=50, default='')
  gender = models.PositiveIntegerField(choices=GENDER, default=0)
  city = models.CharField(max_length=50, default='')
  province = models.CharField(max_length=50, default='')
  country = models.CharField(max_length=50, default='')
  avatar = models.URLField(null=True, default=None, max_length=500)
  language = models.TextField(max_length=50, default='')

'''课程讲师
  name   : 名字
  avatar : 头像
  desc   : 简介
'''
# 课程教师
class Teacher(models.Model):
  name = models.CharField(max_length=50)
  avatar = models.TextField()
  desc = models.TextField()

'''课程基础信息
  name      : 名称
  desc      : 描述
  price     : 价格
  status    : 目前状态
  cover_url : 封面图片
  teacher   : 讲师信息
'''
class Course_Info(models.Model):
  name = models.CharField(max_length=50)
  desc = models.TextField()
  price = models.PositiveIntegerField()
  status = models.CharField(max_length=200)
  cover_url = models.URLField(null=True, default=None, max_length=500)
  teacher = models.ForeignKey(Teacher)
  resource = models.URLField(null=True, default=None, max_length=500)

'''课程样式
'''
class Course_Style(models.Model):
  name_x = models.FloatField(default=0)
  name_y = models.FloatField(default=0)
  font_size = models.FloatField(default=0)
  qrcode_x = models.FloatField(default=0)
  qrcode_y = models.FloatField(default=0)
  qrcode_size = models.FloatField(default=0)
  bg = models.URLField(null=True, default=None, max_length=500)


'''课程组
  name   : 组名
  avatar : 组头像
  desc   : 组简介
  link   : 组链接
'''
class Group(models.Model):
  name = models.CharField(max_length=50)
  avatar = models.TextField()
  desc = models.TextField()
  link = models.URLField(null=True, default=None, max_length=500)

'''系列
name        : 名称
term_length : 系列总长度
'''
class Series(models.Model):
  name = models.CharField(max_length=50)
  term_length = models.PositiveIntegerField()
  cover_url = models.URLField(null=True, default=None, max_length=500)
  unlock_num = models.PositiveIntegerField(default=1)
  create_time = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['-create_time']

'''课程
  info   : 基础信息
  group  : 所属学习群
  series : 所属系列
'''
class Course(models.Model):
  info = models.ForeignKey(Course_Info)
  group = models.ForeignKey(Group)
  series = models.ForeignKey(Series)
  is_selected = models.BooleanField(default=False)
  is_released = models.BooleanField(default=False)
  is_banner = models.BooleanField(default=False)
  recommend_courses = models.ManyToManyField('self', related_name='recommended_by')
  style = models.OneToOneField(Course_Style)
  create_time = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['-create_time']

'''收听记录
user        : 收听用户
course      : 收听课程
create_time : 收听时间
'''
AUDITION_TYPES = ((0, u'试听'), (1, u'收听'))
class Audition(models.Model):
  user = models.ForeignKey(User)
  course = models.ForeignKey(Course)
  create_time = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['-create_time']

'''访问记录
unlock      : 解锁状态
user        : 用户
course      : 课程
invited_by  : 邀请该用户的用户
create_time : 访问时间
'''
class Visit(models.Model):
  unlock = models.BooleanField(default=False)
  user = models.ForeignKey(User)
  course = models.ForeignKey(Course)
  invited_by = models.ForeignKey(User, related_name='invite_visit_set', null=True)
  access_time = models.DateTimeField(auto_now=True)
  invite_url = models.CharField(max_length=100, default=None, null=True)

  class Meta:
    unique_together = ('user', 'course')

'''订阅状态
user        : 订阅系列的用户
series      : 被订阅的系列
create_time : 订阅时间
'''
class Subscribe(models.Model):
  user = models.ForeignKey(User)
  series = models.ForeignKey(Series)
  create_time = models.DateTimeField(auto_now_add=True)

  class Meta:
    unique_together = ('user', 'series')

'''收藏状态
user        : 收藏用户
course      : 收藏课程
create_time : 收藏时间
'''
class Collect(models.Model):
  user = models.ForeignKey(User)
  course = models.ForeignKey(Course)
  create_time = models.DateTimeField(auto_now_add=True)

  class Meta:
    unique_together = ('user', 'course')

'''评论
user        : 用户
create_time : 时间
content     : 内容
course      : 所属课程
'''
class Comment(models.Model):
  user = models.ForeignKey(User)
  create_time = models.DateTimeField(auto_now_add=True)
  content = models.TextField()
  course = models.ForeignKey(Course)

  class Meta:
    ordering = ['-create_time']

# from http://www.pythonfan.org/thread-7614-1-1.html
class SAEFieldFile(FieldFile):
  def getUploadTo(self):
    return self.upload_to

  def save(self, name, content, save=True):
    name = self.field.generate_filename(self.instance, name)
    #for SAE
    s = sae.storage.Client()
    ob = sae.storage.Object(content._get_file().read())
    url = s.put('images', name, ob)
    self.name = name
    setattr(self.instance, self.field.name, self.name)

    # Update the filesize cache
    self._size = content.size
    self._committed = True

    # Save the object because it has changed, unless save is False
    #if save:
    #    self.instance.save()

class SAEImageFieldFile(ImageFile, SAEFieldFile):
  def delete(self, save=True):
    # Clear the image dimensions cache
    if hasattr(self, '_dimensions_cache'):
      del self._dimensions_cache
    super(ImageFieldFile, self).delete(save)

class ZGImageFieldFile(SAEImageFieldFile):
  def save(self, name, content, save=True):
    super(SAEImageFieldFile, self).save(name, content, save=True)

class ZGImageField(ImageField):
  attr_class = ZGImageFieldFile
  def __init__(self, verbose_name=None, name=None, width_field=None, height_field=None, **kwargs):
    super(ZGImageField, self).__init__(verbose_name, name, **kwargs)

############################
remote = not environ.get("APP_NAME", "")
if not remote:
  ImageField = ZGImageField
############################

class Image(models.Model):
  url = ImageField(upload_to = 'images/')