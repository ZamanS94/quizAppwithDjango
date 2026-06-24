from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from django.http import Http404, HttpResponse

from .models import Event, Question, Choice, UserAnswer, Profile
from .forms import SignUpForm


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
    from datetime import timedelta

    window_end = now + timedelta(hours=12)

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
            start_time__gt=now,          # not yet started
            start_time__lte=window_end,  # within next 12 hours
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

        def parse_goals(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return None

        predicted_home = parse_goals(request.POST.get("predicted_home_goals"))
        predicted_away = parse_goals(request.POST.get("predicted_away_goals"))

        _, created = UserAnswer.objects.get_or_create(
            user=request.user,
            question=question,
            defaults={
                'choice': choice,
                'predicted_home_goals': predicted_home,
                'predicted_away_goals': predicted_away,
            }
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
        data.append({
            'username': p.user.username,
            'points': round(p.points, 2),
            'correct': p.correct_answers,
            'total': p.total_resolved_answers,
            'accuracy': p.accuracy,
        })

    data.sort(key=lambda x: x['points'], reverse=True)

    # ✅ fixed: get all active events
    open_events = Event.objects.filter(is_active=True).values_list('name', flat=True)

    return render(request, 'quiz/leaderboard.html', {
        'data': data,
        'open_events': open_events,
    })

def match_votes(request):
    questions = Question.objects.prefetch_related('choices').order_by('-start_time')  # ✅ newest first

    all_votes = []
    for question in questions:
        total = UserAnswer.objects.filter(question=question).count()

        if total == 0:  # ✅ skip questions with no votes
            continue

        vote_data = []
        for choice in question.choices.all():
            count = UserAnswer.objects.filter(question=question, choice=choice).count()
            pct = round(count / total * 100, 1)
            vote_data.append({'choice': choice.text, 'count': count, 'pct': pct})

        all_votes.append({
            'question': question,
            'vote_data': vote_data,
            'total': total,
        })

    return render(request, 'quiz/match_votes.html', {'all_votes': all_votes})

def points_info(request):
    return render(request, 'quiz/points_info.html')