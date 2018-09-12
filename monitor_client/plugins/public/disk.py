import psutil
res = {'status': 0, 'data': {}}
tmp = dict()


def get_data():
    label = psutil.disk_partitions()
    for key in label:
        name = key.mountpoint
        k = key.device.split('/')[-1]
        try:
            raw = psutil.disk_usage(name)
        except OSError:
            continue
        sub_tmp = dict()
        sub_tmp['total'] = round(raw.total/1024/1024/1024, 2)
        sub_tmp['used'] = round(raw.used/1024/1024/1024, 2)
        sub_tmp['free'] = round(raw.free/1024/1024/1024, 2)
        sub_tmp['percent'] = raw.percent
        tmp[k.split(':')[0]] = sub_tmp
    res['data'] = tmp
    return res


if __name__ == '__main__':
    print(get_data())
