# quiz/admin.py
from django.contrib import admin
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import Event, Question, Choice, UserAnswer, Profile

import csv
import io
import datetime
import pytz


# Register simple models
admin.site.register(Profile)
admin.site.register(UserAnswer)


# Inline choices on the Question admin
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'is_open', 'is_scored', 'start_time', 'correct_choice']
    inlines = [ChoiceInline]
    actions = ['score_questions']

    def score_questions(self, request, queryset):
        for question in queryset:
            if not question.correct_choice:
                self.message_user(request, f"'{question.title}' has no correct choice set. Skipped.")
                continue

            # ✅ Skip already scored questions
            if question.is_scored:
                self.message_user(request, f"'{question.title}' already scored. Skipped.")
                continue

            answers = UserAnswer.objects.filter(question=question).select_related('user__profile')
            for answer in answers:
                profile, _ = Profile.objects.get_or_create(user=answer.user)

                profile.total_resolved_answers += 1
                if answer.choice == question.correct_choice:
                    profile.correct_answers += 1
                    profile.points += 10
                    answer.is_correct = True
                    answer.points_awarded = 10
                else:
                    answer.is_correct = False
                    answer.points_awarded = 0

                answer.save()
                profile.save()

            question.is_scored = True
            question.is_open = False
            question.save()

        self.message_user(request, "✅ Questions scored successfully.")

    score_questions.short_description = "⚽ Score selected questions"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['correct_choice'].queryset = obj.choices.all()
        return form


# CSV import form
class CSVImportForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.all())
    csv_file = forms.FileField()


class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    change_list_template = "quiz/event_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='import_csv'),
        ]
        return custom + urls

    def import_csv(self, request):
        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                event = form.cleaned_data['event']
                csv_file = form.cleaned_data['csv_file']
                decoded = csv_file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(decoded))

                helsinki = pytz.timezone("Europe/Helsinki")

                for row in reader:
                    start_time_str = row.get('start_time')
                    start_time = None
                    if start_time_str and start_time_str.strip():
                        naive = datetime.datetime.strptime(
                            start_time_str.strip(),
                            "%Y-%m-%d %H:%M"
                        )
                        start_time = helsinki.localize(naive)

                    q = Question.objects.create(
                        event=event,
                        title=row['question'],
                        start_time=start_time
                    )

                    for key in ['option1', 'option2', 'option3', 'option4']:
                        if row.get(key):
                            Choice.objects.create(question=q, text=row[key])

                self.message_user(request, "Questions imported!")
                return redirect('..')
        else:
            form = CSVImportForm()
        return render(request, 'quiz/csv_import.html', {'form': form})


# Register admins
admin.site.register(Event, EventAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
