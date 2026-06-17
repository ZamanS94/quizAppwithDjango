from django.core.management.base import BaseCommand
from quiz.models import Question, UserAnswer, Profile

class Command(BaseCommand):
    help = 'Score all unscored questions that have a correct answer'

    def handle(self, *args, **kwargs):
        questions = Question.objects.filter(
            is_scored=False,
            correct_choice__isnull=False
        )

        for question in questions:
            answers = UserAnswer.objects.filter(
                question=question
            ).select_related('user', 'choice')

            for answer in answers:
                is_correct = answer.choice == question.correct_choice
                points = 1 if is_correct else 0

                answer.is_correct = is_correct
                answer.points_awarded = points
                answer.save()

                profile, _ = Profile.objects.get_or_create(user=answer.user)
                profile.total_resolved_answers += 1
                if is_correct:
                    profile.correct_answers += 1
                    profile.points += points
                profile.save()

            question.is_scored = True
            question.save()
            self.stdout.write(f'✅ Scored: {question.title}')

        self.stdout.write('Done!')
