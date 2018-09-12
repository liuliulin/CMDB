from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from cmdb import settings
from monitor.serializer import ClientHandler, get_host_triggers
from monitor.backends import redis_conn
from monitor.backends import data_optimization
from monitor import models
from monitor.backends import data_processing
from monitor import serializer
from monitor import graphs
import json, time

REDIS_OBJ = redis_conn.redis_conn(settings)

# Create your views here.


def client_configs(request, client_id):
    print('ID', client_id, "\033[44;1m 获取了监控服务配置项 \033[0m")
    config_obj = ClientHandler(client_id)
    config = config_obj.fetch_configs()
    if config:
        return HttpResponse(json.dumps(config))


@csrf_exempt
def service_data_report(request):
    if request.method == 'POST':
        # print("Receive data ->", request.POST)
        try:
            # print('host=%s, service=%s' % (request.POST.get('client_id'), request.POST.get('service_name')))
            data = json.loads(request.POST['data'])
            client_id = request.POST.get('client_id')
            service_name = request.POST.get('service_name')
            # 数据优化及存储
            data_saveing_obj = data_optimization.DataStore(client_id, service_name, data, REDIS_OBJ)
            data_saveing_obj.process_and_save()
            # redis_key_format = "StatusData_%s_%s_latest" % (client_id, service_name)
            # data['report_time'] = time.time()
            # REDIS_OBJ.lpush(redis_key_format, json.dumps(data))

            # 在这里同时触发监控(在这里触发的好处是什么呢？)
            # 获取目标主机
            host_obj = models.Host.objects.get(id=client_id)
            # 获取触发器
            service_triggers = get_host_triggers(host_obj)
            # {<Trigger: <serice:LinuxCPU, severity:Average>>}
            trigger_handler = data_processing.DataHandler(settings, connect_redis=False)

            for trigger in service_triggers:
                trigger_handler.load_service_data_and_calulating(host_obj, trigger, REDIS_OBJ)
            print("service trigger::", service_triggers)

            # 更新主机存活状态
            host_alive_key = "HostAliveFlag_%s" % client_id
            REDIS_OBJ.set(host_alive_key, time.time())
        except IndexError as e:
            print('----->err:', e)

    return HttpResponse(json.dumps("---report success---"))


def hosts(request):
    host_list = models.Host.objects.all()
    return render(request, 'monitor/host.html', {'host_list': host_list})


def host_detail(request, host_id):
    host_obj = models.Host.objects.get(id=host_id)
    return render(request, 'monitor/host_detail.html', {'host_obj': host_obj})


def graphs_generator(request):
    graph_generator = graphs.GraphGenerator2(request, REDIS_OBJ)
    graphs_data = graph_generator.get_host_graph()
    print("graphs_data", graphs_data)
    return HttpResponse(json.dumps(graphs_data))


def hosts_status(request):
    hosts_data_serializer = serializer.StatusSerializer(request, REDIS_OBJ)
    hosts_data = hosts_data_serializer.by_hosts()
    return HttpResponse(json.dumps(hosts_data))


def trigger_list(request):
    host_id = request.GET.get("by_host_id")
    host_obj = models.Host.objects.get(id=host_id)
    alert_list = host_obj.eventlog_set.all().order_by('-date')
    return render(request, 'monitor/trigger_list.html', locals())
