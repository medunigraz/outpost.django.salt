from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy as reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
)

from . import models


class IndexView(TemplateView):
    pass


class PublicKeyMixin(object):

    def get_queryset(self):
        qs = super().get_queryset()
        suser = models.User.objects.get(local=self.request.user)
        return qs.filter(
            user=suser
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = models.User.objects.get(local=self.request.user)
        return context


class PublicKeyListView(LoginRequiredMixin, PublicKeyMixin, ListView):
    model = models.PublicKey


class PublicKeyCreateView(LoginRequiredMixin, PublicKeyMixin, CreateView):
    model = models.PublicKey
    fields = (
        'name',
        'key',
    )
    success_url = reverse('salt:publickey')

    def form_valid(self, form):
        suser = models.User.objects.get(local=self.request.user)
        form.instance.user = suser
        return super().form_valid(form)


class PublicKeyDeleteView(LoginRequiredMixin, PublicKeyMixin, DeleteView):
    model = models.PublicKey
    success_url = reverse('salt:publickey')
