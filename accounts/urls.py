from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard"),
    path("register/", views.register, name="register"),
    path("login/", views.LoginPageView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),  # POST only (Django 5)
    path("dashboard/resident/", views.resident_dashboard, name="resident_dashboard"),
    path("dashboard/staff/", views.staff_dashboard, name="staff_dashboard"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
]
