#!/usr/bin/env python
import psutil


def monitor(frist_invoke=1):
    status = 0
    tmp = psutil.cpu_times()
    value_dic = {}
    value_dic= {
        'user': tmp.user,
        'nice': tmp.nice,
        'system': tmp.system,
        'iowait': tmp.iowait,
        'steal': tmp.steal,
        'idle': tmp.idle,
        'status': status
        }
    return value_dic


if __name__ == '__main__':
    print(monitor()) 

