# Generated by Django 2.0.5 on 2018-06-01 03:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0004_auto_20180531_1957'),
    ]

    operations = [
        migrations.CreateModel(
            name='SetlistFMStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('finished', models.BooleanField(default=False)),
                ('started', models.DateTimeField(auto_now_add=True)),
                ('published', models.DateTimeField(null=True)),
                ('current_page', models.IntegerField(default=0)),
                ('final_page', models.IntegerField(default=1)),
                ('artist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stats.Artist')),
            ],
        ),
    ]