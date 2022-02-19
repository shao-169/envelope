from django.db import models


# Create your models here.
class user(models.Model):
    uid = models.AutoField('用户id', primary_key=True)
    amount = models.IntegerField('总金额', default=0)


class envelope(models.Model):
    envelope_id = models.AutoField('红包id', primary_key=True)
    uid = models.ForeignKey(user, on_delete=models.CASCADE)
    value = models.IntegerField('红包面值', default=0)
    opened = models.BooleanField('红包状态', default=False)
    snatch_time = models.BigIntegerField('获取时间', default=0)
