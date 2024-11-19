# Users/urls.py
from django.urls import path
from .views import CustomLoginView, SignUpView, main_menu, course_assignments, csv_submission, code_submission, code_submission_result

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('mainmenu/', main_menu, name='main_menu'),
    path('courses/<int:course_id>/assignments/', course_assignments, name='course_assignments'),
    path('assignments/<int:assignment_id>/csv_submission/', csv_submission, name='csv_submission'),
    path('assignments/<int:assignment_id>/code_submission/', code_submission, name='code_submission'),
    path('assignments/<int:assignment_id>/code_submission_result/', code_submission_result, name='code_submission_result'),
]
