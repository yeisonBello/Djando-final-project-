from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled

def submit(request, course_id):
    # Get the current user and course object
    user = request.user
    course = get_object_or_404(Course, pk=course_id)

    # Get the associated enrollment object
    enrollment = get_object_or_404(Enrollment, user=user, course=course)

    if request.method == 'POST':
        # Create a new submission object referring to the enrollment
        submission = Submission.objects.create(enrollment=enrollment)

        # Collect the selected choices from the HTTP request object
        selected_choice_ids = []
        for key, value in request.POST.items():
            if key.startswith('choice'):
                choice_id = int(value)
                selected_choice_ids.append(choice_id)

        # Add each selected choice object to the submission object
        selected_choices = Choice.objects.filter(id__in=selected_choice_ids)
        submission.choices.add(*selected_choices)

        # Redirect to the show_exam_result view with the submission id
        return redirect(reverse('onlinecourse:show_exam_result', args=[course_id, submission.id]))


def show_exam_result(request, course_id, submission_id):
    # Get course and submission based on their IDs
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)

    # Get the selected choice IDs from the submission record
    selected_choice_ids = submission.choices.values_list('id', flat=True)

    # Initialize variables to calculate the total score and store question results
    total_score = 0
    question_results = []

    # Iterate through the questions in the course
    for question in course.question_set.all():
        # Get all choices for the question
        all_choices = question.choice_set.all()

        # Check if each choice is correct or not and whether it was selected
        results = []
        for choice in all_choices:
            is_correct = choice.is_correct
            selected = choice.id in selected_choice_ids
            results.append({'choice': choice, 'is_correct': is_correct, 'selected': selected})

        # Calculate the grade point for the question
        grade_point = question.grade_point

        # Calculate the score for the question (either 0 or the grade point)
        score = grade_point if all(result['is_correct'] == result['selected'] for result in results) else 0

        # Update the total score
        total_score += score
        total_score = int(total_score)
        if total_score == 99:
            total_score=100

         

        question_results.append({'question': question, 'choices': results, 'grade_point': grade_point, 'score': score})

    # Determine if the learner passed the exam (you can set a passing score threshold)
    passing_score_threshold = 80  # Adjust this value as needed
    passed_exam = total_score >= passing_score_threshold

    # Render the template with the exam results
    context = {
        'course': course,
        'submission': submission,
        'question_results': question_results,
        'total_score': total_score,
        'passed_exam': passed_exam,
    }

    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)



# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))

