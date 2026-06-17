from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='questions')
    title = models.TextField()
    correct_choice = models.ForeignKey(
        'Choice', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    is_open = models.BooleanField(default=True)
    is_scored = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    actual_home_goals = models.IntegerField(null=True, blank=True)
    actual_away_goals = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(null=True)
    points_awarded = models.FloatField(default=0)
    predicted_home_goals = models.IntegerField(null=True, blank=True)
    predicted_away_goals = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'question'], name='one_answer_per_question')
        ]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.FloatField(default=0)
    correct_answers = models.IntegerField(default=0)
    total_resolved_answers = models.IntegerField(default=0)

    @property
    def accuracy(self):
        if self.total_resolved_answers == 0:
            return 0
        return round(self.correct_answers / self.total_resolved_answers * 100, 1)

    def __str__(self):
        return f"{self.user.username} profile"