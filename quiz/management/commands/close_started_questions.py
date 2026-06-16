# quiz/management/commands/close_started_questions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from quiz.models import Question

class Command(BaseCommand):
    help = 'Close questions whose start_time has passed (stored in UTC)'

    def handle(self, *args, **options):
        now_utc = timezone.now()

        qs = Question.objects.filter(
            is_open=True,
            start_time__isnull=False,
            start_time__lte=now_utc,
        )

        count = qs.update(is_open=False)
        self.stdout.write(
            f"Closed {count} questions at {now_utc.isoformat()} (UTC)"
        )