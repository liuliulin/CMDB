from conf import settings
from plugins import plugin_api
from urllib import request, parse
import time, json, threading


class ClientHandle(object):
    def __init__(self):
        self.monitored_services = {}
        self.exit_flag = False

    def load_latest_configs(self):
        request_type = settings.configs['urls']['get_configs'][1]
        url = "%s/%s" % (settings.configs['urls']['get_configs'][0], settings.configs['HostID'])
        latest_configs = self.url_request(request_type, url)
        if latest_configs:
            # latest_configs = json.loads(latest_configs)  # for python2
            latest_configs = latest_configs.decode()
            # print(latest_configs, type(latest_configs))
            latest_configs = json.loads(latest_configs)
            self.monitored_services.update(latest_configs)
            # print(self.monitored_services)

    def forever_run(self):
        # exit_flag = False
        config_last_update_time = 0
        while not self.exit_flag:
            if time.time() - config_last_update_time > settings.configs['ConfigUpdateInterval']:
                self.load_latest_configs()
                print("Loaded latest config A:", self.monitored_services)
                config_last_update_time = time.time()
                # start to monitor services
            if self.monitored_services:
                for service_name, val in self.monitored_services['services'].items():
                    if len(val) == 2:  # means it's the first time to monitor
                        self.monitored_services['services'][service_name].append(0)
                    monitor_interval = val[1]
                    last_invoke_time = val[2]
                    # print("Loaded latest config B:", self.monitored_services)

                    if time.time() - last_invoke_time > monitor_interval:  # needs to run the plugin
                        # print(last_invoke_time, time.time())
                        self.monitored_services['services'][service_name][2] = time.time()
                        # start a new thread to call each monitor plugin
                        t = threading.Thread(target=self.invoke_plugin, args=(service_name, val))
                        t.start()
                        print("Going to monitor [%s]" % service_name)
                    else:
                        print("Going to monitor [%s] in [%s] secs" %
                              (service_name, round(monitor_interval - (time.time()-last_invoke_time), 2)))
                time.sleep(1)
            else:
                time.sleep(3)
                self.load_latest_configs()
                print("Loaded latest config B:", self.monitored_services)
                config_last_update_time = time.time()

    def invoke_plugin(self, service_name, val):
        plugin_name = val[0]
        if hasattr(plugin_api, plugin_name):
            func = getattr(plugin_api, plugin_name)
            plugin_callback = func()
            # print("--monitor result:", plugin_callback)
            report_data = {
                'client_id': settings.configs['HostID'],
                'service_name': service_name,
                'data': json.dumps(plugin_callback)
            }
            request_action = settings.configs['urls']['service_report'][1]
            request_url = settings.configs['urls']['service_report'][0]
            # report_data = json.dumps(report_data)
            print('---report data:', report_data, type(report_data))
            self.url_request(request_action, request_url, params=report_data)
        else:
            print("\033[31;1mCannot find plugin names [%s] in plugin_api\033[0m" % plugin_name)
        print('--plugin:', val)

    def url_request(self, action, url, **extra_data):
        abs_url = "http://%s:%s/%s" % (settings.configs['Server'],
                                       settings.configs["ServerPort"], url)
        if action in ('get', 'GET'):
            print(abs_url, extra_data)
            try:
                req = request.Request(abs_url)
                req_data = request.urlopen(req, timeout=settings.configs['RequestTimeout'])
                callback = req_data.read()
                return callback
            except request.URLError:
                print('ConnectionError --please wait 3 seconds')
                time.sleep(3)

        elif action in ('post', 'POST'):
            # print(abs_url,extra_data['params'])
            try:
                data_encode = parse.urlencode(extra_data['params']).encode(encoding='UTF8')
                req = request.Request(url=abs_url, data=data_encode)
                res_data = request.urlopen(req, timeout=settings.configs['RequestTimeout'])
                callback = res_data.read().decode(encoding='UTF8')
                callback = json.loads(callback)
                print("\033[31;1m[%s]:[%s]\033[0m response:\n%s" % (action, abs_url, callback))
                return callback
            except Exception:
                print('report data fail, connection server exception')

    def stop_client(self):
        self.exit_flag = True
