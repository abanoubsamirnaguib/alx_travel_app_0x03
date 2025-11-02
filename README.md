# ALX Travel App 0x02 - Django Travel Booking Platform with Chapa Payment Integration

This project is a comprehensive Django-based travel booking platform that integrates with Chapa Payment Gateway for secure payment processing. The application allows users to browse listings, make bookings, and complete payments through Ethiopia's leading payment processor.

## 🚀 Features

### Core Functionality
- **Listing Management**: Create, read, update, and delete travel property listings
- **Booking System**: Users can book available properties with date range selection
- **Review System**: Users can leave reviews and ratings for properties they've booked
- **User Management**: Built-in Django authentication and user management

### 💳 Payment Integration (New)
- **Chapa Payment Gateway Integration**: Secure payment processing using Chapa API
- **Payment Initiation**: Seamless payment flow initiation for bookings
- **Payment Verification**: Automatic payment status verification and updates
- **Webhook Support**: Real-time payment status updates via Chapa webhooks
- **Email Notifications**: Automated email confirmations for successful/failed payments
- **Background Tasks**: Celery integration for handling email notifications asynchronously

## 📋 Models

### Existing Models
Defined in `alx_travel_app/listings/models.py`:

- **Listing**: title, description, location, price_per_night, max_guests, is_available, image_url, host, timestamps
- **Booking**: listing, user, check_in, check_out, guests, total_price, status, timestamps
- **Review**: listing, user, rating (1-5), comment, timestamps

### New Payment Model
- **Payment**: booking, transaction_id, chapa_reference, payment_reference, amount, currency, status, checkout_url, chapa_data, timestamps

## 🔧 API Endpoints

### Payment Endpoints (New)
- `POST /api/payments/initiate/` - Initiate payment for a booking
- `POST /api/payments/verify/` - Verify payment status
- `GET /api/payments/` - List user's payments
- `POST /api/chapa/webhook/` - Chapa webhook for payment status updates

### Existing Endpoints
- `GET/POST /api/listings/` - List/Create listings
- `GET/PUT/DELETE /api/listings/{id}/` - Retrieve/Update/Delete specific listing
- `GET/POST /api/bookings/` - List/Create bookings
- `GET/PUT/DELETE /api/bookings/{id}/` - Retrieve/Update/Delete specific booking

## 🛠️ Setup & Configuration

### 1. Environment Setup

Create a `.env` file in the `alx_travel_app` folder:

```env
# Django Configuration
SECRET_KEY=your_secret_key_here
DEBUG=True

# Database Configuration
MYSQL_DATABASE=alx_travel_db
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306

# Chapa Payment Configuration (Required)
CHAPA_SECRET_KEY=your_chapa_secret_key_here
CHAPA_WEBHOOK_HASH=your_chapa_webhook_hash_here
CHAPA_BASE_URL=https://api.chapa.co/v1

# Email Configuration (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@alxtravel.com

# Celery Configuration (for background tasks)
CELERY_BROKER_URL=amqp://localhost
CELERY_RESULT_BACKEND=rpc://
```

### 2. Chapa API Setup

**✅ Test Credentials Provided:**
The following test credentials are already configured in the project:

```env
CHAPA_PUBLIC_KEY=CHAPUBK_TEST-u93vw9MHQYaPhtA4Fa89JQi5qsCxoyBt
CHAPA_SECRET_KEY=CHASECK_TEST-TkpRkSUsdv9x3o2A5PRx6hlWE62bvRoI
CHAPA_WEBHOOK_HASH=kimUiM6latpe3r1QhR7LEzht
CHAPA_BASE_URL=https://api.chapa.co/v1
```

**For Production:**
1. **Create Chapa Account**: 
   - Visit [Chapa Developer Portal](https://developer.chapa.co/)
   - Register for a developer account
   - Complete the verification process

2. **Get Production API Keys**:
   - Login to your Chapa dashboard
   - Navigate to API Keys section
   - Replace test credentials with production keys

3. **Configure Webhooks**:
   - Add webhook URL: `https://yourdomain.com/api/chapa/webhook/`
   - Set webhook hash in environment variables

### 3. Installation

```bash
# Install dependencies
pip install -r alx_travel_app/requirement.txt

# Run migrations
python alx_travel_app/manage.py makemigrations
python alx_travel_app/manage.py migrate

# Create superuser (optional)
python alx_travel_app/manage.py createsuperuser

# Seed sample data
python alx_travel_app/manage.py seed
```

### 4. Running the Application

```bash
# Start Django development server
python alx_travel_app/manage.py runserver

# In a separate terminal, start Celery worker for background tasks
celery -A alx_travel_app worker --loglevel=info

# In another terminal, start Celery beat for scheduled tasks (if needed)
celery -A alx_travel_app beat --loglevel=info
```

## 💳 Payment Workflow

### 1. Payment Initiation
```python
# Example API call to initiate payment
POST /api/payments/initiate/
{
    "booking_id": 1,
    "return_url": "http://localhost:3000/payment/success",
    "callback_url": "http://localhost:8000/api/chapa/webhook/"
}
```

### 2. User Payment Process
1. User receives checkout URL from payment initiation
2. User is redirected to Chapa payment page
3. User completes payment using their preferred method
4. Chapa processes payment and sends webhook notification
5. System verifies payment and updates booking status
6. User receives email confirmation

### 3. Payment Verification
```python
# Example API call to verify payment
POST /api/payments/verify/
{
    "tx_ref": "payment-reference-uuid"
}
```

## 🧪 Testing Payment Integration

### Quick Start Testing

1. **Validate Configuration**:
   ```bash
   cd alx_travel_app
   python validate_chapa_config.py
   ```

2. **Run Comprehensive Tests**:
   ```bash
   python test_chapa_integration.py
   ```

3. **Run Demo Workflow**:
   ```bash
   python payment_demo.py
   ```

### Using the Test Script

The project includes several testing scripts:

- **`validate_chapa_config.py`**: Validates configuration and API connectivity
- **`test_chapa_integration.py`**: Comprehensive API testing with real Chapa calls
- **`payment_demo.py`**: Complete payment workflow demonstration

### Manual Testing Steps

1. **Start the Django Server**:
   ```bash
   python manage.py runserver
   ```

2. **Test Payment Flow**:
   - Create a booking through the API or admin interface
   - Use the test scripts to initiate payment
   - Visit the provided checkout URL to complete test payment
   - Verify payment status updates

3. **Test Webhook** (Optional):
   - Use tools like ngrok to expose your local server
   - Configure webhook URL in test environment
   - Complete a test payment and verify webhook processing

### Test Credentials in Use

✅ **Pre-configured Test Credentials:**
- **Public Key**: `CHAPUBK_TEST-u93vw9MHQYaPhtA4Fa89JQi5qsCxoyBt`
- **Secret Key**: `CHASECK_TEST-TkpRkSUsdv9x3o2A5PRx6hlWE62bvRoI`
- **Encryption Key**: `kimUiM6latpe3r1QhR7LEzht`

These credentials are already configured in your `.env` file and ready for testing.

## 📊 Monitoring & Logging

### Payment Logs
- All payment operations are logged with appropriate levels
- Check Django logs for payment initiation, verification, and webhook processing
- Monitor Celery logs for email notification status

### Admin Interface
- Access Django admin at `/admin/`
- View and manage payments, bookings, and listings
- Monitor payment statuses and transaction details

## 🔒 Security Considerations

### API Security
- All payment endpoints require authentication
- Users can only access their own payment records
- Webhook endpoints validate Chapa signatures

### Environment Variables
- Store sensitive data (API keys, passwords) in environment variables
- Never commit `.env` files to version control
- Use different API keys for development and production

## 📈 Production Deployment

### Required Steps
1. **Database**: Use production-ready database (PostgreSQL recommended)
2. **Message Broker**: Setup Redis or RabbitMQ for Celery
3. **Email Service**: Configure production email service (SendGrid, AWS SES)
4. **SSL Certificate**: Ensure HTTPS for payment security
5. **Webhook Security**: Implement proper webhook signature validation
6. **Monitoring**: Setup logging and monitoring for payment transactions

### Environment Configuration
```env
# Production settings
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CHAPA_BASE_URL=https://api.chapa.co/v1  # Production URL
# ... other production configurations
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/payment-enhancement`)
3. Commit your changes (`git commit -am 'Add payment enhancement'`)
4. Push to the branch (`git push origin feature/payment-enhancement`)
5. Create a Pull Request

## 📝 License

This project is part of the ALX Software Engineering program and is for educational purposes.

## 🆘 Support

For issues related to:
- **Chapa Integration**: Check [Chapa Documentation](https://developer.chapa.co/docs)
- **Django Issues**: Refer to [Django Documentation](https://docs.djangoproject.com/)
- **Celery Issues**: Check [Celery Documentation](https://docs.celeryproject.org/)

## 📋 TODO / Future Enhancements

- [ ] Add payment refund functionality
- [ ] Implement partial payments
- [ ] Add payment analytics dashboard
- [ ] Support for multiple currencies
- [ ] Add payment method preferences
- [ ] Implement payment reminders
- [ ] Add fraud detection mechanisms
"# alx_travel_app_0x03" 
"# alx_travel_app_0x03" 
