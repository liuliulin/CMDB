import redis

pool = redis.ConnectionPool(host='10.134.166.40', port=6379)
r = redis.Redis(connection_pool=pool)
tmp = r.info()
# print(type(tmp), tmp)
print(tmp['connected_clients'])
print(tmp['keyspace_hits']/(tmp['keyspace_hits'] + tmp['keyspace_misses']) * 100)
