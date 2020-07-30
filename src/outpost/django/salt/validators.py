from pathlib import Path

from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


@deconstructible
class RelativePathValidator(object):
    """
    """

    def __call__(self, data: str):
        path = Path(data)
        if path.is_absolute():
            raise ValidationError(_("Absolute paths not allowed"), code="no_absolute")
        if ".." in path.parts:
            raise ValidationError(
                _("No parent directory references allowed"), code="no_parent_references"
            )
