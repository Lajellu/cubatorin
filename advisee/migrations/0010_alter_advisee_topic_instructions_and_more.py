# Generated by Django 5.0.6 on 2024-10-25 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advisee', '0009_remove_advisee_capitalization_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advisee',
            name='topic_instructions',
            field=models.TextField(blank=True, default='{}'),
        ),
        migrations.AlterField(
            model_name='advisee',
            name='topic_texts',
            field=models.TextField(blank=True, default='{}'),
        ),
    ]
