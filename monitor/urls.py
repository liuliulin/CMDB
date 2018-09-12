from django.conf.urls import url
from monitor import views


urlpatterns = [
    url(r'hosts/$', views.hosts, name='hosts'),
    url(r'hosts/(\d+)/$', views.host_detail, name='host_detail'),
    url(r'trigger_list/$', views.trigger_list, name='trigger_list'),
    # url(r'host_groups/$', views.host_groups, name='host_groups'),
    # # url(r'graph/$',views.graph ,name='get_graph'),
    # url(r'client/service/report/$',views.service_data_report )
    # url(r'^triggers/$', views.triggers, name='triggers'),
]
