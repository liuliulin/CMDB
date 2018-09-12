import wmi


def get_nic_info():
    """
    网卡信息
    :return:
    """
    data = []
    for nic in wmi.WMI().Win32_NetworkAdapterConfiguration():
        if nic.MACAddress is not None:
            item_data = dict()
            item_data['mac'] = nic.MACAddress
            item_data['model'] = nic.Caption
            item_data['name'] = nic.Index
            if nic.IPAddress is not None:
                item_data['ip_address'] = nic.IPAddress[0]
                print(nic.IPAddress[0], type(nic.IPAddress[0]))
                item_data['net_mask'] = nic.IPSubnet
            else:
                item_data['ip_address'] = ''
                item_data['net_mask'] = ''
            data.append(item_data)
    # print(data, type(data))
    return {'nic': data}

n = get_nic_info()
print(n)
