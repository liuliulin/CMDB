import psutil
res = {'status': 0, }


def net_conn(sport=None):
    status_temp = []
    status_list = ["LISTEN", "TIME_WAIT", "ESTABLISHED", "CLOSE_WAIT"]
    net_connections = psutil.net_connections()
    for key in net_connections:
        if sport is None:
            status_temp.append(key.status)
        else:
            if key.laddr[1] == sport:
                status_temp.append(key.status)
    for status in status_list:
        res[status] = status_temp.count(status)
    return res


if __name__ == "__main__":
    print(net_conn())
