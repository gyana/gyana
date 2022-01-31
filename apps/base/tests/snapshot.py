from itertools import chain

from django.db.models.fields.files import FileField, ImageField
from django.forms.models import model_to_dict


def get_instance_dict(instance, already_passed=frozenset()):
    """Creates a nested dict version of a django model instance

    Follows relationships recursively, circular relationships are terminated by putting
    a model identificator `{model_name}:{instance.id}`.
    Ignores image and file fields."""
    instance_dict = model_to_dict(
        instance,
        fields=[
            f
            for f in instance._meta.concrete_fields
            if not isinstance(f, (ImageField, FileField))
        ],
    )

    already_passed = already_passed.union(
        frozenset((f"{instance.__class__.__name__}:{instance.id}",))
    )
    # Go through possible relationships
    for field in chain(instance._meta.related_objects, instance._meta.concrete_fields):
        if (
            (field.one_to_one or field.many_to_one)
            and hasattr(instance, field.name)
            and (relation := getattr(instance, field.name))
        ):
            if (
                model_id := f"{relation.__class__.__name__}:{relation.id}"
            ) in already_passed:
                instance_dict[field.name] = model_id
            else:
                instance_dict[field.name] = get_instance_dict(relation, already_passed)

        if field.one_to_many or field.many_to_many:
            relations = []
            for relation in getattr(instance, field.get_accessor_name()).all():
                if (
                    model_id := f"{relation.__class__.__name__}:{relation.id}"
                ) in already_passed:
                    relations.append(model_id)
                else:
                    relations.append(get_instance_dict(relation, already_passed))
            instance_dict[field.get_accessor_name()] = relations

    return instance_dict
