from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models.loading import cache
from genericglue.forms import GenericForeignKeyField
from genericglue.utils import table_exists


if table_exists(ContentType._meta.db_table):
    MODELS_WITH_PERMALINKS = [ContentType.objects.get_for_model(model) for model in cache.get_models() if getattr(model, 'get_absolute_url', None)]
    MODEL_IDS_WITH_PERMALINKS = [ct.id for ct in MODELS_WITH_PERMALINKS]
else:
    MODELS_WITH_PERMALINKS = []
    MODEL_IDS_WITH_PERMALINKS = []


class WithGenericObjectForm(forms.ModelForm):
    """
    A class for setting up inlines with a generic FK. It assumes the generic
    object is defined by the fields `object_id` and `object_type` on your
    inline model. It needs to be subclassed and the subclass needs to have a
    meta class defined that sets the model that you're inlining::

        class Meta:
            model = YourInlineModel

    By default this class restricts the GFK model drop down just to content
    types that have get_absolute_url methods. To change this restriction
    override the object property. For example to be able to select from all
    content tpyes, you could add a bit like this to your subclass::

        object = GenericForeignKeyField(required=True, queryset=ContentType.objects.all())

    """
    object = GenericForeignKeyField(required=True, queryset=ContentType.objects.filter(pk__in=MODEL_IDS_WITH_PERMALINKS))

    def __init__(self, *args, **kwargs):
        super(WithGenericObjectForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.object_id:
            self.initial['object'] = [self.instance.object_type.id, self.instance.object_id]

    def clean(self):
        self.instance.object_type, self.instance.object_id = self.cleaned_data['object']
        self.cleaned_data['object_id'] = self.instance.object_id
        self.cleaned_data['object_type'] = self.instance.object_type
        return super(WithGenericObjectForm, self).clean()
