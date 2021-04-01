# Generated by Django 3.1.4 on 2021-03-25 15:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Название сообщества', max_length=200, verbose_name='Название сообщества')),
                ('slug', models.SlugField(help_text='Метка', unique=True, verbose_name='Метка')),
                ('description', models.TextField(help_text='Описание сообщества', max_length=200, verbose_name='Описание сообщества')),
            ],
            options={
                'verbose_name': 'Сообщество',
                'verbose_name_plural': 'Сообщества',
            },
        ),
        migrations.AddField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, help_text='Сообщество', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts', to='posts.group', verbose_name='Сообщество'),
        ),
    ]
