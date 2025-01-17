# Revised views.py
from rest_framework import status, viewsets, mixins, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from office.models import User, Kodepos
from retailer.models import Retailer, RetailerPhoto, Voucher
from wholesales.models import Wholesale, VoucherRedeem
from django.shortcuts import get_object_or_404
from .serializers import (
    UserSerializer, CustomTokenObtainPairSerializer, ChangePasswordSerializer, WholesaleSerializer, 
    VoucherRedeemSerializer, RetailerRegistrationSerializer, RetailerPhotoSerializer, 
    RetailerSerializer, RetailerPhotoVerificationSerializer, RetailerPhotoRejectionSerializer,
    VoucherSerializer, KodeposSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count

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

# Register View
@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

# Wholesale ViewSet
class WholesaleViewSet(viewsets.ModelViewSet):
    queryset = Wholesale.objects.all()
    serializer_class = WholesaleSerializer
    permission_classes = [IsAuthenticated]

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
        if not photos.exists():
            return Response({"message": "No photos found for this retailer."}, status=status.HTTP_404_NOT_FOUND)

        # Mark all photos as verified
        photos.update(is_verified=True, is_approved=True, verified_at=datetime.now())
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

# Redeem Report API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def redeem_report(request, name=None):
    if name:
        wholesaler = get_object_or_404(Wholesale, name=name)
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

# List Retailer Photos
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_photos(request):
    is_verified = request.query_params.get('is_verified')
    is_approved = request.query_params.get('is_approved')

    if is_verified is not None:
        photos = RetailerPhoto.objects.filter(is_verified=is_verified)
    elif is_approved is not None:
        photos = RetailerPhoto.objects.filter(is_approved=is_approved)
    else:
        photos = RetailerPhoto.objects.all()

    if not photos.exists():
        return Response({"message": "No photos found"}, status=status.HTTP_404_NOT_FOUND)

    response_data = {}
    for photo in photos:
        retailer = photo.retailer
        retailer_id = retailer.id
        if retailer_id not in response_data:
            response_data[retailer_id] = {
                "retailer_id": retailer_id,
                "retailer_name": retailer.name,
                "retailer_phone_number": retailer.phone_number,
                "retailer_address": retailer.address,
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
    vouchers = Voucher.objects.all()
    serializer = VoucherSerializer(vouchers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kodepos_list(request):
    kodepos_list = Kodepos.objects.values_list('kodepos', flat=True).distinct()
    return Response(kodepos_list)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kelurahan_list(request):
    kecamatan = request.query_params.get('kecamatan')
    if kecamatan:
        kelurahan_list = Kodepos.objects.filter(kecamatan=kecamatan).values_list('kelurahan', flat=True).distinct()
    else:
        kelurahan_list = Kodepos.objects.values_list('kelurahan', flat=True).distinct()
    return Response(kelurahan_list)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kecamatan_list(request):
    kota = request.query_params.get('kota')
    if kota:
        kecamatan_list = Kodepos.objects.filter(kota=kota).values_list('kecamatan', flat=True).distinct()
    else:
        kecamatan_list = Kodepos.objects.values_list('kecamatan', flat=True).distinct()
    return Response(kecamatan_list)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kota_list(request):
    provinsi = request.query_params.get('provinsi')
    if provinsi:
        kota_list = Kodepos.objects.filter(provinsi=provinsi).values_list('kota', flat=True).distinct()
    else:
        kota_list = Kodepos.objects.values_list('kota', flat=True).distinct()
    return Response(kota_list)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
