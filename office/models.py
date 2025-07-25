from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# 1. Custom User model
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    wholesale = models.ForeignKey('wholesales.Wholesale', null=True, blank=True, on_delete=models.CASCADE)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return self.username


class Kodepos(models.Model):
    kodepos = models.CharField(max_length=5)
    kelurahan = models.CharField(max_length=100)
    kecamatan = models.CharField(max_length=100)
    kota = models.CharField(max_length=100)
    provinsi = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.kodepos} - {self.kelurahan}, {self.kecamatan}, {self.kota}"
    

class Item(models.Model):
    sku = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name
    
# Model untuk Reimburse Voucher
class Reimburse(models.Model):
    voucher = models.ForeignKey('retailer.Voucher', on_delete=models.CASCADE)
    retailer = models.ForeignKey('retailer.Retailer', on_delete=models.CASCADE, null=True, blank=True)
    wholesaler = models.ForeignKey('wholesales.Wholesale', on_delete=models.CASCADE)
    reimbursed_at = models.DateTimeField(auto_now_add=True)
    reimbursed_by = models.CharField(max_length=50, null=True, blank=True)
    status = models.ForeignKey('ReimburseStatus', on_delete=models.CASCADE, null=True, blank=True, related_name='reimburses')

    def __str__(self):
        return f"Reimburse {self.voucher.code} by {self.wholesaler.name}"
    
    def get_latest_status(self):
        return self.status.status, self.status.status_at

# Model untuk status pembayaran Reimburse
class ReimburseStatus(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Reimburse'),
        ('completed', 'Reimburse Completed'),
        ('paid', 'Reimburse Paid'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting',
        help_text="Status Pembayaran"
    )
    status_at = models.DateTimeField(null=True, blank=True)
    status_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Status {self.status} at {self.status_at}"
    
    def get_reimburses(self):
        return self.reimburses.all()

class VoucherLimit(models.Model):
    description = models.CharField(max_length=100, null=True, blank=True)
    limit = models.IntegerField(default=0)
    current_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    voucher_project = models.ForeignKey('VoucherProject', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Voucher Limit: {self.limit}, Current Count: {self.current_count}"

class VoucherProject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    periode_start = models.DateTimeField(null=True, blank=True)
    periode_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Status aktif atau tidaknya voucher project")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name
        
class VoucherRetailerDiscount(models.Model):
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    agen_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    voucher_project = models.ForeignKey(VoucherProject, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Discount {self.discount_amount} or {self.discount_percentage}% for {self.voucher_project.name if self.voucher_project else 'No Project'}"