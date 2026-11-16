from django.urls import path

from . import views_reports as v

urlpatterns = [
    path("reports/", v.report_list, name="report_list"),
    path("reports/new/", v.report_create, name="report_create"),
    path("reports/<int:pk>/", v.report_detail, name="report_detail"),
    path("reports/<int:pk>/edit/", v.report_edit, name="report_edit"),
]
