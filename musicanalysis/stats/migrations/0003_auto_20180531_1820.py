# Generated by Django 2.0.5 on 2018-05-31 22:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0002_auto_20180531_1753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concert',
            name='artist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stats.Artist'),
        ),
        migrations.AlterField(
            model_name='concert',
            name='venue',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stats.Venue'),
        ),
        migrations.AlterField(
            model_name='song',
            name='orig_artist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stats.Artist'),
        ),
    ]
