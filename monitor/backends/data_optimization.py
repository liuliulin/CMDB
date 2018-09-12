# _*_coding:utf-8_*_
from cmdb import settings
import time, json, copy


class DataStore(object):
    """
      处理客户端报告的服务数据，做一些数据优化并将其保存到redis DB中
    """
    def __init__(self, client_id, service_name, data, redis_obj):
        """
        :param client_id:  eg: 2
        :param service_name: eg : LinuxCPU
        :param data: the client reported service clean data ,
        """
        self.client_id = client_id
        self.service_name = service_name
        self.data = data
        self.redis_conn_obj = redis_obj
        # self.process_and_save()

    def get_data_slice(self, lastest_data_key, optimization_interval):
        """
        以优化间隔去redis取数据,例如：600，表示从redis获取最新的10分钟数据
        """
        all_real_data = self.redis_conn_obj.lrange(lastest_data_key, 1, -1)
        # print("get data range of:", lastest_data_key, optimization_interval)
        # get data range of: StatusData_2_LinuxMemory_latest 600
        # print("get data range of:", all_real_data[-1])
        """get datarange of: b'[{"MemFree": "209464", "SwapUsage_p": "3", "status": 0, "Buffers": "952",
        "SwapFree": "8152824", 'b'"MemTotal": "8004920", "MemUsage_p": "46", "MemUsage": 3726496,
        "SwapUsage": 239876, ' b'"SwapTotal": "8392700", "Cached": "4068008"}, 1532689554.7223735]'"""
        data_set = []
        for item in all_real_data:
            # print('json.loads:', json.loads(item.decode()))
            """
            json.loads: [
                {'system': 10576.03, 'steal': 0.0, 'user': 16855.01, 'status': 0, 'nice': 16.22, 'iowait': 17161.81,
                 'idle': 206531170.46}, 1532663569.5631073]
            """
            data = json.loads(item.decode())
            if len(data) == 2:
                # print("real data item:", data[0], data[1])
                """
                real data item: {'iowait': '0.00', 'steal': '0.00', 'user': '1.67', 'status': 0,
                'system': '0.63', 'idle': '97.71', 'nice': '0.00'} 1532688836.647302
                """
                service_data, last_save_time = data
                # print('time:',time.time(), time.time() - last_save_time, optimization_interval)
                if time.time() - last_save_time <= optimization_interval:  # filter this data point out
                    # print(time.time() - last_save_time, optimization_interval)
                    data_set.append(data)
                else:
                    pass
        # print('data set:--->', data_set)
        """
        data set:---> [[{'data': {'eth0': {'t_in': 5.208984375, 't_out': 0.55078125}}, 'status': 0},
        1532690131.4433599],[{'data': {'eth0': {'t_in': 7.24609375, 't_out': 3.4208984375}}, 'status': 0},
        1532690161.4870782], ...]
        """
        return data_set

    def process_and_save(self):
        """
        处理数据并保存到redis
        """
        print('ID:', self.client_id, 'Service:', self.service_name, "\033[34;1m 更新了数据 \033[0m")
        # print(self.client_id, self.service_name, self.data)
        if self.data['status'] == 0:  # service data is valid
            for key, data_series_val in settings.STATUS_DATA_OPTIMIZATION.items():
                data_series_optimize_interval, max_data_point = data_series_val
                # 拼接存入redis中数据的KEY
                # eg: StatusData_1_WinCPU_latest
                data_series_key_in_redis = "StatusData_%s_%s_%s" % (self.client_id, self.service_name, key)
                # print(data_series_key_in_redis, data_series_val)
                """
                StatusData_2_LinuxNetwork_latest[0, 600]
                StatusData_2_LinuxNetwork_10mins[600, 600]
                StatusData_2_LinuxNetwork_30mins[1800, 600]
                StatusData_2_LinuxNetwork_60mins[3600, 600]
                """
                # 用上面的KEY,从redis中取一条最新的数据
                last_point_from_redis = self.redis_conn_obj.lrange(data_series_key_in_redis, -1, -1)
                if not last_point_from_redis:  # this key is not exist in redis
                    # 如果KEY不存在,则在redis中初始化一个新的KEY，并存入当前的时间戳
                    self.redis_conn_obj.rpush(data_series_key_in_redis, json.dumps([None, time.time()]))
                # 判断数据序列优化间隔是否等于 0
                if data_series_optimize_interval == 0:
                    # 只有最新的数据不需要优化
                    self.redis_conn_obj.rpush(data_series_key_in_redis, json.dumps([self.data, time.time()]))

                else:  # 需要优化的数据
                    last_point_data, last_point_save_time =  \
                        json.loads(self.redis_conn_obj.lrange(data_series_key_in_redis, -1, -1)[0].decode())

                    if time.time() - last_point_save_time >= data_series_optimize_interval:
                        # 大于或等于数据优化间隔时需要更新数据
                        # 从最新的数据中取数据来优化(拼接需要数据优化的KEY)
                        lastest_data_key_in_redis = "StatusData_%s_%s_latest" % (self.client_id, self.service_name)
                        print("calculating data for key:\033[31;1m%s\033[0m" % data_series_key_in_redis)
                        """calculating data for key:StatusData_1_LinuxCPU_10mins"""
                        # 取最近n分钟的数据，存入data_set里(n 等于数据优化间隔)
                        data_set = self.get_data_slice(lastest_data_key_in_redis, data_series_optimize_interval)
                        # print('---len data_set :', len(data_set))
                        """---len data_set : 10"""
                        if len(data_set) > 0:
                            # 接下来拿这个data_set交给下面这个方法,让它算出优化的结果来
                            optimized_data = self.get_optimized_data(data_series_key_in_redis, data_set)
                            if optimized_data:
                                self.save_optimized_data(data_series_key_in_redis, optimized_data)
                # 同时确保数据在redis中的存储数量不超过settings中指定的值
                if self.redis_conn_obj.llen(data_series_key_in_redis) >= max_data_point:
                    self.redis_conn_obj.lpop(data_series_key_in_redis)  # 删除最旧的一个数据
                # self.redis_conn_obj.ltrim(data_series_key_in_redis,0,data_series_val[1])
        else:
            print("report data is invalid::", self.data)
            raise ValueError

    def save_optimized_data(self, data_series_key_in_redis, optimized_data):
        """
        保存优化后的数据
        """
        self.redis_conn_obj.rpush(data_series_key_in_redis, json.dumps([optimized_data, time.time()]))

    def get_optimized_data(self, data_set_key, raw_service_data):
        """
        calculate out ava,max,min,mid value from raw service data set
        :param data_set_key: where the optimized data needed to save to in redis db
        :param raw_service_data: raw service data data list
        """
        # index_init =[avg,max,min,mid]
        # print("get_optimized_data:", raw_service_data[0])
        service_data_keys = raw_service_data[0][0].keys()  # [idle, system]
        first_service_data_point = raw_service_data[0][0]  # use this to build up a new empty dic
        optimized_dic = {}  # set a empty dic, will save optimized data later
        if 'data' not in service_data_keys:  # means this dic has  no subdic, works for service like cpu,memory
            for key in service_data_keys:
                optimized_dic[key] = []
            tmp_data_dic = copy.deepcopy(optimized_dic)
            # "为了临时存最近n分钟的数据 ,把它们按照每个指标都搞成一个一个列表 ,来存最近N分钟的数据"
            # print("tmp data dic:", tmp_data_dic)
            # tmp data dic: {'nice': [], 'system': [], 'iowait': [], 'steal': [], 'user': [], 'status': [], 'idle': []}
            for service_data_item, last_save_time in raw_service_data:  # loop 最近n分钟的数据
                # print(service_data_item)
                """{'status': 0, 'steal': 0.0, 'iowait': 17272.44, 'system': 10763.58, 'idle': 207864274.41, 'nice': 16.22,
                 'user': 17213.26}"""
                for service_index, v in service_data_item.items():  # loop 每个数据点的指标
                    # print(service_index, v)
                    # nice 16.22
                    try:
                        tmp_data_dic[service_index].append(round(float(v), 2))
                        # 把这个点的当前这个指标 的值 添加到临时dict中
                    except ValueError as e:
                        pass
                # print(service_data_item,last_save_time)
            for service_k, v_list in tmp_data_dic.items():
                # print(service_k, v_list)
                avg_res = self.get_average(v_list)
                max_res = self.get_max(v_list)
                min_res = self.get_min(v_list)
                mid_res = self.get_mid(v_list)
                optimized_dic[service_k] = [avg_res, max_res, min_res, mid_res]
                # print(service_k, optimized_dic[service_k])

        else:
            # 处理有子服务的数据,比如网卡、硬盘
            for service_item_key, v_dic in first_service_data_point['data'].items():
                # service_item_key 相当于eth0, v_dic ={'t_in': 333,'t_out': 3353}
                optimized_dic[service_item_key] = {}
                for k2, v2 in v_dic.items():
                    optimized_dic[service_item_key][k2] = []  # {'eth0': {'t_in': [], 't_out':[]}}

            tmp_data_dic = copy.deepcopy(optimized_dic)
            if tmp_data_dic:  # some times this tmp_data_dic might be empty due to client report err
                # print('tmp data dic:', tmp_data_dic)
                """tmp data dic: {'enp4s0f1': {'t_in': [], 't_out': []}}"""
                for service_data_item, last_save_time in raw_service_data:  # loop最近n分钟数据
                    for service_index, val_dic in service_data_item['data'].items():
                        # print(service_index,val_dic)
                        # service_index这个值 相当于eth0,eth1...
                        for service_item_sub_key, val in val_dic.items():
                            # 上面这个service_item_sub_key相当于t_in,t_out
                            tmp_data_dic[service_index][service_item_sub_key].append(round(float(val), 2))
                            # 上面的service_index变量相当于 eth0...
                for service_k, v_dic in tmp_data_dic.items():
                    for service_sub_k, v_list in v_dic.items():
                        # print(service_k, service_sub_k, v_list)
                        """eth0 t_in [4.17, 6.69, 5.04, 4.49, 4.76, 5.61,
                        5.47, 5.99, 5.5, 6.28, 4.83, 6.87, 4.74, 6.14, 5.72, 6.25, 5.1, 7.1, 5.29, 6.37]"""
                        avg_res = self.get_average(v_list)
                        max_res = self.get_max(v_list)
                        min_res = self.get_min(v_list)
                        mid_res = self.get_mid(v_list)
                        optimized_dic[service_k][service_sub_k] = [avg_res, max_res, min_res, mid_res]
                        # print(service_k, service_sub_k, optimized_dic[service_k][service_sub_k])
                        # eth0 t_in [5.6205, 7.1, 4.17, 5.61]
            else:
                print("\033[41;1mMust be sth wrong with client report data\033[0m")
        # print("optimized empty dic:", optimized_dic)
        """optimized empty dic: {'eth0': {'t_in': [5.6205, 7.1, 4.17, 5.61],
        't_out': [2.0534999999999997, 4.15, 0.29, 2.37]}}"""
        return optimized_dic

    def get_average(self, data_set):
        # calc the avg value of data set
        if len(data_set) > 0:
            return sum(data_set) / len(data_set)
        else:
            return 0

    def get_max(self, data_set):
        # calc the max value of the data set
        if len(data_set) > 0:
            return max(data_set)
        else:
            return 0

    def get_min(self, data_set):
        # calc the minimum value of the data set
        if len(data_set) > 0:
            return min(data_set)
        else:
            return 0

    def get_mid(self, data_set):
        # calc the mid value of the data set
        data_set.sort()
        if len(data_set) > 0:
            return data_set[int(len(data_set)/2)]
        else:
            return 0
