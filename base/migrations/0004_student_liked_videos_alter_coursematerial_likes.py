# Generated by Django 5.1.2 on 2024-10-31 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_coursematerial_description_coursematerial_likes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='liked_videos',
            field=models.ManyToManyField(to='base.coursematerial'),
        ),
        migrations.AlterField(
            model_name='coursematerial',
            name='likes',
            field=models.IntegerField(default=0),
        ),
    ]
