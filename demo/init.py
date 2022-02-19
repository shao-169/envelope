from . import generate_envelope
from .models import user, envelope
from django.conf import settings

import pymysql
import redis
import time
import random



class warmup:
    def redis_init(self):
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        r.flushdb()
        all_users = user.objects.all()
        for u in all_users:
            r.sadd("uid_set", 'u_' + str(u.uid))

        r.hset('global_variable', 'envelope_id', 0)
        r.hset('global_variable', 'sent_amount', 0)

        now = int(time.time())
        snatchTimeList = list()

        # 预先生成总红包个数的时间戳
        for i in range(settings.MAXENVELOPECOUNT):
            timestamp = random.randint(now, now + settings.CONTINUETIME)
            snatchTimeList.append(timestamp)
        snatchTimeList.sort()

        # 写入redis
        for timestamp in snatchTimeList:
            r.rpush('snatch_time_bucket', timestamp)

        # 预先生成红包
        for amount in generate_envelope.envelope_list(settings.MAXAMOUNT, settings.MAXENVELOPECOUNT):
            r.rpush('envelope_amount', amount)

    def mysql_init(self):
        # 清空user和envelope
        user.objects.all().delete()
        envelope.objects.all().delete()
        # 初始化num个用户
        num = settings.USERCOUNT
        user_list_to_insert = list()
        for i in range(1, num + 1):
            user_list_to_insert.append(user(uid=i, amount=0))
        user.objects.bulk_create(user_list_to_insert)
