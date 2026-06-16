from django.urls import path
from . import views

urlpatterns = [

    # Authentication
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Attendance
    path(
        'mark-attendance/',
        views.mark_attendance,
        name='mark_attendance'
    ),

    path(
        'check-out/',
        views.check_out,
        name='check_out'
    ),

    path(
        'attendance-history/',
        views.attendance_history,
        name='attendance_history'
    ),

    # Projects
    path(
        'projects/',
        views.project_list,
        name='project_list'
    ),

    path(
        'projects/create/',
        views.project_create,
        name='project_create'
    ),

    path(
        'projects/update/<int:pk>/',
        views.project_update,
        name='project_update'
    ),

    path(
        'projects/delete/<int:pk>/',
        views.project_delete,
        name='project_delete'
    ),

    # Tasks
    path(
        'tasks/',
        views.task_list,
        name='task_list'
    ),

    path(
        'tasks/create/',
        views.task_create,
        name='task_create'
    ),

    path(
        'tasks/update/<int:pk>/',
        views.task_update,
        name='task_update'
    ),

    # Employees
    path(
        'employees/',
        views.employee_list,
        name='employee_list'
    ),

    path(
        'employees/create/',
        views.employee_create,
        name='employee_create'
    ),

    path(
       'attendance/',
       views.attendance,
       name='attendance'
),
# Leave Management

path(
    "apply_leave/",
    views.apply_leave,
    name="apply_leave"
),

path(
    "my_leaves/",
    views.my_leaves,
    name="my_leaves"
),

path(
    "leave_requests/",
    views.leave_requests,
    name="leave_requests"
),

path(
    "approve_leave/<int:pk>/",
    views.approve_leave,
    name="approve_leave"
),

path(
    "reject_leave/<int:pk>/",
    views.reject_leave,
    name="reject_leave"
),

path(
    'announcements/',
    views.announcement_list,
    name='announcement_list'
),

path(
    'announcement/add/',
    views.announcement_create,
    name='announcement_create'
),
path(
    "export_request/",
    views.export_request,
    name="export_request"
),

path(
    "my_export_requests/",
    views.my_export_requests,
    name="my_export_requests"
),

path(
    "export_requests/",
    views.export_requests,
    name="export_requests"
),

path(
    "approve_export/<int:pk>/",
    views.approve_export,
    name="approve_export"
),

path(
    "reject_export/<int:pk>/",
    views.reject_export,
    name="reject_export"
),

path(
    "monthly_report/",
    views.monthly_report,
    name="monthly_report"
),

path(
    "search/",
    views.search,
    name="search"
),

path(
    "download_pdf/<int:pk>/",
    views.download_pdf,
    name="download_pdf"
),

path(
    "download_excel/<int:pk>/",
    views.download_excel,
    name="download_excel"
),

path(
    "verify-otp/",
    views.verify_otp,
    name="verify_otp"
),

path(
    "change-password/",
    views.change_password,
    name="change_password"
),

path(
    "update-profile/",
    views.update_profile,
    name="update_profile"
),

path(
    "notifications/",
    views.notifications,
    name="notifications"
),


]