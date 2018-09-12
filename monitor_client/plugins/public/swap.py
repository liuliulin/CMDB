# _*_coding:utf-8_*_
import psutil
unit = {'b': 1, 'k': 2**10, 'm': 2**20, 'g': 2**30}
value_dic = {}


def monitor():
    swap = psutil.swap_memory()
    if swap:
        value_dic['status'] = 0
        value_dic["total"] = round(swap.total/unit['g'], 2)
        value_dic["used"] = round(swap.used/unit['g'], 2)
        value_dic["free"] = round(swap.free/unit['g'], 2)
        # value_dic["sin"] = round(swap.sin/unit['g'], 2)
        # value_dic["sout"] = round(swap.sout/unit['g'], 2)
        value_dic["percent"] = swap.percent
    return value_dic


if __name__ == '__main__':
    print(monitor())
