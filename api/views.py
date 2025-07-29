# Revised views.py
import os
from rest_framework import viewsets, generics
from rest_framework import status as http_status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from office.models import User, Kodepos, Item, Reimburse, ReimburseStatus, VoucherLimit, VoucherProject, VoucherRetailerDiscount
from retailer.models import Retailer, RetailerPhoto, Voucher
from wholesales.models import Wholesale, VoucherRedeem, WholesaleTransaction, WholesaleTransactionDetail
from django.shortcuts import get_object_or_404
from .serializers import (
    UserSerializer, CustomTokenObtainPairSerializer, ChangePasswordSerializer, WholesaleSerializer, 
    VoucherRedeemSerializer, RetailerRegistrationSerializer, RetailerPhotoSerializer, 
    RetailerSerializer, RetailerPhotoVerificationSerializer, RetailerPhotoRejectionSerializer,
    VoucherSerializer, KodeposSerializer, ItemSerializer, WholesaleTransactionSerializer,
    ReimburseSerializer, RetailerReportSerializer, WholesaleTransactionDetailSerializer,
    VoucherLimitSerializer, VoucherProjectSerializer, VoucherRetailerDiscountSerializer,
    VoucherProjectSummarySerializer, VoucherLimitUpdateSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count, Avg, Sum
from datetime import datetime
import pandas as pd
from django.conf import settings
from django.core.mail import send_mail
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import models

# Import untuk Swagger
try:
    from drf_yasg.utils import swagger_auto_schema
    from drf_yasg import openapi
    SWAGGER_AVAILABLE = True
except ImportError:
    SWAGGER_AVAILABLE = False
    def swagger_auto_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Custom Token Obtain Pair View dengan Swagger documentation
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    if SWAGGER_AVAILABLE:
        @swagger_auto_schema(
            operation_description="""
            Login endpoint untuk mendapatkan JWT access dan refresh tokens.
            
            Token akan otomatis tersimpan di Swagger untuk digunakan pada endpoint lain.
            Setelah login sukses, klik tombol "Authorize" dan masukkan: Bearer <access_token>
            """,
            operation_summary="User Login",
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['username', 'password'],
                properties={
                    'username': openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example='admin',
                        description='Username untuk login'
                    ),
                    'password': openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example='Admin123!!',
                        description='Password untuk login'
                    ),
                }
            ),
            responses={
                200: openapi.Response(
                    description="Login successful - Copy access token untuk authorization",
                    examples={
                        "application/json": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM4MjAzNjAwLCJpYXQiOjE3MzgyMDA4MDAsImp0aSI6IjEyMzQ1NjciLCJ1c2VyX2lkIjoxfQ.example",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTczODgwNTYwMCwiaWF0IjoxNzM4MjAwODAwLCJqdGkiOiI3ODkwMTIzIiwidXNlcl9pZCI6MX0.example",
                            "message": "Login successful",
                            "userid": 1,
                            "username": "admin",
                            "email": "admin@example.com",
                            "is_staff": True,
                            "wholesale": 1,
                            "name": "PT Wholesale ABC",
                            "phone_number": "081234567890"
                        }
                    }
                ),
                401: openapi.Response(
                    description="Invalid credentials",
                    examples={
                        "application/json": {
                            "detail": "No active account found with the given credentials"
                        }
                    }
                ),
                400: openapi.Response(
                    description="Validation error",
                    examples={
                        "application/json": {
                            "username": ["This field is required."],
                            "password": ["This field is required."]
                        }
                    }
                )
            },
            tags=['Authentication'],
            security=[]  # No authentication required for login
        )
        def post(self, request, *args, **kwargs):
            return super().post(request, *args, **kwargs)

# User ViewSet
class UserViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def profile(self, request):
        user = request.user
        serializer = UserSerializer(user)
        data = serializer.data

        # Add wholesale details
        if user.wholesale:
            wholesale_serializer = WholesaleSerializer(user.wholesale)
            data['wholesale_name'] = wholesale_serializer.data['name']
            data['wholesale_phone_number'] = wholesale_serializer.data['phone_number']

        return Response(data, status=http_status.HTTP_200_OK)

    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_200_OK)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    def delete_profile(self, request):
        request.user.delete()
        return Response({"message": "Profile deleted successfully"}, status=http_status.HTTP_204_NO_CONTENT)
    
    def list_users(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

# Wholesale ViewSet
class WholesaleViewSet(viewsets.ModelViewSet):
    queryset = Wholesale.objects.all().order_by('-created_at')
    serializer_class = WholesaleSerializer
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimize queryset with select_related for parent"""
        return Wholesale.objects.select_related('parent').prefetch_related('children').order_by('-created_at')

# Register View
@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)
    return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

# Admin Update User View
@swagger_auto_schema(
    method='put',
    operation_description="Update user data by admin",
    operation_summary="Admin Update User",
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="JWT Bearer Token (required)",
            type=openapi.TYPE_STRING,
            format='Bearer <token>',
            required=True
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, example='newusername'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, example='user@example.com'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, example='John'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, example='Doe'),
            'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
        }
    ),
    responses={
        200: openapi.Response(
            description="User updated successfully",
            examples={
                "application/json": {
                    "id": 1,
                    "username": "newusername",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_staff": False
                }
            }
        ),
        401: openapi.Response(
            description="Authentication required",
            examples={
                "application/json": {
                    "detail": "Authentication credentials were not provided."
                }
            }
        ),
        404: openapi.Response(description="User not found")
    },
    tags=['User Management'],
    security=[{'Bearer': []}]
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=http_status.HTTP_200_OK)
    return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

# Admin Delete User View
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return Response({"message": "User deleted successfully"}, status=http_status.HTTP_204_NO_CONTENT)

# Change Password View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Password changed successfully"}, status=http_status.HTTP_200_OK)
    return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

# Reset Password View
@api_view(['POST'])
def reset_password(request):
    user = User.objects.filter(email=request.data.get('email')).first()
    if user:
        # Logic to reset password (send email or reset token)
        return Response({"message": "Reset password link sent"}, status=http_status.HTTP_200_OK)
    return Response({"message": "Email not found"}, status=http_status.HTTP_404_NOT_FOUND)

# Logout View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=http_status.HTTP_205_RESET_CONTENT)
    except Exception:
        return Response({"message": "Invalid token"}, status=http_status.HTTP_400_BAD_REQUEST)

# Retailer ViewSet
class RetailerViewSet(viewsets.ModelViewSet):
    queryset = Retailer.objects.all()
    serializer_class = RetailerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        retailer = self.get_object()
        photos = RetailerPhoto.objects.filter(retailer=retailer)
        serializer = RetailerPhotoSerializer(photos, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def verify_photos(self, request, pk=None):
        retailer = self.get_object()
        photos = RetailerPhoto.objects.filter(retailer=retailer)
        voucher = Voucher.objects.filter(retailer=retailer).first()
        project_id = voucher.project.id if voucher.project else None
        if not photos.exists():
            return Response({"message": "No photos found for this retailer."}, status=http_status.HTTP_404_NOT_FOUND)

        # Update current_count in VoucherLimit with project_id
        voucher_limit = VoucherLimit.objects.filter(voucher_project=project_id).first()
        if not voucher_limit:
            return Response({"message": "Voucher limit not found for this project."}, status=http_status.HTTP_404_NOT_FOUND)

        if voucher_limit.current_count >= voucher_limit.limit:
            return Response({"message": "Voucher limit reached"}, status=http_status.HTTP_200_OK)
        
        if voucher_limit:
            voucher_limit.current_count += 1
            voucher_limit.save()

        # Mark all photos as verified
        photos.update(is_verified=True, is_approved=True, verified_at=datetime.now(), approved_at=datetime.now())
        if voucher:
            voucher.is_approved = True
            voucher.approved_at = datetime.now()
            voucher.save()


        return Response({"message": "All photos for retailer verified successfully."}, status=http_status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject_photos(self, request, pk=None):
        retailer = self.get_object()
        photos = RetailerPhoto.objects.filter(retailer=retailer)
        voucher = Voucher.objects.filter(retailer=retailer).first()
        if not photos.exists():
            return Response({"message": "No photos found for this retailer."}, status=http_status.HTTP_404_NOT_FOUND)

        # Mark all photos as rejected
        photos.update(is_verified=True, is_approved=False, is_rejected=True, verified_at=datetime.now(), rejected_at=datetime.now())
        voucher.is_rejected = True
        voucher.rejected_at = datetime.now()
        voucher.save()
        return Response({"message": "All photos for retailer rejected successfully."}, status=http_status.HTTP_200_OK)

# Retailer Registration API
@api_view(['POST'])
def retailer_register_upload(request):
    serializer = RetailerRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.save()

        return Response({
            "message": "Retailer registered successfully",
            "voucher_code": data["voucher_code"],
            "retailer_id": data["retailer_id"]
        }, status=http_status.HTTP_201_CREATED)
    return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

# Redeem Voucher API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def redeem_voucher(request):
    serializer = VoucherRedeemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Voucher redeemed successfully"}, status=http_status.HTTP_201_CREATED)
    return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

# Submit Transaction Voucher API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_trx_voucher(request):
    required_fields = ['voucher_code', 'ws_id', 'total_price', 'total_price_after_discount', 'image', 'items']
    for field in required_fields:
        if not request.data.get(field):
            return Response({"error": f"{field} is required"}, status=http_status.HTTP_400_BAD_REQUEST)

    voucher = get_object_or_404(Voucher, code=request.data['voucher_code'])
    wholesaler = get_object_or_404(Wholesale, id=request.data['ws_id'])

    # Check if the voucher has already been submitted
    if WholesaleTransaction.objects.filter(voucher_redeem__voucher=voucher, voucher_redeem__wholesaler=wholesaler).exists():
        return Response({"error": "This voucher has already been submitted"}, status=http_status.HTTP_400_BAD_REQUEST)

    voucher_redeem = VoucherRedeem.objects.get(voucher=voucher, wholesaler=wholesaler)
    
    transaction = WholesaleTransaction.objects.create(
        total_price=request.data['total_price'],
        total_price_after_discount=request.data['total_price_after_discount'], 
        image=request.FILES['image'],
        voucher_redeem=voucher_redeem,
        created_by=request.user.username
    )
    items = request.data.get('items', [])
    if isinstance(items, str):
        items = json.loads(items)
    for item_data in items:
        item = get_object_or_404(Item, id=item_data['item_id'])
        WholesaleTransactionDetail.objects.create(
            transaction=transaction,
            item=item,
            qty=item_data['qty'],
            sub_total=item_data['sub_total']
        )

    return Response({
        "message": "Voucher redeemed and transaction saved successfully",
        "voucher_redeem": VoucherRedeemSerializer(voucher_redeem).data,
        "transaction": WholesaleTransactionSerializer(transaction).data
    }, status=http_status.HTTP_201_CREATED)

# Redeem Report API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def redeem_report(request):
    ws_id = request.query_params.get('ws_id')
    redeemed_vouchers = VoucherRedeem.objects.filter(wholesaler_id=ws_id) if ws_id else VoucherRedeem.objects.all()

    data = [
        {
            "voucher_code": voucher.voucher.code,
            "redeemed_at": voucher.redeemed_at,
            "wholesaler": voucher.wholesaler.name
        } for voucher in redeemed_vouchers
    ]
    return Response({"redeemed_vouchers": data}, status=http_status.HTTP_200_OK)

# List Retailer
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_retailers(request):
    filters = {
        'wholesale_id': request.query_params.get('ws_id'),
        'voucher__code': request.query_params.get('voucher_code'),
        'name': request.query_params.get('retailer_name')
    }
    filters = {k: v for k, v in filters.items() if v}

    retailers = Retailer.objects.filter(**filters)

    voucher_status = request.query_params.get('voucher_status')
    if voucher_status:
        status_filters = {
            'PENDING': {'voucher__is_approved': False, 'voucher__redeemed': False},
            'REJECTED': {'voucher__is_rejected': True, 'voucher__redeemed': False},
            'RECEIVED': {'voucher__is_approved': True, 'voucher__redeemed': False},
            'REDEEMED': {'voucher__is_approved': True, 'voucher__redeemed': True},
            'WAITING REIMBURSE': {'voucher__in': Reimburse.objects.filter(status__status='waiting').values_list('voucher', flat=True)},
            'REIMBURSE COMPLETED': {'voucher__in': Reimburse.objects.filter(status__status='completed').values_list('voucher', flat=True)},
            'REIMBURSE PAID': {'voucher__in': Reimburse.objects.filter(status__status='paid').values_list('voucher', flat=True)}
        }
        retailers = retailers.filter(**status_filters.get(voucher_status.upper(), {}))
        
    serializer = RetailerReportSerializer(retailers, many=True)
    return Response(serializer.data, status=http_status.HTTP_200_OK)

# List Retailer Photos
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_photos(request):
    filters = {
        'is_verified': request.query_params.get('is_verified'),
        'is_approved': request.query_params.get('is_approved'),
        'is_rejected': request.query_params.get('is_rejected'),
        'retailer__wholesale_id': request.query_params.get('ws_id')
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    photos = RetailerPhoto.objects.filter(**filters)
    if not photos.exists():
        return Response([], status=http_status.HTTP_200_OK)

    response_data = {}
    for photo in photos:
        retailer = photo.retailer
        retailer_id = retailer.id
        voucher = Voucher.objects.filter(retailer=retailer).first()
        voucher_code = voucher.code if voucher else None
        if retailer_id not in response_data:
            response_data[retailer_id] = {
                "wholesale_name": retailer.wholesale.name,
                "retailer_id": retailer_id,
                "retailer_name": retailer.name,
                "retailer_phone_number": retailer.phone_number,
                "retailer_address": retailer.address,
                "retailer_voucher_code": voucher_code,
                "retailer_voucher_status": "PENDING" if not voucher else "RECEIVED",
                "retailer_voucher_status_at": voucher.created_at if voucher else voucher.approved_at,
                "photos": []
            }
        response_data[retailer_id]["photos"].append({
            "image": photo.image.url if photo.image else None,
            "is_verified": photo.is_verified,
            "is_approved": photo.is_approved,
            "is_rejected": photo.is_rejected,
            "remarks": photo.remarks,
        })

    return Response(list(response_data.values()), status=http_status.HTTP_200_OK)

# Office Verification Report View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def office_verification_report(request):
    photos_to_verify = RetailerPhoto.objects.filter(is_verified=False).values('retailer').annotate(total=Count('id'))
    return Response({"photos_to_verify": list(photos_to_verify)}, status=http_status.HTTP_200_OK)

# List Vouchers
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_vouchers(request):
    filters = {
        'retailer_id': request.query_params.get('retailer_id'),
        'retailer__wholesale_id': request.query_params.get('ws_id'),
        'code': request.query_params.get('voucher_code'),
        'redeemed': request.query_params.get('redeemed')
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    vouchers = Voucher.objects.filter(**filters)
    serializer = VoucherSerializer(vouchers, many=True)
    return Response(serializer.data, status=http_status.HTTP_200_OK) 

@api_view(['GET'])
def kodepos_list(request):
    kodepos_list = Kodepos.objects.values_list('kodepos', flat=True).distinct()
    return Response(kodepos_list)

@api_view(['GET'])
def kelurahan_list(request):
    kecamatan = request.query_params.get('kecamatan')
    kelurahan_list = Kodepos.objects.filter(kecamatan=kecamatan).values_list('kelurahan', flat=True).distinct() if kecamatan else Kodepos.objects.values_list('kelurahan', flat=True).distinct()
    return Response(kelurahan_list)

@api_view(['GET'])
def kecamatan_list(request):
    kota = request.query_params.get('kota')
    kecamatan_list = Kodepos.objects.filter(kota=kota).values_list('kecamatan', flat=True).distinct() if kota else Kodepos.objects.values_list('kecamatan', flat=True).distinct()
    return Response(kecamatan_list)

@api_view(['GET'])
def kota_list(request):
    provinsi = request.query_params.get('provinsi')
    kota_list = Kodepos.objects.filter(provinsi=provinsi).values_list('kota', flat=True).distinct() if provinsi else Kodepos.objects.values_list('kota', flat=True).distinct()
    return Response(kota_list)

@api_view(['GET'])
def provinsi_list(request):
    provinsi_list = Kodepos.objects.values_list('provinsi', flat=True).distinct()
    return Response(provinsi_list)

class KodeposDetailView(APIView):
    def get(self, request):
        filters = {
            'kelurahan': request.query_params.get('kelurahan'),
            'kecamatan': request.query_params.get('kecamatan'),
            'kota': request.query_params.get('kota'),
            'provinsi': request.query_params.get('provinsi')
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        try:
            kodepos = Kodepos.objects.get(**filters)
            serializer = KodeposSerializer(kodepos)
            return Response(serializer.data)
        except Kodepos.DoesNotExist:
            return Response({"error": "Kodepos not found"}, status=http_status.HTTP_404_NOT_FOUND)

class ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, view_name):
        view_map = {
            'redeem_report': VoucherRedeem.objects.select_related('voucher', 'wholesaler').all(),
            'list_photos': RetailerPhoto.objects.all(),
            'list_vouchers': Voucher.objects.all(),
            'list_reimburse': Reimburse.objects.all()
        }
        return view_map.get(view_name)

    def get_serializer_class(self, view_name):
        serializer_map = {
            'redeem_report': VoucherRedeemSerializer,
            'list_photos': RetailerPhotoSerializer,
            'list_vouchers': VoucherSerializer,
            'list_reimburse': ReimburseSerializer
        }
        return serializer_map.get(view_name)

    def export_to_excel(self, queryset, serializer_class, file_path):
        serializer = serializer_class(queryset, many=True)
        data = serializer.data

        if serializer_class == VoucherRedeemSerializer:
            for item in data:
                voucher = Voucher.objects.get(pk=item['voucher'])
                wholesaler = Wholesale.objects.get(pk=item['wholesaler'])
                item.update({
                    'voucher': voucher.code,
                    'wholesaler': wholesaler.name,
                    'redeemed_at': item['redeemed_at'].split('T')[0],
                    'retailer': voucher.retailer.name
                })

        df = pd.DataFrame(data)
        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer._save()

    def get(self, request, view_name):
        queryset = self.get_queryset(view_name)
        serializer_class = self.get_serializer_class(view_name)
        if not queryset or not serializer_class:
            return Response({"error": "Invalid view name"}, status=http_status.HTTP_400_BAD_REQUEST)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(settings.MEDIA_ROOT, f'{view_name}-{timestamp}.xlsx')
        self.export_to_excel(queryset, serializer_class, file_path)
        
        return Response({"message": "Report generated successfully", "file_path": file_path}, status=http_status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_items(request):
    items = Item.objects.all()
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=http_status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_reimburse(request):
    voucher_codes = request.data.get('voucher_codes')
    if not voucher_codes or not isinstance(voucher_codes, list):
        return Response({"error": "Voucher codes must be provided as a list"}, status=http_status.HTTP_400_BAD_REQUEST)

    responses = []
    for voucher_code in voucher_codes:
        try:
            voucher = Voucher.objects.get(code=voucher_code)
        except Voucher.DoesNotExist:
            responses.append({"voucher_code": voucher_code, "error": "Voucher not found"})
            continue

        if Reimburse.objects.filter(voucher=voucher).exists():
            responses.append({"voucher_code": voucher_code, "error": "This voucher has already been submitted"})
            continue

        if not voucher.redeemed:
            responses.append({"voucher_code": voucher_code, "error": "This voucher has not been redeemed"})
            continue

        serializer = ReimburseSerializer(data={"voucher_code": voucher_code}, context={'request': request})
        if serializer.is_valid():
            serializer.save(reimbursed_by=request.user.username)
            responses.append({"voucher_code": voucher_code, "status": "submitted"})
        else:
            responses.append({"voucher_code": voucher_code, "error": serializer.errors})

    return Response(responses, status=http_status.HTTP_201_CREATED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_reimburse_status(request, pk, new_status):
    if new_status not in ['completed', 'paid']:
        return Response({"error": "Invalid status"}, status=http_status.HTTP_400_BAD_REQUEST)
    
    reimburse = get_object_or_404(Reimburse, pk=pk)

    # Create new status in ReimburseStatus
    status = ReimburseStatus.objects.create(
        status=new_status,
        status_at=datetime.now(),
        status_by=request.user.username
    )

    # Update status in Reimburse
    reimburse.status = status
    # if new_status == 'completed':
    #     reimburse.completed_at = datetime.now()
    # elif new_status == 'paid':
    #     reimburse.paid_at = datetime.now()
    reimburse.save()
    
    return Response({"message": f"Reimburse status updated to {new_status}"}, status=http_status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_reimburse(request):
    filters = {
        'status': request.query_params.get('status'),
        'id': request.query_params.get('id'),
        'voucher__code': request.query_params.get('voucher_code')
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    reimburses = Reimburse.objects.filter(**filters)
    reimburse_serializer = ReimburseSerializer(reimburses, many=True)
    reimburse_data = reimburse_serializer.data
    
    for reimburse in reimburse_data:
        if 'voucher_code' in reimburse:
            transactions = WholesaleTransaction.objects.filter(voucher_redeem__voucher__code=reimburse.get('voucher_code'))
            transaction_serializer = WholesaleTransactionSerializer(transactions, many=True)
            
            # Add retailer address details
            voucher = Voucher.objects.filter(code=reimburse.get('voucher_code')).first()
            if voucher and voucher.retailer:
                retailer = voucher.retailer
                reimburse['retailer_address'] = retailer.address
                reimburse['retailer_kelurahan'] = retailer.kelurahan
                reimburse['retailer_kecamatan'] = retailer.kecamatan
                reimburse['retailer_kota'] = retailer.kota
                reimburse['retailer_provinsi'] = retailer.provinsi
                
            reimburse['transactions'] = transaction_serializer.data
            for transaction in reimburse['transactions']:
                transaction_id = transaction['id']
                transaction_details = WholesaleTransactionDetail.objects.filter(transaction_id=transaction_id)
                transaction_detail_serializer = WholesaleTransactionDetailSerializer(transaction_details, many=True)
                transaction['details'] = transaction_detail_serializer.data

    return Response(reimburse_data, status=http_status.HTTP_200_OK)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_current_count(request):
    voucher_limit_id = request.query_params.get('id')
    project_id = request.query_params.get('project_id')

    filters = {}
    if voucher_limit_id:
        filters['id'] = voucher_limit_id
    if project_id:
        filters['voucher_project_id'] = project_id

    voucher_limit = VoucherLimit.objects.filter(**filters).first()

    if not voucher_limit:
        return Response({"error": "Voucher limit not set"}, status=http_status.HTTP_404_NOT_FOUND)

    if voucher_limit.current_count >= voucher_limit.limit:
        return Response({"message": "Voucher limit reached"}, status=http_status.HTTP_200_OK)

    return Response({
        "current_count": voucher_limit.current_count,
        "limit": voucher_limit.limit,
        "project_id": voucher_limit.voucher_project_id if voucher_limit.voucher_project_id else None
    }, status=http_status.HTTP_200_OK)

class VoucherLimitViewSet(viewsets.ModelViewSet):
    queryset = VoucherLimit.objects.select_related('voucher_project').all()
    serializer_class = VoucherLimitSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def increment(self, request, pk=None):
        """Increment current count for voucher limit"""
        voucher_limit = self.get_object()
        serializer = VoucherLimitUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            increment = serializer.validated_data['increment']
            new_count = voucher_limit.current_count + increment
            
            # Check if increment would exceed limit
            if new_count > voucher_limit.limit:
                return Response({
                    'error': f'Cannot increment by {increment}. Would exceed limit of {voucher_limit.limit}',
                    'current_count': voucher_limit.current_count,
                    'limit': voucher_limit.limit,
                    'remaining': voucher_limit.limit - voucher_limit.current_count
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            voucher_limit.current_count = new_count
            voucher_limit.save()
            
            return Response({
                'message': f'Voucher count incremented by {increment}',
                'current_count': voucher_limit.current_count,
                'limit': voucher_limit.limit,
                'remaining': voucher_limit.limit - voucher_limit.current_count
            }, status=http_status.HTTP_200_OK)
        
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of all voucher limits"""
        limits = self.get_queryset()
        total_allocated = sum(limit.limit for limit in limits)
        total_used = sum(limit.current_count for limit in limits)
        total_remaining = total_allocated - total_used
        
        return Response({
            'total_limits': limits.count(),
            'total_allocated': total_allocated,
            'total_used': total_used,
            'total_remaining': total_remaining,
            'usage_percentage': (total_used / total_allocated * 100) if total_allocated > 0 else 0
        }, status=http_status.HTTP_200_OK)


class VoucherProjectViewSet(viewsets.ModelViewSet):
    queryset = VoucherProject.objects.prefetch_related('voucherlimit_set').all()
    serializer_class = VoucherProjectSerializer
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(periode_start__gte=start_date)
        if end_date:
            queryset = queryset.filter(periode_end__lte=end_date)
            
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active voucher projects"""
        active_projects = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_projects, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        }, status=http_status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle active status of voucher project"""
        project = self.get_object()
        project.is_active = not project.is_active
        project.updated_by = request.user.username if hasattr(request, 'user') else None
        project.updated_at = datetime.now()
        project.save()
        
        return Response({
            'message': f'Project status changed to {"active" if project.is_active else "inactive"}',
            'is_active': project.is_active
        }, status=http_status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard summary for voucher projects"""
        projects = self.get_queryset()
        active_projects = projects.filter(is_active=True)
        
        # Calculate totals
        total_allocated = 0
        total_used = 0
        
        for project in projects:
            for limit in project.voucherlimit_set.all():
                total_allocated += limit.limit
                total_used += limit.current_count
        
        summary_data = {
            'total_projects': projects.count(),
            'active_projects': active_projects.count(),
            'inactive_projects': projects.count() - active_projects.count(),
            'total_allocated_vouchers': total_allocated,
            'total_used_vouchers': total_used,
            'total_remaining_vouchers': total_allocated - total_used,
            'usage_percentage': (total_used / total_allocated * 100) if total_allocated > 0 else 0
        }
        
        serializer = VoucherProjectSummarySerializer(summary_data)
        return Response(serializer.data, status=http_status.HTTP_200_OK)


class VoucherRetailerDiscountViewSet(viewsets.ModelViewSet):
    queryset = VoucherRetailerDiscount.objects.select_related('voucher_project').all()
    serializer_class = VoucherRetailerDiscountSerializer
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by voucher project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(voucher_project_id=project_id)
        
        # Filter by discount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        
        if min_amount:
            queryset = queryset.filter(discount_amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(discount_amount__lte=max_amount)
            
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """Get discounts grouped by voucher project"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'project_id parameter required'}, status=http_status.HTTP_400_BAD_REQUEST)
        
        try:
            project = VoucherProject.objects.get(id=project_id)
            discounts = self.get_queryset().filter(voucher_project=project)
            serializer = self.get_serializer(discounts, many=True)
            
            return Response({
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'is_active': project.is_active
                },
                'discounts': serializer.data,
                'count': len(serializer.data)
            }, status=http_status.HTTP_200_OK)
            
        except VoucherProject.DoesNotExist:
            return Response({'error': 'Voucher project not found'}, status=http_status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_voucher(self, request):
        """Get discounts grouped by voucher"""
        voucher_code = request.query_params.get('voucher_code')
        if not voucher_code:
            return Response({'error': 'voucher_code parameter required'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            voucher = Voucher.objects.get(code=voucher_code)
            project = VoucherProject.objects.get(id=voucher.project_id)
            # project = voucher.project_id
            print(project)
            discounts = self.get_queryset().filter(voucher_project=project)
            serializer = self.get_serializer(discounts, many=True)
            
            return Response({
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'is_active': project.is_active
                },
                'discounts': serializer.data,
                'count': len(serializer.data)
            }, status=http_status.HTTP_200_OK)
            
        except VoucherProject.DoesNotExist:
            return Response({'error': 'Voucher project not found'}, status=http_status.HTTP_404_NOT_FOUND)

    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of all voucher discounts"""
        discounts = self.get_queryset()
        
        total_discounts = discounts.count()
        avg_discount_amount = discounts.aggregate(
            avg_amount=models.Avg('discount_amount'),
            avg_percentage=models.Avg('discount_percentage'),
            total_agen_fee=models.Sum('agen_fee')
        )
        
        return Response({
            'total_discounts': total_discounts,
            'average_discount_amount': avg_discount_amount['avg_amount'] or 0,
            'average_discount_percentage': avg_discount_amount['avg_percentage'] or 0,
            'total_agen_fee': avg_discount_amount['total_agen_fee'] or 0
        }, status=http_status.HTTP_200_OK)
    permission_classes = [IsAuthenticated]