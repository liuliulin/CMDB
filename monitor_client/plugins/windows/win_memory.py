# _*_coding:utf-8_*_
import psutil
value_dic = {}


def monitor():
    unit = {'b': 1, 'k': 2**10, 'm': 2**20, 'g': 2**30}
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    if mem:
        value_dic['status'] = 0
        value_dic["MemTotal"] = mem.total/unit['k']
        value_dic["MemUsage"] = mem.used/unit['k']
        # value_dic["Cached"] = mem.cached/unit['k']
        value_dic["MemUsage_p"] = mem.percent
        # value_dic["Buffers"] = mem.buffers/unit['k']
        value_dic["SwapTotal"] = swap.total/unit['k']
        value_dic["SwapUsage"] = swap.used/unit['k']
        value_dic["SwapFree"] = swap.free/unit['k']
        value_dic["SwapUsage_p"] = swap.percent
    return value_dic

if __name__ == '__main__':
    print(monitor())
