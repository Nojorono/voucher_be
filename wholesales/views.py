from django.shortcuts import render
from retailer.models import Voucher
from .models import VoucherRedeem, Wholesale

# Halaman redeem voucher oleh wholesales
def redeem_voucher(request):
    if request.method == 'POST':
        voucher_code = request.POST.get('voucher_code')
        ws_name = request.POST.get('ws_name')
        try:
            voucher = Voucher.objects.get(code=voucher_code, redeemed=False)
            wholesaler = Wholesale.objects.get(name=ws_name)  # Asumsi user sudah login sebagai wholesaler
            voucher.redeemed = True
            voucher.save()

            # Simpan redeem data
            redeem = VoucherRedeem(voucher=voucher, wholesaler=wholesaler)
            redeem.save()
            return render(request, 'wholesales/redeem_success.html')

        except Voucher.DoesNotExist:
            return render(request, 'wholesales/redeem_failed.html')

    return render(request, 'wholesales/redeem_voucher.html')

# Laporan redeem voucher oleh wholesales
def redeem_report(request,name):
    wholesaler = Wholesale.objects.get(name=name)
    redeemed_vouchers = VoucherRedeem.objects.filter(wholesaler=wholesaler)
    return render(request, 'wholesales/redeem_report.html', {'redeemed_vouchers': redeemed_vouchers})
