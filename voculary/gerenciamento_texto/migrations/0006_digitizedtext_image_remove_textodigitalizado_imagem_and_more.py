# Generated by Django 4.1.7 on 2023-10-05 13:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gerenciamento_texto', '0005_alter_textodigitalizado_data_geracao'),
    ]

    operations = [
        migrations.CreateModel(
            name='DigitizedText',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Data de Geração')),
                ('text', models.TextField(verbose_name='Texto')),
                ('name', models.CharField(max_length=255, verbose_name='Nome')),
                ('processing_time', models.FloatField(verbose_name='Tempo de Processamento')),
                ('language', models.CharField(max_length=10, verbose_name='Idioma')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Texto Digitalizado',
                'verbose_name_plural': 'Textos Digitalizados',
                'db_table': 'digitized_text',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('image_id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID da Imagem')),
                ('file', models.ImageField(blank=True, null=True, upload_to='images/', verbose_name='Arquivo')),
                ('url', models.URLField(blank=True, null=True, verbose_name='URL')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='image', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Imagem',
                'verbose_name_plural': 'Imagens',
                'db_table': 'image',
            },
        ),
        migrations.RemoveField(
            model_name='textodigitalizado',
            name='imagem',
        ),
        migrations.RemoveField(
            model_name='textodigitalizado',
            name='usuario',
        ),
        migrations.DeleteModel(
            name='Imagem',
        ),
        migrations.DeleteModel(
            name='TextoDigitalizado',
        ),
        migrations.AddField(
            model_name='digitizedtext',
            name='image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='digitized_text', to='gerenciamento_texto.image', verbose_name='Imagem'),
        ),
        migrations.AddField(
            model_name='digitizedtext',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='digitized_text', to=settings.AUTH_USER_MODEL, verbose_name='Usuário'),
        ),
    ]