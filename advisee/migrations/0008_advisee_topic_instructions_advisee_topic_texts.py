# Generated by Django 5.0.6 on 2024-08-04 02:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advisee', '0007_seed_advisees'),
    ]

    operations = [
        migrations.AddField(
            model_name='advisee',
            name='topic_instructions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='advisee',
            name='topic_texts',
            field=models.TextField(blank=True, default=''),
        ),
    ]
