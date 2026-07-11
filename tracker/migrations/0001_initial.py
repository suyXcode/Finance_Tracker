"""
tracker/migrations/0001_initial.py

Initial migration: creates Category, Transaction, and Budget tables.
Generated to match models.py exactly.
"""

import datetime
import decimal
import django.core.validators
import django.db.models.deletion
import django.db.models.expressions
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── Category ─────────────────────────────────────────
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',         models.CharField(max_length=100)),
                ('icon',         models.CharField(
                                    choices=[
                                        ('bi-cart',        'Shopping Cart'),
                                        ('bi-house',       'House / Rent'),
                                        ('bi-car-front',   'Transport'),
                                        ('bi-heart-pulse', 'Health'),
                                        ('bi-mortarboard', 'Education'),
                                        ('bi-controller',  'Entertainment'),
                                        ('bi-lightning',   'Utilities'),
                                        ('bi-briefcase',   'Work / Salary'),
                                        ('bi-piggy-bank',  'Savings'),
                                        ('bi-gift',        'Gifts'),
                                        ('bi-airplane',    'Travel'),
                                        ('bi-three-dots',  'Other'),
                                    ],
                                    default='bi-three-dots',
                                    max_length=50
                                )),
                ('color',        models.CharField(
                                    choices=[
                                        ('#4361ee', 'Blue'),
                                        ('#f72585', 'Pink'),
                                        ('#4cc9f0', 'Cyan'),
                                        ('#7209b7', 'Purple'),
                                        ('#f77f00', 'Orange'),
                                        ('#2dc653', 'Green'),
                                        ('#e63946', 'Red'),
                                        ('#adb5bd', 'Gray'),
                                        ('#ffd60a', 'Yellow'),
                                        ('#06d6a0', 'Teal'),
                                    ],
                                    default='#4361ee',
                                    max_length=7
                                )),
                ('is_predefined', models.BooleanField(default=False, help_text='Predefined categories are available to all users')),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('user',         models.ForeignKey(
                                    blank=True,
                                    null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    related_name='categories',
                                    to=settings.AUTH_USER_MODEL,
                                    help_text='Null for predefined/global categories'
                                )),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),

        # ── Transaction ───────────────────────────────────────
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount',      models.DecimalField(
                                    decimal_places=2,
                                    max_digits=12,
                                    validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))],
                                    help_text='Must be greater than zero'
                                )),
                ('type',        models.CharField(
                                    choices=[('income', 'Income'), ('expense', 'Expense')],
                                    db_index=True,
                                    max_length=10
                                )),
                ('date',        models.DateField(default=datetime.date.today, db_index=True)),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('category',    models.ForeignKey(
                                    blank=True,
                                    null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='transactions',
                                    to='tracker.category'
                                )),
                ('user',        models.ForeignKey(
                                    on_delete=django.db.models.deletion.CASCADE,
                                    related_name='transactions',
                                    to=settings.AUTH_USER_MODEL
                                )),
            ],
            options={
                'ordering': ['-date', '-created_at'],
            },
        ),

        # ── Budget ────────────────────────────────────────────
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id',            models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount',        models.DecimalField(
                                      decimal_places=2,
                                      max_digits=12,
                                      validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))],
                                      help_text='Monthly budget limit (must be > 0)'
                                  )),
                ('month',         models.PositiveSmallIntegerField(help_text='Month number 1–12')),
                ('year',          models.PositiveSmallIntegerField(help_text='4-digit year, e.g. 2024')),
                ('warning_sent',  models.BooleanField(default=False)),
                ('critical_sent', models.BooleanField(default=False)),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
                ('updated_at',    models.DateTimeField(auto_now=True)),
                ('category',      models.ForeignKey(
                                      on_delete=django.db.models.deletion.CASCADE,
                                      related_name='budgets',
                                      to='tracker.category'
                                  )),
                ('user',          models.ForeignKey(
                                      on_delete=django.db.models.deletion.CASCADE,
                                      related_name='budgets',
                                      to=settings.AUTH_USER_MODEL
                                  )),
            ],
            options={
                'ordering': ['-year', '-month', 'category__name'],
            },
        ),

        # ── Indexes ───────────────────────────────────────────
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user', 'type'], name='tracker_tra_user_id_type_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user', 'date'], name='tracker_tra_user_id_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user', 'category'], name='tracker_tra_user_id_cat_idx'),
        ),

        # ── Unique Constraints ────────────────────────────────
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                condition=models.Q(user__isnull=False),
                fields=['user', 'name'],
                name='unique_category_per_user',
            ),
        ),
        migrations.AddConstraint(
            model_name='budget',
            constraint=models.UniqueConstraint(
                fields=['user', 'category', 'month', 'year'],
                name='unique_budget_per_category_month_year',
            ),
        ),
    ]
