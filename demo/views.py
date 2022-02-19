import random
import time

from django.http import HttpResponse
from django.conf import settings
from django.forms import model_to_dict
import redis
from django_redis import get_redis_connection
import logging
import json
from .models import user, envelope
from .init import warmup
from .errorcode import errorcode
from .producer import p_snatch, p_open

# 日志实例化
logger = logging.getLogger(__name__)


def snatch_view(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
        uid = received_json_data['uid']
        u_uid = 'u_' + str(uid)
        logger.info("抢红包-->uid:%d" % (uid))
        # redis连接
        r = get_redis_connection('default')
        # 返回json
        result = {}

        # 如果uid不在uid_set中
        if not r.sismember('uid_set', u_uid):
            # 且u_id没有hash，说明id无效
            if not r.exists(u_uid):
                result = errorcode('INVALID_UID').get_status_code()
            else:
                result = errorcode('MAX_COUNT').get_status_code()
            return HttpResponse(json.dumps(result), content_type="application/json")

        # 在uid_set中
        if not random.random() > settings.PROBABILITY:
            result = errorcode('FAILURE_SNATCH').get_status_code()
            return HttpResponse(json.dumps(result), content_type="application/json")

        # 抢红包时间戳
        cur_time = int(time.time())
        # 列表最左侧时间戳
        timestamp = r.lpop('snatch_time_bucket')
        # 红包已经被抢光
        if not timestamp:
            result = errorcode('SOLD_OUT').get_status_code()
            return HttpResponse(json.dumps(result), content_type="application/json")

        if cur_time < int(timestamp):
            r.lpush('snatch_time_bucket', timestamp)
            result = errorcode('FAILURE_SNATCH').get_status_code()
            return HttpResponse(json.dumps(result), content_type="application/json")

        # 抢红包事务

        # 在管道中添加命令
        envelope_id = r.hincrby(name='global_variable', key='envelope_id', amount=1)
        envelope_amount = r.lpop('envelope_amount')
        r.hincrby(name='global_variable', key='sent_amount', amount=envelope_amount)

        # 生产者发送消息
        msg = {'envelope_id': envelope_id, 'uid_id': uid, 'value': envelope_amount, 'opened': 0,
               'snatch_time': cur_time}
        producer_snatch = p_snatch(msg)
        # 懒创建
        if not r.exists(u_uid):
            r.hset(name=u_uid, key="cur_count", value=0)
            r.hset(name=u_uid, key="cur_amount", value=0)
            r.hset(name=u_uid, key="finished_count", value=0)
            r.hset(name=u_uid, key="finished_amount", value=0)

        cur_count = r.hincrby(name=u_uid, key="cur_count", amount=1)

        if cur_count == settings.MAXCOUNT:
            r.srem('uid_set', u_uid)

        e_eid = 'e_' + str(envelope_id)
        r.hset(name=e_eid, key="uid", value=uid)
        r.hset(name=e_eid, key="value", value=envelope_amount)
        result = errorcode('SUCCESS').get_status_code()
        result['data'] = {
            'envelope_id': envelope_id,
            'max_count': settings.MAXCOUNT,
            'cur_count': cur_count
        }

        return HttpResponse(json.dumps(result), content_type="application/json")


def open_view(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
        uid = received_json_data['uid']
        envelope_id = received_json_data['envelope_id']
        logger.info("拆红包-->uid:%d envelope_id:%d " % (uid, envelope_id))
        u_uid = 'u_' + str(uid)
        e_eid = 'e_' + str(envelope_id)

        # redis连接
        r = get_redis_connection('default')
        # 返回json
        result = {}
        # 红包id不存在 或者 uid与eid不一致
        if not r.exists(e_eid) or (int(r.hget(e_eid, 'uid')) == uid) is not True:
            result = errorcode('ENVELOPE_NOT_EXIST').get_status_code()
            return HttpResponse(json.dumps(result), content_type="application/json")

        value = r.hget(e_eid, 'value')
        r.hincrby(name=u_uid, key="cur_amount", amount=value)
        r.delete(e_eid)
        # 生产者发送消息
        msg = {'envelope_id': envelope_id, 'uid_id': uid, 'value': value}
        producer_open = p_open(msg)
        result = errorcode('SUCCESS').get_status_code()
        result['data'] = {'value': value}
        return HttpResponse(json.dumps(result), content_type="application/json")


def get_wall_list_view(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
        uid = received_json_data['uid']
        u_uid = 'u_' + str(uid)
        logger.info("查询余额和红包列表-->uid:%d" % (uid))
        # redis连接
        r = get_redis_connection('default')
        # 返回json
        result = {}

        if not r.exists(u_uid):
            if not r.sismember('uid_set', u_uid):
                result = errorcode('INVALID_UID').get_status_code()
                result['data'] = {'amount': 0, 'envelop_list': {}}
                return HttpResponse(json.dumps(result), content_type="application/json")
            result = errorcode('SUCCESS').get_status_code()
            result['data'] = {'amount': 0, 'envelop_list': {}}
            return HttpResponse(json.dumps(result), content_type="application/json")

        cur_count = int(r.hget(u_uid, 'cur_count'))
        cur_amount = int(r.hget(u_uid, 'cur_amount'))
        finished_count = int(r.hget(u_uid, 'finished_count'))
        finished_amount = int(r.hget(u_uid, 'finished_amount'))

        if not (cur_amount == finished_amount and cur_amount == finished_amount):
            result = errorcode('SYSTEM_BUSY').get_status_code()
            result['data'] = {'amount': 0, 'envelop_list': {}}
            return HttpResponse(json.dumps(result), content_type="application/json")

        ue_id = 'ue_' + str(uid)
        if r.exists(ue_id) and finished_count + finished_amount == r.hget(ue_id, 'check'):
            return HttpResponse(r.hget(ue_id, 'cached_reslut'), content_type="application/json")

        res = envelope.objects.filter(uid_id=uid)

        json_list = []
        for row in res:
            json_dict = model_to_dict(row)
            json_list.append(json_dict)

        result = errorcode('SUCCESS').get_status_code()
        result['data']['amount'] = cur_amount
        result['data']['envelope_list'] = json_list

        # 写入缓存优化查询
        r.hset(ue_id, 'check', finished_amount + finished_count)
        r.hset(ue_id, 'cached_result', json.dumps(result))
        return HttpResponse(json.dumps(result), content_type="application/json")


def init_view(request):
    w = warmup()
    w.mysql_init()
    w.redis_init()

    return HttpResponse('已初始化')
