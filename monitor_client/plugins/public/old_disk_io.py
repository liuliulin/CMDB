# _*_coding:utf-8_*_
import psutil


def monitor():
    io = psutil.disk_io_counters(perdisk=True)
    key_info = psutil.disk_io_counters(perdisk=True).keys()
    value_dic = {}
    for k, v in io.items():
        value_dic[k] = {"read_bytes": io[k].read_bytes, "write_bytes": io[k].write_bytes}
    return key_info, value_dic


def io_rate():
    import time
    key_val, old_val = monitor()
    time.sleep(1)
    key_val, new_val = monitor()
    total_dic = {'status': 0, 'data': {}}
    dic_val = {}
    for key in key_val:
        dic_val[key] = {'read_bytes': (new_val[key]['read_bytes'] - old_val[key]['read_bytes'])/1024,
                        'write_bytes': (new_val[key]['write_bytes'] - old_val[key]['write_bytes'])/1024}
        total_dic['data'] = dic_val
    return total_dic

if __name__ == "__main__":
    print(io_rate())
