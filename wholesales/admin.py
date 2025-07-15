from django.contrib import admin
from .models import Wholesale, VoucherRedeem

class WholesaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'parent', 'city', 'is_active', 'created_at')
    list_filter = ('is_active', 'city', 'parent')
    search_fields = ('name', 'phone_number', 'pic')
    raw_id_fields = ('parent',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'phone_number', 'pic', 'address', 'city')
        }),
        ('Hierarchy', {
            'fields': ('parent',),
            'description': 'Set parent wholesale untuk struktur hierarki'
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')

# Register your models here.
admin.site.register(Wholesale, WholesaleAdmin)
admin.site.register(VoucherRedeem)