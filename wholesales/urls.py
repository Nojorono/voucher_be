from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/wholesales', views.WholesaleViewSet, basename='wholesale')

urlpatterns = [
    path('redeem/', views.redeem_voucher, name='redeem_voucher'),
    path('redeem/report/<str:name>/', views.redeem_report, name='redeem_report'),
    path('', include(router.urls)),
]
