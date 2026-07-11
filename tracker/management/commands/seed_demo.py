"""
tracker/management/commands/seed_demo.py

Management command: python manage.py seed_demo

Creates a demo user and populates realistic sample transactions + budgets
so you can explore the full app immediately after setup.
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import Category, Transaction, Budget


DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'Demo@1234'
DEMO_EMAIL    = 'demo@financetracker.local'


class Command(BaseCommand):
    help = 'Seeds the database with a demo user and sample financial data.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data…')

        # ── Create demo user ──────────────────────────────
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={
                'email':      DEMO_EMAIL,
                'first_name': 'Demo',
                'last_name':  'User',
            }
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(f'  Created user: {DEMO_USERNAME} / {DEMO_PASSWORD}')
        else:
            self.stdout.write(f'  User already exists: {DEMO_USERNAME}')

        # ── Get predefined categories ──────────────────────
        cats = {c.name: c for c in Category.objects.filter(is_predefined=True)}
        if not cats:
            self.stdout.write(self.style.ERROR('  No predefined categories found. Run migrate first.'))
            return

        # ── Create transactions for past 3 months ─────────
        today = date.today()
        existing = Transaction.objects.filter(user=user).count()
        if existing > 0:
            self.stdout.write(f'  Transactions already exist ({existing}), skipping.')
        else:
            income_cats  = ['Salary', 'Freelance']
            expense_cats = ['Food & Dining', 'Transport', 'Entertainment',
                            'Utilities', 'Shopping', 'Health']

            for months_back in range(3):
                # Target month
                m = today.month - months_back
                y = today.year
                while m <= 0:
                    m += 12; y -= 1

                # 1-2 income transactions per month
                for cat_name in random.sample(income_cats, k=1):
                    cat = cats.get(cat_name)
                    if cat:
                        Transaction.objects.create(
                            user=user, category=cat,
                            type='income',
                            amount=Decimal(str(random.randint(45000, 85000))),
                            date=date(y, m, random.randint(1, 5)),
                            description=f'{cat_name} payment',
                        )

                # 8-14 expense transactions per month
                for _ in range(random.randint(8, 14)):
                    cat_name = random.choice(expense_cats)
                    cat = cats.get(cat_name)
                    if not cat:
                        continue
                    amount_map = {
                        'Food & Dining': (300, 3500),
                        'Transport':     (100, 1200),
                        'Entertainment': (200, 2000),
                        'Utilities':     (500, 3000),
                        'Shopping':      (500, 5000),
                        'Health':        (200, 2500),
                    }
                    lo, hi = amount_map.get(cat_name, (100, 2000))
                    Transaction.objects.create(
                        user=user, category=cat,
                        type='expense',
                        amount=Decimal(str(random.randint(lo, hi))),
                        date=date(y, m, random.randint(1, 28)),
                        description=f'{cat_name} expense',
                    )
            self.stdout.write('  Transactions created.')

        # ── Create budgets for current month ──────────────
        budget_targets = {
            'Food & Dining': 8000,
            'Transport':     3000,
            'Entertainment': 2000,
            'Utilities':     4000,
            'Shopping':      5000,
            'Health':        2500,
        }
        for cat_name, limit in budget_targets.items():
            cat = cats.get(cat_name)
            if not cat:
                continue
            Budget.objects.get_or_create(
                user=user, category=cat,
                month=today.month, year=today.year,
                defaults={'amount': Decimal(str(limit))}
            )
        self.stdout.write('  Budgets created.')
        self.stdout.write(self.style.SUCCESS(
            f'\nDemo data ready! Login with: {DEMO_USERNAME} / {DEMO_PASSWORD}'
        ))
