from django.db import models
from django.utils import timezone


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
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # Parent-child relationship
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        help_text="Parent wholesale untuk struktur hierarki"
    )

    def __str__(self):
        return self.name
    
    def get_children(self):
        """Get all direct children of this wholesale"""
        return self.children.all()
    
    def get_all_descendants(self):
        """Get all descendants (children, grandchildren, etc.) of this wholesale"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_ancestors(self):
        """Get all ancestors (parent, grandparent, etc.) of this wholesale"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_level(self):
        """Get the level/depth of this wholesale in the hierarchy (0 for root)"""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level
    
    def is_root(self):
        """Check if this wholesale is a root (has no parent)"""
        return self.parent is None
    
    def is_leaf(self):
        """Check if this wholesale is a leaf (has no children)"""
        return not self.children.exists()

    class Meta:
        verbose_name = "Wholesale"
        verbose_name_plural = "Wholesales"

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