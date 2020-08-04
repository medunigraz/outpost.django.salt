from django.conf.urls import url

from . import views

app_name = "salt"

urlpatterns = [
    url(r"^$", views.IndexView.as_view(), name="index"),
    url(r"^publickey/$", views.PublicKeyListView.as_view(), name="publickey"),
    url(
        r"^publickey/add/$",
        views.PublicKeyCreateView.as_view(),
        name="publickey-create",
    ),
    url(
        r"^publickey/delete/(?P<pk>\d+)$",
        views.PublicKeyDeleteView.as_view(),
        name="publickey-delete",
    ),
    url(r"^file/$", views.FileListView.as_view(), name="file"),
    url(r"^file/add/$", views.FileCreateView.as_view(), name="file-create"),
    url(r"^file/edit/(?P<pk>\d+)$", views.FileUpdateView.as_view(), name="file-update"),
    url(
        r"^file/delete/(?P<pk>\d+)$", views.FileDeleteView.as_view(), name="file-delete"
    ),
]
