# _*_coding:utf-8_*_
import psutil, time
res = {'status': 0, 'data': {}}
tmp = dict()


def get_io():
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
        read1 = raw_data[i].read_bytes
        write1 = raw_data[i].write_bytes
        time.sleep(1)
        raw_data_new = psutil.disk_io_counters(perdisk=True)
        read2 = raw_data_new[i].read_bytes
        write2 = raw_data_new[i].write_bytes
        read = read2 - read1
        write = write2 - write1
        sub_tmp = dict()
        sub_tmp['read_kb'] = round(read/1024, 2)
        sub_tmp['write_kb'] = round(write/1024, 2)
        tmp[i] = sub_tmp
    res['data'] = tmp
    return res

if __name__ == "__main__":
    print(get_io())
