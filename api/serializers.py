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
        if hasattr(self.user, 'wholesale_id') and self.user.wholesale_id:
            wholesale = Wholesale.objects.filter(id=self.user.wholesale_id).first()
            if wholesale:
                wholesale_data = {
                    'name': wholesale.name,
                    'phone_number': wholesale.phone_number
                }
        data.update({
            'message': "Login successful",
            'userid': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'is_staff': self.user.is_staff,
            'wholesale': self.user.wholesale_id,
            **wholesale_data
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
        fields = ['id', 'name', 'phone_number', 'address', 'city', 'pic', 'is_active']

    def validate_phone_number(self, value):
        return '62' + value[1:] if value.startswith('0') else value

    def create(self, validated_data):
        return Wholesale.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.phone_number = self.validate_phone_number(instance.phone_number)
        instance.save()
        return instance

# Voucher Redeem Serializer
class VoucherRedeemSerializer(serializers.ModelSerializer):
    voucher_code = serializers.CharField(write_only=True)
    ws_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = VoucherRedeem
        fields = ['voucher_code', 'ws_id', 'voucher', 'wholesaler', 'redeemed_at']
        read_only_fields = ['voucher', 'wholesaler', 'redeemed_at']

    def validate(self, data):
        voucher_code = data.get('voucher_code')
        ws_id = data.get('ws_id')

        voucher = Voucher.objects.filter(code=voucher_code, redeemed=False).first()
        if not voucher:
            raise serializers.ValidationError("Invalid or already redeemed voucher code.")
        if voucher.expired_at < datetime.now():
            raise serializers.ValidationError("Voucher has expired and cannot be redeemed.")

        wholesaler = Wholesale.objects.filter(id=ws_id).first()
        if not wholesaler:
            raise serializers.ValidationError("Invalid wholesaler ID.")
        if wholesaler.id != voucher.retailer.wholesale_id:
            raise serializers.ValidationError("Wholesaler ID does not match retailer's wholesaler ID.")

        if not RetailerPhoto.objects.filter(retailer=voucher.retailer, is_verified=True).exists():
            raise serializers.ValidationError("Retailer's photos have not been verified yet.")
        if RetailerPhoto.objects.filter(retailer=voucher.retailer, is_approved=False).exists():
            raise serializers.ValidationError("Retailer's photos have been rejected.")

        data['voucher'] = voucher
        data['wholesaler'] = wholesaler
        return data

    def create(self, validated_data):
        voucher = validated_data['voucher']
        wholesaler = validated_data['wholesaler']
        voucher.redeemed = True
        voucher.save()
        return VoucherRedeem.objects.create(
            voucher=voucher,
            wholesaler=wholesaler,
            redeemed_at=datetime.now()
        )

# Retailer Photo Serializer
class RetailerPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailerPhoto
        fields = ['retailer_id', 'id', 'image', 'is_verified', 'is_approved', 'remarks']

# Retailer Serializer
class RetailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ['id', 'name', 'phone_number', 'address', 'wholesale', 'kecamatan', 'kelurahan', 'kota', 'provinsi']

    def validate_phone_number(self, value):
        return '62' + value[1:] if value.startswith('0') else value

    def create(self, validated_data):
        return Retailer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.phone_number = self.validate_phone_number(instance.phone_number)
        instance.save()
        return instance

# Retailer Photo Verification Serializer
class RetailerPhotoVerificationSerializer(serializers.Serializer):
    retailer_id = serializers.IntegerField(required=True)
    photo_id = serializers.IntegerField(required=True)

    def validate(self, data):
        retailer = Retailer.objects.filter(id=data.get('retailer_id')).first()
        if not retailer:
            raise serializers.ValidationError("Retailer not found.")
        photo = RetailerPhoto.objects.filter(id=data.get('photo_id'), retailer=retailer).first()
        if not photo:
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
        retailer = Retailer.objects.filter(id=data.get('retailer_id')).first()
        if not retailer:
            raise serializers.ValidationError("Retailer not found.")
        photo = RetailerPhoto.objects.filter(id=data.get('photo_id'), retailer=retailer).first()
        if not photo:
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
        data['phone_number'] = '62' + phone_number[1:] if phone_number.startswith('0') else phone_number

        existing_retailer = Retailer.objects.filter(phone_number=data['phone_number']).first()
        if existing_retailer:
            voucher_rejected = Voucher.objects.filter(retailer=existing_retailer, is_rejected=True).exists()
            # photo_rejected = RetailerPhoto.objects.filter(retailer=existing_retailer, is_rejected=True).exists()
            if not voucher_rejected:
                raise serializers.ValidationError("Phone number is already registered.")

        wholesale = Wholesale.objects.filter(name=data['ws_name']).first()
        if not wholesale:
            raise serializers.ValidationError("Wholesale not found.")
        data['wholesale'] = wholesale
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
        expired_at = validated_data.pop('expired_at', datetime(2025, 7, 2, 23, 59, 59))

        retailer = Retailer.objects.create(
            name=validated_data["name"],
            phone_number=validated_data["phone_number"],
            address=validated_data.get("address"),
            wholesale=wholesale,
            kecamatan=validated_data["kecamatan"],
            kelurahan=validated_data.get("kelurahan"),
            kota=validated_data.get("kota"),
            provinsi=validated_data.get("provinsi")
        )

        for index, photo in enumerate(photos):
            compressed_photo = self.compress_image(photo)
            remarks = photo_remarks[index] if index < len(photo_remarks) else ''
            RetailerPhoto.objects.create(retailer=retailer, image=compressed_photo, remarks=remarks)

        voucher_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        Voucher.objects.create(code=voucher_code, retailer=retailer, expired_at=expired_at)

        return {
            "voucher_code": voucher_code,
            "retailer_id": retailer.id
        }

# Voucher Serializer
class VoucherSerializer(serializers.ModelSerializer):
    retailer_name = serializers.CharField(source='retailer.name', read_only=True)
    wholesaler_name = serializers.CharField(source='retailer.wholesale.name', read_only=True)
    total_price = serializers.SerializerMethodField()
    total_after_discount = serializers.SerializerMethodField()
    redeemed_at = serializers.DateTimeField(source='voucherredeem_set.first.redeemed_at', read_only=True, default=None)
    reimburse_at = serializers.DateTimeField(source='reimburse_set.first.reimbursed_at', read_only=True, default=None)
    reimburse_status = serializers.CharField(source='reimburse_set.first.status', read_only=True, default=None)
    voucher_code = serializers.CharField(source='code', read_only=True)

    class Meta:
        model = Voucher
        fields = ['id', 'voucher_code', 'wholesaler_name', 'total_price', 'total_after_discount', 'retailer_name', 'redeemed', 'redeemed_at', 'reimburse_at', 'reimburse_status']
        read_only_fields = ['id', 'created_at']

    def get_transaction_field(self, obj, field):
        transaction = WholesaleTransaction.objects.filter(voucher_redeem__voucher=obj).first()
        return getattr(transaction, field, 0) if transaction else 0

    def get_total_price(self, obj):
        return self.get_transaction_field(obj, 'total_price')

    def get_total_after_discount(self, obj):
        return self.get_transaction_field(obj, 'total_price_after_discount')

    def create(self, validated_data):
        return Voucher.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# Kodepos Serializer
class KodeposSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kodepos
        fields = ['kodepos', 'kelurahan', 'kecamatan', 'kota', 'provinsi']

# Item Serializer
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'sku', 'name', 'price', 'is_active']

# Wholesale Transaction Serializer
class WholesaleTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholesaleTransaction
        fields = ['total_price', 'image', 'voucher_redeem', 'total_price_after_discount']

# Reimburse Serializer
class ReimburseSerializer(serializers.ModelSerializer):
    voucher_code = serializers.CharField(source='voucher.code', read_only=True)
    wholesaler_name = serializers.CharField(source='wholesaler.name', read_only=True)
    retailer_name = serializers.CharField(source='retailer.name', read_only=True)

    class Meta:
        model = Reimburse
        fields = ['id', 'voucher_code', 'wholesaler_name', 'retailer_name', 'reimbursed_at', 'reimbursed_by', 'status']

    def create(self, validated_data):
        voucher_code = self.initial_data.get('voucher_code')
        voucher = Voucher.objects.filter(code=voucher_code).first()
        if not voucher:
            raise serializers.ValidationError("Voucher not found")

        retailer = voucher.retailer
        wholesaler = retailer.wholesale

        return Reimburse.objects.create(
            voucher=voucher,
            wholesaler=wholesaler,
            retailer=retailer,
            **validated_data
        )

# Retailer Report Serializer
class RetailerReportSerializer(serializers.ModelSerializer):
    agen_name = serializers.CharField(source='wholesale.name', read_only=True)
    retailer_name = serializers.CharField(source='name', read_only=True)
    voucher_code = serializers.SerializerMethodField()
    retailer_photos = serializers.SerializerMethodField()
    voucher_status = serializers.SerializerMethodField()

    def get_voucher_code(self, obj):
        voucher = Voucher.objects.filter(retailer=obj).first()
        if voucher and voucher.is_approved:
            return voucher.code
        return None

    def get_retailer_photos(self, obj):
        photos = RetailerPhoto.objects.filter(retailer=obj)
        return [{'image': photo.image.url, 'remarks': photo.remarks} for photo in photos]

    def get_voucher_status(self, obj):
        voucher = Voucher.objects.filter(retailer=obj).first()
        if not voucher:
            return "No Voucher"
        if voucher.is_rejected:
            return "REJECTED"
        if voucher.redeemed:
            reimburse = Reimburse.objects.filter(voucher=voucher).first()
            if reimburse:
                return "WAITING PAYMENT" if reimburse.status == 'waiting' else "PAYMENT COMPLETED"
            return "REDEEMED"
        return "RECEIVED" if voucher.is_approved else "PENDING"

    class Meta:
        model = Retailer
        fields = ['agen_name', 'retailer_name', 'phone_number', 'address', 'kelurahan', 'kecamatan', 'kota', 'provinsi',
                  'voucher_code', 'voucher_status', 'retailer_photos']
