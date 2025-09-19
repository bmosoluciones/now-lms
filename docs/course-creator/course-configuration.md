# Course Configuration

This comprehensive guide covers the detailed configuration options for courses in NOW-LMS, including pricing models, access controls, advanced settings, and system-wide configurations that affect course behavior.

## Course Pricing Models and Access Control

### Free Courses

Free courses provide immediate access to all students without any payment requirements, making them ideal for educational outreach and marketing.

#### Configuration Settings
```yaml
Paid: False
Price: Not applicable
Auditable: Not applicable
Certificate: Available upon completion
```

#### Features and Benefits
- **Instant Enrollment**: Students can join immediately without barriers
- **Full Content Access**: Complete access to all course materials and resources
- **Certificate Eligibility**: Students can earn certificates upon successful completion
- **No Payment Gateway**: No PayPal or payment configuration required
- **Maximum Reach**: Accessible to global audience regardless of financial status

#### Best Use Cases
- **Educational Outreach**: Community education and public service
- **Company Training**: Internal employee development and onboarding
- **Marketing Content**: Lead generation and brand awareness courses
- **Introductory Material**: Foundation courses that lead to paid advanced content
- **Open Education**: Contributing to open educational resources (OER)

### Paid Courses

Paid courses require payment before students can access the full course content, enabling instructors to monetize their expertise and create sustainable educational businesses.

#### Configuration Settings
```yaml
Paid: True
Price: [Amount in configured system currency]
Auditable: True/False (enables audit mode)
Certificate: Available after payment and completion
PayPal Integration: Required for payment processing
```

#### Core Features
- **Payment Protection**: Full access only after successful payment processing
- **Secure Transactions**: Integrated PayPal payment gateway with SSL security
- **Enrollment Protection**: Prevents unauthorized access to premium content
- **Revenue Generation**: Direct monetization of educational expertise
- **Purchase Analytics**: Track revenue, conversion rates, and enrollment patterns

#### Payment Processing Flow
1. **Course Discovery**: Student finds course through catalog or direct link
2. **Course Preview**: Student views description, syllabus, and any preview content
3. **Purchase Decision**: Student clicks "Enroll" or "Purchase Course" button
4. **Payment Gateway**: Secure redirect to PayPal for payment processing
5. **Verification**: Payment confirmation and account linking
6. **Course Access**: Immediate enrollment and full course access
7. **Receipt Delivery**: Automated email confirmation and receipt

### Auditable Course Model (Freemium Approach)

The auditable course feature creates a freemium model where students can access course content for free but must pay for certification.

#### Configuration Requirements
```yaml
Paid: True (must be a paid course)
Auditable: True (enables free content access)
Price: Set for certification upgrade
Certificate: Only available to paid students
```

#### Student Experience in Audit Mode
**Free Access Includes:**
- ✅ All video lectures and recorded content
- ✅ Course materials and downloadable resources
- ✅ Progress tracking and course completion
- ✅ Forum participation (if enabled)
- ❌ **No access to evaluations or assessments**
- ❌ **No certificate eligibility**
- ❌ **No verified completion credentials**

**Paid Upgrade Benefits:**
- ✅ Everything from audit mode
- ✅ Official course completion certificate
- ✅ Verified credentials for professional use
- ✅ Academic transcript eligibility

#### Strategic Use Cases for Auditable Courses
1. **Course Sampling**: Allow students to evaluate course quality before committing payment
2. **Freemium Strategy**: Attract large audiences with free content, convert percentage to paid
3. **Educational Accessibility**: Provide learning opportunities regardless of financial constraints
4. **Corporate Partnerships**: Companies provide free access, pay separately for certification
5. **Market Testing**: Validate course content and demand before full commercialization

## Advanced Course Configuration Options

### Course Capacity and Enrollment Management

#### Unlimited Enrollment (Default)
```yaml
Limited: False
Capacity: Not applicable
Enrollment: Open-ended based on course availability
```

**Characteristics:**
- Suitable for scalable online content delivery
- No registration restrictions
- Students can enroll anytime during enrollment period
- Ideal for lecture-based and self-paced courses

#### Limited Enrollment (Capacity Control)
```yaml
Limited: True
Capacity: [Maximum number of students]
Enrollment: Restricted to capacity limit
```

**Strategic Applications:**
- **Workshop-Style Courses**: Personal attention and hands-on instruction
- **Laboratory Courses**: Limited by equipment or software license availability
- **Cohort-Based Programs**: Small groups for intensive interaction and collaboration
- **Premium Courses**: Exclusive access creating perceived value
- **Live Instruction**: Technical limitations of video conferencing platforms

**Enrollment Management Features:**
- Automatic enrollment cutoff when capacity is reached
- Instructor notifications when capacity thresholds are met
- Student notifications about availability status

### Course Modality Configuration and Impact

#### Self-Paced Course Configuration
```yaml
Modalidad: "self_paced"
Forum_Enabled: False (automatically disabled)
Start_Date: Optional (rolling enrollment)
End_Date: Optional (flexible completion)
```

**System Behavior:**
- Forums automatically disabled to maintain individual focus
- Content available immediately upon enrollment
- No fixed deadlines unless specifically configured
- Progress tracking based on content consumption
- Flexible completion timeline

#### Time-Based Course Configuration
```yaml
Modalidad: "time_based"
Forum_Enabled: True (available for activation)
Start_Date: Required (course commencement)
End_Date: Required (completion deadline)
```

**System Behavior:**
- Forums available for student collaboration
- Content may be released on schedule
- Fixed deadlines for assignments and completion
- Cohort-based learning experience
- Calendar integration for deadlines

#### Live Course Configuration
```yaml
Modalidad: "live"
Forum_Enabled: True (encouraged for Q&A)
Start_Date: Required (first live session)
End_Date: Required (final session)
Meeting_Integration: Required
```

**System Behavior:**
- Meeting links and schedules integrated
- Forum enabled for session Q&A and discussions
- Recording availability post-session
- Interactive features activated

### Course Visibility and Access Control

#### Public vs. Private Course Settings

**Public Courses** (`Publico: True`):
- Visible in public course catalog
- Searchable by all users
- Appears in category and tag-based listings
- Included in site-wide course recommendations
- SEO optimized for external search engines

**Private Courses** (`Publico: False`):
- Hidden from public catalog and search
- Accessible only via direct link or invitation
- Not included in public course counts
- Requires specific URL knowledge or instructor invitation
- Ideal for:
  - Beta testing new course content
  - Exclusive corporate training
  - Invitation-only premium programs
  - Internal organization courses

## Forum and Discussion Configuration

### Forum Availability by Course Modality

The forum feature availability depends on your chosen course modality:

#### Self-Paced Courses (`Modalidad: "self_paced"`)
```yaml
Forum_Enabled: False (automatically disabled)
```
- **Automatic Disable**: Forums are automatically disabled for self-paced courses
- **Individual Focus**: Maintains focus on individual learning journey
- **No Social Pressure**: Students learn without comparing progress to others
- **Instructor Communication**: One-on-one messaging remains available

#### Time-Based and Live Courses
```yaml
Forum_Enabled: True/False (configurable by instructor)
```
- **Optional Activation**: Instructors can choose to enable or disable forums
- **Community Building**: Encourages peer interaction and collaboration
- **Q&A Support**: Students can ask questions and help each other
- **Moderation Required**: Instructors should actively monitor discussions

### Forum Configuration Options

When forums are available, you can configure:

#### Discussion Settings
- **Open Discussions**: Allow any course topic discussion
- **Structured Topics**: Create specific discussion categories
- **Q&A Format**: Question and answer style interactions

#### Moderation Features
- **Instructor Oversight**: Instructors can moderate all discussions
- **Content Guidelines**: Set community standards for discussions
- **Reporting System**: Students can report inappropriate content

## Course Promotion and Marketing Features

### Promotional Course Status

Mark courses as featured or promoted to increase visibility:

#### Promoted Course Configuration
```yaml
Promocionado: True (enables promotional features)
Fecha_Promocionado: [Timestamp for promotion start]
```

**Promotional Benefits:**
- **Homepage Featured**: Course appears in promoted/featured section
- **Enhanced Visibility**: Higher placement in course listings and search results
- **Marketing Badge**: Special promotional indicators on course cards
- **Increased Traffic**: Better discovery through enhanced placement

#### Strategic Use of Promotions
- **Course Launches**: Promote new courses for initial enrollment boost
- **Seasonal Campaigns**: Highlight relevant courses during specific periods
- **Revenue Focus**: Drive enrollment to high-value or high-margin courses
- **Community Building**: Promote courses that build engaged learning communities

### Course Branding and Visual Identity

#### Course Cover Image Management
- **Professional Images**: Upload high-quality course cover images
- **Recommended Dimensions**: 800x450px (16:9 aspect ratio) for optimal display
- **File Format Support**: JPEG, PNG, GIF, WebP, BMP, SVG formats accepted
- **File Size Limits**: Maximum 5MB per image for performance optimization
- **Visual Consistency**: Maintain brand consistency across course offerings

#### Cover Image Best Practices
- **Clear Typography**: Course title should be legible in thumbnail size
- **Brand Colors**: Use consistent color scheme across your course portfolio
- **Professional Quality**: High-resolution images project credibility
- **Mobile Optimization**: Ensure images look good on mobile devices
- **Cultural Sensitivity**: Consider global audience when selecting imagery

## Course Categorization and Discovery

### Category Assignment

Organize courses into logical categories for better student discovery:

#### Category Benefits
- **Improved Navigation**: Students can browse courses by subject area
- **Better Search**: Enhanced filtering and search capabilities
- **Organized Learning Paths**: Group related courses for progressive learning
- **Academic Structure**: Mirror traditional academic department organization

#### Category Management
- **Single Category**: Each course must be assigned to one primary category
- **Hierarchical Structure**: Categories may have subcategories for detailed organization
- **Administrative Control**: Categories are typically managed by system administrators
- **SEO Benefits**: Improved search engine optimization through structured data

### Tag System for Enhanced Discoverability

#### Multiple Tag Assignment
```yaml
Etiquetas: [multiple tags can be selected]
```
- **Multiple Tags**: Courses can have several relevant tags
- **Keyword Optimization**: Use specific, searchable terms
- **Cross-Referencing**: Tags help students find related courses
- **Skill-Based Tagging**: Tag by skills, tools, or technologies covered

#### Effective Tagging Strategies
- **Specific Terms**: Use precise, relevant keywords over generic terms
- **Technology Names**: Include specific software, programming languages, or tools
- **Skill Levels**: Tag with difficulty indicators (beginner, advanced, etc.)
- **Industry Terms**: Use industry-specific terminology for professional courses
- **Popular Keywords**: Research what terms your target audience searches for

## System-Wide Configuration Impact on Courses

### Global System Settings That Affect Course Behavior

The system administrator can configure global settings that impact all courses:

#### Navigation and Feature Availability
```yaml
enable_programs: True/False (enables program grouping)
enable_masterclass: True/False (enables masterclass content type)
enable_resources: True/False (enables downloadable resources)
enable_blog: True/False (enables integrated blog system)
```

#### File Upload Configuration
```yaml
enable_file_uploads: True/False (enables file upload capabilities)
max_file_size: [MB] (maximum file size for uploads)
```

#### Localization Settings
```yaml
moneda: [currency code] (default currency for paid courses)
lang: [language code] (default system language)
timezone: [timezone] (default timezone for dates and times)
```

#### Email Verification
```yaml
verify_user_by_email: True/False (requires email verification for enrollment)
```

### How Global Settings Affect Course Creation

#### Program Integration
- When **Programs** are enabled, courses can be grouped into learning programs
- Students can enroll in entire programs or individual courses

#### Masterclass Features
- When **Masterclass** is enabled, masterclasses can be created as standalone live sessions
- Masterclasses are independent from courses and have their own enrollment system
- Enhanced promotional features for premium content

#### Resource Downloads
- When **Resources** are enabled, courses can include downloadable materials
- Students can save course materials for offline access
- Instructors can provide supplementary resources and templates

## Advanced Configuration Scenarios

### Corporate Training Configuration
```yaml
Publico: False (private access)
Pagado: False (company-funded)
Limitado: True (controlled enrollment)
Capacidad: [department size]
Modalidad: "time_based" (structured program)
```

### Premium Certification Program
```yaml
Publico: True (market visibility)
Pagado: True (premium pricing)
Auditable: True (trial access)
Certificado: True (verified credentials)
Promocionado: True (featured placement)
Limitado: True (exclusivity)
```

### Open Educational Resource
```yaml
Publico: True (maximum visibility)
Pagado: False (free access)
Auditable: False (not applicable)
Certificado: True (completion recognition)
Modalidad: "self_paced" (flexible learning)
```

## Troubleshooting Configuration Issues

### Common Configuration Problems

#### Course Not Visible in Catalog
**Checklist:**
- ✅ Verify `Publico: True` for public visibility
- ✅ Ensure course status is "Open" (not "Draft" or "Closed")
- ✅ Check if course has required fields completed
- ✅ Confirm category assignment is valid
- ✅ Verify course dates allow current access

#### Payment Processing Issues
**Troubleshooting Steps:**
- ✅ Verify PayPal integration is configured correctly
- ✅ Check currency settings match PayPal account
- ✅ Ensure course price is set properly
- ✅ Test payment flow with sandbox/test account
- ✅ Review PayPal API credentials

#### Forum Access Problems
**Common Solutions:**
- ✅ Verify course modality allows forums (not self-paced)
- ✅ Check if forums are enabled for the specific course
- ✅ Ensure students are enrolled (not just auditing)
- ✅ Verify forum moderation settings aren't blocking access

#### Certificate Generation Issues
**Resolution Steps:**
- ✅ Confirm `Certificado: True` is enabled
- ✅ Verify certificate template is selected and valid
- ✅ Check student completion requirements are met
- ✅ Ensure student has paid status (for paid courses)
- ✅ Review certificate template file integrity

### Configuration Validation Checklist

Before publishing any course, verify:

#### Essential Configuration
- [ ] Course name and description are complete and accurate
- [ ] Course code is unique and follows naming conventions
- [ ] Appropriate category and tags are assigned
- [ ] Course level matches content difficulty
- [ ] Duration estimate is realistic

#### Access and Pricing
- [ ] Public/private setting matches intended audience
- [ ] Pricing model (free/paid/auditable) is configured correctly
- [ ] Capacity limits are appropriate for course type
- [ ] Date restrictions allow proper enrollment period

#### Features and Integration
- [ ] Certificate settings match course objectives
- [ ] Forum settings align with course modality
- [ ] Promotional settings support marketing strategy
- [ ] Payment integration is tested and functional

## Next Steps

Once your course configuration is complete:

- **[Sections and Resources](sections-resources.md)** - Add and organize your course content
- **[Forum and Messaging](forum-messaging.md)** - Set up student communication channels
- **[Certificate Customization](certificate-customization.md)** - Design completion certificates
- **[Moderator Management](moderator-management.md)** - Assign and manage course moderators

For additional configuration support, consult the system administrator or review the [FAQ](../faq.md) for common configuration questions.