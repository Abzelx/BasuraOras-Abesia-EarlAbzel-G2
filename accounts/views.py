from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import ProfileForm, RegistrationForm
from .models import User


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
            messages.success(request, f"Welcome, {user.display_name}! Your account has been created.")
            return redirect("accounts:dashboard")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


class LoginPageView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().display_name}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username/email or password. Please try again.")
        return super().form_invalid(form)


@login_required
def dashboard_redirect(request):
    """After login, send each person to the dashboard that matches their role."""
    user = request.user
    if user.role == User.Role.STAFF:
        return redirect("accounts:staff_dashboard")
    if user.is_superuser and user.street_id is None:
        return redirect("admin:index")
    return redirect("accounts:resident_dashboard")


@role_required(User.Role.RESIDENT)
def resident_dashboard(request):
    return render(request, "accounts/resident_dashboard.html")


@role_required(User.Role.STAFF)
def staff_dashboard(request):
    return render(request, "accounts/staff_dashboard.html")


@login_required
def profile(request):
    # Always request.user -> nobody can open someone else's profile (there is no id in the URL).
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
        messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})
