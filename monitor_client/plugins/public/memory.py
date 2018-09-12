# _*_coding:utf-8_*_
import psutil
value_dic = {}
unit = {'b': 1, 'k': 2 ** 10, 'm': 2 ** 20, 'g': 2 ** 30}


def monitor():
    mem = psutil.virtual_memory()
    if mem:
        value_dic['status'] = 0
        value_dic["total"] = round(mem.total/unit['g'], 2)
        value_dic["used"] = round(mem.used/unit['g'], 2)
        value_dic["free"] = round(mem.free/unit['g'], 2)
        # value_dic["cached"] = round(mem.cached/unit['g'], 2)
        # value_dic["buffers"] = round(mem.buffers/unit['g'], 2)
        value_dic["percent"] = mem.percent
    return value_dic


if __name__ == '__main__':
    print(monitor())
