# Revised views.py
from rest_framework import status, viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from office.models import User, Kodepos, Item, Reimburse
from retailer.models import Retailer, RetailerPhoto, Voucher
from wholesales.models import Wholesale, VoucherRedeem, WholesaleTransaction, WholesaleTransactionDetail
from django.shortcuts import get_object_or_404
from .serializers import (
    UserSerializer, CustomTokenObtainPairSerializer, ChangePasswordSerializer, WholesaleSerializer, 
    VoucherRedeemSerializer, RetailerRegistrationSerializer, RetailerPhotoSerializer, 
    RetailerSerializer, RetailerPhotoVerificationSerializer, RetailerPhotoRejectionSerializer,
    VoucherSerializer, KodeposSerializer, ItemSerializer, WholesaleTransactionSerializer,
    ReimburseSerializer, RetailerReportSerializer, WholesaleTransactionDetailSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count
from datetime import datetime
import pandas as pd
from django.conf import settings
from django.core.mail import send_mail
import json

# Custom Token Obtain Pair View
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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

        return Response(data, status=status.HTTP_200_OK)

    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_profile(self, request):
        request.user.delete()
        return Response({"message": "Profile deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    def list_users(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Wholesale ViewSet
class WholesaleViewSet(viewsets.ModelViewSet):
    queryset = Wholesale.objects.all()
    serializer_class = WholesaleSerializer
    # permission_classes = [IsAuthenticated]

# Register View
@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Admin Update User View
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Admin Delete User View
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

# Change Password View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Reset Password View
@api_view(['POST'])
def reset_password(request):
    user = User.objects.filter(email=request.data.get('email')).first()
    if user:
        # Logic to reset password (send email or reset token)
        return Response({"message": "Reset password link sent"}, status=status.HTTP_200_OK)
    return Response({"message": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

# Logout View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
    except Exception:
        return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def verify_photos(self, request, pk=None):
        retailer = self.get_object()
        photos = RetailerPhoto.objects.filter(retailer=retailer)
        voucher = Voucher.objects.filter(retailer=retailer).first()
        if not photos.exists():
            return Response({"message": "No photos found for this retailer."}, status=status.HTTP_404_NOT_FOUND)

        # Mark all photos as verified
        photos.update(is_verified=True, is_approved=True, verified_at=datetime.now())
        voucher.is_approved = True
        voucher.save()
        return Response({"message": "All photos for retailer verified successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject_photos(self, request, pk=None):
        retailer = self.get_object()
        photos = RetailerPhoto.objects.filter(retailer=retailer)
        voucher = Voucher.objects.filter(retailer=retailer).first()
        if not photos.exists():
            return Response({"message": "No photos found for this retailer."}, status=status.HTTP_404_NOT_FOUND)

        # Mark all photos as rejected
        photos.update(is_verified=True, is_approved=False, is_rejected=True, verified_at=datetime.now())
        voucher.is_rejected = True
        voucher.save()
        return Response({"message": "All photos for retailer rejected successfully."}, status=status.HTTP_200_OK)

# Retailer Registration API
@api_view(['POST'])
def retailer_register_upload(request):
    serializer = RetailerRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.save()
        # send email notification
        subject = f'Verifikasi Retailer'
        message = f"""
        <html>
        <body>
            <p>Dear Admin,</p>
            <p>Berkaitan dengan program Super Perdana, Retailer sudah melakukan pendaftaran dengan detail dibawah ini.</p>
            <table>
            <tr><td><strong>Nama Retailer</strong></td><td>: {request.data['name']}</td></tr>
            <tr><td><strong>No WhatsApp</strong></td><td>: {request.data['phone_number']}</td></tr>
            <tr><td><strong>Nama Agen</strong></td><td>: {request.data['ws_name']}</td></tr>
            <tr><td><strong>Tanggal Pengisian</strong></td><td>: {datetime.now().strftime('%Y-%m-%d')}</td></tr>
            <tr><td><strong>Status</strong></td><td>: Menunggu Verifikasi</td></tr>
            </table>
            <p>Mohon segara melakukan verifikasi data mereka dengan cara klik tombol di bawah Ini untuk melihat dan memverifikasi formulir mereka:</p>
            <p><a href="http://10.0.29.49:81/verification">Verifikasi Sekarang</a></p>
        </body>
        </html>
        """
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['banyu.senjana@limamail.net', 'dimas.rosadi@limamail.net']
        send_mail(subject, message, email_from, recipient_list, html_message=message)

        return Response({
            "message": "Retailer registered successfully",
            "voucher_code": data["voucher_code"],
            "retailer_id": data["retailer_id"]
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Redeem Voucher API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def redeem_voucher(request):
    serializer = VoucherRedeemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Voucher redeemed successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Submit Transaction Voucher API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_trx_voucher(request):
    required_fields = ['voucher_code', 'ws_id', 'total_price', 'total_price_after_discount', 'image', 'items']
    for field in required_fields:
        if not request.data.get(field):
            return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

    voucher = get_object_or_404(Voucher, code=request.data['voucher_code'])
    wholesaler = get_object_or_404(Wholesale, id=request.data['ws_id'])

    # Check if the voucher has already been submitted
    if WholesaleTransaction.objects.filter(voucher_redeem__voucher=voucher, voucher_redeem__wholesaler=wholesaler).exists():
        return Response({"error": "This voucher has already been submitted"}, status=status.HTTP_400_BAD_REQUEST)

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
    }, status=status.HTTP_201_CREATED)

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
    return Response({"redeemed_vouchers": data}, status=status.HTTP_200_OK)

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
            'WAITING PAYMENT': {'voucher__in': Reimburse.objects.exclude(status='closed').values_list('voucher', flat=True)},
            'PAYMENT COMPLETED': {'voucher__in': Reimburse.objects.filter(status='closed').values_list('voucher', flat=True)}
        }
        retailers = retailers.filter(**status_filters.get(voucher_status.upper(), {}))
        
    serializer = RetailerReportSerializer(retailers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

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
        return Response({"message": "No photos found"}, status=status.HTTP_404_NOT_FOUND)

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
                "photos": []
            }
        response_data[retailer_id]["photos"].append({
            "image": photo.image.url,
            "is_verified": photo.is_verified,
            "is_approved": photo.is_approved,
            "is_rejected": photo.is_rejected,
            "remarks": photo.remarks,
        })

    return Response(list(response_data.values()), status=status.HTTP_200_OK)

# Office Verification Report View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def office_verification_report(request):
    photos_to_verify = RetailerPhoto.objects.filter(is_verified=False).values('retailer').annotate(total=Count('id'))
    return Response({"photos_to_verify": list(photos_to_verify)}, status=status.HTTP_200_OK)

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
    return Response(serializer.data, status=status.HTTP_200_OK)

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
            return Response({"error": "Kodepos not found"}, status=status.HTTP_404_NOT_FOUND)

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
            return Response({"error": "Invalid view name"}, status=status.HTTP_400_BAD_REQUEST)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(settings.MEDIA_ROOT, f'{view_name}-{timestamp}.xlsx')
        self.export_to_excel(queryset, serializer_class, file_path)
        
        return Response({"message": "Report generated successfully", "file_path": file_path}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_items(request):
    items = Item.objects.all()
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_reimburse(request):
    voucher_codes = request.data.get('voucher_codes')
    if not voucher_codes or not isinstance(voucher_codes, list):
        return Response({"error": "Voucher codes must be provided as a list"}, status=status.HTTP_400_BAD_REQUEST)

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

        serializer = ReimburseSerializer(data={"voucher_code": voucher_code})
        if serializer.is_valid():
            serializer.save(reimbursed_by=request.user.username)
            responses.append({"voucher_code": voucher_code, "status": "submitted"})
        else:
            responses.append({"voucher_code": voucher_code, "error": serializer.errors})

    return Response(responses, status=status.HTTP_201_CREATED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_reimburse_status(request, pk, new_status):
    if new_status not in ['completed']:
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
    
    reimburse = get_object_or_404(Reimburse, pk=pk)
    reimburse.status = new_status
    reimburse.completed_at = datetime.now()
    reimburse.save()
    return Response({"message": f"Reimburse status updated to {new_status}"}, status=status.HTTP_200_OK)

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

    return Response(reimburse_data, status=status.HTTP_200_OK)
