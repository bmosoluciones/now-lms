There are many ways to get payments to monetice yours online cources.

# Manual Processing Payments

There are many ways to get paid from your courses.

## Including Payments Instructions

Maybe the easy way to get paid on line is to include Payments Instructions

    Bank: ##########

    Account: ###-####-####-###

    Beneficiary: Account Holder Name

    Confirmation: Send your payment confirmation to user@domain.tdl before than DD/MMMM/YYYY

With this info people interested in your course can send you a email with the payment and you can create a new user,
enroll the user in the course and send this information to your users.

!!! note

    Please note that this metod is effective to get paid, but you, or something than help you to check for payment
    notification must be available to process the request as soon as posible, you must consider that the time to
    get a responce from you is very import for the experience of your users.

# Paypal

NOW LMS supports both manual and automated PayPal payment processing. To accept payments with PayPal you need a [Business Account](https://www.paypal.com/es/bizsignup/entry). PayPal accepts many forms of payments.

## Automated PayPal Integration (Recommended)

NOW LMS includes built-in PayPal integration that automatically processes payments and enrolls students in courses. This is the recommended approach for production use.

### Features

- **Automatic payment processing**: Students are redirected to PayPal for secure payment
- **Instant enrollment**: Students are automatically enrolled after successful payment
- **Payment tracking**: All payments are tracked with detailed status information
- **Audit mode**: Optional audit access for students who want to preview course content
- **Secure credential storage**: PayPal API credentials are encrypted in the database

### Setup

1. **Create PayPal Developer Account**
   - Visit [PayPal Developer Portal](https://developer.paypal.com)
   - Create a new application for your LMS
   - Note your Client ID and Client Secret for both sandbox and live environments

2. **Configure NOW LMS**
   - Go to Admin Panel → Settings → PayPal Configuration
   - Enable PayPal payments
   - Enter your PayPal credentials (sandbox for testing, live for production)
   - Configure return URLs in PayPal dashboard

3. **Test the Integration**
   - Create a test course with payment enabled
   - Use PayPal sandbox credentials
   - Test the complete payment flow

### Payment Flow

1. Student selects a paid course and clicks "Enroll"
2. Student fills in billing information
3. System creates a pending payment record
4. Student is redirected to PayPal for secure payment
5. After payment, student is redirected back to NOW LMS
6. System verifies payment with PayPal API
7. Student is automatically enrolled in the course

### Course Types

- **Free Courses**: Students can enroll immediately without payment
- **Paid Courses**: Payment required before enrollment
- **Auditable Courses**: Students can choose between:
  - **Audit Mode**: Free access to content without certificates
  - **Full Access**: Paid access with certificates and evaluations

For detailed technical information, see [PayPal Integration Documentation](paypal_integration.md).

## Manual PayPal Processing

## Accepting payments with Paypal and manually enrolling the user.

With Paypal you can accetp payments and manually enrolling users in course with Paypalme and Payment Request,

### Paypalme

Get paid with a custom link with [Paypal.me](https://www.paypal.com/paypalme/my/landing),

![Paypal.me](/images/paypalme.jpg)

Just note that after the payment is done you must procces the enroll manually.

!!! warning

    Note that if you do not proccess quickly the request the user can fell cheated and issue a reimbursement with Paypal,
    if many customer start issuing reimbursement aganist your account your reputation in the plataform will decrease and
    your account can be canceled.

### Transfer Request

You can may a request to your user to issue a payment to your account with the [Payment Request](https://www.paypal.com/myaccount/transfer/request/)
option, this way a user will contact you, the user must provide its Paypal user and you can generate a invoice to the user, once
the payment is done you can enroll the user in the course.

![Payment Request](/images/paymentrequest.jpg)

!!! warning

    Note that if you do not proccess quickly the request the user can fell cheated and issue a reimbursement with Paypal,
    if many customer start issuing reimbursement aganist your account your reputation in the plataform will decrease and
    your account can be canceled.
