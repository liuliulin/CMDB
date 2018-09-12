#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from subprocess import Popen, PIPE


def collect():
    filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
    raw_data = {}
    for key in filter_keys:
        try:
            res = Popen("sudo dmidecode -t system|grep '%s'" % key, stdout=PIPE, shell=True)
            result = res.stdout.read().decode()
            data_list = result.split(':')
            if len(data_list) > 1:
                raw_data[key] = data_list[1].strip()
            else:
                raw_data[key] = -1
        except Exception as e:
            print(e)
            raw_data[key] = -2
    data = dict()
    data['asset_type'] = 'server'
    data['manufacturer'] = raw_data['Manufacturer']
    data['sn'] = raw_data['Serial Number']
    data['model'] = raw_data['Product Name']
    data['uuid'] = raw_data['UUID']
    data['wake_up_type'] = raw_data['Wake-up Type']

    data.update(get_os_info())
    data.update(get_cpu_info())
    data.update(get_ram_info())
    data.update(get_nic_info())
    # data.update(get_disk_info())
    p = Popen('dmidecode -s system-product-name', stdout=PIPE, stderr=PIPE, shell=True)
    host_type = p.stdout.read().decode().split("\n")
    if host_type[0] == "Virtual Machine":
        data.update(get_vm_disk_info())
    if host_type[0] == "VMware Virtual Platform":
        data.update(get_vm_disk_info())
    else:
        data.update(get_hp_disk_info())

    return data


def get_os_info():
    """
    获取操作系统信息
    :return:
    """
    distributor = Popen("lsb_release -a|grep 'Distributor ID'", stdout=PIPE, shell=True)
    distributor = distributor.stdout.read().decode().split(":")
    release = Popen("lsb_release -a|grep 'Description'", stdout=PIPE, shell=True)
    release = release.stdout.read().decode().split(":")
    data_dic = {
        "os_distribution": distributor[1].strip() if len(distributor) > 1 else "",
        "os_release": release[1].strip() if len(release) > 1 else "",
        "os_type": "Linux",
    }
    return data_dic


def get_cpu_info():
    """
    获取cpu信息
    :return:
    """
    base_cmd = 'lscpu'
    arg1 = "sed 's/  */ /g'"
    arg2 = "cut -d ':' -f 2"
    data = {}
    raw_data = {
        'cpu_model': "%s | grep 'Model name' | %s|%s" % (base_cmd, arg1, arg2),
        'cpu_count': "%s | grep 'Socket(s)' | %s|%s" % (base_cmd, arg1, arg2),
        'cpu_core_count': "%s | grep '^CPU(s)'|%s|%s" % (base_cmd, arg1, arg2),
    }
    for key, cmd in raw_data.items():
        try:
            cmd_res = Popen(cmd, stdout=PIPE, shell=True)
            data[key] = cmd_res.stdout.read().decode().strip()
        except ValueError as e:
            print(e)
            data[key] = ""
    return data


def get_ram_info():
    """
    获取内存信息
    :return:
    """
    raw_data = Popen("sudo dmidecode -t memory", stdout=PIPE, shell=True)
    raw_list = raw_data.stdout.read().decode().split("\n")
    raw_ram_list = []
    item_list = []
    for line in raw_list:
        if line.startswith("Memory Device"):
            raw_ram_list.append(item_list)
            item_list = []
        else:
            item_list.append(line.strip())
    ram_list = []
    for item in raw_ram_list:
        item_ram_size = 0
        ram_item_to_dic = {}
        for i in item:
            data = i.split(":")
            if len(data) == 2:
                key, v = data
                if key == 'Size':
                    if v.strip() != "No Module Installed":
                        ram_item_to_dic['capacity'] = v.split()[0].strip()
                        # item_ram_size = round(v.split()[0])
                        item_ram_size = v.split()[0]
                    else:
                        ram_item_to_dic['capacity'] = 0
                if key == 'Type':
                    ram_item_to_dic['model'] = v.strip()
                if key == 'Manufacturer':
                    ram_item_to_dic['manufacturer'] = v.strip()
                if key == 'Serial Number':
                    ram_item_to_dic['sn'] = v.strip()
                if key == 'Asset Tag':
                    ram_item_to_dic['asset_tag'] = v.strip()
                if key == 'Locator':
                    ram_item_to_dic['slot'] = v.strip()
        if item_ram_size == 0:
            pass
        else:
            ram_list.append(ram_item_to_dic)
    raw_total_size = Popen("cat /proc/meminfo|grep MemTotal ", stdout=PIPE, shell=True)
    raw_total_size = raw_total_size.stdout.read().decode().split(":")
    ram_data = {'ram': ram_list}
    if len(raw_total_size) == 2:
        total_gb_size = int(raw_total_size[1].split()[0]) / 1024**2
        ram_data['ram_size'] = total_gb_size
    return ram_data


def get_nic_info():
    """
    通过Linux 通用的ip add命令获取本机nic信息
    :return:
    """
    p = Popen('ip add', stdout=PIPE, shell=True)
    # 返回标准输出和错误输出
    stdout, stderr = p.communicate()
    # 用换行符切片原数据，同时去掉空数据
    raw_data = [i for i in stdout.decode().split('\n') if i]
    lines = []
    new_line = ''
    for line in raw_data:
        # 判断循环项的首个元素，去掉空格后是否为真
        if line[0].strip():
            # 将拼接的字符追加到列表中
            lines.append(new_line)
            # 拼接字符加上换行符
            new_line = line + '\n'
        else:
            # 拼接字符加上换行符
            new_line += line + '\n'
    lines.append(new_line)
    # 去掉列表中的空元素
    lines = [i for i in lines if i and not len(i) == 0]
    # 去掉 lo 网卡的信息
    lines = [i for i in lines if i and not i.split(":")[1].strip() == "lo"]
    dic = {}
    nic = []
    # 循环列表，获取数据
    for i in lines:
        devname = i.split('\n')[0].split(":")[1].strip()
        mac = i.split('\n')[1].split()[1]
        if len(i.split('\n')[2]) == 0:
            addr = ''
            netmask = ''
        else:
            ip = i.split('\n')[2].split()[1]
            addr, netmask = ip.split("/")
        dic["name"] = devname
        dic["mac"] = mac
        dic["ip_address"] = addr
        dic["net_mask"] = (netmask,)
        dic["model"] = "unknown"
        nic.append(dic)
        dic = {}
    data = dict()
    data["nic"] = nic
    return data


def get_hp_disk_info():
    """
    HP服务器可安以装 hpacucli 软件包获取硬盘信息
    :return:
    """
    # 获取主机第一个阵列卡上所以物理硬盘的详细信息
    p = Popen("hpacucli ctrl slot=0 pd all show detail", stdout=PIPE, shell=True)
    # 用换行符切片原数据，以列表保存
    raw_list = p.stdout.read().decode().split("\n")
    disk_dic = {}
    raw_disk_list = []
    item_list = []
    # 用列表中的空元素切分新列表
    for line in raw_list:
        line = line.strip()
        if len(line) == 0:
            raw_disk_list.append(item_list)
            item_list = []
        else:
            item_list.append(line)
    disk_list = []
    # 循环新列表
    for item in raw_disk_list:
        ram_item_to_dic = {}
        for i in item:
            # 以":"切分字符为列表，指定一个冒号为切分原则
            data = i.split(":", 1)
            # 判断切分后的列表长度为2，则开始循环
            if len(data) == 2:
                key, v = data
                # 查找关键字符，获取需要的数据
                if key == 'Size':
                    ram_item_to_dic['capacity'] = v.split()[0].strip()
                if key == 'Serial Number':
                    ram_item_to_dic['sn'] = v.strip()
                if key == 'Interface Type':
                    ram_item_to_dic['iface_type'] = v.strip()
                if key == 'Bay':
                    ram_item_to_dic['slot'] = v.strip()
                if key == 'Model':
                    ram_item_to_dic['manufacturer'] = v.split()[0].strip()
                    ram_item_to_dic['model'] = v.split()[1].strip()
        # 判断字典是否为空
        if len(ram_item_to_dic) != 0:
            disk_list.append(ram_item_to_dic)
    disk_dic["physical_disk_driver"] = disk_list
    return disk_dic


def get_vm_disk_info():
    raw = Popen('fdisk -l', stdout=PIPE, stderr=PIPE, shell=True)
    raw_data = raw.stdout.read().decode().split("\n")
    raw_disk_list = []
    item_list = []
    for line in raw_data:
        if len(line) == 0:
            raw_disk_list.append(item_list)
            item_list = []
        else:
            item_list.append(line)
    disk_list = []
    for item in raw_disk_list:
        disk_item_dic = {}
        if len(item) == 6:
            for i in item:
                if i.startswith('Disk'):
                    k, v = i.split(":")
                    k = k.split()[1]
                    v = v.split()[0]
                    if k == "identifier":
                        disk_item_dic["sn"] = v
                    if k.startswith("/"):
                        disk_item_dic['capacity'] = v
                        disk_item_dic['slot'] = k
                        cmd1 = "smartctl -i %s | grep Vendor" % k
                        cmd2 = "smartctl -i %s | grep Product" % k
                        raw_1 = Popen(cmd1, stdout=PIPE, stderr=PIPE, shell=True)
                        raw_2 = Popen(cmd2, stdout=PIPE, stderr=PIPE, shell=True)
                        raw_vendor = raw_1.stdout.read().decode().split(":")
                        raw_model = raw_2.stdout.read().decode().split(":")
                        disk_item_dic['manufacturer'] = raw_vendor[1].strip()
                        disk_item_dic['model'] = raw_model[1].strip()
                        disk_item_dic['iface_type'] = "SCSI"
            if len(disk_item_dic) > 0:
                disk_list.append(disk_item_dic)
    data = dict()
    data['physical_disk_driver'] = disk_list
    return data


if __name__ == "__main__":
    # 收集信息功能测试
    d = collect()
    print(d)
