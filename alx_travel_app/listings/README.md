# alx_travel_app

This project contains a Django app for travel listings with models for Listing, Booking, and Review, along with DRF serializers and a database seeder.

## Project Duplication

The inner Django project folder `alx_travel_app` has been duplicated to `alx_travel_app_0x00` as requested.

## Models
 
Defined in `alx_travel_app/listings/models.py`:

- Listing: title, description, location, price_per_night, max_guests, is_available, image_url, host, timestamps
- Booking: listing, user, check_in, check_out, guests, total_price, status, timestamps
- Review: listing, user, rating (1-5), comment, timestamps

## Serializers

Defined in `alx_travel_app/listings/serializers.py`:

- ListingSerializer
- BookingSerializer

## Seeder

Management command at `alx_travel_app/listings/management/commands/seed.py` seeds a few sample listings.

## Setup & Run

1) Create and configure a `.env` file in `alx_travel_app` folder with MySQL credentials (or update settings accordingly):

```
MYSQL_DATABASE=alx_travel_db
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

2) Install dependencies (use a virtual environment if desired):

```
pip install -r alx_travel_app/requirement.txt
```

3) Run migrations:

```
python alx_travel_app/manage.py makemigrations
python alx_travel_app/manage.py migrate
```

4) Seed data:

```
python alx_travel_app/manage.py seed
```

5) Run server (optional):

```
python alx_travel_app/manage.py runserver
```

If you prefer using the duplicated project, replace the path prefix `alx_travel_app/` with `alx_travel_app_0x00/` in the commands above.
