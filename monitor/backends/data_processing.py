# _*_coding:utf-8_*_
from monitor import models
from monitor.backends import redis_conn
import time, json, pickle
import operator


class DataHandler(object):
    def __init__(self, django_settings, connect_redis=True):
        self.django_settings = django_settings
        self.poll_interval = 3  # 3秒进行一次全局轮训
        self.config_update_interval = 120  # 设置120秒的更新间隔
        self.config_last_loading_time = time.time()  # 用当前时间作为最新的检测时间
        self.global_monitor_dic = {}  # 初始化一个全局字典用于存储所有监控主机
        self.exit_flag = False
        if connect_redis:
            self.redis = redis_conn.redis_conn(django_settings)

    def looping(self):
        """循环所有主机,生成需要监控的服务项, 并且检查有没有按时汇报数据(只做基本检测) """
        self.update_or_load_configs()  # 更新或生成全局的监控配置字典
        count = 0
        service_up = False  # 用于服务刚运行时不触发告警
        while not self.exit_flag:
            print("looping %s".center(50, '-') % count)
            count += 1
            # 等于或大于更新配置间隔则重新 更新全局的监控配置字典
            if time.time() - self.config_last_loading_time >= self.config_update_interval:
                print("\033[31;1m need update configs... \033[0m")
                self.update_or_load_configs()
                # print("monitor dic:", self.global_monitor_dic)

            if self.global_monitor_dic:
                for h, config_dic in self.global_monitor_dic.items():
                    print('handling host: \033[32;1m %s \033[0m' % h)
                    for service_id, val in config_dic['services'].items():  # 循环所有要监控的服务
                        # print(service_id,val)
                        service_obj, last_monitor_time = val
                        if time.time() - last_monitor_time >= service_obj.interval:  # reached the next monitor interval
                            print("\033[33;1m serivce [%s] has reached the monitor interval.\033[0m" % service_obj.name)
                            # 更新 last_monitor_time
                            self.global_monitor_dic[h]['services'][service_obj.id][1] = time.time()
                            self.data_point_validation(h, service_obj, service_up)  # 检测此服务最近的汇报数据
                        else:
                            # 下次监控时间
                            next_monitor_time = round(time.time() - last_monitor_time - service_obj.interval, 2)
                            print("service [%s] next monitor time is %s secs" % (service_obj.name, next_monitor_time))
                    # 更新主机的状态
                    if time.time() - self.global_monitor_dic[h]['status_last_check'] > 10:
                        # 检测 有没有这个机器的trigger,如果没有,把机器状态改成ok
                        trigger_redis_key = "host_%s_trigger*" % h.id
                        trigger_keys = self.redis.keys(trigger_redis_key)
                        # print('len trigger keys....', trigger_keys)
                        if len(trigger_keys) == 0:  # 没有trigger被触发,可以把状态改为ok了
                            h.status = 1
                            h.save()
            time.sleep(self.poll_interval)
            service_up = True

    def data_point_validation(self, host_obj, service_obj, service_up):
        """
        only do basic data validation here, alert if the client didn't report data to server in the configured time interval
        此处仅进行基本数据验证，如果客户端未在配置的时间间隔内向服务器报告数据，则发出警报
        :param h:
        :param service_obj:
        """
        service_redis_key = "StatusData_%s_%s_latest" % (host_obj.id, service_obj.name)
        # 拼出此服务在redis中存储的对应key
        latest_data_point = self.redis.lrange(service_redis_key, -1, -1)
        if latest_data_point:  # data list is not empty,
            latest_data_point = json.loads(latest_data_point[0].decode())
            latest_service_data, last_report_time = latest_data_point
            identifiable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_report_time))
            print("\033[41;1m latest data point \033[0m %s, %s" % (latest_service_data, identifiable_time))
            # 适当增加 监控时间间隔 (*2 这会去掉很多不必要的告警)
            monitor_interval = service_obj.interval * 2 + self.django_settings.REPORT_LATE_TOLERANCE_TIME
            print('timeout', monitor_interval)
            if time.time() - last_report_time > monitor_interval:
                service_up = service_up  # 服务器正常运行
                if service_up:
                    # 超过监控间隔但数据还没汇报过来,something wrong with client
                    no_data_secs = time.time() - last_report_time
                    msg = """%s client fault, %s service [%s]s did not receive data report (interval is [%s]) """ % \
                          (host_obj.ip_addr, service_obj.name, round(no_data_secs, 2), service_obj.interval)
                    self.trigger_notifier(host_obj=host_obj, trigger_id=None, positive_expressions=None, msg=msg)
                    print("\033[31;1m %s \033[0m" % msg)

                    if service_obj.name == "uptime":  # 监控主机存活的服务
                        host_obj.status = 3  # unreachable
                        host_obj.save()
                    else:
                        host_obj.status = 5  # problem
                        host_obj.save()

        else:  # no data at all
            print("\033[31;1m no data for serivce [%s] host[%s] at all..\033[0m" % (service_obj.name, host_obj.name))
            msg = '''no data for serivce [%s] host[%s] at all..''' % (service_obj.name, host_obj.name)
            self.trigger_notifier(host_obj=host_obj, trigger_id=None, positive_expressions=None, msg=msg)
            host_obj.status = 5  # problem
            host_obj.save()
        # print("triggers:", self.global_monitor_dic[host_obj]['triggers'])

    def load_service_data_and_calulating(self, host_obj, trigger_obj, redis_obj):
        """
        fetching out service data from redis db and calculate according to each serivce's trigger configuration
        从redis db中获取服务数据并根据每个服务的触发器配置进行计算
        :param redis_obj: # 从外面调用此函数时需传入redis_obj,以减少重复连接
        """
        # StatusData_1_LinuxCPU_10mins
        self.redis = redis_obj
        calc_sub_res_list = []  # 先把每个expression的结果算出来放在这个列表里,最后再统一计算这个列表
        positive_expressions = []
        expression_res_string = ''
        for expression in trigger_obj.triggerexpression_set.select_related().order_by('id'):
            # print("exp:", expression, expression.logic_type)
            # exp: LinuxCPU.idle lt(avg(5)) or
            expression_process_obj = ExpressionProcess(self, host_obj, expression)
            single_expression_res = expression_process_obj.process()  # 得到单条expression表达式的结果
            if single_expression_res:
                calc_sub_res_list.append(single_expression_res)
                if single_expression_res['expression_obj'].logic_type:  # 不是最后一条
                    expression_res_string += str(single_expression_res['calc_res']) + ' ' + \
                                             single_expression_res['expression_obj'].logic_type + ' '
                else:
                    expression_res_string += str(single_expression_res['calc_res']) + ' '
                # 把所有结果为True的expression提出来,报警时你得知道是谁出问题导致trigger触发了

                if single_expression_res['calc_res'] == True:
                    single_expression_res['expression_obj'] = single_expression_res['expression_obj'].id
                    # 要存到redis里,数据库对象转成id
                    positive_expressions.append(single_expression_res)
            # else: #single expression 不成立,随便加个东西,别让程序出错,这个地方我觉得是个bug
            #    expression_res_string += 'None'
        print("触发器返回的结果:", host_obj.ip_addr, trigger_obj.name, '=>', expression_res_string)
        if expression_res_string:
            # eval(expression_res_string)
            trigger_res = eval(expression_res_string)
            # print("whole trigger res:", trigger_res)
            if trigger_res:  # 终于走到这一步,该触发报警了
                # print("### trigger alert:", trigger_obj.severity, trigger_res)
                # print('temp_msg:', trigger_obj.name)
                tmp_dic = positive_expressions[0]

                msg = """hostname:%s[%s] has issue, %s[%s] service abnormal(return value: %s)""" % \
                      (host_obj.name, host_obj.ip_addr, trigger_obj.name, tmp_dic['service_item'],
                       tmp_dic['calc_res_val'])
                print('告警信息: ', msg)
                # print('触发告警的值: ', tmp_dic, type(tmp_dic))
                self.trigger_notifier(host_obj, trigger_obj.id, positive_expressions, msg=msg)
                # msg 需要专门分析后生成, 这里是临时写的

    def update_or_load_configs(self):
        """从Mysql DB 加载监控配置项,并且更新到全局字典中"""
        all_enabled_hosts = models.Host.objects.all()
        # 循环所有主机
        for h in all_enabled_hosts:
            if h not in self.global_monitor_dic:
                # 若主机不在全局字典中, 则初始化该主机的字典结构(新主机)
                self.global_monitor_dic[h] = {'services': {}, 'triggers': {}}
                '''self.global_monitor_dic ={
                    'h1':{'services': {'cpu': [cpu_obj,0], 'mem': [mem_obj, 0], },
                          'trigger': {t1: t1_obj, }}}'''
            # print(h.host_groups.select_related())
            service_list = []
            trigger_list = []
            # 因为主机组关联着服务模板,服务模板包含服务项目,所以需要循环取出来
            for group in h.host_groups.select_related():
                # print("group_templates:", group.templates.select_related())
                for template in group.templates.select_related():
                    # print("templates:", template.services.select_related())
                    # templates: < QuerySet[ < Service: LinuxCPU >, < Service: LinuxMemory >, ...] >
                    # print("triggers:", template.triggers.select_related())
                    # triggers: < QuerySet[ < Trigger: < serice: LinuxCPU, severity: Average >>] >
                    service_list.extend(template.services.select_related())
                    trigger_list.extend(template.triggers.select_related())
                # print('trigger_list:', trigger_list)
                """service_list: [ < Service: LinuxCPU >, < Service: LinuxMemory >, < Service: LinuxNetwork >]"""
                """trigger_list: [<Trigger: <serice:LinuxCPU, severity:Average>>,
                <Trigger: <serice:LinuxNetWork, severity:Average>>]"""
                for service in service_list:
                    if service.id not in self.global_monitor_dic[h]['services']:  # first loop
                        self.global_monitor_dic[h]['services'][service.id] = [service, 0]
                    else:
                        self.global_monitor_dic[h]['services'][service.id][0] = service
                for trigger in trigger_list:
                    # if not self.global_monitor_dic['triggers'][trigger.id]:
                    self.global_monitor_dic[h]['triggers'][trigger.id] = trigger
            # print(h.templates.select_related())
            # 直接从模板中查找服务项
            for template in h.templates.select_related():
                service_list.extend(template.services.select_related())
                trigger_list.extend(template.triggers.select_related())
            for service in service_list:
                if service.id not in self.global_monitor_dic[h]['services']:  # first loop
                    self.global_monitor_dic[h]['services'][service.id] = [service, 0]
                else:
                    self.global_monitor_dic[h]['services'][service.id][0] = service
            for trigger in trigger_list:
                self.global_monitor_dic[h]['triggers'][trigger.id] = trigger
            # print(self.global_monitor_dic[h])

            # 为全局字典增加服务最近的检查时间, 通过这个时间来确定是否需要更新主机状态
            self.global_monitor_dic[h].setdefault('status_last_check', time.time())
            # print('global_dic', self.global_monitor_dic)
            """ global_dic {<Host: devops>: {'services': {1: [<Service: LinuxCPU>, 0], 2: [<Service: LinuxMemory>, 0],
            3: [<Service: LinuxNetwork>, 0]}, 'status_last_check': 1532769595.9664707,
            'triggers': {1: <Trigger: <serice:LinuxCPU, severity:Average>>}}} """
        # 更新检测时间
        self.config_last_loading_time = time.time()
        return True

    def trigger_notifier(self, host_obj, trigger_id, positive_expressions, redis_obj=None, msg=None):
        """
        all the triggers alerts need to be published through here
        所有触发器警报都需要通过此处发布
        :param host_obj:
        :param trigger_id:
        :param positive_expressions: it's list, contains all the expression has True result
        :param redis_obj:
        """
        if redis_obj:  # 从外部调用 时才用的到,为了避免重复调用redis连接
            self.redis = redis_obj
        print("\033[32;1m going to send alert msg to trigger queue... \033[0m")
        # print('trigger_notifier argv:', host_obj, trigger_id, positive_expressions, redis_obj)
        """trigger_notifier argv: django_dev 1 [{'service_item': None, 'calc_res_val': 239876.0,
        'calc_res': True, 'expression_obj': 2}] None"""
        msg_dic = {'host_id': host_obj.id,
                   'trigger_id': trigger_id,
                   'positive_expressions': positive_expressions,
                   'msg': msg,
                   'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                   'start_time': time.time(),
                   'duration': None
                   }
        # 把异常发布到redis中
        self.redis.publish(self.django_settings.TRIGGER_CHAN, pickle.dumps(msg_dic))
        # print('msg_dic', msg_dic)
        # 先把之前的trigger加载回来,获取上次报警的时间,以统计故障持续时间
        trigger_redis_key = "host_%s_trigger_%s" % (host_obj.id, trigger_id)
        old_trigger_data = self.redis.get(trigger_redis_key)
        # print("old_trigger_data", old_trigger_data)
        """old_trigger_data b'{"host_id": 2, "duration": 5452, "msg": "LinuxCPU", "start_time": 1532738214.6515622,
        "positive_expressions": [{"service_item": null, "calc_res_val": 239876.0, "calc_res": true,
        "expression_obj": 2}], "time": "2018-07-28 10:07:47", "trigger_id": 1}'"""
        if old_trigger_data:
            old_trigger_data = old_trigger_data.decode()
            trigger_start_time = json.loads(old_trigger_data)['start_time']
            msg_dic['start_time'] = trigger_start_time
            msg_dic['duration'] = round(time.time() - trigger_start_time)
        # 同时在redis中纪录这个trigger , 前端页面展示时要统计trigger 个数
        self.redis.set(trigger_redis_key, json.dumps(msg_dic), 300)
        # 一个trigger 纪录 5分钟后会自动清除, 为了在前端统计trigger个数用的


class ExpressionProcess(object):
    """
    load data and calc it by different method
    """
    def __init__(self, main_ins, host_obj, expression_obj):
        """
        :param main_ins:   DataHandler 实例
        :param host_obj: 具体的host obj
        :param expression_obj:
        :return:
        计算单条表达式的结果
        """
        self.host_obj = host_obj
        self.expression_obj = expression_obj
        self.main_ins = main_ins
        self.service_redis_key = "StatusData_%s_%s_latest" % (host_obj.id, expression_obj.service.name)
        # 拼出此服务在redis中存储的对应key
        self.time_range = self.expression_obj.data_calc_args.split(',')[0]
        # 获取要从redis中取多长时间的数据,单位为minute
        # print("\033[31;1m------>%s\033[0m" % self.service_redis_key)
        # ------>StatusData_2_Memory_latest

    def load_data_from_redis(self):
        # load data from redis according to expression's configuration
        # 根据表达式的配置从redis加载数据
        time_in_sec = int(self.time_range) * 60  # 下面的+60是默认多取一分钟数据,宁多勿少,多出来的后面会去掉
        approximate_data_points = (time_in_sec + 60) / self.expression_obj.service.interval  # 获取一个大概要取的值
        # stop_loading_flag = False #循环去redis里一个点一个点的取数据,直到变成True
        # while not stop_loading_flag:
        # print("approximate dataset nums:", approximate_data_points, time_in_sec)
        # approximate dataset nums: 6.0 300
        data_range_raw = self.main_ins.redis.lrange(self.service_redis_key, -int(approximate_data_points), -1)
        # print("\033[31;1m------>%s\033[0m" % data_range)
        approximate_data_range = [json.loads(i.decode()) for i in data_range_raw]
        data_range = []  # 精确的需要的数据 列表
        for point in approximate_data_range:
            # print('bread point:', point)
            val, saving_time = point
            if time.time() - saving_time < time_in_sec:  # 代表数据有效
                data_range.append(point)
                # print("service index key:",self.expression_obj.service_index.key)
                # print(point)
                '''if val: #确保数据存在
                    if 'data' not in val:#代表这个dict没有sub_dict
                        print("\033[44;1m%s\033[0m" %val[self.expression_obj.service_index.key])
                        # 如何处理这些数据 呢? 是求avg(5), hit(5,3)....? 看来只能把数据集合交给不同的方法去处理了
                        # self.process(self.)
                        # data_range.append(
                    else: # 像disk , nic这种有多个item的数据
                        for k,v in val['data'].items():
                            print("\033[45;1m%s, %s\033[0m" %(k,v))
                            print("\033[45;1m%s, %s\033[0m" %(k,v[self.expression_obj.service_index.key]))
                '''
            # else:
            #    print("data is invalid")
        # print('data:', data_range)
        """data: [[{'nice': 16.37, 'status': 0, 'steal': 0.0, 'idle': 210236419.99,
        'iowait': 17469.26, 'user': 17978.84, 'system': 11187.41}, 1532740821.7636805],"""
        return data_range

    def process(self):
        """算出单条expression表达式的结果"""
        data_list = self.load_data_from_redis()
        print(data_list)
        # 已经按照用户的配置把数据 从redis里取出来了, 比如 最近5分钟,或10分钟的数据
        data_calc_func = getattr(self, 'get_%s' % self.expression_obj.data_calc_func)
        # data_calc_func = self.get_avg...
        single_expression_calc_res = data_calc_func(data_list)  # [True,43,None]
        # print("---res of single_expression_calc_res ", single_expression_calc_res)
        # ---res of single_expression_calc_res  [False, 93.42, None]
        if single_expression_calc_res:  # 确保上面的条件 有正确的返回
            res_dic = {
                'calc_res': single_expression_calc_res[0],
                'calc_res_val': single_expression_calc_res[1],
                'expression_obj': self.expression_obj,
                'service_item': single_expression_calc_res[2],
            }
            # print("\033[33;1m Calculation result of a single expression: %s\033[0m" % single_expression_calc_res)
            return res_dic
        else:
            return False

    def get_avg(self, data_set):
        """
        返回给定数据集的平均值
        :param data_set:
        """
        clean_data_list = []
        clean_data_dic = {}
        for point in data_set:
            val, save_time = point
            # print('---point:>', val)
            if val:
                if 'data' not in val:  # 没有子dict
                    clean_data_list.append(val[self.expression_obj.service_index.key])
                else:  # has sub dict
                    for k, v in val['data'].items():
                        if k not in clean_data_dic:
                            clean_data_dic[k] = []
                        clean_data_dic[k].append(v[self.expression_obj.service_index.key])

        if clean_data_list:
            clean_data_list = [float(i) for i in clean_data_list]
            # avg_res = 0 if sum(clean_data_list) == 0 else  sum(clean_data_list)/ len(clean_data_list)
            avg_res = sum(clean_data_list) / len(clean_data_list)
            # print("\033[46;1m----avg res:%s\033[0m" % avg_res)
            # ----avg res:97.656
            return [self.judge(avg_res), avg_res, None]
            # print('clean data list:', clean_data_list)
        elif clean_data_dic:
            for k, v in clean_data_dic.items():
                clean_v_list = [float(i) for i in v]
                avg_res = 0 if sum(clean_v_list) == 0 else sum(clean_v_list) / len(clean_v_list)
                # print("\033[46;1m-%s---avg res:%s\033[0m" % (k, avg_res))
                if self.expression_obj.specified_index_key:  # 监控了特定的指标,比如有多个网卡,但这里只特定监控eth0
                    if k == self.expression_obj.specified_index_key:  # 就是监控这个特定指标,match上了
                        # 在这里判断是否超越阈值
                        print("test res [%s] [%s] [%s]=%s") % (
                            avg_res,
                            self.expression_obj.operator_type,
                            self.expression_obj.threshold,
                            self.judge(avg_res), )
                        calc_res = self.judge(avg_res)
                        if calc_res:
                            return [calc_res, avg_res, k]  # 后面的循环不用走了,反正 已经成立了一个了
                else:  # 监控这个服务 的所有项, 比如一台机器的多个网卡, 任意一个超过了阈值,都 算是有问题的
                    calc_res = self.judge(avg_res)
                    if calc_res:
                        return [calc_res, avg_res, k]
                # print('specified monitor key:', self.expression_obj.specified_index_key)
                # print('clean data dic:', k, len(clean_v_list), clean_v_list)
            else:  # 能走到这一步,代表 上面的循环判段都未成立
                return [False, avg_res, k]
        else:  # 可能是由于最近这个服务 没有数据汇报过来,取到的数据为空,所以没办法判断阈值
            return [False, None, None]

    def judge(self, calculated_val):
        """
        determine whether the index has reached the alert benchmark
        :param calculated_val: #已经算好的结果,可能是avg(5) or ....
        """
        # expression_args = self.expression_obj.data_calc_args.split(',')
        # hit_times = expression_args[1] if len(expression_args)>1 else None
        # if hit_times:# 定义了超过阈值几次的条件
        calc_func = getattr(operator, self.expression_obj.operator_type)
        # calc_func = operator.eq....
        return calc_func(calculated_val, self.expression_obj.threshold)

    def get_hit(self, data_set):
        """
        return hit times  value of given data set
        :param data_set:
        :return:
        """
        pass

# 志不坚者智不达
