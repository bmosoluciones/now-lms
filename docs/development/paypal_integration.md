# PayPal Payment Integration

This document describes the PayPal payment functionality implemented for NOW LMS.

## Overview

The PayPal integration allows students to pay for courses using PayPal's secure payment processing. The system supports:

- **Free courses**: Immediate enrollment
- **Paid courses**: Payment required via PayPal before enrollment
- **Audit mode**: Free access to course content without certificates (for auditable courses)

## Features

### Course Enrollment Flow

1. **Free Courses**: Students can enroll immediately without payment
2. **Paid Courses**: 
   - Creates a pending payment record
   - Redirects to PayPal for secure payment
   - Creates course enrollment only after successful payment
3. **Audit Mode**: Students can access course content without payment but cannot receive certificates

### Payment Processing

- Uses PayPal JavaScript SDK for client-side payment processing
- Supports both sandbox (development) and production (live) environments
- Encrypted storage of PayPal API credentials
- Server-side payment verification through PayPal REST API
- Automatic payment status updates based on PayPal responses
- Retry mechanism for payment confirmation with exponential backoff

### Security

- PayPal API credentials are encrypted before storage
- Secure redirect to PayPal's payment pages
- Payment verification through PayPal's API
- CSRF protection on all forms

## Configuration

### PayPal Developer Setup

1. Create a PayPal Developer account at https://developer.paypal.com
2. Create a new application for your LMS
3. Note down your Client ID and Client Secret for both sandbox and live environments

### LMS Configuration

1. Go to Admin Panel → Settings → PayPal Configuration (`/setting/paypal`)
2. Enable PayPal payments
3. Configure your PayPal credentials:
   - **Sandbox Mode**: Use for testing and development
   - **Production Mode**: Use for live payments

#### Configuration Fields

- **Enable PayPal**: Toggle to enable/disable PayPal payments
- **Sandbox Mode**: Toggle between sandbox and production
- **Client ID (Production)**: Your live PayPal Client ID
- **Client Secret (Production)**: Your live PayPal Client Secret (encrypted)
- **Client ID (Sandbox)**: Your sandbox PayPal Client ID  
- **Client Secret (Sandbox)**: Your sandbox PayPal Client Secret (encrypted)

**Note**: Client secrets are automatically encrypted before storage using the site's encryption key.

### Payment Flow

The payment flow uses the PayPal JavaScript SDK for a seamless user experience:

1. Student navigates to course payment page
2. Page loads PayPal JavaScript SDK with client ID
3. PayPal buttons render with course amount and currency
4. Student clicks PayPal button and completes payment in popup
5. Payment is captured on the client side
6. Client sends payment confirmation to server (`/paypal_checkout/confirm_payment`)
7. Server verifies payment with PayPal REST API
8. Server creates enrollment record and marks payment as completed
9. Student is redirected to course page

## Database Schema

### PaypalConfig Table

- `enable`: Boolean flag to enable/disable PayPal payments
- `sandbox`: Boolean flag for sandbox/production mode
- `paypal_id`: Production client ID (plain text)
- `paypal_sandbox`: Sandbox client ID (plain text)
- `paypal_secret`: Encrypted production client secret (binary)
- `paypal_sandbox_secret`: Encrypted sandbox client secret (binary)

### Payment Records (Pago)

Payment records track the following states:
- `pending`: Payment created, awaiting PayPal processing
- `completed`: Payment successful, course enrollment created
- `failed`: Payment failed or cancelled

Key fields:
- `usuario`: Student username (foreign key)
- `curso`: Course code (foreign key)
- `monto`: Payment amount (decimal)
- `moneda`: Currency code (e.g., USD, EUR, CRC)
- `metodo`: Payment method (e.g., "paypal")
- `estado`: Payment status (pending, completed, failed)
- `referencia`: PayPal order ID for verification
- `audit`: Boolean flag for audit-mode enrollments
- `descripcion`: Additional payment details (e.g., coupon applied)

## Implementation Details

### Client-Side JavaScript (`static/js/paypal.js`)

The client-side implementation handles:
- PayPal SDK loading with retry mechanism
- PayPal button rendering and configuration
- Order creation with course details
- Payment capture and approval
- Payment confirmation with server-side retry logic
- Error handling and user feedback
- CSRF token management
- Browser state management (page visibility, unload events)

Key features:
- **Exponential backoff retry**: Automatically retries failed SDK loads and payment confirmations
- **State management**: Tracks payment state (idle, processing, completed, failed)
- **CSRF protection**: Includes CSRF token in all API requests
- **User experience**: Shows loading indicators and user-friendly error messages

### Server-Side Implementation (`vistas/paypal.py`)

The server-side implementation provides:

**Configuration Functions:**
- `check_paypal_enabled()`: Checks if PayPal is enabled (cached)
- `get_site_currency()`: Returns site's default currency (cached)
- `validate_paypal_configuration()`: Validates PayPal credentials by requesting access token
- `get_paypal_access_token()`: Obtains PayPal API access token with credential decryption
- `verify_paypal_payment()`: Verifies payment order with PayPal REST API

**Payment Endpoints:**
- `payment_page()`: Displays PayPal payment form for a course
- `get_client_id()`: Returns PayPal client ID for JavaScript SDK initialization
- `confirm_payment()`: Processes payment confirmation from client
  - Validates all payment data (order ID, payer ID, amount, currency)
  - Verifies payment with PayPal API
  - Checks amount matches expected course price (with coupon support)
  - Prevents duplicate payment processing
  - Creates enrollment record on success
  - Updates coupon usage if applicable
  - Creates course progress index
- `resume_payment()`: Allows resuming pending payments
- `payment_status()`: Returns detailed payment and enrollment information
- `debug_config()`: Admin-only endpoint for debugging configuration

**Security Features:**
- All payment amounts are verified server-side
- PayPal order verification before enrollment
- Duplicate payment detection
- User authentication required for all operations
- Admin-only access to sensitive configuration data

## API Endpoints

### Payment Processing Routes

- `GET /paypal_checkout/payment/<course_code>` - Display PayPal payment page for a course
- `POST /paypal_checkout/confirm_payment` - Confirm PayPal payment after client-side processing
- `GET /paypal_checkout/resume_payment/<payment_id>` - Resume an existing pending payment
- `GET /paypal_checkout/get_client_id` - Get PayPal client ID for JavaScript SDK
- `GET /paypal_checkout/payment_status/<course_code>` - Check payment status for a course
- `GET /paypal_checkout/debug_config` - Debug PayPal configuration (admin only)

## Error Handling

The system handles various error scenarios:

- PayPal API configuration errors
- Payment creation failures
- Payment verification failures
- Network connectivity issues
- Invalid payment states
- Amount mismatch errors
- Duplicate payment prevention

Users receive appropriate error messages and are redirected to safe pages.

## Testing

### Unit Tests

Run the PayPal integration tests:

```bash
python -m pytest tests/test_paypal_integration.py -v
```

The test suite includes 29 comprehensive tests covering:
- PayPal configuration validation
- Payment flow endpoints
- Payment confirmation logic
- Error handling scenarios
- Client ID retrieval
- Payment status checking

### Manual Testing

1. Create a test course with payment enabled
2. Attempt enrollment as a student
3. Verify redirect to PayPal sandbox
4. Complete or cancel payment
5. Verify correct enrollment status

### Test Scenarios

- Free course enrollment
- Paid course enrollment with successful payment
- Paid course enrollment with cancelled payment
- Audit mode enrollment
- PayPal configuration errors

## Security Considerations

- All PayPal API credentials are encrypted in the database
- Payment amounts are validated against course prices
- User authentication is required for all payment operations
- CSRF tokens protect against cross-site request forgery
- Payment status is verified through PayPal API

## Troubleshooting

### Common Issues

1. **PayPal credentials not configured**
   - Ensure Client ID and Secret are set in admin panel
   - Verify credentials are correct for your environment (sandbox/live)

2. **Payment creation fails**
   - Check PayPal API connectivity
   - Verify return URLs are configured correctly
   - Check application logs for API errors

3. **Students not enrolled after payment**
   - Verify payment execution callback is working
   - Check payment status in database
   - Ensure course enrollment logic is not failing

### Logging

Payment operations are logged for debugging:
- Payment creation attempts
- PayPal API responses
- Payment status changes
- Error conditions

## Maintenance

### Regular Tasks

- Monitor payment success rates
- Review failed payment logs
- Update PayPal credentials as needed
- Test payment flow periodically

### Updates

When updating PayPal integration:
- Test in sandbox environment first
- Verify backward compatibility
- Update documentation as needed
- Communicate changes to administrators