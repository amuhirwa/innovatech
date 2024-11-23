from django.contrib import admin

from base.models import Course, CourseMaterial, Student, Tutor, User

# Register your models here.
admin.site.register([User, Course, CourseMaterial, Student, Tutor])