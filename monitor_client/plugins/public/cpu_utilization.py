# _*_coding:utf-8_*_
import psutil
value_dic = {}


def monitor():
    value_dic['status'] = 0
    cpu_percent = psutil.cpu_percent(interval=1)
    value_dic['utilization'] = cpu_percent
    return value_dic


if __name__ == '__main__':
    print(monitor())
