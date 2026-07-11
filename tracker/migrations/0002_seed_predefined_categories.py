"""
tracker/migrations/0002_seed_predefined_categories.py

Data migration: inserts the predefined global categories that are
available to all users. These have user=None and is_predefined=True.
"""

from django.db import migrations


PREDEFINED_CATEGORIES = [
    # (name, icon, color)
    ('Salary',        'bi-briefcase',   '#4361ee'),
    ('Freelance',     'bi-laptop',      '#7209b7'),
    ('Investment',    'bi-graph-up',    '#2dc653'),
    ('Food & Dining', 'bi-cart',        '#f77f00'),
    ('Rent',          'bi-house',       '#e63946'),
    ('Transport',     'bi-car-front',   '#4cc9f0'),
    ('Health',        'bi-heart-pulse', '#f72585'),
    ('Education',     'bi-mortarboard', '#06d6a0'),
    ('Entertainment', 'bi-controller',  '#ffd60a'),
    ('Utilities',     'bi-lightning',   '#adb5bd'),
    ('Shopping',      'bi-bag',         '#f72585'),
    ('Savings',       'bi-piggy-bank',  '#2dc653'),
    ('Gifts',         'bi-gift',        '#7209b7'),
    ('Travel',        'bi-airplane',    '#4361ee'),
    ('Other',         'bi-three-dots',  '#adb5bd'),
]


def seed_categories(apps, schema_editor):
    """Insert predefined categories (idempotent — skips existing ones)."""
    Category = apps.get_model('tracker', 'Category')
    for name, icon, color in PREDEFINED_CATEGORIES:
        Category.objects.get_or_create(
            name=name,
            user=None,
            defaults={
                'icon':         icon,
                'color':        color,
                'is_predefined': True,
            }
        )


def remove_seeded_categories(apps, schema_editor):
    """Reverse: remove only the seeded predefined categories."""
    Category = apps.get_model('tracker', 'Category')
    names = [row[0] for row in PREDEFINED_CATEGORIES]
    Category.objects.filter(name__in=names, user=None, is_predefined=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_code=remove_seeded_categories),
    ]
