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

- Uses PayPal REST API SDK for secure payment processing
- Supports both sandbox (development) and live (production) environments
- Encrypted storage of PayPal API credentials
- Automatic payment status updates based on PayPal responses

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

1. Go to Admin Panel → Settings → PayPal Configuration
2. Enable PayPal payments
3. Configure your PayPal credentials:
   - **Sandbox Mode**: Use for testing and development
   - **Production Mode**: Use for live payments

#### Configuration Fields

- **Enable PayPal**: Toggle to enable/disable PayPal payments
- **Sandbox Mode**: Toggle between sandbox and production
- **Client ID (Production)**: Your live PayPal Client ID
- **Client Secret (Production)**: Your live PayPal Client Secret
- **Client ID (Sandbox)**: Your sandbox PayPal Client ID  
- **Client Secret (Sandbox)**: Your sandbox PayPal Client Secret

### PayPal Return URLs

Configure these URLs in your PayPal application:

- **Return URL**: `https://yourdomain.com/paypal_checkout/execute_payment/{payment_id}`
- **Cancel URL**: `https://yourdomain.com/paypal_checkout/cancel_payment/{payment_id}`

## Database Schema

### New Fields in PaypalConfig

- `paypal_secret`: Encrypted production client secret
- `paypal_sandbox_secret`: Encrypted sandbox client secret

### Payment Records (Pago)

Payment records track the following states:
- `pending`: Payment created, awaiting PayPal processing
- `completed`: Payment successful, course enrollment created
- `failed`: Payment failed or cancelled

## API Endpoints

### Payment Processing Routes

- `POST /course/{course_code}/enroll` - Course enrollment with payment logic
- `GET /paypal_checkout/create_payment/{payment_id}` - Create PayPal payment
- `GET /paypal_checkout/execute_payment/{payment_id}` - Handle successful payment
- `GET /paypal_checkout/cancel_payment/{payment_id}` - Handle cancelled payment

## Error Handling

The system handles various error scenarios:

- PayPal API configuration errors
- Payment creation failures
- Payment execution failures
- Network connectivity issues
- Invalid payment states

Users receive appropriate error messages and are redirected to safe pages.

## Testing

### Unit Tests

Run the payment flow tests:

```bash
python -m pytest tests/test_payment_flow.py -v
```

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