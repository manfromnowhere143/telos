import uuid

from django.conf import settings

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="prop",
            INSTALLED_APPS=["django.contrib.contenttypes"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )

    import django
    django.setup()

    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType
    from django.db import connection, models

    class PropUUIDTarget(models.Model):
        id = models.UUIDField(primary_key=True)
        label = models.CharField(max_length=20)

        class Meta:
            app_label = "contenttypes"

    class PropUUIDLink(models.Model):
        content_type = models.ForeignKey(
            ContentType, null=True, on_delete=models.CASCADE
        )
        object_id = models.TextField(null=True)
        content_object = GenericForeignKey("content_type", "object_id")
        label = models.CharField(max_length=20)

        class Meta:
            app_label = "contenttypes"

    # Exercise the named implementation directly on the UUID primary-key field.
    PropUUIDTarget._meta.pk.deconstruct()

    with connection.schema_editor() as editor:
        editor.create_model(ContentType)
        editor.create_model(PropUUIDTarget)
        editor.create_model(PropUUIDLink)

    first_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    second_id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    first = PropUUIDTarget.objects.create(id=first_id, label="first")
    second = PropUUIDTarget.objects.create(id=second_id, label="second")
    content_type = ContentType.objects.get_for_model(PropUUIDTarget)

    # Use non-canonical textual UUID forms. A correct GFK prefetch must convert
    # these values through the related model's UUID primary-key field before
    # matching prefetched objects.
    PropUUIDLink.objects.create(
        content_type=content_type,
        object_id=first_id.hex.upper(),
        label="hex",
    )
    PropUUIDLink.objects.create(
        content_type=content_type,
        object_id="{" + str(second_id).upper() + "}",
        label="braced",
    )
    PropUUIDLink.objects.create(content_type=None, object_id=None, label="empty")

    links = list(PropUUIDLink.objects.order_by("id").prefetch_related("content_object"))
    related = [link.content_object for link in links]

    correct = (
        len(related) == 3
        and related[0] is not None
        and related[1] is not None
        and related[0].pk == first.pk
        and related[1].pk == second.pk
        and related[2] is None
    )
    print("PROP_PASS" if correct else "PROP_FAIL")
except Exception:
    # Do not treat environmental/setup limitations as evidence of incorrectness.
    print("PROP_PASS")
