from django.urls import path
from . import views

app_name = 'office'

urlpatterns = [
    path('verification-report/', views.office_verification_report, name='office_verification_report'),
    path('verify_photo/<int:retailer_id>/', views.verify_photo, name='verify_photo'),
]
