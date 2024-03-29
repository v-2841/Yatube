# Generated by Django 2.2.9 on 2023-01-21 09:18

from django.db import migrations, models
import posts.validators


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20230121_0016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(validators=[posts.validators.validate_not_empty]),
        ),
    ]
