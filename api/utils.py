# -*- coding: utf-8 -*-
'''基础python模块'''
import logging
'''自定义模块'''
from coursearea.models import Visit, User

'''获取用户的朋友
'''
def get_friends(user):
  friends = []
  friends.extend(user.visit_set.select_related('invited_by'))
  friends.extend(user.invite_visit_set.select_related('user'))
  friends = map(lambda x:x.user, list(set(friends)))
  return friends