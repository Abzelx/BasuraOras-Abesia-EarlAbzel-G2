from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import User

from .forms_review import StaffReviewForm
from .models import MissedReport

STAFF = User.Role.STAFF


def _barangay_reports(staff_user):
    """BR-25: staff see only reports for streets in their own barangay."""
    return MissedReport.objects.filter(schedule__street__barangay=staff_user.barangay).select_related(
        "user", "schedule__street", "handled_by"
    )


@role_required(STAFF)
def staff_report_list(request):
    reports = _barangay_reports(request.user)
    status = request.GET.get("status", "")
    if status in MissedReport.Status.values:
        reports = reports.filter(status=status)
    return render(request, "pickups/staff_report_list.html", {
        "reports": reports, "status": status, "statuses": MissedReport.Status.choices,
    })


@role_required(STAFF)
def staff_report_review(request, pk):
    report = get_object_or_404(_barangay_reports(request.user), pk=pk)

    if report.is_final:
        if request.method == "POST":
            messages.error(request, "This report is already closed and can't be changed.")
            return redirect("pickups:staff_report_review", pk=report.pk)
        return render(request, "pickups/staff_report_review.html", {"report": report, "form": None})

    if request.method == "POST":
        form = StaffReviewForm(request.POST, report=report)
        if form.is_valid():
            report.status = form.cleaned_data["status"]
            report.staff_response = form.cleaned_data["staff_response"].strip()
            report.handled_by = request.user
            if report.is_final:
                report.resolved_at = timezone.now()
            report.save()
            messages.success(request, f"Report #{report.pk} marked as {report.get_status_display()}.")
            return redirect("pickups:staff_report_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = StaffReviewForm(report=report)
    return render(request, "pickups/staff_report_review.html", {"report": report, "form": form})
