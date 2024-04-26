from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy as reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)
from outpost.django.base.mixins import ContextMixin

from . import (
    forms,
    models,
)


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


class PublicKeyCreateView(LoginRequiredMixin, ContextMixin, PublicKeyMixin, CreateView):
    model = models.PublicKey
    success_url = reverse("salt:publickey")
    form_class = forms.PublicKeyForm
    extra_context = {"title": _("Create new public key")}

    def form_valid(self, form):
        suser = models.User.objects.get(local=self.request.user)
        form.instance.user = suser
        return super().form_valid(form)


class PublicKeyDeleteView(LoginRequiredMixin, PublicKeyMixin, DeleteView):
    model = models.PublicKey
    success_url = reverse("salt:publickey")


class FileListView(LoginRequiredMixin, FileMixin, ListView):
    model = models.File


class FileCreateView(LoginRequiredMixin, ContextMixin, FileMixin, CreateView):
    model = models.File
    success_url = reverse("salt:file")
    form_class = forms.FileForm
    extra_context = {"title": _("Create new deployment file")}

    def form_valid(self, form):
        suser = models.User.objects.get(local=self.request.user)
        form.instance.user = suser
        form.instance.save()
        for system in form.cleaned_data["systems"]:
            models.SystemFile.objects.create(file=form.instance, system=system)
        self.object = form.instance
        return HttpResponseRedirect(self.get_success_url())


class FileUpdateView(LoginRequiredMixin, ContextMixin, FileMixin, UpdateView):
    model = models.File
    success_url = reverse("salt:file")
    form_class = forms.FileForm
    extra_context = {"title": _("Edit deployment file")}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["pk"] = self.object.pk
        return kwargs

    def form_valid(self, form):
        form.instance.save()
        for system in form.cleaned_data["systems"]:
            models.SystemFile.objects.get_or_create(file=form.instance, system=system)
        models.SystemFile.objects.filter(file=form.instance).exclude(
            system__in=form.cleaned_data["systems"]
        ).delete()
        self.object = form.instance
        return HttpResponseRedirect(self.get_success_url())


class FileDeleteView(LoginRequiredMixin, FileMixin, DeleteView):
    model = models.File
    success_url = reverse("salt:file")
