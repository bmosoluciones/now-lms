# PayPal Integration Manual Testing Guide

This guide provides comprehensive instructions for manually testing the PayPal payment integration in NOW LMS.

## Prerequisites

1. **PayPal Developer Account**: Create a [PayPal Developer](https://developer.paypal.com) account
2. **PayPal Sandbox Application**: Create a sandbox application to get:
   - Client ID (sandbox)
   - Client Secret (sandbox)
3. **Test PayPal Accounts**: Create sandbox buyer and seller accounts

## Configuration Setup

### 1. PayPal Configuration in Admin Panel

Navigate to the admin panel and configure PayPal settings:

```
/admin/paypal-config
```

**Required Fields:**
- ✅ Enable PayPal: `True`
- ✅ Sandbox Mode: `True` (for testing)
- ✅ PayPal Client ID (Live): Your live client ID
- ✅ PayPal Client Secret (Live): Your live client secret  
- ✅ PayPal Client ID (Sandbox): Your sandbox client ID
- ✅ PayPal Client Secret (Sandbox): Your sandbox client secret

### 2. Site Currency Configuration

Configure the default currency in site settings:

```
/admin/site-config
```

**Currency Options:**
- USD (US Dollar)
- EUR (Euro) 
- CRC (Costa Rican Colón)
- Any PayPal-supported currency

## Manual Testing Scenarios

### Test Case 1: Free Course Enrollment

**Objective**: Verify free courses can be enrolled without payment

**Steps:**
1. Create a free course (`pagado = False`)
2. Navigate to course page
3. Click "Inscribirse al curso"
4. Verify immediate enrollment
5. Check payment record has `estado = "completed"` and `monto = 0`

**Expected Result**: Immediate course access without PayPal redirect

### Test Case 2: Paid Course Enrollment

**Objective**: Verify paid courses redirect to PayPal payment

**Steps:**
1. Create a paid course (`pagado = True`, `precio > 0`)
2. Navigate to course page  
3. Click "Proceder al pago"
4. Verify redirect to PayPal payment page
5. Complete PayPal payment flow
6. Verify course enrollment after payment

**Expected Result**: PayPal payment page → Payment → Course access

### Test Case 3: Audit Mode Enrollment

**Objective**: Verify audit mode allows course access without payment

**Steps:**
1. Create an auditable paid course (`pagado = True`, `auditable = True`)
2. Navigate to course page
3. Click "Auditar contenido del curso"
4. Verify immediate enrollment with audit flag
5. Check payment record has `audit = True`

**Expected Result**: Immediate course access with audit limitations

### Test Case 4: PayPal Payment Flow

**Objective**: Test complete PayPal payment processing

**Steps:**
1. Configure PayPal in sandbox mode
2. Create paid course with site currency
3. Navigate to payment page: `/paypal_checkout/payment/{course_code}`
4. Verify PayPal buttons load correctly
5. Complete payment with sandbox buyer account
6. Verify payment confirmation and course enrollment

**Expected Result**: Successful payment and course enrollment

### Test Case 5: Currency Support

**Objective**: Test different currencies work correctly

**Steps:**
1. Set site currency to EUR in configuration  
2. Create course with EUR price
3. Verify payment page shows EUR currency
4. Complete PayPal payment (PayPal handles conversion)
5. Verify payment record stores correct currency

**Expected Result**: Payment processed in configured currency

### Test Case 6: Payment Resumption

**Objective**: Test resuming existing pending payments

**Steps:**
1. Start payment process but don't complete
2. Try to enroll in same course again
3. Verify redirect to resume existing payment
4. Complete the resumed payment

**Expected Result**: No duplicate payments created

### Test Case 7: Error Handling

**Objective**: Test error scenarios are handled gracefully

**Test Scenarios:**
- Invalid PayPal configuration
- Network timeouts
- Payment amount mismatches
- Course not found
- PayPal API errors

**Expected Result**: User-friendly error messages and proper logging

## Debug Endpoints (Admin Only)

### PayPal Configuration Debug

```
GET /paypal_checkout/debug_config
```

Returns PayPal configuration status for troubleshooting.

### Payment Status Check

```
GET /paypal_checkout/payment_status/{course_code}
```

Returns detailed payment and enrollment status for a course.

## Browser Console Testing

### PayPal SDK Loading

Monitor browser console for:
- `PayPal SDK loaded successfully`
- `PayPal buttons rendered successfully` 
- Any error messages

### Payment State Management

Watch for payment state changes:
- `IDLE` → `PROCESSING` → `COMPLETED`
- Error states and recovery

### CSRF Token Handling

Verify CSRF token is found:
- `Using CSRF token from meta tag`
- No CSRF warnings

## Common Issues and Solutions

### PayPal Buttons Not Loading

**Check:**
1. PayPal configuration is correct
2. Client ID is valid for sandbox/production
3. Currency is supported by PayPal
4. Network connectivity to PayPal

### Payment Confirmation Fails

**Check:**
1. CSRF token is present in template
2. Course price matches payment amount
3. PayPal API credentials are correct
4. Database connection is working

### Currency Issues

**Check:**
1. Site currency is configured in `Configuracion` table
2. Currency cache is not stale
3. PayPal supports the currency

### Duplicate Payments

**Verify:**
1. Payment resumption logic works
2. Existing pending payments are detected
3. Payment IDs are unique

## Performance Testing

### Load Testing Scenarios

1. **Multiple concurrent payments**
2. **PayPal API timeout handling**  
3. **Database transaction rollbacks**
4. **Cache invalidation under load**

### Stress Testing

1. Rapid payment attempts
2. Browser refresh during payment
3. Network interruptions
4. PayPal API unavailability

## Security Testing

### Payment Security

1. **Amount tampering**: Verify server-side validation
2. **Order ID reuse**: Ensure payments can't be replayed
3. **User isolation**: Users can only see their own payments
4. **CSRF protection**: All forms protected

### Configuration Security

1. **Encrypted secrets**: PayPal secrets encrypted in database
2. **Admin-only access**: Configuration requires admin privileges
3. **Input validation**: All inputs properly validated

## Logging and Monitoring

### Key Log Messages

Monitor application logs for:
- Payment attempts and completions
- PayPal API errors
- Configuration issues
- User enrollment events

### Metrics to Track

- Payment success/failure rates
- PayPal API response times
- Course enrollment conversion rates
- Error frequencies by type

## Test Data Cleanup

After testing, clean up:
1. Remove test payment records
2. Reset course enrollments
3. Clear cache if needed
4. Remove test user accounts

## Automated Test Integration

Run automated tests alongside manual testing:

```bash
# Run payment flow tests
pytest tests/test_payment_flow.py --slow

# Run with coverage
pytest tests/test_payment_flow.py --slow --cov=now_lms.vistas.paypal
```

This comprehensive manual testing approach ensures the PayPal integration works reliably across all scenarios and edge cases.
