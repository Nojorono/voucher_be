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

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="RYO Project API",
      default_version='v1',
      description="API documentation for RYO Project",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="banyu.senjana@limamail.net"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'wholesales', WholesaleViewSet, basename='wholesale')
router.register(r'retailers', RetailerViewSet, basename='retailer')
router.register(r'voucherlimit', VoucherLimitViewSet, basename='voucherlimit')


urlpatterns = [
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('user/register/', register, name='register'),
    path('user/update/<int:user_id>/', admin_update_user, name='admin-update-user'),
    path('user/delete/<int:user_id>/', admin_delete_user, name='admin-delete-user'),
    path('reset_password/', reset_password, name='reset_password'),
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('change_password/', change_password, name='change_password'),
    path('redeem_voucher/', redeem_voucher, name='redeem_voucher'),
    path('submit_redeem_voucher/', submit_trx_voucher, name='submit_trx_voucher'),
    # path('list_redeem_voucher/', list_trx_voucher, name='list_trx_voucher'),
    path('redeem_report/', redeem_report, name='redeem_report'),
    path('list_photos/', list_photos, name='list_photos'),
    path('list_vouchers/', list_vouchers, name='list_vouchers'),
    path('office_verification_report/', office_verification_report, name='office_verification_report'),
    path('retailer_register_upload/', retailer_register_upload, name='retailer_register_upload'),
    path('logout/', logout, name='logout'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/profile/', UserViewSet.as_view({'get': 'profile'}), name='user-profile'),  # Custom route
    path('user/updprofile/', UserViewSet.as_view({'put': 'update_profile'}), name='user-update-profile'),  # Custom route
    path('user/delprofile/', UserViewSet.as_view({'delete': 'delete_profile'}), name='user-delete-profile'),  # Custom route
    path('user/', UserViewSet.as_view({'get': 'list_users'}), name='user-list'),  # Custom route
    path('kodepos/', kodepos_list, name='kodepos-list'),
    path('kelurahan/', kelurahan_list, name='kelurahan-list'),
    path('kecamatan/', kecamatan_list, name='kecamatan-list'),
    path('kota/', kota_list, name='kota-list'),
    path('provinsi/', provinsi_list, name='provinsi-list'),
    path('kodepos/detail/', KodeposDetailView.as_view(), name='kodepos-detail'),
    path('report/list_retailers/', list_retailers, name='list_retailers'),
    path('report/<str:view_name>/', ReportView.as_view(), name='report-view'),
    path('items/', list_items, name='list-items'),
    path('submit_reimburse/', submit_reimburse, name='submit_reimburse'),
    path('list_reimburse/', list_reimburse, name='list_reimburse'),
    path('update_reimburse_status/<int:pk>/<str:new_status>/', update_reimburse_status, name='update_reimburse_status'),
    path('current-count/', get_current_count, name='get_current_count'),

    # Include ViewSet routes
    path('', include(router.urls)),
]
