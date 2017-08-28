#coding:utf8
import random

def randstr(n, url_safe=False):
    '''
    生成指定长度随机字符串
    '''
    temp = ''
    for i in range(n):
        if url_safe:
            seed = random.randint(1,62)
            if seed in range(1,10):
                temp += random.randint(48,57).to_bytes(1,'little').decode()
            elif seed in range(10,37):
                temp += random.randint(97,122).to_bytes(1,'little').decode()
            else:
                temp += random.randint(65,90).to_bytes(1,'little').decode()
        else:
            temp += random.randint(33,126).to_bytes(1,'little').decode()
    return temp

