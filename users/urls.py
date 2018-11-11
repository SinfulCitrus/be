from django.conf.urls import url
from django.conf.urls import include

urlpatterns = [
    url(r'^auth/', include('rest_auth.urls')),
]