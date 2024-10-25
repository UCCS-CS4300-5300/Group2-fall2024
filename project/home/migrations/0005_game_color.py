# Generated by Django 4.2.11 on 2024-10-24 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_event_game'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='color',
            field=models.CharField(choices=[('#FF5733', 'Red'), ('#FFA500', 'Orange'), ('#FFFF33', 'Yellow'), ('#33FF57', 'Green'), ('#3357FF', 'Blue'), ('#FF33FF', 'Pink'), ('#800080', 'Purple')], default='#FFFFFF', max_length=7),
        ),
    ]