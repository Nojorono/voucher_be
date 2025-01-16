from django.urls import path
from . import views

app_name = 'retailer'

urlpatterns = [
    path('register/', views.retailer_register_upload, name='retailer_register_upload'),
]
