from subprocess import Popen, PIPE


def get_vm_disk_info():
    """
    通过fdisk -l 收集本机硬盘信息
    主机需要安装smartmontools
    :return: 'physical_disk_driver':
[{'capacity': '136.4', 'slot': '/dev/sda', 'manufacturer': 'Msft', 'model': 'Virtual Disk', 'iface_type': 'SCSI', 'sn': '0x00077fc6'}
    """
    raw = Popen('fdisk -l', stdout=PIPE, stderr=PIPE, shell=True)
    # 用换行符切片原数据，以列表保存
    raw_data = raw.stdout.read().decode().split("\n")
    raw_disk_list = []
    item_list = []
    # 用列表中的空元素切分新列表
    for line in raw_data:
        if len(line) == 0:
            raw_disk_list.append(item_list)
            item_list = []
        else:
            item_list.append(line)
    disk_list = []
    # 循环新列表
    for item in raw_disk_list:
        disk_item_dic = {}
        # 判断子列表的长度，长度为6则循环子列表
        if len(item) == 6:
            for i in item:
                # 查找以Disk开头的字符数据
                if i.startswith('Disk'):
                    # 以":"切分字符为列表
                    k, v = i.split(":")
                    # 取列表的中需要的数据，同时去掉空格
                    k = k.split()[1]
                    v = v.split()[0]
                    # 查找关键字符
                    if k == "identifier":
                        disk_item_dic["sn"] = v
                    if k.startswith("/"):
                        disk_item_dic['capacity'] = v
                        disk_item_dic['slot'] = k
                        # 结合 smartctl 查找硬盘的Vendor和Product
                        # 通过字符格式化定义命令
                        cmd1 = "smartctl -i %s | grep Vendor" % k
                        cmd2 = "smartctl -i %s | grep Product" % k
                        raw_1 = Popen(cmd1, stdout=PIPE, stderr=PIPE, shell=True)
                        raw_2 = Popen(cmd2, stdout=PIPE, stderr=PIPE, shell=True)
                        raw_vendor = raw_1.stdout.read().decode().split(":")
                        raw_model = raw_2.stdout.read().decode().split(":")
                        disk_item_dic['manufacturer'] = raw_vendor[1].strip()
                        disk_item_dic['model'] = raw_model[1].strip()
                        # 虚拟机直接写死硬盘接口类型
                        disk_item_dic['iface_type'] = "SCSI"
            # 去掉空的字典
            if len(disk_item_dic) > 0:
                disk_list.append(disk_item_dic)
    data = dict()
    data['physical_disk_driver'] = disk_list
    return data
