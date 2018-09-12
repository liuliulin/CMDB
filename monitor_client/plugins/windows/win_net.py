# _*_coding:utf-8_*_
try:
    import psutil
except ImportError:
    print('Error: psutil module not found!')
    exit()
eth = ["lan", "vpn", ]
# 获取各网卡发送、接收字节数


def monitor():
    net = psutil.net_io_counters(pernic=True)
    # key_info = psutil.net_io_counters(pernic=True).keys()
    key_info = eth
    value_dic = {}
    for key, val in net.items():
        for i in eth:
            if i == key:
                value_dic[key] = {"t_out": net[key].bytes_sent, "t_in": net[key].bytes_recv}
    return key_info, value_dic


# 计算每秒速率
def net_rate():
    import time
    key_val, old_val = monitor()
    time.sleep(1)
    key_val, new_val = monitor()
    total_dic = {'status': 0, 'data': {}}
    dic_val = {}

    for key in key_val:
        dic_val[key] = {'t_in': (new_val[key]['t_in'] - old_val[key]['t_in'])/1024,
                        't_out': (new_val[key]['t_out'] - old_val[key]['t_out'])/1024}
        total_dic['data'] = dic_val
    return total_dic

if __name__ == '__main__':
    print(net_rate())
