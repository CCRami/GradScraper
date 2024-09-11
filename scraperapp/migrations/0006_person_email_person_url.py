# Generated by Django 5.0.6 on 2024-08-09 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraperapp', '0005_company_alter_person_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='email',
            field=models.EmailField(blank=True, default='SMTP E515 : Email Not Found', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='url',
            field=models.URLField(default='invalid url', max_length=2048),
        ),
    ]
