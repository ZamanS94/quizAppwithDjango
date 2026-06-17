from django.core.management.base import BaseCommand
from quiz.models import UserAnswer, Profile, Question


class Command(BaseCommand):
    help = 'Reset all scores and rescore from scratch'

    def goal_points(self, actual, predicted):
        if actual is None or predicted is None:
            return 0
        deviation = abs(actual - predicted)
        if deviation == 0: return 1
        elif deviation == 1: return 0.75
        elif deviation == 2: return 0.5
        elif deviation == 3: return 0.25
        else: return 0

    def handle(self, *args, **options):
        # Step 1: reset all profiles
        Profile.objects.all().update(points=0, correct_answers=0, total_resolved_answers=0)
        # Step 2: reset all answers
        UserAnswer.objects.all().update(is_correct=None, points_awarded=0)
        # Step 3: reset all questions
        Question.objects.all().update(is_scored=False)

        self.stdout.write("✅ All scores reset.")

        # Step 4: rescore all scored questions
        scored_questions = Question.objects.filter(correct_choice__isnull=False)
        for question in scored_questions:
            answers = UserAnswer.objects.filter(question=question).select_related('user')
            for answer in answers:
                profile, _ = Profile.objects.get_or_create(user=answer.user)
                profile.total_resolved_answers += 1

                winner_points = 1 if answer.choice == question.correct_choice else 0
                if winner_points:
                    profile.correct_answers += 1
                    answer.is_correct = True
                else:
                    answer.is_correct = False

                home_pts = self.goal_points(question.actual_home_goals, answer.predicted_home_goals)
                away_pts = self.goal_points(question.actual_away_goals, answer.predicted_away_goals)

                total_points = winner_points + home_pts + away_pts
                answer.points_awarded = total_points
                profile.points += total_points

                answer.save()
                profile.save()

            question.is_scored = True
            question.save()

        self.stdout.write("✅ All questions rescored with new system.")