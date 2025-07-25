from django.urls import path, include
from rest_framework.routers import DefaultRouter
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
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'wholesales', WholesaleViewSet, basename='wholesale')
router.register(r'retailers', RetailerViewSet, basename='retailer')
router.register(r'voucherlimit', VoucherLimitViewSet, basename='voucherlimit')


urlpatterns = [
    # Authentication endpoints - langsung di root level
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('api/logout/', logout, name='logout'),
    
    # password management
    path('api/reset_password/', reset_password, name='reset_password'),
    path('api/change_password/', change_password, name='change_password'),

    # User management routes
    path('api/user/register/', register, name='register'),
    path('api/user/update/<int:user_id>/', admin_update_user, name='admin-update-user'),
    path('api/user/delete/<int:user_id>/', admin_delete_user, name='admin-delete-user'),
    path('api/user/profile/', UserViewSet.as_view({'get': 'profile'}), name='user-profile'),  # Custom route
    path('api/user/updprofile/', UserViewSet.as_view({'put': 'update_profile'}), name='user-update-profile'),  # Custom route
    path('api/user/delprofile/', UserViewSet.as_view({'delete': 'delete_profile'}), name='user-delete-profile'),  # Custom route
    path('api/user/', UserViewSet.as_view({'get': 'list_users'}), name='user-list'),  # Custom route

    # Retailer, Wholesale, Voucher management
    path('api/list_photos/', list_photos, name='list_photos'),
    path('api/retailer_register_upload/', retailer_register_upload, name='retailer_register_upload'),
    path('api/list_vouchers/', list_vouchers, name='list_vouchers'),
    path('api/redeem_voucher/', redeem_voucher, name='redeem_voucher'),
    path('api/submit_redeem_voucher/', submit_trx_voucher, name='submit_trx_voucher'),
    path('api/redeem_report/', redeem_report, name='redeem_report'),
    path('api/office_verification_report/', office_verification_report, name='office_verification_report'),
    path('api/report/list_retailers/', list_retailers, name='list_retailers'),
    path('api/report/<str:view_name>/', ReportView.as_view(), name='report-view'),
   
    # location and kodepos management
    path('api/kodepos/', kodepos_list, name='kodepos-list'),
    path('api/kelurahan/', kelurahan_list, name='kelurahan-list'),
    path('api/kecamatan/', kecamatan_list, name='kecamatan-list'),
    path('api/kota/', kota_list, name='kota-list'),
    path('api/provinsi/', provinsi_list, name='provinsi-list'),
    path('api/kodepos/detail/', KodeposDetailView.as_view(), name='kodepos-detail'),

    # Item and Reimburse management
    path('api/items/', list_items, name='list-items'),
    path('api/submit_reimburse/', submit_reimburse, name='submit_reimburse'),
    path('api/list_reimburse/', list_reimburse, name='list_reimburse'),
    path('api/update_reimburse_status/<int:pk>/<str:new_status>/', update_reimburse_status, name='update_reimburse_status'),
    path('api/current-count/', get_current_count, name='get_current_count'),

    # Include ViewSet routes
    path('api/', include(router.urls)),
]

# ✅ Add API documentation
try:
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    from rest_framework import permissions

    schema_view = get_schema_view(
        openapi.Info(
            title="RYO API",
            default_version='v1',
            description="RYO Marketing API Documentation",
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
    )
    
    # Add docs URLs
    docs_urls = [
        path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    ]
    
    urlpatterns += docs_urls
    print("✅ Added API documentation URLs")

except ImportError:
    schema_view = None
    print("⚠️ drf-yasg not available, skipping API docs")

print(f"API URL patterns configured ({len(urlpatterns)} patterns)")