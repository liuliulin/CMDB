# _*_coding:utf-8_*_
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 程序文件所在的当前目录
from public import disk, disk_io, disk_iops, nic, swap, memory, cpu_utilization, net_conn


def get_disk_info():
    return disk.get_data()


def get_disk_io():
    return disk_io.get_io()


def get_disk_iops():
    return disk_iops.get_iops()


def get_nic_traffic():
    return nic.nic_traffic()


def get_swap():
    return swap.monitor()


def get_memory():
    return memory.monitor()


def get_cpu_utilization():
    return cpu_utilization.monitor()


def get_net_conn():
    return net_conn.net_conn()
