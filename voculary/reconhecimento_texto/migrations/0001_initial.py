# Generated by Django 4.1.7 on 2023-07-26 01:19

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Imagem',
            fields=[
                ('id_imagem', models.AutoField(primary_key=True, serialize=False)),
                ('imagem', models.ImageField(blank=True, upload_to='imagens')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ArquivoDigitalizado',
            fields=[
                ('id_arquivo', models.AutoField(primary_key=True, serialize=False)),
                ('data_geracao', models.DateTimeField(default=datetime.datetime.now)),
                ('tempo_processamento', models.FloatField()),
                ('acuracia', models.DecimalField(decimal_places=2, max_digits=6)),
                ('nome_arquivo', models.CharField(max_length=150)),
                ('imagem', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='image', to='reconhecimento_texto.imagem')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
