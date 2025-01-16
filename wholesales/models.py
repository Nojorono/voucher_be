from django.db import models


# Create your models here.
# Model untuk Wholesales (Pengguna yang redeem voucher)
class Wholesale(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Model untuk Rekaman Redeem Voucher oleh Wholesales
class VoucherRedeem(models.Model):
    voucher = models.ForeignKey('retailer.Voucher', on_delete=models.CASCADE)
    wholesaler = models.ForeignKey(Wholesale, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voucher {self.voucher.code} redeemed by {self.wholesaler.name}"