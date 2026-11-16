from django.urls import path

from . import views_review as v

urlpatterns = [
    path("staff/reports/", v.staff_report_list, name="staff_report_list"),
    path("staff/reports/<int:pk>/", v.staff_report_review, name="staff_report_review"),
]
