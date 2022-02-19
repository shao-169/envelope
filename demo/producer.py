from rocketmq.client import Producer, Message
import logging
import json


class p_snatch:
    def __init__(self, snatch_msg):
        self.producer = Producer('PID-snatch')
        self.producer.set_namesrv_addr('localhost:9876')  # rocketmq队列接口地址（服务器ip:port）
        self.producer.start()
        msg_body = snatch_msg
        data = json.dumps(msg_body, ensure_ascii=False).encode('utf-8')
        self.logger = logging.getLogger(__name__)

        msg = Message('snatch')  # topic名称
        msg.set_body(data)  # message body
        ret = self.producer.send_sync(msg)
        self.logger.info(ret)
        self.producer.shutdown()
        print(snatch_msg)


class p_open:
    def __init__(self, open_msg):
        self.producer = Producer('PID-open')
        self.producer.set_namesrv_addr('localhost:9876')  # rocketmq队列接口地址（服务器ip:port）
        self.producer.start()
        msg_body = open_msg
        data = json.dumps(msg_body, ensure_ascii=False).encode('utf-8')
        self.logger = logging.getLogger(__name__)

        msg = Message('open')  # topic名称
        msg.set_body(data)  # message body
        ret = self.producer.send_sync(msg)
        self.logger.info(ret)
        self.producer.shutdown()


