# quiz/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.http import Http404
import math

from .models import Event, Question, Choice, UserAnswer, Profile
from .forms import SignUpForm

from django.http import HttpResponse

def ping(request):
    return HttpResponse("ok")

def signup(request):
    if request.user.is_authenticated:
        return redirect('question_list')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome.")
            return redirect('question_list')
    else:
        form = SignUpForm()
    return render(request, 'quiz/signup.html', {'form': form})
@login_required
def question_list(request):
    now = timezone.now()
    today = now.date()

    answered_ids = set(
        UserAnswer.objects.filter(
            user=request.user
        ).values_list('question_id', flat=True)
    )

    events = Event.objects.filter(is_active=True)
    event_data = []

    for event in events:
        questions = event.questions.filter(
            is_open=True,
            start_time__date=today,
            start_time__gt=now        # ← only future kickoffs today
        ).exclude(
            useranswer__user=request.user
        ).order_by('start_time').prefetch_related('choices')

        if questions.exists():
            event_data.append({
                'event': event,
                'questions': questions,
            })

    return render(request, 'quiz/question_list.html', {
        'event_data': event_data,
        'answered_ids': answered_ids,
    })

@login_required
def my_predictions(request):
    answers = UserAnswer.objects.filter(
        user=request.user
    ).select_related(
        'question', 'question__event', 'choice', 'question__correct_choice'
    ).order_by('-submitted_at')

    return render(request, 'quiz/my_predictions.html', {
        'answers': answers,
    })


@login_required
def submit_answer(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404("Question does not exist.")

    if not question.is_open:
        messages.error(request, "Predictions for this match are closed.")
        return redirect('question_list')

    if request.method == "POST":
        choice_id = request.POST.get("choice")
        if not choice_id:
            messages.error(request, "Please select an answer.")
            return redirect('question_list')

        choice = get_object_or_404(Choice, pk=choice_id, question=question)

        _, created = UserAnswer.objects.get_or_create(
            user=request.user,
            question=question,
            defaults={'choice': choice}
        )

        if created:
            messages.success(request, "✅ Prediction submitted!")
        else:
            messages.warning(request, "You already submitted a prediction for this match.")

    return redirect('question_list')


def leaderboard(request):
    profiles = Profile.objects.select_related('user')

    data = []
    for p in profiles:
        user_events = Event.objects.filter(
            questions__useranswer__user=p.user
        ).distinct().values_list('name', flat=True)

        total = p.total_resolved_answers
        correct = p.correct_answers
        accuracy = round((correct / total * 100), 1) if total > 0 else 0
        score = round(accuracy * math.log(total + 1), 3) if total > 0 else 0

        data.append({
            'username': p.user.username,
            'points': p.points,
            'correct': correct,
            'total': total,
            'accuracy': accuracy,
            'score': score,
            'events': ", ".join(user_events) if user_events else "—",
        })

    data.sort(key=lambda x: x['score'], reverse=True)

    open_events = Event.objects.filter(
        questions__is_open=True
    ).distinct().values_list('name', flat=True)

    return render(request, 'quiz/leaderboard.html', {
        'data': data,
        'open_events': open_events,
    })
