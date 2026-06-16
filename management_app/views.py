import random
import openpyxl
import calendar

from datetime import date

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse

from reportlab.pdfgen import canvas

from .models import (
    Attendance,
    Project,
    Task,
    Leave,
    Announcement,
    ExportRequest,
    CompletedProject,
    EmailVerification,
    Notification
)

from .forms import (
    LoginForm,
    AttendanceForm,
    ProjectForm,
    TaskForm,
    TaskStatusUpdateForm,
    EmployeeCreationForm,
)

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(
        request,
        data=request.POST or None
    )

    if request.method == "POST":

        if form.is_valid():

            user = form.get_user()

            otp = str(
                random.randint(
                    100000,
                    999999
                )
            )

            verification, created = EmailVerification.objects.get_or_create(
                user=user
            )

            verification.otp = otp
            verification.save()

            try:

                send_mail(

                    "OTP Verification",

                    f"""
Hello {user.username},

Your OTP is:

{otp}

Thank You
                    """,

                    settings.EMAIL_HOST_USER,

                    [user.email],

                    fail_silently=True

                )

            except:
                pass

            request.session["otp_user_id"] = user.id

            return redirect(
                "verify_otp"
            )

        else:

            messages.error(

                request,

                "Invalid username or password."

            )

    return render(

        request,

        "management_app/login.html",

        {

            "form": form

        }

    )

@login_required
def verify_otp(request):

    user_id = request.session.get(
        "otp_user_id"
    )

    if not user_id:
        return redirect(
            "login"
        )

    user = User.objects.get(
        id=user_id
    )

    verification = EmailVerification.objects.get(
        user=user
    )

    if request.method == "POST":

        otp = request.POST.get(
            "otp"
        )

        if otp == verification.otp:

            login(
                request,
                user
            )

            del request.session["otp_user_id"]

            messages.success(
                request,
                "OTP Verified Successfully."
            )

            return redirect(
                "dashboard"
            )

        else:

            messages.error(
                request,
                "Invalid OTP"
            )

    return render(
        request,
        "management_app/verify_otp.html"
    )

@login_required
def logout_view(request):

    logout(
        request
    )

    messages.success(

        request,

        "Logged out successfully."

    )

    return redirect(
        "login"
    )

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

            "is_admin": True,

            "total_employees": total_employees,

            "total_projects": total_projects,

            "total_tasks": total_tasks,

            "present_today": present_today,

        }

    else:

        my_projects = Project.objects.filter(

            assigned_employees=request.user

        ).count()

        pending_tasks = Task.objects.filter(

            employee=request.user,

            status="Pending"

        ).count()

        completed_tasks = Task.objects.filter(

            employee=request.user,

            status="Completed"

        ).count()

        attendance_marked = Attendance.objects.filter(

            employee=request.user,

            date=timezone.now().date()

        ).exists()

        context = {

            "is_admin": False,

            "my_projects": my_projects,

            "pending_tasks": pending_tasks,

            "completed_tasks": completed_tasks,

            "attendance_marked": attendance_marked,

        }

    return render(

        request,

        "management_app/dashboard.html",

        context

    )

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
            "You have already marked attendance today."
        )

        return redirect(
            "attendance_history"
        )

    Attendance.objects.create(
        employee=request.user
    )

    Notification.objects.create(
        user=request.user,
        title="Attendance",
        message="Attendance marked successfully."
    )

    messages.success(
        request,
        "Attendance marked successfully."
    )

    return redirect(
        "attendance_history"
    )

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
            "Please check in first."
        )

        return redirect(
            "dashboard"
        )

    if attendance.check_out:

        messages.warning(
            request,
            "Already checked out."
        )

        return redirect(
            "attendance_history"
        )

    attendance.check_out = timezone.localtime()

    attendance.save()

    Notification.objects.create(
        user=request.user,
        title="Check Out",
        message="Checked out successfully."
    )

    messages.success(
        request,
        "Check-out successful."
    )

    return redirect(
        "attendance_history"
    )

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
        "management_app/attendance_history.html",
        {
            "attendances": attendances
        }
    )

@login_required
def attendance(request):

    return render(
        request,
        "management_app/attendance.html"
    )

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
        "management_app/project_list.html",
        {
            "projects": projects
        }
    )

@login_required
def project_create(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            "Permission denied."
        )

        return redirect(
            "dashboard"
        )

    if request.method == "POST":

        form = ProjectForm(
            request.POST
        )

        if form.is_valid():

            project = form.save()

            for employee in project.assigned_employees.all():

                Notification.objects.create(

                    user=employee,

                    title="Project Assigned",

                    message=f"You have been assigned to {project.name}"

                )

                if employee.email:

                    try:

                        send_mail(

                            "Project Assigned",

                            f"""
Hello {employee.username},

You have been assigned to a new project.

Project :

{project.name}

                            """,

                            settings.EMAIL_HOST_USER,

                            [employee.email],

                            fail_silently=True

                        )

                    except:
                        pass

            messages.success(

                request,

                "Project created successfully."

            )

            return redirect(
                "project_list"
            )

    else:

        form = ProjectForm()

    return render(

        request,

        "management_app/project_form.html",

        {

            "form": form,

            "title": "Create Project"

        }

    )

@login_required
def project_update(request, pk):

    if not request.user.is_superuser:

        return redirect(
            "dashboard"
        )

    project = get_object_or_404(
        Project,
        pk=pk
    )

    if request.method == "POST":

        form = ProjectForm(
            request.POST,
            instance=project
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Project updated."
            )

            return redirect(
                "project_list"
            )

    else:

        form = ProjectForm(
            instance=project
        )

    return render(

        request,

        "management_app/project_form.html",

        {

            "form": form,

            "title": "Edit Project"

        }

    )

@login_required
def project_delete(request, pk):

    if not request.user.is_superuser:

        return redirect(
            "dashboard"
        )

    project = get_object_or_404(
        Project,
        pk=pk
    )

    if request.method == "POST":

        project.delete()

        messages.success(

            request,

            "Project deleted."

        )

        return redirect(
            "project_list"
        )

    return render(

        request,

        "management_app/project_delete.html",

        {

            "project": project

        }

    )

@login_required
def project_delete(request, pk):

    if not request.user.is_superuser:

        return redirect(
            "dashboard"
        )

    project = get_object_or_404(
        Project,
        pk=pk
    )

    if request.method == "POST":

        project.delete()

        messages.success(

            request,

            "Project deleted."

        )

        return redirect(
            "project_list"
        )

    return render(

        request,

        "management_app/project_delete.html",

        {

            "project": project

        }

    )


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
        "management_app/task_list.html",
        {
            "tasks": tasks
        }
    )


@login_required
def task_create(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            "Permission Denied."
        )

        return redirect(
            "dashboard"
        )

    if request.method == "POST":

        form = TaskForm(
            request.POST
        )

        if form.is_valid():

            task = form.save()

            Notification.objects.create(

                user=task.employee,

                title="New Task",

                message=f"You have been assigned {task.title}"

            )

            if task.employee.email:

                try:

                    send_mail(

                        "New Task Assigned",

                        f"""
Hello {task.employee.username},

You have been assigned a new task.

Task :

{task.title}

                        """,

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

            return redirect(
                "task_list"
            )

    else:

        form = TaskForm()

    return render(

        request,

        "management_app/task_form.html",

        {

            "form": form,

            "title": "Assign Task"

        }

    )

@login_required
def task_update(request, pk):

    task = get_object_or_404(
        Task,
        pk=pk
    )

    if (
        not request.user.is_superuser
        and
        task.employee != request.user
    ):

        return redirect(
            "task_list"
        )

    if request.method == "POST":

        form = TaskStatusUpdateForm(

            request.POST,

            instance=task

        )

        if form.is_valid():

            form.save()

            Notification.objects.create(

                user=task.employee,

                title="Task Updated",

                message=f"{task.title} updated."

            )

            messages.success(

                request,

                "Task updated."

            )

            return redirect(
                "task_list"
            )

    else:

        form = TaskStatusUpdateForm(

            instance=task

        )

    return render(

        request,

        "management_app/task_update.html",

        {

            "form": form,

            "task": task

        }

    )

@login_required
def employee_create(request):

    if not request.user.is_superuser:

        return redirect(
            "dashboard"
        )

    if request.method == "POST":

        form = EmployeeCreationForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            otp = str(
                random.randint(
                    100000,
                    999999
                )
            )

            EmailVerification.objects.create(

                user=user,

                otp=otp,



            )

            if user.email:

                try:

                    send_mail(

                        "Welcome",

                        f"""
Hello {user.username}

Your account has been created.

OTP :

{otp}

                        """,

                        settings.EMAIL_HOST_USER,

                        [user.email],

                        fail_silently=True

                    )

                except:
                    pass

            messages.success(

                request,

                "Employee created."

            )

            return redirect(
                "employee_list"
            )

    else:

        form = EmployeeCreationForm()

    return render(

        request,

        "management_app/employee_form.html",

        {

            "form": form,

            "title": "Create Employee"

        }

    )

@login_required
def employee_list(request):

    if not request.user.is_superuser:

        return redirect(
            "dashboard"
        )

    employees = User.objects.filter(
        is_superuser=False
    )

    return render(

        request,

        "management_app/employee_list.html",

        {

            "employees": employees

        }

    )

@login_required
def apply_leave(request):

    if request.method == "POST":

        leave = Leave.objects.create(

            employee=request.user,

            leave_type=request.POST.get(
                "leave_type"
            ),

            start_date=request.POST.get(
                "start_date"
            ),

            end_date=request.POST.get(
                "end_date"
            ),

            reason=request.POST.get(
                "reason"
            )

        )

        Notification.objects.create(

            user=request.user,

            title="Leave Applied",

            message="Leave request submitted."

        )

        messages.success(

            request,

            "Leave applied."

        )

        return redirect(
            "my_leaves"
        )

    return render(

        request,

        "management_app/apply_leave.html"

    )

@login_required
def my_leaves(request):

    leaves = Leave.objects.filter(

        employee=request.user

    ).order_by(

        "-applied_on"

    )

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

        return redirect(
            "dashboard"
        )

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

    leave = get_object_or_404(
        Leave,
        id=pk
    )

    leave.status = "Approved"

    leave.save()

    Notification.objects.create(

        user=leave.employee,

        title="Leave Approved",

        message="Your leave request was approved."

    )

    if leave.employee.email:

        try:

            send_mail(

                "Leave Approved",

                "Your leave request was approved.",

                settings.EMAIL_HOST_USER,

                [leave.employee.email],

                fail_silently=True

            )

        except:
            pass

    messages.success(

        request,

        "Leave approved."

    )

    return redirect(
        "leave_requests"
    )

@login_required
def reject_leave(request, pk):

    leave = get_object_or_404(
        Leave,
        id=pk
    )

    leave.status = "Rejected"

    leave.save()

    Notification.objects.create(

        user=leave.employee,

        title="Leave Rejected",

        message="Your leave request was rejected."

    )

    if leave.employee.email:

        try:

            send_mail(

                "Leave Rejected",

                "Your leave request was rejected.",

                settings.EMAIL_HOST_USER,

                [leave.employee.email],

                fail_silently=True

            )

        except:
            pass

    messages.success(

        request,

        "Leave rejected."

    )

    return redirect(
        "leave_requests"
    )

@login_required
def announcement_list(request):

    announcements = Announcement.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "management_app/announcement_list.html",
        {
            "announcements": announcements
        }
    )

@login_required
def announcement_create(request):

    if not request.user.is_superuser:
        return redirect("dashboard")

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

        for user in users:

            Notification.objects.create(

                user=user,

                title=title,

                message=message

            )

        emails = []

        for user in users:
            emails.append(user.email)

        try:

            send_mail(

                title,

                message,

                settings.EMAIL_HOST_USER,

                emails,

                fail_silently=True

            )

        except:
            pass

        messages.success(

            request,

            "Announcement created."

        )

        return redirect(
            "announcement_list"
        )

    return render(
        request,
        "management_app/announcement_form.html"
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
def export_request(request):

    if request.method == "POST":

        ExportRequest.objects.create(

            employee=request.user,

            report_type=request.POST.get(
                "report_type"
            )

        )

        Notification.objects.create(

            user=request.user,

            title="Export Request",

            message="Export request submitted."

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

    obj = get_object_or_404(
        ExportRequest,
        id=pk
    )

    obj.status = "Approved"

    obj.save()

    Notification.objects.create(

        user=obj.employee,

        title="Export Approved",

        message="Your export request was approved."

    )

    try:

        send_mail(

            "Export Approved",

            "Your export request has been approved.",

            settings.EMAIL_HOST_USER,

            [obj.employee.email],

            fail_silently=True

        )

    except:
        pass

    return redirect(
        "export_requests"
    )

@login_required
def reject_export(request, pk):

    obj = get_object_or_404(
        ExportRequest,
        id=pk
    )

    obj.status = "Rejected"

    obj.save()

    Notification.objects.create(

        user=obj.employee,

        title="Export Rejected",

        message="Your export request was rejected."

    )

    return redirect(
        "export_requests"
    )

@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(

            request.user,

            request.POST

        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(

                request,

                user

            )

            Notification.objects.create(

                user=user,

                title="Password Changed",

                message="Password changed successfully."

            )

            try:

                send_mail(

                    "Password Changed",

                    "Your password has been changed.",

                    settings.EMAIL_HOST_USER,

                    [user.email],

                    fail_silently=True

                )

            except:
                pass

            messages.success(

                request,

                "Password changed."

            )

            return redirect(
                "dashboard"
            )

    else:

        form = PasswordChangeForm(
            request.user
        )

    return render(

        request,

        "management_app/change_password.html",

        {

            "form": form

        }

    )

@login_required
def update_profile(request):

    if request.method == "POST":

        user = request.user

        user.username = request.POST.get(
            "username"
        )

        user.first_name = request.POST.get(
            "first_name"
        )

        user.last_name = request.POST.get(
            "last_name"
        )

        user.email = request.POST.get(
            "email"
        )

        user.save()

        Notification.objects.create(

            user=user,

            title="Profile Updated",

            message="Profile updated successfully."

        )

        try:

            send_mail(

                "Profile Updated",

                "Your profile was updated.",

                settings.EMAIL_HOST_USER,

                [user.email],

                fail_silently=True

            )

        except:
            pass

        return redirect(
            "dashboard"
        )

    return render(

        request,

        "management_app/update_profile.html"

    )

@login_required
def notifications(request):

    notifications = Notification.objects.filter(

        user=request.user

    )

    return render(

        request,

        "management_app/notifications.html",

        {

            "notifications": notifications

        }

    )

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

@login_required
def search(request):

    query = request.GET.get(
        "q"
    )

    employees = []

    projects = []

    tasks = []

    if query:

        employees = User.objects.filter(

            Q(username__icontains=query)

            |

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

        content_type="application/pdf"

    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="report.pdf"'

    p = canvas.Canvas(
        response
    )

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
    ] = 'attachment; filename="report.xlsx"'

    workbook.save(
        response
    )

    return response