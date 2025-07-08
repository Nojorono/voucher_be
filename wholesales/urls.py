from django.urls import path
from . import views

urlpatterns = [
    path('redeem/', views.redeem_voucher, name='redeem_voucher'),
    path('redeem/report/<str:name>/', views.redeem_report, name='redeem_report'),
]
