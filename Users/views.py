from django.urls import reverse_lazy, reverse
from django.views import generic, View
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CsvUploadForm, CodeSubmissionForm
from .models import Users, Assignments, UserCourses, Courses, UserAssignments
import logging
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.http import HttpResponseRedirect
import traceback
import os
import subprocess
import tempfile
import threading
import time

logger = logging.getLogger(__name__)

class CustomLoginView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'users/login.html')

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email and password:
            try:
                user = Users.objects.get(email=email)
                if check_password(password, user.password):
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, 'ログインに成功しました。')
                    return redirect('main_menu')
                else:
                    messages.error(request, '無効なメールアドレスまたはパスワードです。')
            except Users.DoesNotExist:
                messages.error(request, '無効なメールアドレスまたはパスワードです。')
        else:
            messages.error(request, 'メールアドレスとパスワードを入力してください。')

        return render(request, 'users/login.html')

class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        logger.debug("フォームバリデーション成功")
        user = form.save(commit=False)
        logger.debug(f"Creating user: {user.email}")
        user.save()
        logger.debug(f"User created: {user.email}")
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, 'アカウント作成に成功しました。')
        return redirect('login')

    def form_invalid(self, form):
        logger.error(f"フォームバリデーション失敗: {form.errors}")
        return super().form_invalid(form)

@login_required
def main_menu(request):
    user = request.user
    user_courses = UserCourses.objects.filter(user=user)
    context = {
        'user_courses': user_courses,
    }
    return render(request, 'users/main_menu.html', context)


@login_required
def course_assignments(request, course_id):
    course = get_object_or_404(Courses, id=course_id)
    assignments = Assignments.objects.filter(course=course)

    # ユーザーの提出物を取得
    user_assignments = {ua.assignment_id: ua for ua in
                        UserAssignments.objects.filter(user=request.user, assignment__in=assignments)}

    context = {
        'course': course,
        'assignments': assignments,
        'user_assignments': user_assignments,
    }
    return render(request, 'users/assignments.html', context)

@login_required
def csv_submission(request, assignment_id):
    assignment = get_object_or_404(Assignments, id=assignment_id)

    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            submitted_csv = request.FILES['file']
            submitted_content = submitted_csv.read().decode('utf-8')

            # BOMを削除
            if submitted_content.startswith('\ufeff'):
                submitted_content = submitted_content[1:]

            # 改行コードの修正
            submitted_content = submitted_content.replace('\r\n', '\n').strip()

            # 正解CSVデータの改行コードの修正
            correct_csv_content = assignment.answer_csv.replace('\\n', '\n').strip()
            correct_csv = correct_csv_content.split('\n')

            # 提出されたCSVデータを行単位で分割
            submitted_csv_lines = submitted_content.split('\n')

            # 正解率の計算
            correct_count = 0
            for correct, submitted in zip(correct_csv, submitted_csv_lines):
                if correct.strip() == submitted.strip():
                    correct_count += 1
            score = correct_count / len(correct_csv) * 100

            # 既存の提出物を削除
            UserAssignments.objects.filter(user=request.user, assignment=assignment).delete()

            # UserAssignmentsに保存
            UserAssignments.objects.create(
                user=request.user,
                assignment=assignment,
                submitted_csv=submitted_content,
                score=score,
                submission_date=timezone.now()
            )

            return HttpResponseRedirect(reverse('csv_submission', args=[assignment_id]))
    else:
        form = CsvUploadForm()

    # 提出結果を取得
    user_assignments = UserAssignments.objects.filter(user=request.user, assignment=assignment)

    context = {
        'assignment': assignment,
        'form': form,
        'user_assignments': user_assignments,
    }
    return render(request, 'users/csv_submission.html', context)

logger = logging.getLogger(__name__)

def execute_user_code_docker(code):
    try:
        # 提出コードを一時ファイルに保存
        with open("submitted_code.py", "w") as code_file:
            code_file.write(code)

        # Dockerコマンドの実行
        # result = subprocess.run(
        #     ['docker', 'build', '-t', 'submission_image', '.'], check=True
        # )
        start_time = time.time()
        result = subprocess.run(
            ['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/app', 'submission_image'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # 無限ループ対策
        # output = ""
        # while True:
        #     if result.poll() is not None:
        #         break
        #     time.sleep(1)
        #     current_output = result.stdout.read(1)
        #     if current_output:
        #         output += current_output
        #     elapsed_time = time.time() - start_time
        #     if elapsed_time > 10 and not output:
        #         result.kill()
        #         return "", "Execution timed out (possibly an infinite loop).", -1
        #
        # stdout, stderr = result.communicate()
        # output += stdout

        # FileNotFoundErrorを無視
        if "FileNotFoundError" in result.stderr:
            result.stderr = ""
            result.returncode = 0

        return result.stdout, result.stderr, result.returncode
    except subprocess.CalledProcessError as e:
        return '', str(e), e.returncode
    except Exception as e:
        return '', str(e), -1

@login_required
def code_submission(request, assignment_id):
    assignment = get_object_or_404(Assignments, id=assignment_id)
    execution_result = None

    if request.method == 'POST':
        form = CodeSubmissionForm(request.POST)
        if form.is_valid():
            submitted_code = form.cleaned_data['code']
            logger.debug(f"Submitted code: {submitted_code}")

            # 既存の提出物を削除
            UserAssignments.objects.filter(user=request.user, assignment=assignment).delete()

            # 提出コードをDockerコンテナで実行
            stdout, stderr, returncode = execute_user_code_docker(submitted_code)
            if returncode == 0:
                execution_result = "このコードは正常に実行可能です。\n"
                score = 100  # 成功した場合のスコア
            elif 'Execution timed out (possibly an infinite loop)' in stderr:
                logger.error(f"Execution timed out (possibly an infinite loop): {stderr}")
                execution_result = "Execution timed out (possibly an infinite loop)."
                score = 0  # 無限ループと判断
            else:
                logger.error(f"Docker run failed with return code {returncode}: {stderr}")
                execution_result = "このコードにはエラーが存在します。"
                score = 0  # エラーが発生した場合のスコア

            # UserAssignmentsに保存
            UserAssignments.objects.create(
                user=request.user,
                assignment=assignment,
                submitted_csv=submitted_code,  # submitted_csv フィールドにコードを保存
                score=score,
                submission_date=timezone.now()
            )
            logger.debug("User assignment saved successfully.")

            # 再度ページをレンダリングして結果を表示
            user_assignments = UserAssignments.objects.filter(user=request.user, assignment=assignment)
            context = {
                'assignment': assignment,
                'form': form,
                'user_assignments': user_assignments,
                'execution_result': execution_result
            }
            return render(request, 'users/code_submission.html', context)
        else:
            logger.debug("Form is not valid.")
    else:
        form = CodeSubmissionForm()

    # 提出結果を取得
    user_assignments = UserAssignments.objects.filter(user=request.user, assignment=assignment)
    context = {
        'assignment': assignment,
        'form': form,
        'user_assignments': user_assignments,
        'execution_result': execution_result
    }
    return render(request, 'users/code_submission.html', context)

@login_required
def code_submission_result(request, assignment_id):
    assignment = get_object_or_404(Assignments, id=assignment_id)
    user_assignment = UserAssignments.objects.filter(user=request.user, assignment=assignment)
    context = {
        'assignment': assignment,
        'user_assignment': user_assignment,
    }
    return render(request, 'users/code_submission_result.html', context)