import random

def envelope_list(money, num):
    """抢红包算法 - 线段切割法。传入参数：红包金额（单位：分）money、红包个数num"""
    if num <= 0:
        return None
    # 只有一个红包，直接返回红包总额
    if num == 1:
        return [money]

    # 从【1,money-1】取随机整数作为线段切割点。若该整数不在列表当中，插入该整数，直到获取够num-1的切割点
    envelope_split_list = []
    while len(envelope_split_list) < num - 1:
        single_envelope = random.randint(1, money - 1)
        if single_envelope not in envelope_split_list:
            envelope_split_list.append(single_envelope)

    # 对切割点升序排序，遍历列表时用当前切割点的值减上一个切割点的值
    # 第一个切割点与0相减
    # 这样得到num-1个红包金额
    envelope_split_list.sort()
    envelope_list = []
    last_value = 0
    for split_line_value in envelope_split_list:
        envelope_list.append(split_line_value - last_value)
        last_value = split_line_value

    envelope_list.append(money - last_value)
    return envelope_list