from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms_reports import MissedReportForm, ReportEditForm
from .models import MissedReport

RESIDENT = User.Role.RESIDENT


@role_required(RESIDENT)
def report_list(request):
    reports = MissedReport.objects.filter(user=request.user).select_related("schedule__street")
    status = request.GET.get("status", "")
    if status in MissedReport.Status.values:
        reports = reports.filter(status=status)
    return render(request, "pickups/report_list.html", {
        "reports": reports, "status": status, "statuses": MissedReport.Status.choices,
    })


@role_required(RESIDENT)
def report_create(request):
    if request.method == "POST":
        form = MissedReportForm(request.POST, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user  # the record belongs to whoever is logged in
            report.save()
            messages.success(request, "Your missed-collection report was submitted. Barangay staff will review it.")
            return redirect("pickups:report_detail", pk=report.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = MissedReportForm(user=request.user)
    return render(request, "pickups/report_form.html", {"form": form, "title": "Report a missed collection"})


@role_required(RESIDENT)
def report_detail(request, pk):
    # filtering by user=request.user means other people's reports simply don't exist for you (404)
    report = get_object_or_404(MissedReport.objects.select_related("schedule__street", "handled_by"), pk=pk, user=request.user)
    return render(request, "pickups/report_detail.html", {"report": report})


@role_required(RESIDENT)
def report_edit(request, pk):
    report = get_object_or_404(MissedReport, pk=pk, user=request.user)
    if not report.can_resident_edit:
        messages.error(request, "This report can no longer be edited because staff already responded to it.")
        return redirect("pickups:report_detail", pk=report.pk)
    if request.method == "POST":
        form = ReportEditForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Your report was updated.")
            return redirect("pickups:report_detail", pk=report.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = ReportEditForm(instance=report)
    return render(request, "pickups/report_form.html", {"form": form, "title": f"Edit report #{report.pk}"})
