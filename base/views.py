import json
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model,login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.core.files.storage import default_storage
import os
from django.utils import timezone
from datetime import timedelta

from base.models import Course, CourseMaterial, Student, Tutor, VideoComment


# Create your views here.
User = get_user_model()

def index(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'tutor'):
            return redirect('tutor_dashboard')
        else:
            student = Student.objects.get(user=request.user)
            courses = Course.objects.all()
            context = {"student": student, 'courses': courses}
            return render(request, 'home.html', context)
    else:
        return redirect('login')

def signin(request):
    context = {'status': ''}
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(email=email, password=password)
        if user:
            messages.success(request, 'Logged in successfully')
            login(request, user)
            if hasattr(user, 'tutor'):
                return redirect('tutor_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Log in failed. Try again.')
            return render(request, 'login.html')
    return render(request, 'login.html', context)

def register(request):
    if request.method == "POST":
        name = request.POST["name"]
        names = name.split(' ')
        fname = ' '.join(names[:-1])
        lname = names[-1]
        email = request.POST["email"]
        ps1 = request.POST["ps1"]
        ps2 = request.POST["ps2"]

        if ps1 == ps2:
            try:
                new_user = User.objects.create_user(email=email, password=ps1)
                new_user.first_name = fname
                new_user.last_name = lname
                student = Student(user=new_user)
                if request.FILES:
                    student.profile_pic = request.FILES['profile_pic']
                student.save()
                new_user.save()
                messages.success(request, 'Account Successfully Created.')
                if request.user.is_authenticated:
                    logout(request)
                return redirect('home')
            except:
                messages.error(request, 'There was a problem with account creation. Try again.')
        else:
            messages.error(request, 'Password and confirm password should be the same.')
    context = {'status': 'active'}
    return render(request, 'register.html', context)

def signout(request):
    logout(request)
    return redirect('home')

@login_required
def playlist(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    playlist = CourseMaterial.objects.filter(course=course)
    
    context = {
        'playlist': playlist,
        'course': course,
    }
    return render(request, 'playlist.html', context)

@login_required
def save_course(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course')
            
            if not hasattr(request.user, 'student'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Only students can save courses'
                }, status=403)
            
            course = Course.objects.get(id=course_id)
            student = request.user.student
            
            # Check if course is already saved
            if course in student.saved_courses.all():
                # Unsave the course
                student.saved_courses.remove(course)
                saved = False
            else:
                # Save the course
                student.saved_courses.add(course)
                saved = True
            
            return JsonResponse({
                'status': 'success',
                'saved': saved,
                'savedCount': course.saved_by.count()  # Return updated count
            })
            
        except Course.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Course not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

def watch_video(request, id):
    video = CourseMaterial.objects.get(id=id)
    student = Student.objects.get(user=request.user)
    context = {"video": video, "user": request.user, "student": student}
    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_text = request.POST['comment-box']
        new_comment = VideoComment(course_material=video, student=student, comment=comment_text)
        new_comment.save()

    return render(request, 'watch-video.html', context)

def delete_comment(request, id):
    comment = VideoComment.objects.get(id=id)
    comment.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def edit_comment(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        comment_edit = body['comment_edit']
        comment_id = body['comment_id']
        prev_comment = VideoComment.objects.get(id=comment_id)
        prev_comment.comment = comment_edit
        prev_comment.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def like_video(request, id):
    video = CourseMaterial.objects.get(id=id)
    student = Student.objects.get(user=request.user)
    if (video not in student.liked_videos.all()):
        print(student.liked_videos.all())
        video.likes += 1
        student.liked_videos.add(video)
    else:
        print(student.liked_videos.all())
        video.likes -= 1
        student.liked_videos.remove(video)
    video.likes = max(video.likes, 0)
    video.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def about(request):
    student = Student.objects.get(user=request.user)
    context = {"student": student}
    return render(request, 'about.html', context)

def contact(request):
    student = Student.objects.get(user=request.user)
    context = {"student": student}
    return render(request, 'contact.html', context)

def courses(request):
    student = Student.objects.get(user=request.user)
    courses = Course.objects.all()
    context = {"student": student, 'courses': courses}
    return render(request, 'courses.html', context)

def tutors(request):
    search_query = request.GET.get('search_box', '')
    
    if search_query:
        tutors = Tutor.objects.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    else:
        tutors = Tutor.objects.all()

    # Calculate video and like counts for each tutor
    for tutor in tutors:
        video_count = 0
        like_count = 0
        for course in tutor.course_set.all():
            video_count += course.materials.count()
            for material in course.materials.all():
                like_count += material.likes

        tutor.video_count = video_count
        tutor.like_count = like_count

    context = {
        'tutors': tutors,
        'search_query': search_query,
        'student': Student.objects.get(user=request.user) if request.user.is_authenticated else None
    }
    return render(request, 'teachers.html', context)

def profile(request):
    student = Student.objects.get(user=request.user)
    user = request.user
    context = {
        'saved_playlists_count': student.saved_courses.count(),
        'liked_videos_count': student.liked_videos.count(),
        'comments_count': student.comments.count(),
    }
    return render(request, 'profile.html', context)

def teacher_profile(request, id):
    teacher = Tutor.objects.get(id=id)
    student = Student.objects.get(user=request.user)
    context = {"teacher": teacher, "student": student}
    return render(request, 'teacher_profile.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        student = user.student

        # Update user information
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Update student information
        student.role = request.POST.get('role', 'learner')

        # Handle profile picture upload
        if 'profile_pic' in request.FILES:
            # Delete old profile picture if it exists
            if student.profile_pic:
                try:
                    old_pic_path = student.profile_pic.path
                    if os.path.exists(old_pic_path):
                        default_storage.delete(old_pic_path)
                except:
                    pass
            
            student.profile_pic = request.FILES['profile_pic']

        try:
            user.save()
            student.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return render(request, 'update_profile.html')

@login_required
def saved_playlists(request):
    student = Student.objects.get(user=request.user)
    saved_courses = student.saved_courses.all()
    context = {
        "student": student,
        "saved_courses": saved_courses
    }
    return render(request, 'saved_playlists.html', context)

@login_required
def liked_videos(request):
    student = Student.objects.get(user=request.user)
    liked_videos = student.liked_videos.all()
    context = {
        "student": student,
        "liked_videos": liked_videos
    }
    return render(request, 'liked_videos.html', context)

@login_required
def user_comments(request):
    student = Student.objects.get(user=request.user)
    user_comments = student.comments.all().order_by('-added_at')
    context = {
        "student": student,
        "user_comments": user_comments
    }
    return render(request, 'user_comments.html', context)

@login_required
def tutor_dashboard(request):
    if not hasattr(request.user, 'tutor'):
        messages.error(request, 'You must be a tutor to access this page.')
        return redirect('home')
    
    tutor = request.user.tutor
    courses = tutor.course_set.all()
    
    # Calculate statistics
    total_students = Student.objects.filter(saved_courses__course_tutor=tutor).distinct().count()
    courses_count = courses.count()
    total_videos = sum(course.materials.count() for course in courses)
    total_likes = sum(
        material.likes 
        for course in courses 
        for material in course.materials.all()
    )
    
    # Get recent data
    recent_courses = courses.order_by('-created_at')[:4]
    recent_comments = VideoComment.objects.filter(
        course_material__course__course_tutor=tutor
    ).order_by('-added_at')[:5]
    
    context = {
        'tutor': tutor,
        'total_students': total_students,
        'courses_count': courses_count,
        'total_videos': total_videos,
        'total_likes': total_likes,
        'recent_courses': recent_courses,
        'recent_comments': recent_comments,
    }
    
    return render(request, 'tutor_dashboard.html', context)

@login_required
def add_course(request):
    if not hasattr(request.user, 'tutor'):
        return redirect('home')
        
    if request.method == 'POST':
        course = Course.objects.create(
            course_tutor=request.user.tutor,
            course_name=request.POST.get('course_name'),
            course_description=request.POST.get('description'),
            course_image=request.FILES.get('course_image'),
            level=request.POST.get('level')
        )
        return redirect('my_courses')
        
    context = {
        'tutor': request.user.tutor
    }
    return render(request, 'tutor/add_course.html', context)

@login_required
def my_courses(request):
    if not hasattr(request.user, 'tutor'):
        return redirect('home')
            
    courses = Course.objects.filter(course_tutor=request.user.tutor)
    
    # Add additional stats for each course
    for course in courses:
        course.student_count = Student.objects.filter(saved_courses=course).count()
        course.total_likes = sum(material.likes for material in course.materials.all())
        
    context = {
        'tutor': request.user.tutor,
        'courses': courses
    }
    return render(request, 'tutor/my_courses.html', context)

@login_required
def edit_course(request, course_id):
    if not hasattr(request.user, 'tutor'):
        return redirect('home')
        
    course = get_object_or_404(Course, id=course_id, course_tutor=request.user.tutor)
    
    if request.method == 'POST':
        course.course_name = request.POST.get('course_name')
        course.description = request.POST.get('description')
        if 'course_image' in request.FILES:
            course.course_image = request.FILES['course_image']
        course.level = request.POST.get('level')
        course.save()
        return redirect('my_courses')
        
    context = {
        'tutor': request.user.tutor,
        'course': course
    }
    return render(request, 'tutor/edit_course.html', context)

@login_required
def delete_course(request, course_id):
    if not hasattr(request.user, 'tutor'):
        return JsonResponse({'status': 'error'})
        
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id, course_tutor=request.user.tutor)
        course.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def students_list(request):
    if not hasattr(request.user, 'tutor'):
        return redirect('home')
        
    tutor = request.user.tutor
    courses = Course.objects.filter(course_tutor=tutor)
    
    # Get all students enrolled in any of the tutor's courses
    enrollments = []
    for course in courses:
        students = Student.objects.filter(saved_courses=course)
        for student in students:
            # Calculate engagement based on likes and comments
            student_likes = course.materials.filter(liked_by=student).count()
            student_comments = VideoComment.objects.filter(
                student=student,
                course_material__course=course
            ).count()
            
            # Simple engagement score
            engagement = ((student_likes * 2) + student_comments) / max(course.materials.count(), 1) * 100
            
            enrollments.append({
                'student': student,
                'course': course,
                'enrolled_date': student.saved_courses.through.objects.filter(
                    course=course, student=student
                ).first().created_at,
                'engagement': round(engagement, 1)
            })
    
    context = {
        'tutor': tutor,
        'courses': courses,
        'enrollments': enrollments
    }
    return render(request, 'tutor/students.html', context)

@login_required
def analytics(request):
    if not hasattr(request.user, 'tutor'):
        return redirect('home')
        
    tutor = request.user.tutor
    courses = Course.objects.filter(course_tutor=tutor)
    
    # Get date range from request, default to last 30 days
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Course performance data
    course_data = []
    for course in courses:
        total_likes = sum(material.likes for material in course.materials.all())
        total_comments = VideoComment.objects.filter(
            course_material__course=course
        ).count()
        
        students = Student.objects.filter(
            saved_courses=course
        ).count()
        
        course_data.append({
            'name': course.course_name,
            'likes': total_likes,
            'comments': total_comments,
            'students': students,
            'videos': course.materials.count()
        })
    
    # Get popular videos
    popular_videos = []
    for course in courses:
        for video in course.materials.all():
            popular_videos.append({
                'title': video.title,
                'likes': video.likes,
                'comments': video.comments.count()
            })
    
    # Sort by likes and get top 5
    popular_videos.sort(key=lambda x: x['likes'], reverse=True)
    popular_videos = popular_videos[:5]
    
    # Calculate percentages for visualization
    if popular_videos:
        max_likes = max(video['likes'] for video in popular_videos)
        max_comments = max(video['comments'] for video in popular_videos)
        
        for video in popular_videos:
            video['likes_percentage'] = (video['likes'] / max_likes * 100) if max_likes else 0
            video['comments_percentage'] = (video['comments'] / max_comments * 100) if max_comments else 0
    
    context = {
        'tutor': tutor,
        'course_data': json.dumps(course_data),
        'popular_videos': popular_videos
    }
    return render(request, 'tutor/analytics.html', context)

@login_required
def student_progress(request, student_id, course_id):
    if not hasattr(request.user, 'tutor'):
        return redirect('home')
        
    student = get_object_or_404(Student, id=student_id)
    course = get_object_or_404(Course, id=course_id, course_tutor=request.user.tutor)
    
    # Get student's activity in the course
    course_videos = course.materials.all()
    liked_videos = course_videos.filter(liked_by=student)
    commented_videos = course_videos.filter(comments__student=student).distinct()
    
    activity_data = {
        'total_videos': course_videos.count(),
        'liked_videos': liked_videos.count(),
        'commented_videos': commented_videos.count(),
        'recent_comments': VideoComment.objects.filter(
            student=student,
            course_material__course=course
        ).order_by('-added_at')[:5]
    }
    
    context = {
        'tutor': request.user.tutor,
        'student': student,
        'course': course,
        'activity_data': activity_data
    }
    return render(request, 'tutor/student_progress.html', context)

@login_required
def tutor_profile(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id)
    courses = Course.objects.filter(course_tutor=tutor)
    
    context = {
        'tutor': tutor,
        'courses': courses,
    }
    return render(request, 'tutor_profile.html', context)

@login_required
def saved_courses(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')
        
    saved_courses = request.user.student.saved_courses.all()
    context = {
        'saved_courses': saved_courses
    }
    return render(request, 'student/saved_courses.html', context)

def search(request):
    query = request.GET.get('query', '')
    
    if query:
        # Search in course names, descriptions, and tutor names
        courses = Course.objects.filter(
            Q(course_name__icontains=query) |
            Q(course_description__icontains=query) |
            Q(course_tutor__user__first_name__icontains=query) |
            Q(course_tutor__user__last_name__icontains=query)
        ).distinct()
        
        # Search in video titles and descriptions
        videos = CourseMaterial.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
    else:
        courses = []
        videos = []
    
    context = {
        'query': query,
        'courses': courses,
        'videos': videos,
        'total_results': len(courses) + len(videos)
    }
    return render(request, 'search.html', context)  