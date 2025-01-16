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
    # verify_photo,      
    office_verification_report,
    retailer_register_upload,
    list_photos,
    list_vouchers,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='user')
router.register(r'wholesales', WholesaleViewSet, basename='wholesale')
router.register(r'retailers', RetailerViewSet, basename='retailer')


urlpatterns = [
    path('user/register/', register, name='register'),
    path('reset_password/', reset_password, name='reset_password'),
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('change_password/', change_password, name='change_password'),
    path('redeem_voucher/', redeem_voucher, name='redeem_voucher'),
    path('redeem_report/', redeem_report, name='redeem_report'),
    path('redeem_report/<str:name>/', redeem_report, name='redeem_report'),
    # path('verify_photo/', verify_photo, name='verify_photo'),
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
    # path('retailer/photos/<int:pk>/', RetailerViewSet.as_view({'get': 'photos'}), name='retailer-list-photos'),  # Custom route
    # path('retailer/verify_photos/', RetailerViewSet.as_view({'post': 'verify_photo'}), name='retailer-verify-photos'),  # Custom route
    # path('retailer/reject_photos/', RetailerViewSet.as_view({'post': 'reject_photo'}), name='retailer-reject-photos'),  # Custom route

    # Include ViewSet routes
    path('', include(router.urls)),
]
