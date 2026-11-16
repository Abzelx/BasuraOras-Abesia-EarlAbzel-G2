from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from .forms_schedule import ScheduleForm
from .models import CollectionSchedule

STAFF = User.Role.STAFF


def _own_schedules(staff_user):
    """Only schedules for streets in the staff member's own barangay (BR-10)."""
    return CollectionSchedule.objects.filter(street__barangay=staff_user.barangay).select_related("street")


@role_required(STAFF)
def schedule_list(request):
    return render(request, "pickups/schedule_list.html", {"schedules": _own_schedules(request.user)})


@role_required(STAFF)
def schedule_create(request):
    if request.method == "POST":
        form = ScheduleForm(request.POST, staff_user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, f"Schedule added: {schedule}.")
            return redirect("pickups:schedule_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = ScheduleForm(staff_user=request.user)
    return render(request, "pickups/schedule_form.html", {"form": form, "title": "Add collection schedule"})


@role_required(STAFF)
def schedule_edit(request, pk):
    schedule = get_object_or_404(_own_schedules(request.user), pk=pk)
    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule, staff_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Schedule updated.")
            return redirect("pickups:schedule_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = ScheduleForm(instance=schedule, staff_user=request.user)
    return render(request, "pickups/schedule_form.html", {"form": form, "title": "Edit collection schedule"})


@role_required(STAFF)
@require_POST
def schedule_delete(request, pk):
    schedule = get_object_or_404(_own_schedules(request.user), pk=pk)
    try:
        schedule.delete()
        messages.success(request, "Schedule deleted.")
    except ProtectedError:
        # BR-11: entries that already have reports can't be deleted, only deactivated.
        schedule.is_active = False
        schedule.save(update_fields=["is_active"])
        messages.warning(request, "This schedule has reports attached, so it was deactivated instead of deleted.")
    return redirect("pickups:schedule_list")
