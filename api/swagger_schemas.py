"""
OpenAPI/Swagger schema definitions untuk dokumentasi API yang komprehensif.
Digunakan oleh @swagger_auto_schema di views.py agar parameter dan response jelas di Swagger UI.
"""
from drf_yasg import openapi

# --- Authentication ---
login_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['username', 'password'],
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, example='admin', description='Username untuk login'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, example='password123!!', description='Password untuk login'),
    },
    description='Kredensial login'
)

register_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['username', 'password', 'email', 'wholesale'],
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, example='user1', description='Username unik'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, example='Password123!!', description='Password (min 8 karakter)'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example='user@example.com'),
        'wholesale': openapi.Schema(type=openapi.TYPE_INTEGER, example=1, description='ID Wholesale'),
        'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
    }
)

change_password_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['current_password', 'new_password'],
    properties={
        'current_password': openapi.Schema(type=openapi.TYPE_STRING, description='Password saat ini'),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Password baru (ikuti kebijakan password)'),
    }
)

reset_password_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example='user@example.com', description='Email terdaftar'),
    }
)

logout_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['refresh'],
    properties={
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token JWT (dari response login)'),
    }
)

# --- Retailer Registration ---
retailer_register_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['ws_name', 'name', 'phone_number', 'kecamatan', 'photos', 'photo_remarks'],
    properties={
        'ws_name': openapi.Schema(type=openapi.TYPE_STRING, example='PT Wholesale ABC', description='Nama wholesale'),
        'name': openapi.Schema(type=openapi.TYPE_STRING, example='Toko Retailer 1', description='Nama retailer'),
        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, example='081234567890', description='No HP (08xxx atau 628xxx)'),
        'address': openapi.Schema(type=openapi.TYPE_STRING, example='Jl. Contoh No. 1'),
        'provinsi': openapi.Schema(type=openapi.TYPE_STRING, example='DKI Jakarta'),
        'kota': openapi.Schema(type=openapi.TYPE_STRING, example='Jakarta Selatan'),
        'kecamatan': openapi.Schema(type=openapi.TYPE_STRING, example='Kebayoran Baru', description='Wajib'),
        'kelurahan': openapi.Schema(type=openapi.TYPE_STRING, example='Gunung'),
        'expired_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'project_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'photos': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_FILE), description='File gambar (min 1)'),
        'photo_remarks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='Keterangan per foto, urutan sesuai photos'),
    }
)

# --- Voucher Redeem ---
redeem_voucher_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['voucher_code', 'ws_id'],
    properties={
        'voucher_code': openapi.Schema(type=openapi.TYPE_STRING, example='VCR-XXXX-XXXX', description='Kode voucher dari retailer'),
        'ws_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1, description='ID Wholesale yang menebus'),
    }
)

# --- Submit Transaction Voucher ---
submit_trx_voucher_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['voucher_code', 'ws_id', 'total_price', 'total_price_after_discount', 'image', 'items'],
    properties={
        'voucher_code': openapi.Schema(type=openapi.TYPE_STRING),
        'ws_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'total_price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total harga sebelum diskon'),
        'total_price_after_discount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total setelah diskon'),
        'image': openapi.Schema(type=openapi.TYPE_FILE, description='Bukti transaksi (gambar)'),
        'items': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['item_id', 'qty', 'sub_total'],
                properties={
                    'item_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'qty': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'sub_total': openapi.Schema(type=openapi.TYPE_NUMBER),
                }
            )
        ),
    }
)

# --- Reimburse ---
submit_reimburse_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['voucher_codes'],
    properties={
        'voucher_codes': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING),
            example=['VCR-001', 'VCR-002'],
            description='Daftar kode voucher yang akan direimburse'
        ),
    }
)

# --- Query parameters (manual_parameters) ---
def param_query(name, type_, description, required=False):
    return openapi.Parameter(name, openapi.IN_QUERY, description=description, type=type_, required=required)

def param_path(name, type_, description):
    return openapi.Parameter(name, openapi.IN_PATH, description=description, type=type_, required=True)

# Redeem report
redeem_report_params = [
    param_query('ws_id', openapi.TYPE_INTEGER, 'Filter by wholesaler ID', required=False),
]

# List retailers
list_retailers_params = [
    param_query('ws_id', openapi.TYPE_INTEGER, 'Filter by wholesale ID'),
    param_query('voucher_code', openapi.TYPE_STRING, 'Filter by kode voucher'),
    param_query('retailer_name', openapi.TYPE_STRING, 'Filter by nama retailer'),
    param_query('voucher_status', openapi.TYPE_STRING, 'PENDING | REJECTED | RECEIVED | REDEEMED | WAITING REIMBURSE | REIMBURSE COMPLETED | REIMBURSE PAID'),
]

# List photos
list_photos_params = [
    param_query('is_verified', openapi.TYPE_BOOLEAN, 'Filter foto sudah/belum diverifikasi'),
    param_query('is_approved', openapi.TYPE_BOOLEAN, 'Filter foto disetujui/ditolak'),
    param_query('is_rejected', openapi.TYPE_BOOLEAN, 'Filter foto ditolak'),
    param_query('ws_id', openapi.TYPE_INTEGER, 'Filter by wholesale ID'),
]

# List vouchers
list_vouchers_params = [
    param_query('retailer_id', openapi.TYPE_INTEGER, 'Filter by retailer ID'),
    param_query('ws_id', openapi.TYPE_INTEGER, 'Filter by wholesale ID'),
    param_query('voucher_code', openapi.TYPE_STRING, 'Filter by kode voucher'),
    param_query('redeemed', openapi.TYPE_BOOLEAN, 'Filter sudah/belum ditebus'),
]

# Location (kodepos, kelurahan, dll)
kelurahan_params = [param_query('kecamatan', openapi.TYPE_STRING, 'Nama kecamatan (untuk filter kelurahan)')]
kecamatan_params = [param_query('kota', openapi.TYPE_STRING, 'Nama kota (untuk filter kecamatan)')]
kota_params = [param_query('provinsi', openapi.TYPE_STRING, 'Nama provinsi (untuk filter kota)')]
kodepos_detail_params = [
    param_query('kelurahan', openapi.TYPE_STRING, 'Nama kelurahan'),
    param_query('kecamatan', openapi.TYPE_STRING, 'Nama kecamatan'),
    param_query('kota', openapi.TYPE_STRING, 'Nama kota'),
    param_query('provinsi', openapi.TYPE_STRING, 'Nama provinsi'),
]

# List reimburse
list_reimburse_params = [
    param_query('status', openapi.TYPE_STRING, 'waiting | completed | paid'),
    param_query('id', openapi.TYPE_INTEGER, 'ID reimburse'),
    param_query('voucher_code', openapi.TYPE_STRING, 'Kode voucher'),
]

# Current count
get_current_count_params = [
    param_query('id', openapi.TYPE_INTEGER, 'ID voucher limit'),
    param_query('project_id', openapi.TYPE_INTEGER, 'ID project voucher'),
]

# Admin update user body
admin_update_user_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING),
        'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
        'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    }
)

# VoucherLimit increment
voucher_limit_increment_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['increment'],
    properties={
        'increment': openapi.Schema(type=openapi.TYPE_INTEGER, example=1, description='Jumlah yang ditambah'),
    }
)
