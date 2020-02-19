from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy as reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from . import models


class IndexView(TemplateView):
    pass


class PublicKeyMixin(object):
    def get_queryset(self):
        qs = super().get_queryset()
        suser = models.User.objects.get(local=self.request.user)
        return qs.filter(user=suser)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = models.User.objects.get(local=self.request.user)
        return context


class FileMixin(object):
    def get_queryset(self):
        qs = super().get_queryset()
        suser = models.User.objects.get(local=self.request.user)
        return qs.filter(user=suser)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = models.User.objects.get(local=self.request.user)
        return context


class PublicKeyListView(LoginRequiredMixin, PublicKeyMixin, ListView):
    model = models.PublicKey


class PublicKeyCreateView(LoginRequiredMixin, PublicKeyMixin, CreateView):
    model = models.PublicKey
    fields = ("name", "key")
    success_url = reverse("salt:publickey")

    def form_valid(self, form):
        suser = models.User.objects.get(local=self.request.user)
        form.instance.user = suser
        return super().form_valid(form)


class PublicKeyDeleteView(LoginRequiredMixin, PublicKeyMixin, DeleteView):
    model = models.PublicKey
    success_url = reverse("salt:publickey")


class FileListView(LoginRequiredMixin, FileMixin, ListView):
    model = models.File


class FileCreateView(LoginRequiredMixin, FileMixin, CreateView):
    model = models.File
    fields = ("path", "content", "systems", "permissions")
    success_url = reverse("salt:file")

    def form_valid(self, form):
        suser = models.User.objects.get(local=self.request.user)
        form.instance.user = suser
        form.instance.save()
        for system in form.cleaned_data["systems"]:
            models.SystemFile.objects.create(file=form.instance, system=system)
        self.object = form.instance
        return HttpResponseRedirect(self.get_success_url())


class FileUpdateView(LoginRequiredMixin, FileMixin, UpdateView):
    model = models.File
    fields = ("path", "systems", "permissions")
    success_url = reverse("salt:file")


class FileDeleteView(LoginRequiredMixin, FileMixin, DeleteView):
    model = models.File
    success_url = reverse("salt:file")
