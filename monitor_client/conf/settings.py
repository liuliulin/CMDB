# _*_coding:utf-8_*_

configs = {
    'HostID': 4,
    "Server": "10.148.52.200",
    "ServerPort": 80,
    "urls": {
        'get_configs': ['api/client/config', 'get'],  # acquire all the services will be monitored
        'service_report': ['api/client/service/report/', 'post'],
    },
    'RequestTimeout': 30,
    'ConfigUpdateInterval': 300,  # 5 min as default
}
