# _*_coding:utf-8_*_
import redis


def redis_conn(django_settings):
    pool = redis.ConnectionPool(host=django_settings.REDIS_CONN['HOST'],
                                db=django_settings.REDIS_CONN['DB'],
                                port=django_settings.REDIS_CONN['PORT'])
    r = redis.Redis(connection_pool=pool)
    return r
