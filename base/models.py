from django.db import models

from email.policy import default
from random import choices
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator, FileExtensionValidator
import random


# Create your models here.
class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Model representing a User.

    Attributes:
        id (Integer): The primary key and unique identifier of the user.
        email (String): The email of the user.
        phone_number (String): The phone number of the user.
        first_name (String): The first name of the user.
        last_name (String): The last name of the user.
        password (String): The password of the user.
        user_role (String): The role of the user.
        totalPoints (Integer): The total achievement points of the user.
        canShare (Boolean): Whether the user can share his sharecode or not.
        created_at (DateTime): The date and time when the user was created.
    """
    username = None
    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    REQUIRED_FIELDS = []      
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        verbose_name=_('groups'),
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text=_('Specific permissions for this user.'),
        verbose_name=_('user permissions'),
    )


class Student(models.Model):
    """
    Model representing a student.

    Attributes:
        user (OneToOneField): The user associated with the student.
        level (CharField): The education level of the student.
        country (CharField): The country of residence of the student.
        created_at (DateField): The date when the student record was created.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to="profile_pics", default="profile_pics/Default_pfp.svg") # Should also change this to imagefield
    profile_views = models.IntegerField(validators=[MaxValueValidator(100)], default=0)
    bio = models.TextField(blank=True, null=True)
    preferred_name = models.CharField(max_length=20, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    enrolled_courses = models.ManyToManyField('Course', related_name='enrolled_students')
    liked_videos = models.ManyToManyField('CourseMaterial')
    saved_courses = models.ManyToManyField('Course', related_name='saved_students')
    created_at = models.DateField(auto_now_add=True)
    socials = models.OneToOneField('Socials', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.user.first_name
    
class Socials(models.Model):
    github = models.URLField(max_length=200,blank=True, null=True)
    instagram = models.URLField(max_length=200, blank=True, null=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True)
    facebook = models.URLField(max_length=200, blank=True, null=True)
    twitter = models.URLField(max_length=200, blank=True, null=True) 
    number = models.CharField(max_length=20, blank=True, null=True)


class Tutor(models.Model):
    """
    Model representing a tutor.

    Attributes:
        user (OneToOneField): The user associated with the tutor.
        level (CharField): The education level of the tutor.
        subject (CharField): The subject taught by the tutor.
        verified (BooleanField): Indicates whether the tutor is verified.
        created_at (DateField): The date when the tutor record was created.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to="profile_pics", default="https://upload.wikimedia.org/wikipedia/commons/2/2c/Default_pfp.svg") # Should also change this to imagefield
    subject = models.CharField(max_length=100)
    verified = models.BooleanField(default=False)
    rating = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    likes = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        if self.user.is_superuser:
            return "Admin"
        return self.user.first_name + " " + self.user.last_name

class Course(models.Model):
    """
    Model representing a course.

    Attributes:
        course_name (CharField): The name of the course.
        course_description (TextField): The description of the course.
        time_to_complete (CharField): The estimated time to complete the course.
        price (DecimalField): The price of the course.
        created_at (DateField): The date when the course record was created.
    """
    course_name = models.CharField(max_length=100)
    course_image = models.ImageField(upload_to="course_images", default="course_images/default.jpg")
    course_description = models.TextField()
    course_category = models.TextField(blank=True, null=True)
    course_tutor = models.ForeignKey(Tutor, on_delete=models.SET_DEFAULT, default=1)
    time_to_complete = models.CharField(max_length=100)
    price = models.DecimalField(blank=True, validators=[MinValueValidator(0)], decimal_places=2, max_digits=10, default=0.0)
    level = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    saved_by = models.ManyToManyField(Student, related_name='courses_saved')

    @property
    def saved_count(self):
        return self.saved_by.count()

    def __str__(self):
        return self.course_name


class CourseMaterial(models.Model):
    """
    Model representing course materials for a course week.

    Attributes:
        week (ForeignKey): The week associated with the material.
        material_type (CharField): The type of material (text or video).
        text (TextField): The text content (if material_type is text).
        video (FileField): The video file (if material_type is video).
    """
    TEXT = 'text'
    VIDEO = 'video'
    MATERIAL_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (VIDEO, 'Video'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    thumbnail = models.TextField(default="https://www.myutilitygenius.co.uk/assets/images/blogs/default-image.jpg")
    title = models.CharField(max_length=200)
    likes = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    time_to_complete = models.IntegerField(blank=True, null=True)
    video = models.FileField(upload_to='videos_uploaded', null=True, blank=True,
                             validators=[FileExtensionValidator(
                                 allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])
    

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class VideoComment(models.Model):
    """
    Represents a comment on a course.

    Attributes:
        course (Course): The course on which the comment is made.
        user (User): The user who made the comment.
        comment (str): The text of the comment.
        added_at (DateTime): The date and time when the comment was added.
    """
    course_material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE, related_name="comments")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    added_at = models.DateTimeField(auto_now=True)
