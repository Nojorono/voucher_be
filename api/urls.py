from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
import os

from .views import (
    register, 
    reset_password,
    change_password, 
    logout,
    UserViewSet,
    WholesaleViewSet,
    CustomTokenObtainPairView, 
    RetailerViewSet,
    redeem_voucher,
    redeem_report,   
    office_verification_report,
    retailer_register_upload,
    list_photos,
    list_vouchers,
    kodepos_list,
    kelurahan_list,
    kecamatan_list,
    kota_list,
    provinsi_list,
    KodeposDetailView,
    ReportView,
    admin_update_user,
    admin_delete_user,
    list_items,
    submit_trx_voucher,
    submit_reimburse,
    update_reimburse_status,
    list_reimburse,
    list_retailers,
    get_current_count, 
    VoucherLimitViewSet,
    VoucherProjectViewSet,
    VoucherRetailerDiscountViewSet,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# ✅ Single schema_view definition
try:
    from rest_framework import permissions
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="RYO Project API",
      default_version='v1',
      description="""
      # RYO Marketing Campaign API
      
      API documentation for RYO Project - Marketing Campaign Management System
      
      ## Authentication
      
      This API uses JWT (JSON Web Token) authentication. To access protected endpoints:
      
      1. **Get Token**: Use the `/login/` endpoint with your username and password
      2. **Use Token**: Click the "Authorize" button and enter: `Bearer <your-access-token>`
      3. **All subsequent requests** will automatically include the JWT token
      
      ### Example:
      ```
      Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
      ```
      
      ## Features:
      - 🔐 JWT Authentication  
      - 👥 User & Retailer Management
      - 🎫 Voucher Management & Verification
      - 📸 Photo Verification System
      - 📊 Reporting & Analytics
      - 🗺️ Geographic Data Management
      """,
      terms_of_service="https://www.kcsi.id/terms/",
      contact=openapi.Contact(
         name="RYO API Support",
         email="banyu.senjana@limamail.net"
      ),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   authentication_classes=[],
)

# Router setup
router = DefaultRouter()
router.register(r'wholesales', WholesaleViewSet, basename='wholesale')
router.register(r'retailers', RetailerViewSet, basename='retailer')
router.register(r'voucherlimit', VoucherLimitViewSet, basename='voucherlimit')
router.register(r'voucher-projects', VoucherProjectViewSet, basename='voucher-project')
router.register(r'voucher-discounts', VoucherRetailerDiscountViewSet, basename='voucher-discount')

urlpatterns = [
    # Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('logout/', logout, name='logout'),
    
    # Password management
    path('reset_password/', reset_password, name='reset_password'),
    path('change_password/', change_password, name='change_password'),

    # User management routes
    path('user/register/', register, name='register'),
    path('user/update/<int:user_id>/', admin_update_user, name='admin-update-user'),
    path('user/delete/<int:user_id>/', admin_delete_user, name='admin-delete-user'),
    path('user/profile/', UserViewSet.as_view({'get': 'profile'}), name='user-profile'),
    path('user/updprofile/', UserViewSet.as_view({'put': 'update_profile'}), name='user-update-profile'),
    path('user/delprofile/', UserViewSet.as_view({'delete': 'delete_profile'}), name='user-delete-profile'),
    path('user/', UserViewSet.as_view({'get': 'list_users'}), name='user-list'),

    # Retailer, Wholesale, Voucher management
    path('list_photos/', list_photos, name='list_photos'),
    path('retailer_register_upload/', retailer_register_upload, name='retailer_register_upload'),
    path('list_vouchers/', list_vouchers, name='list_vouchers'),
    path('redeem_voucher/', redeem_voucher, name='redeem_voucher'),
    path('submit_redeem_voucher/', submit_trx_voucher, name='submit_trx_voucher'),
    path('redeem_report/', redeem_report, name='redeem_report'),
    path('office_verification_report/', office_verification_report, name='office_verification_report'),
    path('report/list_retailers/', list_retailers, name='list_retailers'),
    path('report/<str:view_name>/', ReportView.as_view(), name='report-view'),
   
    # Location and kodepos management
    path('kodepos/', kodepos_list, name='kodepos-list'),
    path('kelurahan/', kelurahan_list, name='kelurahan-list'),
    path('kecamatan/', kecamatan_list, name='kecamatan-list'),
    path('kota/', kota_list, name='kota-list'),
    path('provinsi/', provinsi_list, name='provinsi-list'),
    path('kodepos/detail/', KodeposDetailView.as_view(), name='kodepos-detail'),

    # Item and Reimburse management
    path('items/', list_items, name='list-items'),
    path('submit_reimburse/', submit_reimburse, name='submit_reimburse'),
    path('list_reimburse/', list_reimburse, name='list_reimburse'),
    path('update_reimburse_status/<int:pk>/<str:new_status>/', update_reimburse_status, name='update_reimburse_status'),
    path('current-count/', get_current_count, name='get_current_count'),

    # Include ViewSet routes
    path('', include(router.urls)),
]

# ✅ Add API documentation URLs
if SWAGGER_AVAILABLE:
    docs_urls = [
        path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    ]
    
    urlpatterns += docs_urls
    print("✅ Added API documentation URLs")

print(f"✅ API URL patterns configured ({len(urlpatterns)} total patterns)")