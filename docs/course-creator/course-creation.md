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

### Course Level
Choose the appropriate difficulty level:
- **0 - Introductory**: No prior knowledge required
- **1 - Beginner**: Basic familiarity helpful
- **2 - Intermediate**: Some experience recommended
- **3 - Advanced**: Significant prior knowledge required

### Course Duration
- Set estimated completion time in hours
- Helps students plan their learning schedule

### Course Modality
Select the learning format:

#### Self-Paced
```
- Students learn independently
- No fixed schedule
- Forums automatically disabled
- Best for: Individual learning, skill development
```

#### Time-Based
```
- Fixed start and end dates
- Structured schedule
- Forums enabled for interaction
- Best for: Cohort learning, group projects
```

#### Live
```
- Real-time instruction
- Meeting sessions included
- Interactive discussions
- Best for: Workshops, seminars
```

## Step 3: Payment Configuration

### Free Course Setup
1. Set `Paid` status to `False`
2. Students can enroll immediately
3. Full access to all materials
4. Certificate eligibility enabled

### Paid Course Setup
1. Set `Paid` status to `True`
2. Enter course price in your currency
3. Configure PayPal integration (see [Payment Setup](../payments.md))
4. Set `Auditable` option if desired

### Audit Mode
When enabled for paid courses:
- Students can access content without payment
- No certificate eligibility
- Useful for course previews or trial access

## Step 4: Course Capacity and Availability

### Enrollment Limits
- **Unlimited**: Leave `Limited` unchecked
- **Limited**: Check `Limited` and set `Capacity` number

### Course Dates (Time-Based/Live Courses)
- **Start Date**: When course becomes available
- **End Date**: Course completion deadline
- **Registration Period**: Can be set before start date

## Step 5: Certificate Configuration

1. **Enable Certificates**: Check `Certificate` option
2. **Choose Template**: Select from available certificate templates
3. **Custom Templates**: Create custom designs (see [Certificate Customization](certificate-customization.md))

### Default Certificate Templates
- **Basic**: Simple text-based certificate
- **Professional**: Formal business style
- **Academic**: University-style diploma
- **Creative**: Colorful design with graphics

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