# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='HostRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host', models.ForeignKey(to='servicemap.Host')),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200, db_index=True)),
                ('notes', models.TextField(null=True)),
                ('hostroles', models.ManyToManyField(to='servicemap.HostRole')),
                ('prereqs', models.ManyToManyField(to='servicemap.Service')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('login', models.CharField(unique=True, max_length=100, db_index=True)),
            ],
        ),
        migrations.AddField(
            model_name='hostrole',
            name='role',
            field=models.ForeignKey(to='servicemap.Role'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='deployed_by',
            field=models.ForeignKey(to='servicemap.User'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='deployed_from',
            field=models.ForeignKey(to='servicemap.Host'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='service',
            field=models.ForeignKey(to='servicemap.Service'),
        ),
    ]
