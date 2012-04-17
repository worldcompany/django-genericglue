from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models


class SingleGFK(models.Model):
    """
    An abstract base model to simplify the creation of models with a GFK'd 
    "object" relationship.
    """
    object_type = models.ForeignKey(ContentType, related_name="related_%(class)s")
    object_id = models.IntegerField(db_index=True)
    object = generic.GenericForeignKey(ct_field="object_type", fk_field="object_id")

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"%s - %s" % (self.object_type, self.object)


class DualGfk(SingleGFK):
    """
    An abstract base model to simplify the creation of models with dual-ended
    GFKs.
    """
    parent_type = models.ForeignKey(ContentType, related_name="child_%(class)s")
    parent_id = models.IntegerField(db_index=True)
    parent = generic.GenericForeignKey(ct_field="parent_type", fk_field="parent_id")
    dnorm_parent = models.CharField(max_length=200)

    class Meta:
        abstract = True

    def save(self, **kwargs):
        self.dnorm_parent = "%s.%s" % (self.parent_type.id, self.parent_id)
        self.save_base(**kwargs)


class GenericglueRelation(generic.GenericRelation):
    """
    A simple override of Django's GenericRelation class to assume the default field names DualGfk uses.
    
    """
    def __init__(self, model, **kwargs):
        defaults = dict(object_id_field="parent_id", content_type_field="parent_type")
        defaults.update(kwargs)
        return super(GenericglueRelation, self).__init__(model, **defaults)
    