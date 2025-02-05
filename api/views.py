# Revised views.py
from rest_framework import status, viewsets, mixins, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from office.models import User, Kodepos, Item, Reimburse
from retailer.models import Retailer, RetailerPhoto, Voucher
from wholesales.models import Wholesale, VoucherRedeem, WholesaleTransaction
from django.shortcuts import get_object_or_404
from .serializers import (
    UserSerializer, CustomTokenObtainPairSerializer, ChangePasswordSerializer, WholesaleSerializer, 
    VoucherRedeemSerializer, RetailerRegistrationSerializer, RetailerPhotoSerializer, 
    RetailerSerializer, RetailerPhotoVerificationSerializer, RetailerPhotoRejectionSerializer,
    VoucherSerializer, KodeposSerializer, ItemSerializer, WholesaleTransactionSerializer,
    ReimburseSerializer, RetailerReportSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count
from datetime import datetime
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
import os
from django.conf import settings

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
        if not photos.exists():
            return Response({"message": "No photos found for this retailer."}, status=status.HTTP_404_NOT_FOUND)

        # Mark all photos as rejected
        photos.update(is_verified=True, is_approved=False)
        return Response({"message": "All photos for retailer rejected successfully."}, status=status.HTTP_200_OK)

from django.core.mail import send_mail
# Retailer Registration API
@api_view(['POST'])
def retailer_register_upload(request):
    serializer = RetailerRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.save()
        # send email notification
        subject = 'Retailer Registration Notification'
        message = f"Retailer with Name {request.data['name']} has registered successfully, please do verification"
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['dimas.rosadi@limamail.net']
        send_mail(subject, message, email_from, recipient_list)

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
    voucher_code = request.data.get('voucher_code')
    wholesaler_id = request.data.get('wholesaler_id')
    ryp_qty = request.data.get('ryp_qty')
    rys_qty = request.data.get('rys_qty')
    rym_qty = request.data.get('rym_qty')
    total_price = request.data.get('total_price')
    total_price_after_discount = request.data.get('total_price_after_discount')
    image = request.FILES.get('image')

    # Validate required fields
    if not voucher_code:
        return Response({"error": "Voucher code is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not wholesaler_id:
        return Response({"error": "Wholesaler ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    if ryp_qty is None:
        return Response({"error": "ryp_qty is required"}, status=status.HTTP_400_BAD_REQUEST)
    if rys_qty is None:
        return Response({"error": "rys_qty is required"}, status=status.HTTP_400_BAD_REQUEST)
    if rym_qty is None:
        return Response({"error": "rym_qty is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not total_price:
        return Response({"error": "total_price is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not total_price_after_discount:
        return Response({"error": "total_price_after_discount is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not image:
        return Response({"error": "image is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        voucher = Voucher.objects.get(code=voucher_code)
    except Voucher.DoesNotExist:
        return Response({"error": "Voucher not found"}, status=status.HTTP_404_NOT_FOUND)

    # if voucher.redeemed:
    #     return Response({"error": "Voucher has already been redeemed"}, status=status.HTTP_400_BAD_REQUEST)

    wholesaler = get_object_or_404(Wholesale, id=wholesaler_id)

    # Redeem the voucher
    voucher_redeem = VoucherRedeem.objects.get(voucher=voucher, wholesaler=wholesaler)
    # voucher_id = voucher_redeem.id
    # print(voucher_redeem)

    # # Update voucher as redeemed
    # voucher.redeemed = 1
    # voucher.save()

    # Save the transaction
    transaction = WholesaleTransaction.objects.create(
        ryp_qty=ryp_qty,
        rys_qty=rys_qty,
        rym_qty=rym_qty,
        total_price=total_price,
        total_price_after_discount=total_price_after_discount, 
        image=image,
        voucher_redeem=voucher_redeem,
        created_by=request.user.username
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
    if ws_id:
        wholesaler = get_object_or_404(Wholesale, id=ws_id)
        redeemed_vouchers = VoucherRedeem.objects.filter(wholesaler=wholesaler)
    else:
        redeemed_vouchers = VoucherRedeem.objects.all()

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
    ws_id = request.query_params.get('ws_id')
    voucher_code = request.query_params.get('voucher_code')
    voucher_status = request.query_params.get('voucher_status')
    retailer_name = request.query_params.get('retailer_name')
    

    if ws_id:
        retailers = Retailer.objects.filter(wholesale_id=ws_id)
    else:
        retailers = Retailer.objects.all()

    if retailer_name:
        retailers = Retailer.objects.filter(name=retailer_name)
    
    if voucher_code:
        retailers = Retailer.objects.filter(voucher__code=voucher_code)

    if voucher_status:
        if voucher_status.upper() == 'PENDING':
            retailers = retailers.filter(voucher__is_approved=False, voucher__redeemed=False)
        elif voucher_status.upper() == 'RECEIVED':
            retailers = retailers.filter(voucher__is_approved=True, voucher__redeemed=False)
        elif voucher_status.upper() == 'CLAIMED':
            retailers = retailers.filter(voucher__is_approved=True, voucher__redeemed=True)
        elif voucher_status.upper() == 'REIMBURSED':
            reimbursed_vouchers = Reimburse.objects.exclude(status='closed').values_list('voucher', flat=True)
            retailers = retailers.filter(voucher__in=reimbursed_vouchers)
        elif voucher_status.upper() == 'PAID':
            reimbursed_vouchers = Reimburse.objects.filter(status='closed').values_list('voucher', flat=True)
            retailers = retailers.filter(voucher__in=reimbursed_vouchers)
        
    serializer = RetailerReportSerializer(retailers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# List Retailer Photos
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_photos(request):
    is_verified = request.query_params.get('is_verified')
    is_approved = request.query_params.get('is_approved')
    ws_id = request.query_params.get('ws_id')  

    if is_verified is not None:
        photos = RetailerPhoto.objects.filter(is_verified=is_verified)
    elif is_approved is not None:
        photos = RetailerPhoto.objects.filter(is_approved=is_approved)
    else:
        photos = RetailerPhoto.objects.all()

    if ws_id:  
        retailers = Retailer.objects.filter(wholesale_id=ws_id)
        photos = photos.filter(retailer__in=retailers)

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
            "remarks": photo.remarks,
        })

    return Response(list(response_data.values()), status=status.HTTP_200_OK)

# Verify Photo View
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def verify_photo(request):
#     serializer = RetailerPhotoVerificationSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({"message": "Photo verified successfully"}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    retailer_id = request.query_params.get('retailer_id')
    ws_id = request.query_params.get('ws_id')
    redeemed = request.query_params.get('redeemed')
    voucher_code = request.query_params.get('voucher_code')

    if retailer_id:
        vouchers = Voucher.objects.filter(retailer_id=retailer_id)
    elif ws_id:
        retailers = Retailer.objects.filter(wholesale_id=ws_id)
        vouchers = Voucher.objects.filter(retailer__in=retailers)
    else:
        vouchers = Voucher.objects.all()
    
    if voucher_code is not None:
        vouchers = Voucher.objects.filter(code=voucher_code)

    if redeemed is not None:
        vouchers = vouchers.filter(redeemed=redeemed)

    serializer = VoucherSerializer(vouchers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def kodepos_list(request):
    kodepos_list = Kodepos.objects.values_list('kodepos', flat=True).distinct()
    return Response(kodepos_list)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def kelurahan_list(request):
    kecamatan = request.query_params.get('kecamatan')
    if kecamatan:
        kelurahan_list = Kodepos.objects.filter(kecamatan=kecamatan).values_list('kelurahan', flat=True).distinct()
    else:
        kelurahan_list = Kodepos.objects.values_list('kelurahan', flat=True).distinct()
    return Response(kelurahan_list)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def kecamatan_list(request):
    kota = request.query_params.get('kota')
    if kota:
        kecamatan_list = Kodepos.objects.filter(kota=kota).values_list('kecamatan', flat=True).distinct()
    else:
        kecamatan_list = Kodepos.objects.values_list('kecamatan', flat=True).distinct()
    return Response(kecamatan_list)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def kota_list(request):
    provinsi = request.query_params.get('provinsi')
    if provinsi:
        kota_list = Kodepos.objects.filter(provinsi=provinsi).values_list('kota', flat=True).distinct()
    else:
        kota_list = Kodepos.objects.values_list('kota', flat=True).distinct()
    return Response(kota_list)
    
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def provinsi_list(request):
    provinsi_list = Kodepos.objects.values_list('provinsi', flat=True).distinct()
    return Response(provinsi_list)

class KodeposDetailView(APIView):
    def get(self, request):
        kelurahan = request.query_params.get('kelurahan')
        kecamatan = request.query_params.get('kecamatan')
        kota = request.query_params.get('kota')
        provinsi = request.query_params.get('provinsi')
        
        try:
            kodepos = Kodepos.objects.get(kelurahan=kelurahan, kecamatan=kecamatan, kota=kota, provinsi=provinsi)
            serializer = KodeposSerializer(kodepos)
            return Response(serializer.data)
        except Kodepos.DoesNotExist:
            return Response({"error": "Kodepos not found"}, status=404)

class ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, view_name):
        if view_name == 'redeem_report':
            return VoucherRedeem.objects.select_related('voucher', 'wholesaler').all()
        elif view_name == 'list_photos':
            return RetailerPhoto.objects.all()
        elif view_name == 'list_vouchers':
            return Voucher.objects.all()
        elif view_name == 'list_reimburse':
            return Reimburse.objects.all()
        # Add more views as needed
        return None

    def get_serializer_class(self, view_name):
        if view_name == 'redeem_report':
            return VoucherRedeemSerializer
        elif view_name == 'list_photos':
            return RetailerPhotoSerializer
        elif view_name == 'list_vouchers':
            return VoucherSerializer
        elif view_name == 'list_reimburse':
            return ReimburseSerializer
        # Add more serializers as needed
        return None

    def export_to_excel(self, queryset, serializer_class, file_path):
        serializer = serializer_class(queryset, many=True)
        data = serializer.data

        # Modify data for redeem_report to include voucher code
        if serializer_class == VoucherRedeemSerializer:
            for item in data:
                voucher = Voucher.objects.get(pk=item['voucher'])
                wholesaler = Wholesale.objects.get(pk=item['wholesaler'])
                item['voucher'] = voucher.code
                item['wholesaler'] = wholesaler.name
                item['redeemed_at'] = item['redeemed_at'].split('T')[0]
                item['retailer'] = voucher.retailer.name

        df = pd.DataFrame(data)
        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer._save()

    def get(self, request, view_name):
        # Access the request object to avoid compile error
        user = request.user
        queryset = self.get_queryset(view_name)
        serializer_class = self.get_serializer_class(view_name)
        if queryset is None or serializer_class is None:
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

        # Check if the voucher has already been submitted
        if Reimburse.objects.filter(voucher=voucher).exists():
            responses.append({"voucher_code": voucher_code, "error": "This voucher has already been submitted"})
            continue

        # Check if the voucher has been redeemed
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
    reimburse = get_object_or_404(Reimburse, pk=pk)
    if new_status not in ['inprogress', 'closed']:
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
    
    reimburse.status = new_status
    reimburse.save()
    return Response({"message": f"Reimburse status updated to {new_status}"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_reimburse(request):
    status_filter = request.query_params.get('status')
    id_filter = request.query_params.get('id')
    voucher_code = request.query_params.get('voucher_code')

    if status_filter:
        reimburses = Reimburse.objects.filter(status=status_filter)
    elif id_filter:
        reimburses = Reimburse.objects.filter(id=id_filter)
    else:
        reimburses = Reimburse.objects.all()

    if voucher_code:
        reimburses = reimburses.filter(voucher__code=voucher_code)

    serializer = ReimburseSerializer(reimburses, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)