from rocketmq.client import Producer, Message
import json


class p_snatch:
    def __init__(self, envelope):
        self.producer = Producer('PID-snatch')
        self.producer.set_namesrv_addr('127.0.0.1:9000')  # rocketmq队列接口地址（服务器ip:port）
        self.producer.start()
        msg_body = {"id": "001", "name": "test_mq", "message": "abcdefg"}
        ss = json.dumps(msg_body).encode('utf-8')

        msg = Message('topic_name')  # topic名称
        msg.set_keys('xxxxxx')
        msg.set_tags('xxxxxx')
        msg.set_body(ss)  # message body

        retmq = producer.send_sync(msg)
        print(retmq.status, retmq.msg_id, retmq.offset)
        producer.shutdown()
