from django.db import models

from .rule_logic import CHECK_TYPE_LABELS


class Rule(models.Model):
    CHECK_CHOICES = list(CHECK_TYPE_LABELS.items())

    rule_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    check_type = models.CharField(max_length=30, choices=CHECK_CHOICES)
    field_key = models.CharField(max_length=200, blank=True)
    weight = models.PositiveSmallIntegerField(default=1)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.rule_id}: {self.name}'
