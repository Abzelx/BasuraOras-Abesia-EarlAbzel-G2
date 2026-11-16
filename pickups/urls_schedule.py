from django.urls import path

from . import views_schedule as v

urlpatterns = [
    path("staff/schedules/", v.schedule_list, name="schedule_list"),
    path("staff/schedules/new/", v.schedule_create, name="schedule_create"),
    path("staff/schedules/<int:pk>/edit/", v.schedule_edit, name="schedule_edit"),
    path("staff/schedules/<int:pk>/delete/", v.schedule_delete, name="schedule_delete"),
]
