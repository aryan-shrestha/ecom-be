from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from cart.models import Cart


class Command(BaseCommand):
    help = 'Clean expired anonymous carts older than specified days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days after which anonymous carts are considered expired (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        expiry_date = timezone.now().date() - timedelta(days=days)
        expired_carts = Cart.objects.filter(
            date_added__lt=expiry_date,
            user__isnull=True  # Only anonymous carts
        )

        count = expired_carts.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} expired anonymous carts older than {days} days'
                )
            )
            for cart in expired_carts[:10]:  # Show first 10 as examples
                self.stdout.write(
                    f'  - Cart ID {cart.id} (session: {cart.session_key}, date: {cart.date_added})')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more carts')
        else:
            expired_carts.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} expired anonymous carts older than {days} days'
                )
            )
