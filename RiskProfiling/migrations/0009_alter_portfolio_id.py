# Generated by Django 4.2.20 on 2025-04-19 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("RiskProfiling", "0008_alter_portfolio_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="portfolio",
            name="id",
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
