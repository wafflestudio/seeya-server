# Generated by Django 5.0.2 on 2024-02-15 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0002_alter_userlikespost_unique_together_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image_link',
        ),
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='post_images'),
        ),
    ]
