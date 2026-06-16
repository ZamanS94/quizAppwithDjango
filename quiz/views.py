from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, Question, UserAnswer, Profile
from django.contrib.auth import login
from .forms import SignUpForm

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
    events = Event.objects.filter(is_active=True).prefetch_related('questions__choices')
    answered_ids = UserAnswer.objects.filter(user=request.user).values_list('question_id', flat=True)
    return render(request, 'quiz/question_list.html', {
        'events': events,
        'answered_ids': set(answered_ids),
    })

from django.http import Http404

@login_required
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

        from .models import Choice, UserAnswer

        choice = get_object_or_404(Choice, pk=choice_id, question=question)

        _, created = UserAnswer.objects.get_or_create(
            user=request.user,
            question=question,
            defaults={'choice': choice}
        )
        if created:
            messages.success(request, "Prediction submitted!")
        else:
            messages.warning(request, "You already submitted a prediction for this match.")

    return redirect('question_list')


from .models import Event, Profile
import math
from .models import Profile, Event

def leaderboard(request):
    profiles = Profile.objects.select_related('user')

    data = []
    for p in profiles:
        user_events = Event.objects.filter(
            questions__useranswer__user=p.user
        ).distinct().values_list('name', flat=True)

        data.append({
            'username': p.user.username,
            'points': p.points,
            'correct': p.correct_answers,
            'total': p.total_resolved_answers,
            'accuracy': round(p.accuracy * 100, 1),
            'score': round(p.score, 3),
            'events': ", ".join(user_events) if user_events else "",
        })

    data.sort(key=lambda x: x['score'], reverse=True)

    # NEW: all events that have at least one open question
    open_events = Event.objects.filter(
        questions__is_open=True
    ).distinct().values_list('name', flat=True)

    return render(
        request,
        'quiz/leaderboard.html',
        {'data': data, 'open_events': open_events}
    )