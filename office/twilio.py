from twilio.rest import Client
from django.conf import settings
from retailer.models import Retailer, Voucher

def send_whatsapp_voucher(retailer_id):
    # Ambil data retailer
    retailer = Retailer.objects.get(id=retailer_id)
    # Ambil voucher yang belum diredeem untuk retailer
    voucher = Voucher.objects.filter(retailer=retailer, redeemed=False).first()

    if voucher:
        # Setup Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Kirim pesan WhatsApp ke nomor retailer
        message = client.messages.create(
            body=f"Selamat! Voucher Anda dengan kode: {voucher.code} telah disetujui dan siap digunakan.",
            from_=settings.TWILIO_PHONE_NUMBER,  # Nomor WhatsApp Twilio Anda
            to=f"whatsapp:{retailer.phone_number}"  # Nomor WhatsApp retailer
        )

        return message.sid  # Kembalikan SID pesan
    else:
        return None
