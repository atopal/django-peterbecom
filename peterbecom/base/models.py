from django.db import models

from jsonfield import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import pre_save
from django.dispatch import receiver


class CommandRun(models.Model):
    app = models.CharField(max_length=100)
    command = models.CharField(max_length=100)
    duration = models.DurationField()
    notes = models.TextField(null=True)
    exception = models.TextField(null=True)
    options = JSONField(default={}, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return "<{}: {!r} {!r}{}>".format(
            self.__class__.__name__,
            self.app,
            self.command,
            self.exception and " (Errored)" or "",
        )


class PostProcessing(models.Model):
    filepath = models.CharField(max_length=400)
    url = models.URLField(max_length=400, db_index=True)
    duration = models.DurationField(null=True)
    notes = ArrayField(models.CharField(max_length=100), default=list)
    exception = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    previous = models.ForeignKey(
        "self",
        null=True,
        related_name="postprocessing",
        on_delete=models.CASCADE,
        db_index=False,
    )

    @classmethod
    def ongoing(cls):
        return cls.objects.filter(exception__isnull=True, duration__isnull=True)


@receiver(pre_save, sender=PostProcessing)
def set_previous(sender, instance, **kwargs):
    qs = PostProcessing.objects.filter(url=instance.url)
    if instance.id:
        qs = qs.exclude(id=instance.id)
    for previous in qs.order_by("-created")[:1]:
        instance.previous = previous
