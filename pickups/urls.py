from .urls_reports import urlpatterns as report_urls
from .urls_review import urlpatterns as review_urls
from .urls_schedule import urlpatterns as schedule_urls

app_name = "pickups"

urlpatterns = schedule_urls + report_urls + review_urls
