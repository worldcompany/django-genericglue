from django import forms
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

class ContentTypeChoiceIterator(object):
    """
    A class which generates choices for content-type select fields
    a single time and caches them.

    It takes a single optional queryset argument which should be a queryset of
    ContentType objects. This lets you narrow your choices to a subset of all
    ContentTypes.

    """
    def __init__(self, queryset=ContentType.objects.all()):
        self.queryset = queryset
        self.ctype_choices = [(ctype.id, "%s | %s" % (ctype.app_label, ctype.model)) for ctype in self.queryset.order_by('app_label', 'model')]

    def __iter__(self):
        yield (u"", u"---------") # initial empty choice
        for choice in self.ctype_choices:
            yield choice


class GenericRawIdWidget(forms.TextInput):
    """
    A raw-id widget which automatically includes JavaScript for the
    necessary object-selection popup.

    """
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'vGenericRawIdField' # The JS looks for this class name.
        output_str = u'&nbsp;&nbsp;%s<a href="#" id="lookup_id_%s" class="related-lookup" onclick="return showGenericRelatedObjectLookupPopup(this);">&nbsp;<img src="%simg/admin/selector-search.gif" alt="Lookup" height="16" width="16" /></a>'
        return mark_safe(output_str % (super(GenericRawIdWidget, self).render(name, value, attrs),
                                       name,
                                       settings.ADMIN_MEDIA_PREFIX))

    class Media:
        js = [
            '%sjs/getElementsBySelector.js' % settings.ADMIN_MEDIA_PREFIX,
            '%s%sgenericglue/show_generic_relations.js' % (settings.STATIC_MEDIA_URL, getattr(settings, "APP_MEDIA_PREFIX", "app_media/")),
        ]


class GenericForeignKeyWidget(forms.MultiWidget):
    """
    A combined widget for object-type and object-id selection in a generic FK.

    """
    def __init__(self, attrs=None, queryset=ContentType.objects.all()):
        super(GenericForeignKeyWidget, self).__init__(widgets=(forms.Select(choices=ContentTypeChoiceIterator(queryset=queryset)),
                                                               GenericRawIdWidget))

    def render(self, name, value, attrs=None):
        output = super(GenericForeignKeyWidget, self).render(name, value, attrs)
        obj_repr = self.get_repr(value)
        return obj_repr and mark_safe("%s %s"% (output, self.get_repr(value))) or mark_safe(output)

    def value_from_datadict(self, data, files, name):
        return [data.get("%s_0" % name, ''), data.get("%s_1" % name, '')]

    def decompress(self, value):
        """
        Given the currently-selected object, return the content-type
        id and object id corresponding to it.

        """
        if value:
            return [ContentType.objects.get_for_model(value).id, value.pk]
        return [None, None]

    def get_repr(self, value):
        """
        Return the truncated string representation of the
        currently-selected object.

        """
        if isinstance(value, (list, tuple)) and (value[0] and value[1]):
            value = ContentType.objects.get(pk=value[0]).get_object_for_this_type(pk=value[1])
            return u"&nbsp;<strong>%s</strong>" % unicode(value)
        return None


class GenericForeignKeyField(forms.MultiValueField):
    """
    A field which combines the content-type selection and object-id
    selection of a generic foreign key, and which returns the object
    represented by that combination.

    """
    def __init__(self, queryset=ContentType.objects.all(), *args, **kwargs):
        super(GenericForeignKeyField, self).__init__(fields=(forms.ModelChoiceField(queryset=queryset),
                                                             forms.IntegerField()), widget=GenericForeignKeyWidget(queryset=queryset), *args, **kwargs)

    def compress(self, data_list):
        """
        Given the content-type and object id, return the actual
        object.

        """
        if data_list is None or data_list == [] or not data_list[0] or not data_list[1]:
            return data_list
        ctype, object_id = data_list
        try:
            ctype.get_object_for_this_type(pk=object_id)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            #
            # We raise a ValidationError here, rather than in a custom
            # clean(), because doing it in clean() requires
            # duplicating a large amount of code, and clean() ends up
            # calling this method anyway.
            #
            raise forms.ValidationError(u"Please select a valid object")
        return (ctype, object_id)


class GenericglueInlineModelAdmin(generic.GenericInlineModelAdmin):
    ct_field = "parent_type"
    ct_fk_field = "parent_id"


class GenericglueStackedInline(GenericglueInlineModelAdmin):
    template = 'admin/edit_inline/stacked.html'


class GenericglueTabularInline(GenericglueInlineModelAdmin):
    template = 'admin/edit_inline/tabular.html'
