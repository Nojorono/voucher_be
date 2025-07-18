from datetime import datetime
from django.db import models


# Create your models here.
class Retailer(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    kelurahan = models.CharField(max_length=100, null=True, blank=True)
    kecamatan = models.CharField(max_length=100, null=True, blank=True)
    kota = models.CharField(max_length=100, null=True, blank=True)
    provinsi = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    wholesale = models.ForeignKey('wholesales.Wholesale', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

# Model untuk Voucher
class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    is_rejected = models.BooleanField(default=False)
    rejected_at = models.DateTimeField(null=True, blank=True)
    redeemed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.code

# Model untuk Foto Retailer (Menambahkan relasi banyak foto)
class RetailerPhoto(models.Model):
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='retailer_photos/')
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    remarks = models.CharField(max_length=50, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Photo of {self.retailer.name} - {self.remarks}"

    # ✅ Add method untuk get public URL
    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return None
    
    # ✅ Debug method
    def get_full_url(self):
        if self.image:
            return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.ap-southeast-3.amazonaws.com/{self.image.name}"
        return None