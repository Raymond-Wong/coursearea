#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-04-13 01:12:10
# @Author  : Raymond Wong (549425036@qq.com)
# @Link    : http://github.com/Raymond-Wong

from coursearea.models import *
import string
import random

def random_str(length):
  return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))

def create_users(num):
  users = []
  for i in xrange(num):
    user = User(openid=random_str(30), session_key=random_str(30), credential=random_str(32), nickname=random_str(5))
    user.save()
    users.append(user)
    print 'user: %s, id: %d' % (user.nickname, i)
  return users

def create_courses(num):
  courses = []
  series = Series(name='series', term_length=random.randint(0, 100), cover_url='series cover url')
  group = Group(name='group', avatar='group avatar', desc='group description', link='group link')
  series.save()
  group.save()
  for i in xrange(num):
    teacher = Teacher(name=random_str(5), avatar=random_str(20), desc=random_str(50))
    teacher.save()
    info = Course_Info(name=random_str(5), price=random.randint(0, 500), desc=random_str(50), status=random_str(10), cover_url=random_str(20), teacher=teacher)
    info.save()
    course = Course(series=series, group=group, info=info, is_selected=random.choice([True, False]), is_banner=random.choice([True, False]))
    course.save()
    courses.append(course)
    print 'course: %s, id: %d' % (course.info.name, i)
  return courses

def create_visit(course, user, invited_by):
  try:
    visit = Visit(course=course, user=user, invited_by=invited_by, unlock=random.choice([True, False]))
    visit.save()
    tmp = None if invited_by is None else invited_by.nickname
    print '%s invite %s to visit %s, unlock status is %s' % (tmp, user.nickname, course.info.name, visit.unlock)
  except:
    pass

def create_collect(course, user):
  try:
    collect = Collect(course=course, user=user)
    collect.save()
    print '%s add %s to his collection' % (user.nickname, course.info.name)
  except:
    pass

def create_audition(course, user):
  audition = Audition(course=course, user=user)
  audition.save()
  print '%s listen to %s' % (user.nickname, course.info.name)

def create_comment(course, user):
  Comment(course=course, user=user, content=random_str(50)).save()
  print '%s comment to %s' % (user.nickname, course.info.name)

def create_recommend(courses):
  courses[0].recommend_courses.add(courses[1])
  courses[0].save()

def main():
  users = create_users(5)
  courses = create_courses(3)
  for i in xrange(10):
    course = random.choice(courses)
    create_visit(random.choice(courses), random.choice(users), random.choice(users + [None]))
    create_collect(random.choice(courses), random.choice(users))
    create_audition(random.choice(courses), random.choice(users))
    create_recommend(random.sample(courses, 2))
  for i in xrange(30):
    create_comment(random.choice(courses), random.choice(users))
