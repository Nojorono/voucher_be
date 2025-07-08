from django.db import models


# Create your models here.
# Model untuk Wholesales (Pengguna yang redeem voucher)
class Wholesale(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255, null=True, blank=True)
    pic = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Status aktif atau tidaknya wholesales")
    city = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

# Model untuk Rekaman Redeem Voucher oleh Wholesales
class VoucherRedeem(models.Model):
    voucher = models.ForeignKey('retailer.Voucher', on_delete=models.CASCADE)
    wholesaler = models.ForeignKey(Wholesale, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voucher {self.voucher.code} redeemed by {self.wholesaler.name}"
    
# Model untuk Transaksi Wholesale
class WholesaleTransaction(models.Model):
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='receipt_photos/')
    voucher_redeem = models.ForeignKey(VoucherRedeem, on_delete=models.CASCADE)
    total_price_after_discount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Transaction by {self.voucher_redeem.voucher.code}"
    
# Model untuk detail Transaksi Wholesale
class WholesaleTransactionDetail(models.Model):
    transaction = models.ForeignKey(WholesaleTransaction, on_delete=models.CASCADE)
    item = models.ForeignKey('office.Item', on_delete=models.CASCADE, related_name='wholesale_transaction_details')
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Transaction {self.transaction.id} - {self.item.name}"