from rest_framework import serializers
from office.models import User, Kodepos, Item, Reimburse
from wholesales.models import Wholesale, VoucherRedeem, WholesaleTransaction
from retailer.models import Voucher, Retailer, RetailerPhoto
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import random, string
from datetime import datetime
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

# Custom Token Serializer
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        wholesale_data = {}

        # Include additional wholesale details if applicable
        if hasattr(self.user, 'wholesale_id') and self.user.wholesale_id:
            try:
                wholesale = Wholesale.objects.get(id=self.user.wholesale_id)
                wholesale_data = {
                    'name': wholesale.name,
                    'phone_number': wholesale.phone_number
                }
            except Wholesale.DoesNotExist:
                wholesale_data = {
                    'name': None,
                    'phone_number': None
                }
                
        # Add custom fields to the response
        data.update({
            'message': "Login successful",
            'userid': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'is_staff': self.user.is_staff,
            'wholesale': self.user.wholesale_id,
            **wholesale_data  # Tambahkan data wholesale
        })
        return data

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    wholesale_name = serializers.CharField(source='wholesale.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'wholesale', 'wholesale_name', 'is_active', 'is_staff']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user

# Change Password Serializer
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError("Current password is incorrect.")
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# Wholesale Serializer
class WholesaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wholesale
        fields = ['id', 'name', 'phone_number', 'address', 'pic', 'is_active']

    def validate_phone_number(self, value):
        if value.startswith('0'):
            value = '62' + value[1:]
        return value

    def create(self, validated_data):
        return Wholesale.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.phone_number = self.validate_phone_number(validated_data.get('phone_number', instance.phone_number))
        instance.address = validated_data.get('address', instance.address)
        instance.pic = validated_data.get('pic', instance.pic)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance 
    
# Voucher Redeem Serializer
class VoucherRedeemSerializer(serializers.ModelSerializer):
    voucher_code = serializers.CharField(write_only=True)
    ws_name = serializers.CharField(write_only=True)

    class Meta:
        model = VoucherRedeem
        fields = ['voucher_code', 'ws_name', 'voucher', 'wholesaler', 'redeemed_at']
        read_only_fields = ['voucher_code', 'ws_name', 'voucher', 'wholesaler', 'redeemed_at']

    def validate(self, data):
        voucher_code = data.get('voucher_code')
        ws_name = data.get('ws_name')

        # Validate voucher existence and availability
        try:
            voucher = Voucher.objects.get(code=voucher_code, redeemed=False)
        except Voucher.DoesNotExist:
            raise serializers.ValidationError("Invalid or already redeemed voucher code.")

        # Validate wholesaler existence
        try:
            wholesaler = Wholesale.objects.get(name=ws_name)
        except Wholesale.DoesNotExist:
            raise serializers.ValidationError("Invalid wholesaler name.")

        # Validate wholesaler ID matches retailer's wholesaler ID
        retailer = voucher.retailer
        if wholesaler.id != retailer.wholesale_id:
            raise serializers.ValidationError("Wholesaler ID does not match retailer's wholesaler ID.")

        # Validate retailer photo verification
        retailer = voucher.retailer
        if not RetailerPhoto.objects.filter(retailer=retailer, is_verified=True).exists():
            raise serializers.ValidationError("Retailer's photos have not been verified yet.")
        elif not RetailerPhoto.objects.filter(retailer=retailer, is_approved=True).exists():
            raise serializers.ValidationError("Retailer's photos have been rejected.")

        data['voucher'] = voucher
        data['wholesaler'] = wholesaler
        return data

    def create(self, validated_data):
        voucher = validated_data['voucher']
        wholesaler = validated_data['wholesaler']

        # Mark voucher as redeemed
        voucher.redeemed = True
        voucher.save()

        # Save redemption record
        return VoucherRedeem.objects.create(voucher=voucher, wholesaler=wholesaler)
    
# Retailer Photo Serializer
class RetailerPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailerPhoto
        fields = ['retailer_id', 'id', 'image', 'is_verified', 'is_approved']

# Retailer Serializer
class RetailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ['id', 'name', 'phone_number', 'address', 'wholesale']

    def validate_phone_number(self, value):
        if value.startswith('0'):
            value = '62' + value[1:]
        return value

    def create(self, validated_data):
        return Retailer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.phone_number = self.validate_phone_number(validated_data.get('phone_number', instance.phone_number))
        instance.address = validated_data.get('address', instance.address)
        instance.wholesale = validated_data.get('wholesale', instance.wholesale)
        instance.save()
        return instance
    
# Retailer Photo Verification Serializer
class RetailerPhotoVerificationSerializer(serializers.Serializer):
    retailer_id = serializers.IntegerField(required=True)
    photo_id = serializers.IntegerField(required=True)

    def validate(self, data):
        retailer_id = data.get('retailer_id')
        photo_id = data.get('photo_id')

        # Validate retailer existence
        try:
            retailer = Retailer.objects.get(id=retailer_id)
        except Retailer.DoesNotExist:
            raise serializers.ValidationError("Retailer not found.")

        # Validate photo existence
        try:
            photo = RetailerPhoto.objects.get(id=photo_id, retailer=retailer)
        except RetailerPhoto.DoesNotExist:
            raise serializers.ValidationError("Photo not found.")

        data['retailer'] = retailer
        data['photo'] = photo
        return data

    def save(self):
        photo = self.validated_data['photo']
        photo.is_verified = True
        photo.save()

        return photo

# Retailer Photo Rejection Serializer
class RetailerPhotoRejectionSerializer(serializers.Serializer):
    retailer_id = serializers.IntegerField(required=True)
    photo_id = serializers.IntegerField(required=True)

    def validate(self, data):
        retailer_id = data.get('retailer_id')
        photo_id = data.get('photo_id')

        # Validate retailer existence
        try:
            retailer = Retailer.objects.get(id=retailer_id)
        except Retailer.DoesNotExist:
            raise serializers.ValidationError("Retailer not found.")

        # Validate photo existence
        try:
            photo = RetailerPhoto.objects.get(id=photo_id, retailer=retailer)
        except RetailerPhoto.DoesNotExist:
            raise serializers.ValidationError("Photo not found.")

        data['retailer'] = retailer
        data['photo'] = photo
        return data

    def save(self):
        photo = self.validated_data['photo']
        photo.is_verified = False
        photo.save()

        return photo
    

# Retailer Registration Serializer
class RetailerRegistrationSerializer(serializers.Serializer):
    ws_name = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    address = serializers.CharField(required=False)
    provinsi = serializers.CharField(required=False)
    kota = serializers.CharField(required=False)
    kecamatan = serializers.CharField(required=True)
    kelurahan = serializers.CharField(required=False)
    expired_at = serializers.DateTimeField(required=False)
    photos = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=True
    )
    photo_remarks = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=True
    )

    def validate(self, data):
        phone_number = data.get('phone_number')

        # Format phone number
        if phone_number.startswith('0'):
            data['phone_number'] = '62' + phone_number[1:]

        # Check if phone number already exists
        if Retailer.objects.filter(phone_number=data['phone_number']).exists():
            raise serializers.ValidationError("Phone number is already registered.")

        # Validate wholesale existence
        try:
            data['wholesale'] = Wholesale.objects.get(name=data['ws_name'])
        except Wholesale.DoesNotExist:
            raise serializers.ValidationError("Wholesale not found.")

        return data

    def compress_image(self, image):
        img = Image.open(image)
        img_format = img.format
        img_io = BytesIO()
        img.save(img_io, format=img_format, quality=85)
        img_size = img_io.tell()

        while img_size > 500 * 1024:  # 500 KB
            img_io = BytesIO()
            img.save(img_io, format=img_format, quality=85)
            img_size = img_io.tell()
            if img_size <= 500 * 1024:
                break
            img = img.resize((int(img.width * 0.9), int(img.height * 0.9)), Image.LANCZOS)

        img_io.seek(0)
        return InMemoryUploadedFile(
            img_io, None, image.name, 'image/jpeg', img_io.tell(), None
        )

    def create(self, validated_data):
        photos = validated_data.pop('photos')
        photo_remarks = validated_data.pop('photo_remarks', [])
        wholesale = validated_data.pop('wholesale')
        expired_at = validated_data.pop('expired_at', datetime(2025, 7, 3, 23, 59, 59))

        # Save retailer
        retailer_data = {
            "name": validated_data["name"],
            "phone_number": validated_data["phone_number"],
            "address": validated_data["address"],
            "wholesale": wholesale,
            "kecamatan": validated_data["kecamatan"],
            "kelurahan": validated_data["kelurahan"],
            "kota": validated_data["kota"],
            "provinsi": validated_data["provinsi"]
        }
        retailer = Retailer.objects.create(**retailer_data)

        # Save photos with remarks
        for index, photo in enumerate(photos):
            compressed_photo = self.compress_image(photo)
            remarks = photo_remarks[index] if index < len(photo_remarks) else ''
            RetailerPhoto.objects.create(retailer=retailer, image=compressed_photo, remarks=remarks)

        # Generate and save voucher
        voucher_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        Voucher.objects.create(code=voucher_code, retailer=retailer, expired_at=expired_at)

        return {
            "voucher_code": voucher_code,
            "retailer_id": retailer.id
        }
    
class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ['id', 'code', 'retailer', 'redeemed']
        read_only_fields = ['id', 'retailer', 'redeemed', 'created_at']

    def create(self, validated_data):
        return Voucher.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.code = validated_data.get('code', instance.code)
        instance.retailer = validated_data.get('retailer', instance.retailer)
        instance.redeemed = validated_data.get('redeemed', instance.redeemed)
        instance.save()
        return instance
    
class KodeposSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kodepos
        fields = ['kodepos', 'kelurahan', 'kecamatan', 'kota', 'provinsi']


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['sku', 'name', 'price', 'is_active']


class WholesaleTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholesaleTransaction
        fields = ['ryp_qty', 'rys_qty', 'rym_qty', 'total_price', 'image', 'voucher_redeem', 'total_price_after_discount']

class ReimburseSerializer(serializers.ModelSerializer):
    voucher_code = serializers.CharField(source='voucher.code', read_only=True)
    wholesaler_name = serializers.CharField(source='wholesaler.name', read_only=True)
    retailer_name = serializers.CharField(source='retailer.name', read_only=True)

    class Meta:
        model = Reimburse
        fields = ['id', 'voucher_code', 'wholesaler', 'wholesaler_name', 'retailer', 'retailer_name', 'reimbursed_at', 'reimbursed_by', 'status']

    def create(self, validated_data):
        voucher_code = validated_data.pop('voucher_code')
        try:
            voucher = Voucher.objects.get(code=voucher_code)
        except Voucher.DoesNotExist:
            raise serializers.ValidationError("Voucher not found")

        retailer = voucher.retailer  # Assuming Voucher has a foreign key to Retailer
        wholesaler = retailer.wholesale  # Retailer has a foreign key to Wholesale

        validated_data['wholesaler'] = wholesaler
        reimburse = Reimburse.objects.create(
            voucher=voucher,
            retailer=retailer,
            **validated_data
        )
        return reimburse