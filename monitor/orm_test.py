# _*_coding:utf8_*_
import os, json
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'cmdb.settings'
django.setup()

from monitor import models
from cmdb import settings
from monitor.backends import redis_conn
redis = redis_conn.redis_conn(settings)

host_obj = models.Host.objects.get(id=2)
print(host_obj)

# def get_services_data(cid=1, name='CPU'):
#     service_redis_key = "StatusData_%s_%s_latest" % (cid, name)
#     latest_data_point = redis.lrange(service_redis_key, -10, -1)
#     latest_data_point = [json.loads(i.decode()) for i in latest_data_point]
#     print(latest_data_point)
#     service_obj = models.Service.objects.get(name=name)
#     key_obj = service_obj.items.select_related()
#     res = {}
#     for key in key_obj:
#         data_list = []
#         data_dict = {}
#         key = str(key).split('.')[1]
#
#         for data in latest_data_point:
#             v, t_tmp = data
#             if 'data' not in v:
#                 data_list.append(v[key])
#             else:
#                 for k2, v2 in v['data'].items():
#                     if k2 not in data_dict:
#                         data_dict[k2] = []
#                     data_dict[k2].append(v2[key])
#             if data_list:
#                 res[key] = data_list
#             elif data_dict:
#                 res[key] = data_dict
#     return res
#
# if __name__ == '__main__':
#     print(get_services_data())
