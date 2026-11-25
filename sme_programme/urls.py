from django.contrib import admin
from django.urls import path
from showcase.views import (
    calendar_view, dashboard, export_excel, sme_portal_view, update_calendar_date
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('calendar/', calendar_view, name='calendar_view'),
    path('sme-portal/', sme_portal_view, name='sme_portal'),
    path('export-excel/', export_excel, name='export_excel'),
    path('api/calendar/update-date/', update_calendar_date, name='update_calendar_date'),
]