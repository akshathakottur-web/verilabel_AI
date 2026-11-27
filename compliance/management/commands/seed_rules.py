from django.core.management.base import BaseCommand

from compliance.default_rules import DEFAULT_RULES
from compliance.models import Rule


class Command(BaseCommand):
    help = 'Creates the 11 default FSSAI rules. Rules that already exist are left as they are.'

    def handle(self, *args, **options):
        created = 0
        for data in DEFAULT_RULES:
            rule_id = data['rule_id']
            defaults = {key: value for key, value in data.items() if key != 'rule_id'}
            _, was_created = Rule.objects.get_or_create(rule_id=rule_id, defaults=defaults)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'{created} rules created, {len(DEFAULT_RULES) - created} already existed.'
        ))
