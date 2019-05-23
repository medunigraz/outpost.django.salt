from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.IndexView.as_view(),
        name='index'
    ),
    url(
        r'^publickey/$',
        views.PublicKeyListView.as_view(),
        name='publickey'
    ),
    url(
        r'^publickey/add/$',
        views.PublicKeyCreateView.as_view(),
        name='publickey-create'
    ),
    url(
        r'^publickey/delete/(?P<pk>\d+)$',
        views.PublicKeyDeleteView.as_view(),
        name='publickey-delete'
    ),
]
