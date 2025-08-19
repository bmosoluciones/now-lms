# Certificate Customization Guide

This comprehensive guide covers designing and configuring custom certificates in NOW-LMS using CSS and HTML to create professional, personalized completion certificates.

## Overview

NOW-LMS certificate system allows complete customization of certificate designs using HTML templates and CSS styling. Certificates are automatically generated when students complete course requirements and can be downloaded as PDF documents.

## Certificate Architecture

### Components

```
Certificate System
├── HTML Template
│   ├── Layout Structure
│   ├── Dynamic Content Fields
│   └── Styling Hooks
├── CSS Styling
│   ├── Typography
│   ├── Colors and Branding
│   └── Layout and Positioning
├── Dynamic Data
│   ├── Student Information
│   ├── Course Details
│   └── Completion Data
└── PDF Generation
    ├── Page Settings
    ├── Print Optimization
    └── Download Delivery
```

### Certificate Types

#### Academic Certificates
- Traditional diploma-style design
- Formal typography and layout
- Institution branding
- Suitable for educational institutions

#### Professional Certificates
- Business-oriented design
- Corporate branding elements
- Modern, clean appearance
- Ideal for professional development

#### Creative Certificates
- Artistic and colorful designs
- Custom graphics and imagery
- Unique layouts
- Perfect for creative courses

#### Minimalist Certificates
- Clean, simple design
- Focus on essential information
- Elegant typography
- Suitable for any course type

## Creating Custom Certificates

### Step 1: Certificate Template Setup

Navigate to the certificate management section and create a new template:

#### Basic Template Information
```
Template Name: Professional Course Certificate
Template Code: prof_cert_v1
Description: Clean, professional certificate design
Status: Active
```

### Step 2: HTML Structure

Create the basic HTML structure for your certificate:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificate of Completion</title>
    <style>
        /* CSS will be embedded here */
    </style>
</head>
<body>
    <div class="certificate-container">
        <!-- Certificate border -->
        <div class="certificate-border">
            
            <!-- Header section -->
            <div class="certificate-header">
                <div class="logo-section">
                    <img src="{{institution_logo}}" alt="Institution Logo" class="logo">
                </div>
                <div class="title-section">
                    <h1 class="certificate-title">Certificate of Completion</h1>
                    <div class="certificate-subtitle">This is to certify that</div>
                </div>
            </div>

            <!-- Student name section -->
            <div class="recipient-section">
                <div class="recipient-name">{{student_name}}</div>
                <div class="recipient-details">has successfully completed</div>
            </div>

            <!-- Course information -->
            <div class="course-section">
                <div class="course-name">{{course_name}}</div>
                <div class="course-details">
                    <div class="course-duration">Duration: {{course_duration}} hours</div>
                    <div class="completion-date">Completed on: {{completion_date}}</div>
                </div>
            </div>

            <!-- Signature section -->
            <div class="signature-section">
                <div class="signature-block">
                    <div class="signature-line"></div>
                    <div class="signature-name">{{instructor_name}}</div>
                    <div class="signature-title">Course Instructor</div>
                </div>
                <div class="seal-section">
                    <img src="{{institution_seal}}" alt="Institution Seal" class="seal">
                </div>
            </div>

            <!-- Footer section -->
            <div class="certificate-footer">
                <div class="certificate-id">Certificate ID: {{certificate_id}}</div>
                <div class="issue-date">Issued: {{issue_date}}</div>
                <div class="verification-url">Verify at: {{verification_url}}</div>
            </div>

        </div>
    </div>
</body>
</html>
```

### Step 3: CSS Styling

Create comprehensive CSS styling for your certificate:

```css
/* Certificate container and page setup */
.certificate-container {
    width: 11in;
    height: 8.5in;
    margin: 0 auto;
    padding: 0.5in;
    background: white;
    font-family: 'Georgia', serif;
    color: #333;
    position: relative;
    box-sizing: border-box;
}

/* Certificate border and background */
.certificate-border {
    width: 100%;
    height: 100%;
    border: 8px solid #1e3a8a;
    border-radius: 15px;
    padding: 40px;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    box-shadow: inset 0 0 20px rgba(30, 58, 138, 0.1);
    position: relative;
    box-sizing: border-box;
}

/* Decorative corner elements */
.certificate-border::before,
.certificate-border::after {
    content: '';
    position: absolute;
    width: 50px;
    height: 50px;
    border: 3px solid #1e3a8a;
}

.certificate-border::before {
    top: 20px;
    left: 20px;
    border-right: none;
    border-bottom: none;
}

.certificate-border::after {
    bottom: 20px;
    right: 20px;
    border-left: none;
    border-top: none;
}

/* Header section styling */
.certificate-header {
    text-align: center;
    margin-bottom: 40px;
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 20px;
}

.logo-section {
    margin-bottom: 20px;
}

.logo {
    max-height: 80px;
    max-width: 200px;
    object-fit: contain;
}

.certificate-title {
    font-size: 36px;
    font-weight: bold;
    color: #1e3a8a;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 3px;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

.certificate-subtitle {
    font-size: 18px;
    color: #64748b;
    margin-top: 10px;
    font-style: italic;
}

/* Recipient section styling */
.recipient-section {
    text-align: center;
    margin: 40px 0;
}

.recipient-name {
    font-size: 42px;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 10px;
    border-bottom: 3px solid #1e3a8a;
    padding-bottom: 10px;
    display: inline-block;
    min-width: 400px;
    text-transform: capitalize;
}

.recipient-details {
    font-size: 20px;
    color: #475569;
    margin-top: 20px;
}

/* Course section styling */
.course-section {
    text-align: center;
    margin: 40px 0;
    background: rgba(30, 58, 138, 0.05);
    padding: 30px;
    border-radius: 10px;
    border: 2px solid #1e3a8a;
}

.course-name {
    font-size: 28px;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 20px;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.course-details {
    display: flex;
    justify-content: space-around;
    font-size: 16px;
    color: #475569;
}

.course-duration,
.completion-date {
    background: white;
    padding: 10px 20px;
    border-radius: 25px;
    border: 1px solid #1e3a8a;
    font-weight: 500;
}

/* Signature section styling */
.signature-section {
    display: flex;
    justify-content: space-between;
    align-items: end;
    margin: 60px 0 40px 0;
}

.signature-block {
    text-align: center;
    flex: 1;
}

.signature-line {
    width: 200px;
    height: 2px;
    background: #1e3a8a;
    margin: 0 auto 10px auto;
}

.signature-name {
    font-size: 18px;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 5px;
}

.signature-title {
    font-size: 14px;
    color: #64748b;
    font-style: italic;
}

.seal-section {
    flex: 0 0 auto;
    margin-left: 40px;
}

.seal {
    width: 100px;
    height: 100px;
    object-fit: contain;
    opacity: 0.8;
}

/* Footer section styling */
.certificate-footer {
    text-align: center;
    border-top: 1px solid #cbd5e1;
    padding-top: 20px;
    font-size: 12px;
    color: #64748b;
    display: flex;
    justify-content: space-between;
}

.certificate-id,
.issue-date,
.verification-url {
    flex: 1;
}

/* Print optimization */
@media print {
    .certificate-container {
        width: 100%;
        height: 100vh;
        margin: 0;
        padding: 0;
    }
    
    .certificate-border {
        border-radius: 0;
        box-shadow: none;
    }
    
    /* Remove any interactive elements */
    .verification-url {
        color: #000 !important;
    }
}

/* Responsive design for preview */
@media screen and (max-width: 1024px) {
    .certificate-container {
        width: 100%;
        max-width: 800px;
        height: auto;
        padding: 20px;
    }
    
    .certificate-title {
        font-size: 28px;
    }
    
    .recipient-name {
        font-size: 32px;
        min-width: 300px;
    }
    
    .course-name {
        font-size: 22px;
    }
    
    .signature-section {
        flex-direction: column;
        align-items: center;
        gap: 30px;
    }
    
    .seal-section {
        margin-left: 0;
    }
}
```

## Advanced Certificate Designs

### Academic Diploma Style

```css
/* Academic certificate styling */
.academic-certificate {
    background: linear-gradient(45deg, #f8f9fa, #ffffff);
    border: 12px solid #2c3e50;
    font-family: 'Times New Roman', serif;
}

.academic-seal {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    opacity: 0.05;
    width: 300px;
    height: 300px;
    z-index: 1;
}

.academic-content {
    position: relative;
    z-index: 2;
}

.academic-title {
    font-size: 48px;
    color: #2c3e50;
    text-align: center;
    margin-bottom: 30px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.latin-motto {
    font-style: italic;
    text-align: center;
    color: #7f8c8d;
    margin: 20px 0;
    font-size: 16px;
}
```

### Modern Professional Style

```css
/* Modern professional certificate */
.modern-certificate {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 20px;
}

.modern-header {
    background: rgba(255, 255, 255, 0.1);
    padding: 30px;
    border-radius: 20px 20px 0 0;
    backdrop-filter: blur(10px);
}

.modern-title {
    font-family: 'Helvetica Neue', sans-serif;
    font-weight: 300;
    font-size: 36px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.achievement-badge {
    display: inline-block;
    background: #ffd700;
    color: #333;
    padding: 10px 20px;
    border-radius: 50px;
    font-weight: bold;
    margin: 20px 0;
}

.modern-signature {
    background: rgba(255, 255, 255, 0.9);
    color: #333;
    padding: 20px;
    border-radius: 0 0 20px 20px;
}
```

### Creative Artistic Style

```css
/* Creative certificate with artistic elements */
.creative-certificate {
    background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
    border: 8px solid white;
    box-shadow: 0 0 30px rgba(0,0,0,0.3);
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.creative-elements {
    position: absolute;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.creative-shape {
    position: absolute;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
}

.shape-1 {
    width: 100px;
    height: 100px;
    top: 10%;
    left: 80%;
}

.shape-2 {
    width: 150px;
    height: 150px;
    bottom: 20%;
    left: 10%;
}

.creative-text {
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    font-family: 'Comic Sans MS', cursive;
}
```

## Dynamic Content Fields

### Available Variables

NOW-LMS provides various dynamic fields that can be used in certificate templates:

#### Student Information
```html
{{student_name}} - Full name of the student
{{student_email}} - Student's email address
{{student_id}} - Unique student identifier
{{enrollment_date}} - When student enrolled in course
```

#### Course Information
```html
{{course_name}} - Full course title
{{course_code}} - Course identifier code
{{course_duration}} - Course duration in hours
{{course_level}} - Course difficulty level
{{course_description}} - Brief course description
{{instructor_name}} - Primary instructor name
{{instructor_title}} - Instructor's title/position
```

#### Completion Data
```html
{{completion_date}} - Date course was completed
{{completion_percentage}} - Final completion percentage
{{final_grade}} - Final course grade (if applicable)
{{study_time}} - Total time spent on course
```

#### Certificate Metadata
```html
{{certificate_id}} - Unique certificate identifier
{{issue_date}} - Certificate generation date
{{verification_url}} - URL for certificate verification
{{institution_name}} - Name of issuing institution
{{institution_logo}} - URL to institution logo
{{institution_seal}} - URL to official seal
```

### Conditional Content

Use conditional statements to show content based on specific criteria:

```html
<!-- Show grade only if course has grading -->
{{#if final_grade}}
<div class="grade-section">
    <strong>Final Grade: {{final_grade}}</strong>
</div>
{{/if}}

<!-- Show honors designation for high performers -->
{{#if completion_percentage >= 95}}
<div class="honors-badge">
    <strong>Graduated with Distinction</strong>
</div>
{{/if}}

<!-- Show different messages based on completion time -->
{{#if study_time < course_duration}}
<div class="efficiency-note">
    Completed efficiently in {{study_time}} hours
</div>
{{else}}
<div class="dedication-note">
    Demonstrated dedication with {{study_time}} hours of study
</div>
{{/if}}
```

### Formatting Helpers

Apply formatting to dynamic content:

```html
<!-- Format dates -->
{{format_date completion_date "MMMM DD, YYYY"}}
{{format_date issue_date "MMM DD, YYYY"}}

<!-- Format numbers -->
{{format_number completion_percentage}}%
{{format_number study_time}}

<!-- Text transformations -->
{{uppercase student_name}}
{{titlecase course_name}}
{{lowercase student_email}}

<!-- Truncate long text -->
{{truncate course_description 100}}
```

## Certificate Templates Management

### Creating Template Variations

#### Template Inheritance
Create base templates and extend them for variations:

```html
<!-- Base template: base_certificate.html -->
<div class="certificate-base">
    <div class="header">{{> header_block}}</div>
    <div class="content">{{> content_block}}</div>
    <div class="footer">{{> footer_block}}</div>
</div>

<!-- Professional variation: professional_certificate.html -->
{{#extend "base_certificate"}}
    {{#content "header_block"}}
        <h1 class="professional-title">{{certificate_title}}</h1>
    {{/content}}
    
    {{#content "content_block"}}
        <div class="professional-content">
            <!-- Professional-specific content -->
        </div>
    {{/content}}
{{/extend}}
```

#### Template Configuration

Configure template settings and options:

```json
{
    "template_id": "professional_v2",
    "template_name": "Professional Certificate v2",
    "description": "Clean, professional design for business courses",
    "category": "professional",
    "author": "Your Organization",
    "version": "2.0",
    "created_date": "2024-01-15",
    "settings": {
        "page_size": "landscape_letter",
        "margins": {
            "top": "0.5in",
            "bottom": "0.5in",
            "left": "0.5in",
            "right": "0.5in"
        },
        "fonts": {
            "primary": "Georgia, serif",
            "secondary": "Arial, sans-serif"
        },
        "colors": {
            "primary": "#1e3a8a",
            "secondary": "#64748b",
            "accent": "#ffd700"
        },
        "features": {
            "digital_signature": true,
            "qr_verification": true,
            "watermark": false,
            "border": true
        }
    },
    "preview_data": {
        "student_name": "John Doe",
        "course_name": "Advanced Web Development",
        "completion_date": "2024-01-15",
        "instructor_name": "Jane Smith"
    }
}
```

## PDF Generation Settings

### Page Configuration

```css
/* PDF-specific styling */
@page {
    size: 11in 8.5in landscape;
    margin: 0;
    
    /* Headers and footers for PDF */
    @top-center {
        content: "Certificate of Completion";
        font-size: 10pt;
        color: #666;
    }
    
    @bottom-right {
        content: "Page " counter(page);
        font-size: 8pt;
        color: #666;
    }
}

/* Optimize for print quality */
.certificate-container {
    /* Use points for precise print measurements */
    font-size: 12pt;
    line-height: 1.2;
    
    /* Ensure crisp text rendering */
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    
    /* Optimize image rendering */
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
}
```

### Quality Settings

Configure PDF generation quality:

```json
{
    "pdf_settings": {
        "format": "A4",
        "orientation": "landscape",
        "quality": "high",
        "dpi": 300,
        "compress": false,
        "embed_fonts": true,
        "color_profile": "RGB",
        "encryption": {
            "enabled": false,
            "allow_print": true,
            "allow_copy": false,
            "allow_modify": false
        }
    }
}
```

## Security and Verification

### Digital Verification

Add verification features to certificates:

```html
<!-- QR Code for verification -->
<div class="verification-section">
    <div class="qr-code">
        <img src="{{generate_qr_code verification_url}}" alt="Verification QR Code">
    </div>
    <div class="verification-text">
        <p>Scan to verify certificate authenticity</p>
        <p>{{verification_url}}</p>
    </div>
</div>

<!-- Security watermark -->
<div class="security-watermark">
    <img src="{{institution_seal}}" alt="Security Seal" class="watermark-image">
</div>
```

### Certificate Validation

Implement validation checks:

```javascript
// Certificate validation system
class CertificateValidator {
    static validateCertificate(certificateId) {
        return fetch(`/api/certificates/validate/${certificateId}`)
            .then(response => response.json())
            .then(data => {
                if (data.valid) {
                    return {
                        valid: true,
                        student: data.student_name,
                        course: data.course_name,
                        completion_date: data.completion_date,
                        institution: data.institution_name
                    };
                } else {
                    return { valid: false, message: data.error };
                }
            });
    }
}
```

## Testing and Preview

### Template Testing

Test certificate templates thoroughly:

#### Preview System
1. **Live Preview**: Real-time template preview
2. **Sample Data**: Test with various student names and course titles
3. **Multiple Browsers**: Ensure cross-browser compatibility
4. **PDF Generation**: Test actual PDF output

#### Test Cases
- **Long Names**: Test with very long student names
- **Special Characters**: Unicode and accented characters
- **Different Course Types**: Various course titles and descriptions
- **Edge Cases**: Missing data, empty fields

### Quality Assurance

#### Visual Checks
- Typography clarity and readability
- Proper alignment and spacing
- Color accuracy and contrast
- Logo and image quality
- Overall design balance

#### Technical Validation
- HTML markup validation
- CSS syntax checking
- PDF generation success
- File size optimization
- Print quality verification

## Deployment and Management

### Template Deployment

Deploy templates to production:

1. **Upload Template Files**: HTML, CSS, and assets
2. **Configure Settings**: Template metadata and options
3. **Test Generation**: Generate sample certificates
4. **Assign to Courses**: Link templates to specific courses
5. **Monitor Usage**: Track certificate generation

### Version Control

Manage template versions:

```
templates/
├── professional/
│   ├── v1.0/
│   │   ├── template.html
│   │   ├── style.css
│   │   └── config.json
│   ├── v2.0/
│   │   ├── template.html
│   │   ├── style.css
│   │   ├── script.js
│   │   └── config.json
│   └── current -> v2.0/
└── academic/
    └── v1.0/
        ├── template.html
        ├── style.css
        └── config.json
```

## Best Practices

### Design Principles

#### Visual Hierarchy
- **Clear Title**: Prominent certificate title
- **Student Focus**: Emphasize student name
- **Course Information**: Clearly display course details
- **Authority**: Show institutional credibility

#### Professional Appearance
- **Consistent Branding**: Match institutional identity
- **Quality Typography**: Use readable, professional fonts
- **Balanced Layout**: Proper spacing and alignment
- **Color Scheme**: Professional color palette

### Technical Best Practices

#### Performance
- **Optimize Images**: Compress logos and seals
- **Minimize CSS**: Remove unused styles
- **Font Loading**: Use web-safe fonts or optimized web fonts
- **Efficient HTML**: Clean, semantic markup

#### Accessibility
- **Alt Text**: Provide for all images
- **Color Contrast**: Ensure sufficient contrast ratios
- **Font Sizes**: Use readable font sizes
- **Semantic HTML**: Use proper heading hierarchy

### Maintenance

#### Regular Updates
- **Template Reviews**: Periodically review and update designs
- **Compatibility Checks**: Test with new browser versions
- **Feedback Integration**: Incorporate user feedback
- **Security Updates**: Keep verification systems current

## Troubleshooting

### Common Issues

#### PDF Generation Problems
- **Font Issues**: Embed fonts or use web-safe alternatives
- **Layout Breaks**: Test print CSS thoroughly
- **Image Quality**: Use high-resolution images
- **File Size**: Optimize without losing quality

#### Template Rendering Issues
- **CSS Conflicts**: Check for conflicting styles
- **Missing Variables**: Verify all dynamic fields exist
- **Browser Differences**: Test across browsers
- **Mobile Display**: Ensure responsive design

#### Verification Problems
- **Broken Links**: Check verification URL generation
- **QR Code Issues**: Verify QR code generation
- **Database Errors**: Ensure proper data storage
- **Security Validation**: Test validation endpoints

## Next Steps

Now that you understand certificate customization:
- [Forum and Messaging](forum-messaging.md) - Celebrate achievements in course discussions
- [Moderator Management](moderator-management.md) - Manage certificate approval workflows
- [Course Configuration](course-configuration.md) - Configure certificate eligibility settings