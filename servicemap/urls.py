from django.conf.urls import patterns, url
import servicemap.views as views

urlpatterns = patterns(
    'servicemap.views',
    url('^api/v1/service/(?P<name>.+)/deployments', views.deployments),
    url('^api/v1/service/(?P<name>.+)', views.service),
    url('^api/v1/service', views.service_list),
    url('^service/(?P<name>.+)', views.display_service,
        name="service_display"),
    url('^$', views.home),
)
