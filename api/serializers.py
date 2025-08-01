from rest_framework import serializers
from office.models import User, Kodepos, Item, Reimburse, ReimburseStatus, VoucherLimit, VoucherProject, VoucherRetailerDiscount
from wholesales.models import Wholesale, VoucherRedeem, WholesaleTransaction, WholesaleTransactionDetail
from retailer.models import Voucher, Retailer, RetailerPhoto
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import random, string, threading, logging
from datetime import datetime, time
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import os
import pytz

# Konfigurasi logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Simpan log ke file `retailer_registration.log`
file_handler = logging.FileHandler('retailer_registration.log')
file_handler.setLevel(logging.DEBUG)

# Format log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Tambahkan handler ke logger
logger.addHandler(file_handler)

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
                    'phone_number': wholesale.phone_number,
                    'project': wholesale.project_id if wholesale.project else None
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
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    is_root = serializers.SerializerMethodField()
    is_leaf = serializers.SerializerMethodField()
    
    class Meta:
        model = Wholesale
        fields = [
            'id', 'name', 'phone_number', 'address', 'city', 'pic', 'is_active',
            'created_at', 'updated_at', 'parent', 'parent_name', 'project', 'project_name',
            'children_count', 'level', 'is_root', 'is_leaf'
        ]
        ref_name = 'APIWholesale'

    def get_children_count(self, obj):
        """Get count of direct children that are active"""
        return obj.get_children(active_only=True).count()
        
    def get_level(self, obj):
        """Get hierarchy level"""
        return obj.get_level()
        
    def get_is_root(self, obj):
        """Check if is root"""
        return obj.is_root()
        
    def get_is_leaf(self, obj):
        """Check if is leaf (has no active children)"""
        return obj.is_leaf(active_only=True)

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
        ref_name = 'APIVoucherRedeem'

    def validate(self, data):
        voucher_code = data.get('voucher_code')
        ws_id = data.get('ws_id')

        voucher = Voucher.objects.filter(code=voucher_code, redeemed=False).first()
        if not voucher:
            raise serializers.ValidationError("Invalid or already redeemed voucher code.")
        if voucher.expired_at < timezone.now():
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
            redeemed_at=timezone.now()
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
    project_id = serializers.IntegerField(required=False)
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
        logger.info(f"Validating retailer data: {data}")

        phone_number = data.get('phone_number')
        data['phone_number'] = '62' + phone_number[1:] if phone_number.startswith('0') else phone_number

        existing_retailer = Retailer.objects.filter(phone_number=data['phone_number']).first()
        if existing_retailer:
            voucher_rejected = Voucher.objects.filter(retailer=existing_retailer, is_rejected=True).exists()
            # photo_rejected = RetailerPhoto.objects.filter(retailer=existing_retailer, is_rejected=True).exists()
            if not voucher_rejected:
                logger.warning(f"Phone number {data['phone_number']} is already registered.")
                raise serializers.ValidationError("Phone number is already registered.")

        wholesale = Wholesale.objects.filter(name=data['ws_name']).first()
        if not wholesale:
            logger.error(f"Wholesale '{data['ws_name']}' not found.")
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
        logger.info("Starting retailer registration process...")

        photos = validated_data.pop('photos', [])
        photo_remarks = validated_data.pop('photo_remarks', [])
        wholesale = validated_data.pop('wholesale')
        # Ambil expired_at dari validated_data, jika tidak ada gunakan periode_end dari VoucherProject
        project_id = validated_data.get('project_id')
        voucher_project = VoucherProject.objects.filter(id=project_id).first()
        expired_at = voucher_project.periode_end if voucher_project and voucher_project.periode_end else None
        
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

        logger.info(f"Retailer {retailer.name} created successfully.")

        for index, photo in enumerate(photos):
            compressed_photo = self.compress_image(photo)
            remarks = photo_remarks[index] if index < len(photo_remarks) else ''
            RetailerPhoto.objects.create(retailer=retailer, image=photo, remarks=remarks)

        logger.info(f"Uploaded {len(photos)} photos for retailer {retailer.name}")

        voucher_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        Voucher.objects.create(code=voucher_code, retailer=retailer, expired_at=expired_at, project_id=project_id)

        logger.info(f"Voucher {voucher_code} generated for retailer {retailer.name}")

        # Send email asynchronously using threading
        self.send_email_async(retailer, wholesale)

        return {
            "voucher_code": voucher_code,
            "retailer_id": retailer.id
        }

    def send_email_async(self, retailer, wholesale):
        """Mengirim email secara asynchronous menggunakan threading"""

        def email_task():
            subject = 'Verifikasi Retailer'
            
            # ✅ Fix: Use request host instead of sites framework
            request = self.context.get('request')
            frontend_url = os.getenv('FRONTEND_URL','')

            verification_url = f"{frontend_url}/verification"

            html_content = f"""
                <html>
                <body>
                    <p>Dear Admin,</p>
                    <p>Berkaitan dengan program Super Perdana, Retailer telah melakukan pendaftaran dengan detail berikut:</p>
                    <table>
                        <tr><td><strong>Nama Retailer</strong></td><td>: {retailer.name}</td></tr>
                        <tr><td><strong>No WhatsApp</strong></td><td>: {retailer.phone_number}</td></tr>
                        <tr><td><strong>Nama Agen</strong></td><td>: {wholesale.name}</td></tr>
                        <tr><td><strong>Tanggal Pengisian</strong></td><td>: {timezone.now().strftime('%Y-%m-%d')}</td></tr>
                        <tr><td><strong>Status</strong></td><td>: Menunggu Verifikasi</td></tr>
                    </table>
                    <p>Mohon segera melakukan verifikasi data mereka dengan klik tombol di bawah ini:</p>
                    <p><a href="{verification_url}">Verifikasi Sekarang</a></p>
                </body>
                </html>
            """

            email_from = settings.DEFAULT_FROM_EMAIL
            to_emails = os.getenv('RETAILER_REGISTRATION_TO_EMAILS', 'banyu.senjana@limamail.net').split(',')
            cc_emails = [email.strip() for email in os.getenv('RETAILER_REGISTRATION_CC_EMAILS', 'dimas.rosadi@limamail.net').split(',') if email.strip()]

            logger.info(f"Email from: {email_from}")
            logger.info(f"To emails: {to_emails}")
            logger.info(f"CC emails: {cc_emails}")

            try:
                email = EmailMessage(
                    subject=subject,
                    body=html_content,
                    from_email=email_from,
                    to=to_emails,
                    cc=cc_emails,
                )
                email.content_subtype = 'html'  # Agar email dikirim dalam format HTML
                email.send(fail_silently=False)
                logger.info(f"Email sent successfully to {to_emails} with CC to {cc_emails}")
                logger.info("Email sent successfully!")
                logger.info(f"Email sent to {to_emails} with CC to {cc_emails}")
            except Exception as e:
                logger.exception("Error sending email")
                logger.exception("Email sending exception details:")

            logger.info("=== EMAIL SENDING END ===")

        # Jalankan fungsi `email_task` dalam thread terpisah
        try:
            email_thread = threading.Thread(target=email_task)
            email_thread.start()
            logger.info("Email thread started successfully")
        except Exception as e:
            logger.error(f"Error starting email thread: {str(e)}")    

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
        fields = ['id','total_price', 'image', 'total_price_after_discount']
        read_only_fields = ['id', 'created_at']

# Reimburse Serializer
class ReimburseSerializer(serializers.ModelSerializer):
    voucher_code = serializers.CharField(source='voucher.code', read_only=True)
    wholesaler_name = serializers.CharField(source='wholesaler.name', read_only=True)
    retailer_name = serializers.CharField(source='retailer.name', read_only=True)
    status = serializers.CharField(source='status.status', read_only=True)
    status_at = serializers.DateTimeField(source='status.status_at', read_only=True)
    project = serializers.CharField(source='voucher.project', read_only=True)
    project_name = serializers.CharField(source='voucher.project.name', read_only=True)
    discount_amount = serializers.SerializerMethodField()
    agen_fee = serializers.SerializerMethodField()

    def get_discount_amount(self, obj):
        # Get discount from VoucherRetailerDiscount (office_voucherretaildiscount)
        if obj.voucher and obj.voucher.project_id:
            discount = VoucherRetailerDiscount.objects.filter(voucher_project_id=obj.voucher.project_id).first()
            if discount:
                return float(discount.discount_amount)
        return 0
    
    def get_agen_fee(self, obj):
        # Get agen fee from VoucherRetailerDiscount (office_voucherretaildiscount)
        if obj.voucher and obj.voucher.project_id:
            discount = VoucherRetailerDiscount.objects.filter(voucher_project_id=obj.voucher.project_id).first()
            if discount:
                return float(discount.agen_fee)
        return 0

    class Meta:
        model = Reimburse
        fields = ['id', 'voucher_code', 'wholesaler_name', 'retailer_name', 'reimbursed_at', 'reimbursed_by', 'status', 'status_at', 'project', 'project_name', 'discount_amount', 'agen_fee']

    def create(self, validated_data):
        voucher_code = self.initial_data.get('voucher_code')
        voucher = Voucher.objects.filter(code=voucher_code).first()
        if not voucher:
            raise serializers.ValidationError("Voucher not found")

        retailer = voucher.retailer
        wholesaler = retailer.wholesale

        # Create ReimburseStatus with default values
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required.")
        
        status = ReimburseStatus.objects.create(
            status='waiting',
            status_at=timezone.now(),
            status_by=request.user.username
        )

        # Remove reimbursed_by from validated_data to avoid duplication
        validated_data.pop('reimbursed_by', None)

        return Reimburse.objects.create(
            voucher=voucher,
            wholesaler=wholesaler,
            retailer=retailer,
            status=status,  # Set status
            reimbursed_by=request.user.username,
            **validated_data 
        )
    
# Retailer Report Serializer
class RetailerReportSerializer(serializers.ModelSerializer):
    agen_name = serializers.CharField(source='wholesale.name', read_only=True)
    retailer_name = serializers.CharField(source='name', read_only=True)
    voucher_code = serializers.SerializerMethodField()
    retailer_photos = serializers.SerializerMethodField()
    voucher_status = serializers.SerializerMethodField()
    voucher_status_at = serializers.SerializerMethodField()

    def get_voucher_code(self, obj):
        voucher = Voucher.objects.filter(retailer=obj).first()
        if voucher and voucher.is_approved:
            return voucher.code
        return None

    def get_retailer_photos(self, obj):
        photos = RetailerPhoto.objects.filter(retailer=obj)
        return [{'image': photo.image.url if photo.image else None, 'remarks': photo.remarks} for photo in photos]

    def get_voucher_status(self, obj):
        voucher = Voucher.objects.filter(retailer=obj).first()
        if not voucher:
            return "No Voucher"
        if voucher.is_rejected:
            return "REJECTED"
        if voucher.redeemed:
            reimburse = Reimburse.objects.filter(voucher=voucher).first()
            if reimburse and reimburse.status:
                if reimburse.status.status == 'waiting':
                    return "WAITING REIMBURSE"
                elif reimburse.status.status == 'completed':
                    return "REIMBURSE COMPLETED"
                elif reimburse.status.status == 'paid':
                    return "REIMBURSE PAID"
            return "REDEEMED"
        return "RECEIVED" if voucher.is_approved else "PENDING"

    def get_voucher_status_at(self, obj):
        voucher = Voucher.objects.filter(retailer=obj).first()
        if not voucher:
            return None
        if voucher.is_rejected:
            return voucher.rejected_at
        if voucher.redeemed:
            redeem = VoucherRedeem.objects.filter(voucher=voucher).first()
            if redeem:
                reimburse = Reimburse.objects.filter(voucher=voucher).first()
                if reimburse and reimburse.status:
                    return reimburse.status.status_at
                return redeem.redeemed_at
        if voucher.is_approved:
            return voucher.approved_at
        return voucher.created_at

    class Meta:
        model = Retailer
        fields = ['agen_name', 'retailer_name', 'phone_number', 'address', 'kelurahan', 'kecamatan', 'kota', 'provinsi',
                  'voucher_code', 'voucher_status', 'voucher_status_at', 'retailer_photos']


class WholesaleTransactionDetailSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    
    class Meta:
        model = WholesaleTransactionDetail
        fields = ['item_name', 'qty', 'sub_total']


class VoucherLimitSerializer(serializers.ModelSerializer):
    voucher_project_name = serializers.CharField(source='voucher_project.name', read_only=True)
    remaining = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()
    
    class Meta:
        model = VoucherLimit
        fields = ['id', 'description', 'limit', 'current_count', 'remaining', 'percentage_used', 
                 'voucher_project', 'voucher_project_name', 'created_at']
    
    def get_remaining(self, obj):
        return obj.limit - obj.current_count
    
    def get_percentage_used(self, obj):
        if obj.limit > 0:
            return round((obj.current_count / obj.limit) * 100, 2)
        return 0


class VoucherProjectSerializer(serializers.ModelSerializer):
    voucher_limits = VoucherLimitSerializer(many=True, read_only=True, source='voucherlimit_set')
    total_allocated = serializers.SerializerMethodField()
    total_used = serializers.SerializerMethodField()
    
    class Meta:
        model = VoucherProject
        fields = ['id', 'name', 'description', 'periode_start', 'periode_end', 'is_active',
                 'created_at', 'created_by', 'updated_at', 'updated_by', 'voucher_limits',
                 'total_allocated', 'total_used']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_allocated(self, obj):
        return sum(limit.limit for limit in obj.voucherlimit_set.all())
    
    def get_total_used(self, obj):
        return sum(limit.current_count for limit in obj.voucherlimit_set.all())
    
    def validate_periode_end(self, value):
        """Normalize periode_end to end of day (23:59:59) in Asia/Jakarta"""
        if value:
            # Get date part only
            if hasattr(value, 'date'):
                date_part = value.date()
            else:
                # If value is string, parse it
                if isinstance(value, str):
                    date_part = datetime.strptime(value, '%Y-%m-%d').date()
                else:
                    date_part = value
            
            # Create end of day in Jakarta timezone
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            end_of_day = datetime.combine(date_part, time(23, 59, 59, 999999))
            
            # Localize to Jakarta timezone
            jakarta_end = jakarta_tz.localize(end_of_day)
            
            return jakarta_end
        return value

    def validate_periode_start(self, value):
        """Normalize periode_start to start of day (00:00:00) in Asia/Jakarta"""
        if value:
            # Get date part only
            if hasattr(value, 'date'):
                date_part = value.date()
            else:
                # If value is string, parse it
                if isinstance(value, str):
                    date_part = datetime.strptime(value, '%Y-%m-%d').date()
                else:
                    date_part = value
            
            # Create start of day in Jakarta timezone
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            start_of_day = datetime.combine(date_part, time(0, 0, 0, 0))
            
            # Localize to Jakarta timezone
            jakarta_start = jakarta_tz.localize(start_of_day)
            
            return jakarta_start
        return value
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.username if self.context.get('request') else None
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Check if periode_end is being updated
        periode_end = validated_data.get('periode_end', None)
        if periode_end and periode_end != instance.periode_end:
            # Normalize to end of day before updating vouchers
            normalized_end = periode_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Update expired_at for all related vouchers
            Voucher.objects.filter(project=instance, redeemed=False).update(expired_at=normalized_end)
            
            # Update the validated_data with normalized end date
            validated_data['periode_end'] = normalized_end
            
        validated_data['updated_by'] = self.context['request'].user.username if self.context.get('request') else None
        validated_data['updated_at'] = timezone.now()
        return super().update(instance, validated_data)


class VoucherRetailerDiscountSerializer(serializers.ModelSerializer):
    voucher_project_name = serializers.CharField(source='voucher_project.name', read_only=True)
    total_discount = serializers.SerializerMethodField()
    
    class Meta:
        model = VoucherRetailerDiscount
        fields = ['id', 'discount_amount', 'discount_percentage', 'agen_fee', 'total_discount',
                 'voucher_project', 'voucher_project_name', 'created_at', 'created_by',
                 'updated_at', 'updated_by']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_discount(self, obj):
        """Calculate total discount (amount + percentage equivalent)"""
        return {
            'discount_amount': float(obj.discount_amount),
            'discount_percentage': float(obj.discount_percentage),
            'agen_fee': float(obj.agen_fee) if obj.agen_fee else 0,
        }
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.username if self.context.get('request') else None
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user.username if self.context.get('request') else None
        validated_data['updated_at'] = timezone.now()
        return super().update(instance, validated_data)


# Serializer untuk summary/dashboard
class VoucherProjectSummarySerializer(serializers.Serializer):
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    inactive_projects = serializers.IntegerField()
    total_allocated_vouchers = serializers.IntegerField()
    total_used_vouchers = serializers.IntegerField()
    total_remaining_vouchers = serializers.IntegerField()
    usage_percentage = serializers.FloatField()
    
    
class VoucherLimitUpdateSerializer(serializers.Serializer):
    increment = serializers.IntegerField(default=1, min_value=1)
    
    def validate_increment(self, value):
        if value < 1:
            raise serializers.ValidationError("Increment must be at least 1")
        return value