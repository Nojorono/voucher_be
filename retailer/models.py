from django.db import models


# Create your models here.
class Retailer(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    wholesale = models.ForeignKey('wholesales.Wholesale', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

# Model untuk Voucher
class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE)
    redeemed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code

# Model untuk Foto Retailer (Menambahkan relasi banyak foto)
class RetailerPhoto(models.Model):
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='retailer_photos/')
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Photo of {self.retailer.name}"

