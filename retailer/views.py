from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .models import Retailer, RetailerPhoto, Voucher
from wholesales.models import Wholesale
import random
import string

# Fungsi untuk menghasilkan kode voucher acak
def generate_voucher_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Fungsi untuk memformat nomor telepon
def format_phone_number(phone_number):
    if phone_number.startswith('0'):
        return '62' + phone_number[1:]
    return phone_number

# Halaman untuk pendaftaran dan upload foto
def retailer_register_upload(request):
    if request.method == 'POST':
        ws_name = request.POST.get('ws_name', '').strip()
        name = request.POST.get('name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()

        # Validasi input
        if not ws_name or not name or not phone_number or not address:
            return render(request, 'retailer/error.html', {'error': 'Semua kolom wajib diisi.'})
        if not phone_number.isdigit():
            return render(request, 'retailer/error.html', {'error': 'Nomor telepon harus berupa angka.'})

        # Format nomor telepon
        phone_number = format_phone_number(phone_number)

        # Validasi Wholesale
        try:
            wholesale = Wholesale.objects.get(name=ws_name)
        except Wholesale.DoesNotExist:
            return render(request, 'retailer/error.html', {'error': f'Wholesale dengan nama "{ws_name}" tidak ditemukan.'})

        # Cek jika nomor telepon sudah ada (untuk validasi)
        if Retailer.objects.filter(phone_number=phone_number).exists():
            return render(request, 'retailer/error.html', {'error': f'Nomor telepon {phone_number} sudah terdaftar.'})

        try:
            # Simpan data Retailer
            retailer = Retailer(wholesale=wholesale, name=name, phone_number=phone_number, address=address)
            retailer.save()

            # Simpan foto yang diupload
            photos = request.FILES.getlist('photo')
            if not photos:
                return render(request, 'retailer/error.html', {'error': 'Anda harus mengunggah setidaknya satu foto.'})

            for photo in photos:
                RetailerPhoto.objects.create(retailer=retailer, image=photo)

            # Generate voucher code
            voucher_code = generate_voucher_code()
            voucher = Voucher(code=voucher_code, retailer=retailer)
            voucher.save()

            # Redirect ke halaman sukses dengan kode voucher
            return render(request, 'retailer/submit_success.html', {'voucher_code': voucher_code})

        except ValidationError as e:
            return render(request, 'retailer/error.html', {'error': f'Error validasi: {str(e)}'})
        except Exception as e:
            return render(request, 'retailer/error.html', {'error': f'Error tidak terduga: {str(e)}'})

    return render(request, 'retailer/register_upload.html')
