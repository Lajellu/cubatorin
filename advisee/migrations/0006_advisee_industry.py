# Generated by Django 5.0.6 on 2024-07-17 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advisee', '0005_add_topic_data_to_seeded_advisees'),
    ]

    operations = [
        migrations.AddField(
            model_name='advisee',
            name='industry',
            field=models.TextField(blank=True, default=''),
        ),
    ]