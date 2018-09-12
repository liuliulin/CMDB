# _*_coding:utf-8_*_
import psutil, time
res = {'status': 0, 'data': {}}
tmp = dict()


def get_iops():
    keys = psutil.disk_io_counters(perdisk=True).keys()
    keys = [i for i in keys if i and not i == 'sr0']
    keys = [i for i in keys if i and not i == 'fd0']
    keys = [i for i in keys if i and not i == 'loop1']
    keys = [i for i in keys if i and not i == 'loop0']
    keys = [i for i in keys if i and not i == 'dm-0']
    keys = [i for i in keys if i and not i == 'dm-1']
    keys = [i for i in keys if i and not i == 'dm-2']

    for i in keys:
        raw_data = psutil.disk_io_counters(perdisk=True)
        count1 = raw_data[i].read_count + raw_data[i].write_count
        time.sleep(1)
        raw_data_new = psutil.disk_io_counters(perdisk=True)
        count2 = raw_data_new[i].read_count + raw_data_new[i].write_count
        total_count = count2 - count1
        sub_tmp = dict()
        sub_tmp['total_count'] = total_count
        tmp[i] = sub_tmp 
    res['data'] = tmp
    return res


if __name__ == "__main__":
    print(get_iops())

