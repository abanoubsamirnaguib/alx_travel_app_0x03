# alx_travel_app

This project contains a Django app for travel listings with models for Listing, Booking, and Review, along with DRF serializers, a database seeder, and background task management with Celery.

## Project Duplication

The inner Django project folder `alx_travel_app` has been duplicated to `alx_travel_app_0x00` as requested.

## Features

- **Travel Listings Management**: Create, read, update, and delete property listings
- **Booking System**: Handle property bookings with status tracking
- **Payment Integration**: Chapa payment gateway integration
- **Background Tasks**: Celery with RabbitMQ for email notifications
- **Email Notifications**: Automated emails for booking confirmations and payment status

## Models
 
Defined in `alx_travel_app/listings/models.py`:

- **Listing**: title, description, location, price_per_night, max_guests, is_available, image_url, host, timestamps
- **Booking**: listing, user, check_in, check_out, guests, total_price, status, timestamps
- **Review**: listing, user, rating (1-5), comment, timestamps
- **Payment**: booking, transaction_id, payment_reference, amount, currency, status, timestamps

## Serializers

Defined in `alx_travel_app/listings/serializers.py`:

- ListingSerializer
- BookingSerializer
- PaymentSerializer
- PaymentInitiateSerializer

## Background Tasks

Defined in `alx_travel_app/listings/tasks.py`:

- **send_booking_confirmation_email**: Sent when a new booking is created
- **send_payment_confirmation_email**: Sent when payment is successfully completed
- **send_payment_failed_email**: Sent when payment fails

## Seeder

Management command at `alx_travel_app/listings/management/commands/seed.py` seeds a few sample listings.

## Setup & Run

### Prerequisites

1. **Install RabbitMQ** (Message Broker for Celery):
   - **Windows**: Download and install from [RabbitMQ website](https://www.rabbitmq.com/install-windows.html)
   - **macOS**: `brew install rabbitmq`
   - **Ubuntu/Debian**: `sudo apt-get install rabbitmq-server`

2. **Start RabbitMQ Service**:
   - **Windows**: RabbitMQ should start automatically after installation
   - **macOS**: `brew services start rabbitmq`
   - **Ubuntu/Debian**: `sudo systemctl start rabbitmq-server`

### Installation

1) Create and configure a `.env` file in `alx_travel_app` folder:

```env
# Database Configuration
MYSQL_DATABASE=alx_travel_db
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306

# Celery Configuration
CELERY_BROKER_URL=amqp://guest@localhost//
CELERY_RESULT_BACKEND=rpc://

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@alxtravel.com

# Chapa Payment Configuration (Optional)
CHAPA_PUBLIC_KEY=your_chapa_public_key
CHAPA_SECRET_KEY=your_chapa_secret_key
CHAPA_WEBHOOK_HASH=your_webhook_hash
```

2) Install dependencies (use a virtual environment if desired):

```bash
pip install -r alx_travel_app/requirement.txt
```

3) Run migrations:

```bash
python alx_travel_app/manage.py makemigrations
python alx_travel_app/manage.py migrate
```

4) Seed data:

```bash
python alx_travel_app/manage.py seed
```

5) Start the Django development server:

```bash
python alx_travel_app/manage.py runserver
```

6) **Start Celery Worker** (in a separate terminal):

```bash
cd alx_travel_app
celery -A alx_travel_app worker --loglevel=info
```

7) **Start Celery Beat** (optional, for scheduled tasks):

```bash
cd alx_travel_app
celery -A alx_travel_app beat --loglevel=info
```

### Testing Background Tasks

1. Create a booking via the API at `POST /api/bookings/`
2. Check the Celery worker logs to see the email task being processed
3. Check your email to verify the booking confirmation was sent

### API Endpoints

- `GET /api/listings/` - List all listings
- `POST /api/listings/` - Create a new listing (authenticated)
- `GET /api/bookings/` - List all bookings
- `POST /api/bookings/` - Create a new booking (authenticated)
- `POST /api/payments/initiate/` - Initiate payment for a booking
- `POST /api/payments/verify/` - Verify payment status

### Troubleshooting

1. **RabbitMQ Connection Issues**: Ensure RabbitMQ is running and accessible at the configured URL
2. **Email Not Sending**: Check your email configuration in the `.env` file
3. **Celery Tasks Not Processing**: Verify the Celery worker is running and connected to RabbitMQ

If you prefer using the duplicated project, replace the path prefix `alx_travel_app/` with `alx_travel_app_0x00/` in the commands above.
