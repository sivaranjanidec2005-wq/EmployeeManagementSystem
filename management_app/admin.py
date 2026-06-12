from django.contrib import admin
from .models import Attendance, Project, Task, Announcement, ExportRequest
from .models import Leave


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'date',
        'check_in',
        'check_out',
    )

    list_filter = (
        'date',
        'employee',
    )

    search_fields = (
        'employee__username',
    )

    ordering = (
        '-date',
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'status',
        'start_date',
        'end_date',
        'created_at',
    )

    list_filter = (
        'status',
        'start_date',
    )

    search_fields = (
        'name',
    )

    filter_horizontal = (
        'assigned_employees',
    )

    ordering = (
        '-created_at',
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'employee',
        'project',
        'status',
        'due_date',
    )

    list_filter = (
        'status',
        'project',
    )

    search_fields = (
        'title',
        'employee__username',
        'project__name',
    )

    ordering = (
        'status',
        '-created_at',
    )

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
        list_display = (
            'employee',
            'leave_type',
            'start_date',
            'end_date',
            'status',
        )

        list_filter = (
            'status',
        )

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'created_by',
        'created_at',
    )

@admin.register(ExportRequest)
class ExportRequestAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'report_type',
        'status',
        'requested_on',
    )