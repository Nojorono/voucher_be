# Generated by Django 4.2 on 2025-02-03 14:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wholesales', '0003_wholesale_address_wholesale_pic'),
    ]

    operations = [
        migrations.CreateModel(
            name='WholesaleTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ryp_qty', models.DecimalField(decimal_places=2, help_text='Jumlah RYP', max_digits=10)),
                ('rys_qty', models.DecimalField(decimal_places=2, help_text='Jumlah RYS', max_digits=10)),
                ('rym_qty', models.DecimalField(decimal_places=2, help_text='Jumlah RYM', max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('image', models.ImageField(upload_to='receipt_photos/')),
                ('total_price_after_discount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, max_length=50, null=True)),
                ('voucher_redeem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wholesales.voucherredeem')),
            ],
        ),
    ]
