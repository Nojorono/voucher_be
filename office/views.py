

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from retailer.models import RetailerPhoto, Retailer
from .twilio import send_whatsapp_voucher  # Impor fungsi kirim WhatsApp




# Fungsi untuk verifikasi foto oleh kantor dan mengirimkan voucher
def verify_photo(request, retailer_id):
    # Get the retailer details
    retailer = get_object_or_404(Retailer, id=retailer_id)

    # Ambil semua foto untuk retailer berdasarkan retailer_id
    photos = RetailerPhoto.objects.all().filter(retailer_id=retailer_id)
    
    # Jika ada foto yang tidak ditemukan
    if not photos.exists():
        return redirect('office:office_verification_report')  # Jika tidak ada foto, redirect ke laporan

    if request.method == 'POST':
        # Tentukan status verifikasi berdasarkan pilihan
        is_verified = request.POST.get('is_verified') == 'True'
        
        # Update status verifikasi untuk setiap foto
        for photo in photos:
            photo.is_verified = is_verified
            photo.save()

        # Setelah verifikasi, redirect ke laporan verifikasi
        if is_verified:
            # Kirim voucher melalui WhatsApp jika disetujui
            # send_whatsapp_voucher(photos[0].retailer.id)  # Kirim voucher untuk retailer pertama
            return redirect('office:office_verification_report')

    context = {
        'retailer': retailer,
        'photos': photos,
    }

    return render(request, 'office/verify_photo.html', context)

# Fungsi untuk menampilkan laporan foto yang belum diverifikasi oleh Office
def office_verification_report(request):
    # Get all retailers
    retailers = Retailer.objects.all()
    
    # Get photos that are not verified and group them by retailer
    photos_to_verify = RetailerPhoto.objects.filter(is_verified=False).values('retailer').annotate(total=Count('id'))
    
    # Create a dictionary to hold the retailer and their unverified photos
    retailer_photos = {}
    for retailer in retailers:
        retailer_photos[retailer] = RetailerPhoto.objects.filter(retailer=retailer, is_verified=False)
    
    context = {
        'retailer_photos': retailer_photos,
        'photos_to_verify': photos_to_verify,
    }
    return render(request, 'office/verification_report.html', context)
