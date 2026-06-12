import openpyxl
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
import calendar
from django.core.mail import send_mail
from django.conf import settings
from reportlab.pdfgen import canvas
from django.http import HttpResponse


from .models import Attendance, Project, Task, ExportRequest, Announcement, CompletedProject
from .forms import (
    LoginForm,
    AttendanceForm,
    ProjectForm,
    TaskForm,
    TaskStatusUpdateForm,
    EmployeeCreationForm,
)

from .models import Leave


# ==========================
# LOGIN VIEW
# ==========================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            messages.success(
                request,
                f'Welcome, {user.username}!'
            )

            return redirect('dashboard')

        else:
            messages.error(
                request,
                'Invalid username or password.'
            )

    return render(
        request,
        'management_app/login.html',
        {'form': form}
    )


# ==========================
# LOGOUT VIEW
# ==========================
@login_required
def logout_view(request):
    logout(request)

    messages.success(
        request,
        'You have been logged out successfully.'
    )

    return redirect('login')


# ==========================
# DASHBOARD VIEW
# ==========================
@login_required
def dashboard(request):

    if request.user.is_superuser:

        total_employees = User.objects.filter(
            is_superuser=False
        ).count()

        total_projects = Project.objects.count()

        total_tasks = Task.objects.count()

        present_today = Attendance.objects.filter(
            date=timezone.now().date()
        ).count()

        context = {
            'is_admin': True,
            'total_employees': total_employees,
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'present_today': present_today,
        }

    else:

        my_projects = Project.objects.filter(
            assigned_employees=request.user
        ).count()

        pending_tasks = Task.objects.filter(
            employee=request.user,
            status='Pending'
        ).count()

        completed_tasks = Task.objects.filter(
            employee=request.user,
            status='Completed'
        ).count()

        attendance_marked = Attendance.objects.filter(
            employee=request.user,
            date=timezone.now().date()
        ).exists()

        context = {
            'is_admin': False,
            'my_projects': my_projects,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'attendance_marked': attendance_marked,
        }

    return render(
        request,
        'management_app/dashboard.html',
        context
    )


# ==========================
# MARK ATTENDANCE
# ==========================
@login_required
def mark_attendance(request):

    today = timezone.now().date()

    attendance = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()

    if attendance:
        messages.warning(
            request,
            'You have already marked attendance today.'
        )

        return redirect('attendance_history')

    Attendance.objects.create(
        employee=request.user
    )

    messages.success(
        request,
        'Attendance marked successfully.'
    )

    return redirect('attendance_history')


# ==========================
# CHECK OUT
# ==========================
@login_required
def check_out(request):

    today = timezone.now().date()

    attendance = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()

    if not attendance:
        messages.error(
            request,
            'Please check in first.'
        )

        return redirect('dashboard')

    if attendance.check_out:
        messages.warning(
            request,
            'You have already checked out.'
        )

        return redirect('attendance_history')

    attendance.check_out = timezone.localtime()
    attendance.save()

    messages.success(
        request,
        'Check-out recorded successfully.'
    )

    return redirect('attendance_history')


# ==========================
# ATTENDANCE HISTORY
# ==========================
@login_required
def attendance_history(request):

    if request.user.is_superuser:

        attendances = Attendance.objects.all()

    else:

        attendances = Attendance.objects.filter(
            employee=request.user
        )

    return render(
        request,
        'management_app/attendance_history.html',
        {'attendances': attendances}
    )
# ==========================
# PROJECT LIST
# ==========================
@login_required
def project_list(request):

    if request.user.is_superuser:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(
            assigned_employees=request.user
        )

    return render(
        request,
        'management_app/project_list.html',
        {'projects': projects}
    )


# ==========================
# CREATE PROJECT
# ==========================
@login_required
def project_create(request):

    if not request.user.is_superuser:
        messages.error(
            request,
            'You are not authorized to create projects.'
        )
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProjectForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Project created successfully.'
            )

            return redirect('project_list')

    else:
        form = ProjectForm()

    return render(
        request,
        'management_app/project_form.html',
        {
            'form': form,
            'title': 'Create Project'
        }
    )


# ==========================
# UPDATE PROJECT
# ==========================
@login_required
def project_update(request, pk):

    if not request.user.is_superuser:
        messages.error(
            request,
            'You are not authorized to edit projects.'
        )
        return redirect('dashboard')

    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        form = ProjectForm(
            request.POST,
            instance=project
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Project updated successfully.'
            )

            return redirect('project_list')

    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        'management_app/project_form.html',
        {
            'form': form,
            'title': 'Edit Project'
        }
    )


# ==========================
# DELETE PROJECT
# ==========================
@login_required
def project_delete(request, pk):

    if not request.user.is_superuser:
        messages.error(
            request,
            'You are not authorized to delete projects.'
        )
        return redirect('dashboard')

    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        project.delete()

        messages.success(
            request,
            'Project deleted successfully.'
        )

        return redirect('project_list')

    return render(
        request,
        'management_app/project_delete.html',
        {'project': project}
    )


# ==========================
# TASK LIST
# ==========================
@login_required
def task_list(request):

    if request.user.is_superuser:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(
            employee=request.user
        )

    return render(
        request,
        'management_app/task_list.html',
        {'tasks': tasks}
    )


# ==========================
# CREATE TASK
# ==========================
@login_required
def task_create(request):

    if not request.user.is_superuser:
        messages.error(
            request,
            'You are not authorized to create tasks.'
        )
        return redirect('dashboard')

    if request.method == 'POST':

        form = TaskForm(request.POST)

        if form.is_valid():

            task = form.save()

            if task.employee.email:

                try:
                    send_mail(
                        "New Task Assigned",
                        f"You have been assigned a new task.\n\nTask: {task.title}",
                        settings.EMAIL_HOST_USER,
                        [task.employee.email],
                        fail_silently=True
                    )
                except:
                    pass

                messages.success(
                    request,
                    "Task assigned successfully."
                )

                return redirect("task_list")

    else:

        form = TaskForm()

    return render(
        request,
        'management_app/task_form.html',
        {
            'form': form,
            'title': 'Assign Task'
        }
    )


# ==========================
# UPDATE TASK STATUS
# ==========================
@login_required
def task_update(request, pk):

    task = get_object_or_404(Task, pk=pk)

    if (
        not request.user.is_superuser and
        task.employee != request.user
    ):
        messages.error(
            request,
            'You are not authorized to update this task.'
        )

        return redirect('task_list')

    if request.method == 'POST':
        form = TaskStatusUpdateForm(
            request.POST,
            instance=task
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Task status updated successfully.'
            )

            return redirect('task_list')

    else:
        form = TaskStatusUpdateForm(
            instance=task
        )

    return render(
        request,
        'management_app/task_update.html',
        {
            'form': form,
            'task': task
        }
    )


# ==========================
# CREATE EMPLOYEE
# ==========================
@login_required
def employee_create(request):

    if not request.user.is_superuser:
        messages.error(
            request,
            'You are not authorized to create employees.'
        )

        return redirect('dashboard')

    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Employee created successfully.'
            )

            return redirect('employee_list')

    else:
        form = EmployeeCreationForm()

    return render(
        request,
        'management_app/employee_form.html',
        {
            'form': form,
            'title': 'Create Employee'
        }
    )


# ==========================
# EMPLOYEE LIST
# ==========================
@login_required
def employee_list(request):

    if not request.user.is_superuser:
        messages.error(
            request,
            'You are not authorized to view employees.'
        )

        return redirect('dashboard')

    employees = User.objects.filter(
        is_superuser=False
    )

    return render(
        request,
        'management_app/employee_list.html',
        {'employees': employees}
    )

@login_required
def attendance(request):
    return render(
        request,
        'management_app/attendance.html'
    )

#=======================
#      Leave
#=======================

@login_required
def apply_leave(request):

    if request.method == "POST":

        leave_type = request.POST.get("leave_type")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason")

        Leave.objects.create(
            employee=request.user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
        )

        messages.success(
            request,
            "Leave request submitted successfully."
        )

        return redirect("my_leaves")

    return render(
        request,
        "management_app/apply_leave.html"
    )

@login_required
def my_leaves(request):

    leaves = Leave.objects.filter(
        employee=request.user
    ).order_by("-applied_on")

    return render(
        request,
        "management_app/my_leaves.html",
        {
            "leaves": leaves
        }
    )

@login_required
def leave_requests(request):

    if not request.user.is_superuser:
        return redirect("dashboard")

    leaves = Leave.objects.all().order_by(
        "-applied_on"
    )

    return render(
        request,
        "management_app/leave_requests.html",
        {
            "leaves": leaves
        }
    )

@login_required
def approve_leave(request, pk):

    if not request.user.is_superuser:
        return redirect("dashboard")

    leave = get_object_or_404(
        Leave,
        id=pk
    )

    leave.status = "Approved"

    leave.save()

    if leave.employee.email:

        try:
            send_mail(
                "Leave Approved",
                f"Dear {leave.employee.username}, your leave request has been approved.",
                settings.EMAIL_HOST_USER,
                [leave.employee.email],
                fail_silently=True
            )
        except:
            pass

    messages.success(
        request,
        "Leave Approved Successfully."
    )

    return redirect(
        "leave_requests"
    )

@login_required
def reject_leave(request, pk):

    if not request.user.is_superuser:
        return redirect("dashboard")

    leave = get_object_or_404(
        Leave,
        id=pk
    )

    leave.status = "Rejected"

    leave.save()

    if leave.employee.email:

        try:
            send_mail(
                "Leave Rejected",
                f"Dear {leave.employee.username}, your leave request has been rejected.",
                settings.EMAIL_HOST_USER,
                [leave.employee.email],
                fail_silently=True
            )
        except:
            pass

    messages.success(
        request,
        "Leave Rejected Successfully."
    )

    return redirect(
        "leave_requests"
    )

@login_required
def announcement_list(request):

    announcements = Announcement.objects.all().order_by(
        '-created_at'
    )

    return render(
        request,
        'management_app/announcement_list.html',
        {
            'announcements': announcements
        }
    )

#=======================
#    Announcement
#=======================

@login_required
def announcement_create(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    if request.method == "POST":

        title = request.POST.get("title")
        message = request.POST.get("message")

        Announcement.objects.create(
            title=title,
            message=message,
            created_by=request.user
        )

        users = User.objects.exclude(
            email=""
        )

        emails = []

        for user in users:
            emails.append(user.email)

        send_mail(
            subject=title,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=emails,
            fail_silently=True
        )

        messages.success(
            request,
            "Announcement Created and Email Sent."
        )

        return redirect(
            'announcement_list'
        )

    return render(
        request,
        'management_app/announcement_form.html'
    )

#=======================
#     Export request
#=======================

@login_required
def export_request(request):

    if request.method == "POST":

        report_type = request.POST.get(
            "report_type"
        )

        ExportRequest.objects.create(
            employee=request.user,
            report_type=report_type
        )

        messages.success(
            request,
            "Export request submitted."
        )

        return redirect(
            "my_export_requests"
        )

    return render(
        request,
        "management_app/export_request.html"
    )


@login_required
def my_export_requests(request):

    requests = ExportRequest.objects.filter(
        employee=request.user
    ).order_by(
        "-requested_on"
    )

    return render(
        request,
        "management_app/my_export_requests.html",
        {
            "requests": requests
        }
    )


@login_required
def export_requests(request):

    if not request.user.is_superuser:
        return redirect(
            "dashboard"
        )

    requests = ExportRequest.objects.all().order_by(
        "-requested_on"
    )

    return render(
        request,
        "management_app/export_requests.html",
        {
            "requests": requests
        }
    )


@login_required
def approve_export(request, pk):

    if not request.user.is_superuser:
        return redirect("dashboard")

    obj = ExportRequest.objects.get(
        id=pk
    )

    obj.status = "Approved"
    obj.save()

    try:
        send_mail(
            "Export Request Approved",
            f"Your {obj.report_type} report request has been approved.",
            settings.EMAIL_HOST_USER,
            [obj.employee.email],
            fail_silently=True
        )
    except:
        pass

    messages.success(
        request,
        "Export Approved"
    )

    return redirect(
        "export_requests"
    )


@login_required
def reject_export(request, pk):

    if not request.user.is_superuser:
        return redirect(
            "dashboard"
        )

    obj = ExportRequest.objects.get(
        id=pk
    )

    obj.status = "Rejected"
    obj.save()

    messages.success(
        request,
        "Export Rejected"
    )

    return redirect(
        "export_requests"
    )

#=======================
#     Monthly Report
#=======================

@login_required
def monthly_report(request):

    today = date.today()

    attendance = Attendance.objects.filter(
        employee=request.user,
        date__year=today.year,
        date__month=today.month
    )

    completed_tasks = Task.objects.filter(
        employee=request.user,
        status="Completed"
    ).count()

    completed_projects = CompletedProject.objects.filter(
        employee=request.user
    )

    present_days = attendance.count()

    total_days = calendar.monthrange(
        today.year,
        today.month
    )[1]

    absent_days = total_days - present_days

    percentage = 0

    if total_days > 0:
        percentage = round(
            (present_days / total_days) * 100,
            2
        )

    context = {

        "present_days": present_days,
        "absent_days": absent_days,
        "attendance_percentage": percentage,
        "completed_tasks": completed_tasks,
        "completed_projects": completed_projects,
        "month": today.strftime("%B"),
        "year": today.year,
    }

    return render(
        request,
        "management_app/monthly_report.html",
        context
    )

#=======================
#     Search
#=======================

@login_required
def search(request):

    query = request.GET.get("q")

    employees = []
    projects = []
    tasks = []

    if query:

        employees = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

        projects = Project.objects.filter(
            Q(name__icontains=query)
        )

        tasks = Task.objects.filter(
            Q(title__icontains=query)
        )

    context = {

        "query": query,
        "employees": employees,
        "projects": projects,
        "tasks": tasks,

    }

    return render(
        request,
        "management_app/search.html",
        context
    )

#=======================
#    Download PDF
#=======================

@login_required
def download_pdf(request, pk):

    export = ExportRequest.objects.get(
        id=pk,
        employee=request.user
    )

    if export.status != "Approved":
        messages.error(
            request,
            "Admin approval required."
        )
        return redirect(
            "my_export_requests"
        )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = \
        'attachment; filename="report.pdf"'

    p = canvas.Canvas(response)

    p.setFont(
        "Helvetica-Bold",
        16
    )

    p.drawString(
        100,
        800,
        "Employee Management System"
    )

    p.setFont(
        "Helvetica",
        12
    )

    p.drawString(
        100,
        760,
        f"Employee : {request.user.username}"
    )

    p.drawString(
        100,
        730,
        f"Report : {export.report_type}"
    )

    p.drawString(
        100,
        700,
        "Generated Successfully"
    )

    p.showPage()

    p.save()

    export.is_downloaded = True
    export.save()

    return response


#=======================
#    Download_Excel
#=======================

@login_required
def download_excel(request, pk):

    export = ExportRequest.objects.get(
        id=pk,
        employee=request.user
    )

    if export.status != "Approved":
        messages.error(
            request,
            "Admin approval required."
        )
        return redirect(
            "my_export_requests"
        )

    workbook = openpyxl.Workbook()

    sheet = workbook.active

    sheet.title = "Report"

    sheet.append([
        "Employee",
        request.user.username
    ])

    sheet.append([
        "Report Type",
        export.report_type
    ])

    sheet.append([
        "Status",
        export.status
    ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename=report.xlsx'

    workbook.save(response)

    return response