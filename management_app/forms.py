from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from .models import Attendance, Project, Task




class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter Username'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter Password'
        })

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['check_out']

        widgets = {
            'check_out': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time'
                }
            )
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'start_date',
            'end_date',
            'status',
            'assigned_employees'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),

            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'status': forms.Select(attrs={
                'class': 'form-select'
            }),

            'assigned_employees': forms.SelectMultiple(attrs={
                'class': 'form-select'
            }),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'project',
            'employee',
            'title',
            'description',
            'status',
            'due_date'
        ]

        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-select'
            }),

            'employee': forms.Select(attrs={
                'class': 'form-select'
            }),

            'title': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),

            'status': forms.Select(attrs={
                'class': 'form-select'
            }),

            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class TaskStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']

        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class EmployeeCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password'
        ]

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),

            'first_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'last_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }

    def save(self, commit=True):
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )

        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        return user