# Generated by Django 4.2 on 2025-02-24 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('office', '0013_alter_item_sku'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reimburse',
            name='status',
            field=models.CharField(choices=[('waiting', 'Waiting for Payment'), ('completed', 'Reimburse Completed'), ('paid', 'Paid')], default='waiting', help_text='Status Reimburse', max_length=20),
        ),
    ]
