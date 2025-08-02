# Course Configuration

This guide covers the detailed configuration options for courses in NOW-LMS, including pricing models, access controls, and advanced settings.

## Course Pricing Models

### Free Courses

Free courses provide immediate access to all students without any payment requirements.

#### Configuration
```
Paid: False
Price: N/A
Auditable: N/A
```

#### Features
- **Instant Enrollment**: Students can join immediately
- **Full Access**: Complete access to all course materials
- **Certificates**: Available upon course completion
- **No Payment Gateway**: No PayPal configuration required

#### Best For
- Introductory content
- Company training
- Educational outreach
- Marketing and lead generation

### Paid Courses

Paid courses require payment before students can access the full course content.

#### Configuration
```
Paid: True
Price: [Amount in your currency]
Auditable: True/False (optional)
```

#### Features
- **Payment Required**: Full access only after successful payment
- **PayPal Integration**: Secure payment processing
- **Enrollment Protection**: Prevents unauthorized access
- **Revenue Generation**: Monetize your expertise

#### Payment Flow
1. Student discovers course
2. Views course description and preview (if available)
3. Clicks "Enroll" or "Purchase"
4. Redirected to PayPal payment page
5. Completes payment transaction
6. Automatically enrolled upon successful payment
7. Gains full access to course materials

### Auditable Courses

Auditable courses allow free access to content without certificate eligibility.

#### Configuration
```
Paid: True
Price: [Amount]
Auditable: True
```

#### Features
- **Dual Access Model**: Both paid and audit enrollment options
- **Free Content Access**: Audit students see all materials
- **No Certificates**: Audit students cannot receive certificates
- **Upgrade Path**: Audit students can upgrade to paid enrollment

#### Audit Student Experience
- Access all course content
- Participate in forums (if enabled)
- Complete assessments (for learning, not certification)
- Cannot download certificates
- Option to upgrade to paid enrollment

## Course Access Controls

### Public vs Private Courses

#### Public Courses
```
Public: True
```
- Listed in course catalog
- Visible to all users
- Searchable
- SEO optimized

#### Private Courses
```
Public: False
```
- Hidden from public catalog
- Direct link access only
- Invitation-based enrollment
- Internal training use

### Course Status Management

#### Draft Status
```
Status: draft
```
- Course under development
- Not visible to students
- Allows content creation and testing
- Can be switched to other statuses

#### Open Status
```
Status: open
```
- Active and accepting enrollments
- Students can join (if free) or purchase (if paid)
- All features functional
- Standard operational state

#### Closed Status
```
Status: closed
```
- No new enrollments accepted
- Existing students maintain access
- Course content remains available
- Useful for retired courses

#### Finalized Status
```
Status: finalized
```
- Course permanently closed
- No new enrollments
- Existing access may be restricted
- Archive state

## Enrollment Controls

### Capacity Management

#### Unlimited Enrollment
```
Limited: False
Capacity: N/A
```
- No enrollment restrictions
- Suitable for self-paced courses
- Scalable content delivery

#### Limited Enrollment
```
Limited: True
Capacity: [Number]
```
- Restricts enrollment to specified number
- First-come, first-served basis
- Useful for instructor-led courses
- Creates exclusivity

### Date-Based Controls

#### Course Dates
```
Start Date: [YYYY-MM-DD]
End Date: [YYYY-MM-DD]
```
- **Start Date**: When course becomes available
- **End Date**: Course completion deadline
- **Automatic Enforcement**: System manages access based on dates

#### Enrollment Periods
- **Early Bird**: Open enrollment before start date
- **Regular**: Enrollment during course period
- **Late**: Allow late enrollments (if configured)

## Advanced Configuration Options

### Course Levels and Prerequisites

#### Difficulty Levels
```
Level: 0-3
0: Introductory
1: Beginner  
2: Intermediate
3: Advanced
```

#### Duration Estimation
```
Duration: [Hours]
```
- Helps students plan their time
- Sets expectations
- Used for progress tracking

### Course Modality Settings

#### Self-Paced Configuration
```
Modality: self_paced
Forum Enabled: False (automatically disabled)
```
- **Individual Learning**: Students progress independently
- **No Fixed Schedule**: Learn at own pace
- **Flexible Deadlines**: No time pressure
- **Ideal For**: Skill-based training, certification prep

#### Time-Based Configuration
```
Modality: time_based
Forum Enabled: True/False
Start Date: Required
End Date: Required
```
- **Structured Learning**: Fixed schedule and deadlines
- **Cohort Experience**: Students learn together
- **Community Building**: Forum interactions encouraged
- **Ideal For**: Academic courses, group projects

#### Live Configuration
```
Modality: live
Forum Enabled: True
Meeting Sessions: Configured
```
- **Real-Time Instruction**: Live sessions with instructor
- **Interactive Learning**: Direct Q&A and discussions
- **Scheduled Sessions**: Fixed meeting times
- **Ideal For**: Workshops, seminars, masterclasses

## Marketing and Promotion

### Course Promotion
```
Promoted: True
Promotion Date: [YYYY-MM-DD HH:MM:SS]
```
- **Homepage Feature**: Course appears in promoted section
- **Increased Visibility**: Higher placement in listings
- **Marketing Tool**: Drive enrollment to specific courses

### Course Branding
- **Cover Image**: Attractive visual representation
- **Course Logo**: Branding consistency
- **Color Scheme**: Matches your brand (if customized)

## Integration Settings

### PayPal Configuration

For paid courses, ensure PayPal is properly configured:

#### Required Settings
- PayPal Business Account
- API Credentials configured in NOW-LMS
- Currency settings match your locale
- Test mode for development

#### Payment Processing
- **Immediate**: Instant enrollment upon payment
- **Verification**: Optional manual verification step
- **Refund Support**: Handle refund requests

### Certificate Integration
```
Certificate: True
Certificate Template: [Template ID]
```
- Links course completion to certificate generation
- Customizable templates
- Automated delivery system

## Configuration Best Practices

### Course Planning
1. **Define Learning Objectives**: Clear goals and outcomes
2. **Choose Appropriate Model**: Free vs Paid vs Auditable
3. **Set Realistic Duration**: Based on content depth
4. **Plan Capacity**: Balance exclusivity with accessibility

### Pricing Strategy
1. **Market Research**: Compare similar courses
2. **Value Proposition**: Justify pricing with quality content
3. **Audit Option**: Consider offering audit access
4. **Promotional Pricing**: Use for course launches

### Access Management
1. **Start with Draft**: Test thoroughly before publishing
2. **Gradual Rollout**: Consider limited initial capacity
3. **Monitor Enrollments**: Track conversion rates
4. **Adjust as Needed**: Modify settings based on feedback

## Troubleshooting Common Issues

### Enrollment Problems
- **Check Course Status**: Must be "open" for enrollments
- **Verify Public Setting**: Course must be public unless invitation-based
- **Capacity Limits**: Ensure capacity isn't reached

### Payment Issues
- **PayPal Configuration**: Verify API settings
- **Currency Mismatch**: Ensure currency settings are correct
- **Test Payments**: Use PayPal sandbox for testing

### Access Problems
- **Date Restrictions**: Check if course dates allow access
- **Student Status**: Verify student enrollment status
- **Technical Issues**: Check system logs for errors

## Next Steps

Once your course is properly configured:
- [Sections and Resources](sections-resources.md) - Add your course content
- [Forum and Messaging](forum-messaging.md) - Set up student communication
- [Certificate Customization](certificate-customization.md) - Design completion certificates