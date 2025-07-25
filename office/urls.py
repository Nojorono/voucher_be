from django.urls import path
from . import views

app_name = 'office'

urlpatterns = [
    # Original verification views
    path('verification-report/', views.office_verification_report, name='office_verification_report'),
    path('verify_photo/<int:retailer_id>/', views.verify_photo, name='verify_photo'),
    
    # Voucher Project views
    path('voucher-projects/', views.voucher_project_list, name='voucher_project_list'),
    path('voucher-projects/<int:project_id>/', views.voucher_project_detail, name='voucher_project_detail'),
    path('voucher-projects/active/', views.voucher_project_active_list, name='voucher_project_active_list'),
    
    # Voucher Limit views
    path('voucher-limits/', views.voucher_limit_list, name='voucher_limit_list'),
    path('voucher-limits/<int:limit_id>/', views.voucher_limit_detail, name='voucher_limit_detail'),
    path('voucher-limits/<int:limit_id>/increment/', views.voucher_limit_increment, name='voucher_limit_increment'),
    
    # Voucher Retailer Discount views
    path('voucher-discounts/', views.voucher_discount_list, name='voucher_discount_list'),
    path('voucher-discounts/<int:discount_id>/', views.voucher_discount_detail, name='voucher_discount_detail'),
    
    # Utility views
    path('voucher-summary/', views.voucher_summary, name='voucher_summary'),
]
