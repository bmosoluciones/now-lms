# Course Creation Flow

This guide walks you through the complete process of creating a course in NOW-LMS, from initial setup to publishing.

## Prerequisites

Before creating your first course, ensure you have:

- **Instructor Role**: You need instructor or administrator privileges
- **Content Ready**: Course materials, learning objectives, and structure planned
- **Technical Resources**: Videos uploaded, documents prepared, images optimized

## Step 1: Create New Course

1. **Navigate to Course Management**
   - Log into your NOW-LMS dashboard
   - Go to `Courses` → `Create New Course`

2. **Basic Course Information**
   - **Course Name**: Enter a clear, descriptive title
   - **Course Code**: Unique identifier (auto-generated or custom)
   - **Short Description**: Brief summary (max 280 characters)
   - **Full Description**: Comprehensive course overview (max 1000 characters)

## Step 2: Configure Course Settings

### Basic Course Identity
Fill in the essential course information:

#### Course Information Fields
- **Course Name**: Enter a clear, descriptive title that accurately represents the course content
- **Course Code**: Create a unique identifier (e.g., "INTRO-PYTHON-2024", "ADV-MARKETING-001")
  - Must be unique across the entire system
  - Used in URLs and course references
  - Cannot be changed after course creation
- **Short Description**: Write a compelling summary (displays in course listings)
  - Keep it concise but informative
  - Focus on key benefits and outcomes
  - Used in course previews and search results

### Course Level and Duration
Set the appropriate course difficulty and time commitment:

#### Course Level Options
Choose the appropriate difficulty level:
- **0 - Introductory (Introductorio)**: No prior knowledge required, perfect for complete beginners
- **1 - Beginner (Principiante)**: Basic familiarity helpful, minimal background needed
- **2 - Intermediate (Intermedio)**: Some experience recommended, moderate expertise required
- **3 - Advanced (Avanzado)**: Significant prior knowledge required, expert-level content

#### Course Duration
- Set estimated completion time in hours
- Helps students plan their learning schedule
- Used for progress tracking and scheduling
- Consider including both active learning time and practice time

### Course Visibility and Access Control

#### Public Course Settings
- **Public Course**: Toggle to control course visibility
  - ✅ **Enabled**: Course appears in public catalog for all users to discover
  - ❌ **Disabled**: Course is private and requires direct enrollment or invitation
  - Hidden courses can still be accessed via direct link if users have the URL

### Course Modality Options
Select the learning format that best fits your teaching style and content:

#### Self-Paced (A su propio ritmo)
```
✅ Students learn independently at their own speed
✅ No fixed schedule or deadlines
✅ Forums automatically disabled to maintain individual focus
✅ Perfect for: Skill development, certification prep, flexible learning
❌ Limited student interaction
❌ Requires strong self-motivation
```

#### Time-Based (Con tiempo definido)
```
✅ Fixed start and end dates provide structure
✅ Scheduled content release and deadlines
✅ Forums enabled for student interaction and collaboration
✅ Cohort-based learning experience
✅ Perfect for: Group projects, peer learning, structured programs
❌ Less flexibility for busy students
❌ Requires active moderation
```

#### Live (En vivo)
```
✅ Real-time instruction with scheduled meetings
✅ Direct interaction with instructors
✅ Interactive discussions and Q&A sessions
✅ Workshop-style learning environment
✅ Perfect for: Workshops, seminars, hands-on training
❌ Requires specific time commitment
❌ May not accommodate all time zones
❌ Technical requirements for live sessions
```

## Step 3: Enrollment and Capacity Management

### Course Capacity Settings
Control how many students can enroll in your course:

#### Unlimited Enrollment
- **Limited Capacity**: Leave unchecked for unlimited enrollment
- Suitable for online courses with scalable content
- No registration restrictions
- Students can enroll anytime (based on course availability)

#### Limited Enrollment
- **Limited Capacity**: Check to enable enrollment restrictions
- **Capacity Number**: Set the maximum number of students
- **Use Cases**:
  - Workshop-style courses requiring personal attention
  - Laboratory courses with equipment limitations  
  - Small group discussions and interactive sessions
  - Courses requiring individual feedback and assessment
  
#### Enrollment Management Tips
- Consider your ability to provide support and feedback
- Factor in technical limitations (live session capacity)
- Plan for instructor-to-student ratio requirements
- Allow for some buffer in live courses for technical issues

## Step 4: Payment Configuration and Course Access

### Free Course Setup
1. **Paid Course**: Set to `False` (unchecked)
2. **Student Benefits**:
   - Immediate enrollment access
   - Full access to all course materials
   - Certificate eligibility upon completion
   - Complete learning experience at no cost

### Paid Course Setup
1. **Paid Course**: Set to `True` (checked)
2. **Price**: Enter course price in your system's configured currency
3. **Payment Integration**: Ensure PayPal is configured (see [Payment Setup](../payments.md))
4. **Revenue Model**: Consider your pricing strategy and market research

### Auditable Course Feature
When **Auditable** option is enabled for paid courses:

#### Student Experience
- **Free Access**: Students can access all course content without payment
- **Content Availability**: Course materials, videos, documents, and resources
- **Learning Experience**: Course interaction except evaluations and certification
- **No Evaluations**: Students cannot access quizzes, tests, or assessments
- **No Certificate**: Students cannot receive completion certificates
- **Upgrade Path**: Students can upgrade to paid version anytime for full access

#### Use Cases for Auditable Courses
- **Course Preview**: Let students sample content before purchasing
- **Freemium Model**: Attract students with free content, convert for certification
- **Educational Access**: Provide learning opportunities regardless of financial situation
- **Trial Period**: Allow students to evaluate course quality before committing payment
- **Corporate Training**: Companies can provide access while managing certification separately

#### Audit Mode Best Practices
- Clearly communicate what's included vs. what requires payment
- Make upgrade process simple and straightforward
- Consider offering limited-time promotions for upgrades
- Monitor conversion rates from audit to paid enrollment

## Step 5: Course Schedule and Timeline (Time-Based/Live Courses)

### Date Configuration for Structured Courses
For Time-Based and Live courses, you must set specific dates:

#### Course Start and End Dates
- **Start Date**: When the course officially begins and content becomes available
  - Students can enroll before this date (based on enrollment settings)
  - Course materials are released according to this schedule
  - Affects automated email notifications and calendar integration
  
- **End Date**: When the course concludes and final submissions are due
  - Students must complete course requirements by this date
  - Late submissions may not be accepted (configurable)
  - Certificate generation becomes available after end date
  
#### Date Setting Guidelines
- **Planning Buffer**: Allow adequate time between enrollment and start date
- **Realistic Timeline**: Ensure sufficient time for course completion
- **Time Zone Consideration**: Dates are displayed in student's local time zone
- **Holiday Awareness**: Consider holidays and cultural events in your target regions

#### Self-Paced Course Considerations
- **Start/End Dates**: Optional for self-paced courses
- **Rolling Enrollment**: Students can start anytime when dates are not set
- **Flexible Completion**: No strict deadlines unless specifically configured

### Registration and Enrollment Windows
- **Early Registration**: Allow enrollment before course start date
- **Late Registration**: Configure if students can join after start date
- **Registration Deadlines**: Set cutoff dates for enrollment (optional)

## Step 6: Certificate Configuration and Recognition

### Certificate Setup Options
Configure how students receive recognition for course completion:

#### Enable Course Certificates
1. **Issue Certificate**: Check to enable certification upon course completion
2. **Completion Requirements**: System automatically tracks based on:
   - All required resources completed
   - Minimum score achieved on assessments (if configured - not available in audit mode)
   - Final evaluation passed (if applicable - not available in audit mode)
   - Payment status (for paid courses)

#### Certificate Template Selection
Choose from available certificate designs:

##### Default Templates Available
- **Default**: Clean, professional template suitable for most courses
- **Academic**: Formal university-style diploma design
- **Professional**: Business-oriented certificate for corporate training
- **Creative**: Colorful design with modern graphics for creative courses

##### Custom Certificate Templates
- **Administrative Upload**: Custom templates can be uploaded by system administrators
- **Brand Consistency**: Incorporate organization logos and colors
- **Special Recognition**: Create unique designs for premium or specialized courses
- **Template Requirements**: Contact your administrator for custom template specifications

#### Certificate Generation Process
1. **Automatic Generation**: Certificates are created when completion criteria are met
2. **Student Access**: Students can download PDF certificates from their profile
3. **Verification**: Each certificate includes unique verification codes
4. **Digital Delivery**: Automatic email notification when certificate is available

### Certificate Validation and Verification
- **Unique Codes**: Each certificate contains a verification code
- **Online Verification**: Students and employers can verify certificate authenticity
- **Secure Storage**: Certificates are stored securely in student profiles
- **Reprint Capability**: Students can redownload certificates anytime

## Step 6: Forum and Messaging Setup

### Forum Configuration
- **Self-Paced Courses**: Forums automatically disabled
- **Time-Based/Live Courses**: Forums can be enabled
- **Benefits**: Student interaction, Q&A, peer learning

### Messaging Features
- **Student-to-Instructor**: Always available
- **Instructor Responses**: Configurable notification settings
- **Moderator Support**: Assign moderators for large courses

## Step 7: Course Promotion

### Marketing Features
- **Promoted Status**: Feature course on homepage
- **Promotional Dates**: Set promotion period
- **Course Cover**: Upload attractive cover image

### SEO Optimization
- Use descriptive course names
- Include relevant keywords in descriptions
- Add appropriate tags and categories

## Step 8: Save and Review

1. **Save Draft**: Save course as draft for later editing
2. **Review Settings**: Double-check all configurations
3. **Test Access**: Verify course behavior in different modes

## Step 9: Add Course Content

Once your course structure is created:

1. **Create Sections**: Organize content into logical modules
2. **Add Resources**: Upload materials and create interactive content
3. **Set Prerequisites**: Define section completion requirements
4. **Configure Assessments**: Add quizzes and evaluations

See [Sections and Resources](sections-resources.md) for detailed content creation guidance.

## Step 10: Publish Course

### Before Publishing Checklist
- [ ] All course information complete and accurate
- [ ] Content uploaded and organized
- [ ] Assessments created and tested
- [ ] Certificate template configured
- [ ] Payment settings verified (if applicable)
- [ ] Moderators assigned (if needed)

### Publishing Process
1. Change course status from `Draft` to `Open`
2. Set `Public` visibility to `True`
3. Announce course availability to your audience
4. Monitor initial enrollments and feedback

## Post-Publication Tasks

### Course Monitoring
- Track enrollment numbers
- Monitor student progress
- Review forum discussions
- Respond to student messages

### Continuous Improvement
- Gather student feedback
- Update content based on questions
- Add new resources as needed
- Refine course structure

## Common Issues and Solutions

### Course Not Visible
- **Check**: Public status is enabled
- **Check**: Course status is set to "Open"
- **Check**: User permissions are correct

### Payment Issues
- **Verify**: PayPal integration is configured
- **Check**: Course price is set correctly
- **Test**: Payment flow with test account

### Forum Not Available
- **Remember**: Forums are disabled for self-paced courses
- **Check**: Course modality is time-based or live
- **Verify**: Forum is enabled in course settings

### Certificate Problems
- **Ensure**: Certificate option is enabled
- **Check**: Template is selected and valid
- **Verify**: Student has completed course requirements

## Next Steps

Now that your course is created, continue with:
- [Sections and Resources](sections-resources.md) - Adding and organizing content
- [Certificate Customization](certificate-customization.md) - Creating custom certificates
- [Forum and Messaging](forum-messaging.md) - Managing student communications