# _*_coding:utf-8_*_
import psutil, time

nic = ['lan', 'vpn', ]
# nic = psutil.net_io_counters(pernic=True).keys()
res = {'status': 0, 'data': {}}
tmp = dict()


def nic_traffic():
    for i in nic:
        raw1 = psutil.net_io_counters(pernic=True)
        t_out1 = raw1[i].bytes_sent
        t_in1 = raw1[i].bytes_recv
        time.sleep(1)
        raw2 = psutil.net_io_counters(pernic=True)
        t_out2 = raw2[i].bytes_sent
        t_in2 = raw2[i].bytes_recv
        t_out = round((t_out2 - t_out1)/1024, 2)
        t_in = round((t_in2 - t_in1)/1024, 2)
        sub_tmp = dict()
        sub_tmp['t_out_kb'] = t_out
        sub_tmp['t_in_kb'] = t_in
        tmp[i] = sub_tmp
    res['data'] = tmp
    return res

if __name__ == '__main__':
    print(nic_traffic())
