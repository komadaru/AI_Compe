from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, user_name, password=None, role='Student'):
        if not email:
            raise ValueError('The Email field must be set')
        if not user_name:
            raise ValueError('The User name field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, user_name, password=None, role='Admin'):
        user = self.create_user(email, user_name, password, role)
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Users(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # AbstractBaseUser already has a password field
    role = models.CharField(max_length=50, default='Student')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    class Meta:
        db_table = 'Users'  # テーブル名を明示的に指定

    def __str__(self):
        return self.user_name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

class Admins(models.Model):
    id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50, default='Admin')

    class Meta:
        db_table = 'Admins'  # テーブル名を明示的に指定

    def __str__(self):
        return self.user_name

class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Courses'

    def __str__(self):
        return self.course_name

class Assignments(models.Model):
    id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50)
    due_date = models.DateField()
    answer_csv = models.TextField()

    class Meta:
        db_table = 'Assignments'

    def __str__(self):
        return self.title

class UserAssignments(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignments, on_delete=models.CASCADE)
    submitted_csv = models.TextField()
    submission_date = models.DateTimeField(default=timezone.now)
    score = models.FloatField()

    class Meta:
        db_table = 'UserAssignments'

    def __str__(self):
        return f"{self.user.username} - {self.assignment.title}"


class UserCourses(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)

    class Meta:
        unique_together = (('user', 'course'),)
        db_table = 'UserCourses'

    def __str__(self):
        return f'{self.user.user_name} - {self.course.course_name}'

class Grades(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignments, on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        unique_together = (('user', 'assignment'),)
        db_table = 'Grades'

    def __str__(self):
        return f'{self.user.user_name} - {self.assignment.title}'

class AdminCourses(models.Model):
    admin = models.ForeignKey(Admins, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    permission = models.CharField(max_length=50)

    class Meta:
        unique_together = (('admin', 'course'),)
        db_table = 'AdminCourses'

    def __str__(self):
        return f'{self.admin.user_name} - {self.course.course_name}'

class AdminAssignments(models.Model):
    admin = models.ForeignKey(Admins, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignments, on_delete=models.CASCADE)
    permission = models.CharField(max_length=50)

    class Meta:
        unique_together = (('admin', 'assignment'),)
        db_table = 'AdminAssignments'

    def __str__(self):
        return f'{self.admin.user_name} - {self.assignment.title}'
