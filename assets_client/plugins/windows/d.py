import wmi


def get_disk_info():
    """
    硬盘信息
    :return:
    """
    data = []
    for disk in wmi.WMI().Win32_DiskDrive():  # 每块硬盘都要获取相应信息
        item_data = dict()
        iface_choices = ["SAS", "SCSI", "SATA", "SSD"]
        for iface in iface_choices:
            if iface in disk.Model:
                item_data['iface_type'] = iface
                break
        else:
            item_data['iface_type'] = 'unknown'
        item_data['slot'] = disk.Index
        item_data['sn'] = disk.SerialNumber
        item_data['model'] = disk.Model
        item_data['manufacturer'] = disk.Manufacturer
        item_data['capacity'] = int(int(disk.Size) / (1024 ** 3))
        data.append(item_data)

    return {'physical_disk_driver': data}
d = get_disk_info()
print(d)
