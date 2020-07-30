from typing import Optional
from django import forms
from django.urls import reverse_lazy as reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit, Button
from crispy_forms.bootstrap import StrictButton, PrependedText, FormActions
from outpost.django.base.layout import StaticField, IconButton, LinkIconButton

from . import models


class PublicKeyForm(forms.ModelForm):
    class Meta:
        model = models.PublicKey
        fields = ("name", "key")

    @property
    def helper(self) -> FormHelper:
        h = FormHelper()
        h.html5_required = True
        h.form_method = "POST"
        h.form_tag = True
        h.form_action = reverse("salt:publickey-create")
        h.layout = Layout(
            Field("name"),
            Field("key"),
            FormActions(
                IconButton(
                    "glyphicon glyphicon-ok-sign",
                    "Save changes",
                    css_class="btn-success",
                    type="submit",
                ),
                LinkIconButton(
                    reverse("salt:publickey"),
                    "glyphicon glyphicon-ban-circle",
                    "Cancel",
                    css_class="btn-warning",
                ),
            ),
        )
        return h


class FileForm(forms.ModelForm):
    def __init__(self, pk: Optional[int] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pk = pk

    class Meta:
        model = models.File
        fields = ("path", "systems", "permissions", "content")

    @property
    def helper(self) -> FormHelper:
        h = FormHelper()
        h.html5_required = True
        h.form_method = "POST"
        h.form_tag = True
        h.layout = Layout(
            PrependedText("path", "~/"), Field("systems"), Field("permissions")
        )
        if self.pk:
            h.form_action = reverse("salt:file-update", kwargs={"pk": self.pk})
            h.layout.extend([StaticField("sha256"), StaticField("mimetype")])
        else:
            h.form_action = reverse("salt:file-create")
            h.layout.append(Field("content"))
        h.layout.append(
            FormActions(
                IconButton(
                    "glyphicon glyphicon-ok-sign",
                    "Save changes",
                    css_class="btn-success",
                    type="submit",
                ),
                LinkIconButton(
                    reverse("salt:file"),
                    "glyphicon glyphicon-ban-circle",
                    "Cancel",
                    css_class="btn-warning",
                ),
            )
        )
        return h
