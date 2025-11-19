from django.urls import re_path, path

from . import views

app_name = "salt"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("publickey/", views.PublicKeyListView.as_view(), name="publickey"),
    path(
        "publickey/add/",
        views.PublicKeyCreateView.as_view(),
        name="publickey-create",
    ),
    path(
        "publickey/delete/<int:pk>/",
        views.PublicKeyDeleteView.as_view(),
        name="publickey-delete",
    ),
    path("file/", views.FileListView.as_view(), name="file"),
    path("file/add/", views.FileCreateView.as_view(), name="file-create"),
    path("file/edit/<int:pk>/", views.FileUpdateView.as_view(), name="file-edit"),
    path("file/delete/<int:pk>/", views.FileDeleteView.as_view(), name="file-delete"),
]
