from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing


class Command(BaseCommand):
    help = "Seed the database with sample listings data"

    def handle(self, *args, **options):
        User = get_user_model()
        # Ensure a default host user exists
        host, _ = User.objects.get_or_create(
            username="host",
            defaults={"email": "host@example.com"},
        )

        samples = [
            {
                "title": "Cozy Beach House",
                "description": "A cozy beach house with ocean views.",
                "location": "Miami, FL",
                "price_per_night": 220.00,
                "max_guests": 4,
                "image_url": "https://picsum.photos/seed/beach/800/600",
            },
            {
                "title": "Downtown Apartment",
                "description": "Modern apartment in the heart of the city.",
                "location": "New York, NY",
                "price_per_night": 180.00,
                "max_guests": 2,
                "image_url": "https://picsum.photos/seed/city/800/600",
            },
            {
                "title": "Mountain Cabin Retreat",
                "description": "Quiet cabin with stunning mountain views.",
                "location": "Denver, CO",
                "price_per_night": 150.00,
                "max_guests": 5,
                "image_url": "https://picsum.photos/seed/mountain/800/600",
            },
        ]

        created = 0
        for item in samples:
            obj, was_created = Listing.objects.get_or_create(
                title=item["title"],
                location=item["location"],
                defaults={
                    "description": item["description"],
                    "price_per_night": item["price_per_night"],
                    "max_guests": item["max_guests"],
                    "image_url": item["image_url"],
                    "host": host,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seed completed. {created} new listings created."))
