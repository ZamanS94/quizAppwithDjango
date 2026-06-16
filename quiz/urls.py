from django.urls import path
from . import views

urlpatterns = [
    path('', views.leaderboard, name='home'),
    path('questions/', views.question_list, name='question_list'),
    path('submit/<int:question_id>/', views.submit_answer, name='submit_answer'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('signup/', views.signup, name='signup'),
    path('my-predictions/', views.my_predictions, name='my_predictions'),
]
