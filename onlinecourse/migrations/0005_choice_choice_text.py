# Generated by Django 4.2.5 on 2023-09-17 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinecourse', '0004_alter_choice_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='choice',
            name='choice_text',
            field=models.CharField(default='Default Choice Text', max_length=200),
        ),
    ]
