# Generated by Django 4.2 on 2025-01-21 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retailer', '0009_alter_voucher_expired_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='retailerphoto',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
