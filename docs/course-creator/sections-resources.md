# Sections and Resources

This guide covers how to organize your course content into sections and add various types of learning resources in NOW-LMS.

## Course Structure Overview

Courses in NOW-LMS are organized hierarchically:

```
Course
├── Section 1
│   ├── Resource 1 (Video)
│   ├── Resource 2 (PDF)
│   └── Resource 3 (Quiz)
├── Section 2
│   ├── Resource 1 (Audio)
│   ├── Resource 2 (Text)
│   └── Resource 3 (Slideshow)
└── Section 3
    ├── Resource 1 (Meeting)
    ├── Resource 2 (Image)
    └── Resource 3 (HTML)
```

## Managing Course Sections

### Creating Sections

Sections help organize your course content into logical modules or chapters.

#### Section Properties
- **Name**: Clear, descriptive section title
- **Description**: Brief overview of section content
- **Order**: Sequential position in course
- **Visibility**: Public or hidden from students
- **Prerequisites**: Require completion of previous sections

#### Section Best Practices
1. **Logical Grouping**: Group related concepts together
2. **Progressive Difficulty**: Start simple, increase complexity
3. **Balanced Length**: Aim for 3-7 resources per section
4. **Clear Objectives**: Define what students will learn

### Section Configuration

#### Visibility Settings
```
Public: True/False
```
- **Public**: Visible to enrolled students
- **Hidden**: Instructor-only visibility (for preparation)

#### Prerequisites
- Require completion of specific sections
- Ensure sequential learning progression
- Prevent students from skipping ahead

## Resource Types

NOW-LMS supports eight different resource types to create diverse learning experiences:

### 1. YouTube Videos

Embed YouTube videos directly into your course content.

#### Configuration
- **YouTube URL**: Full video URL or video ID
- **Start Time**: Optional timestamp to begin playback
- **Player Options**: Autoplay, controls, privacy settings

#### Best Practices
- Use high-quality, relevant videos
- Provide transcripts when possible
- Include discussion questions after videos
- Check video availability and permissions

#### Example Usage
```
Resource Type: Video
Source: YouTube
URL: https://www.youtube.com/watch?v=VIDEO_ID
Description: Introduction to the main concepts
```

### 2. PDF Files

Upload and share PDF documents with your students.

#### Supported Features
- **File Upload**: Direct PDF upload to platform
- **Download Control**: Allow/restrict downloading
- **Inline Viewing**: PDFs display within the course
- **Search Integration**: Text content becomes searchable

#### File Requirements
- Maximum file size: 50MB (configurable)
- Supported format: PDF only
- Recommended: Optimized for web viewing

#### Best Practices
- Optimize PDFs for web viewing
- Include bookmarks for navigation
- Ensure text is selectable (not image-based)
- Provide alternative formats for accessibility

### 3. Audio Files

Add audio content like lectures, podcasts, or music.

#### Supported Formats
- MP3 (recommended)
- WAV
- OGG
- M4A

#### Features
- **Built-in Player**: Audio controls within course
- **Progress Tracking**: Monitor student listening progress
- **Download Options**: Allow/restrict audio downloads
- **Transcripts**: Optional text transcriptions

#### Best Practices
- Use clear, high-quality audio
- Keep files reasonably sized (under 100MB)
- Provide transcripts for accessibility
- Include chapter markers for long recordings

### 4. Images

Visual content to support learning objectives.

#### Supported Formats
- JPEG/JPG
- PNG
- GIF
- SVG
- WebP

#### Features
- **Responsive Display**: Automatic sizing for different devices
- **Zoom Functionality**: Click to enlarge images
- **Alt Text**: Accessibility descriptions
- **Gallery Mode**: Multiple images in sequence

#### Best Practices
- Optimize images for web (reasonable file sizes)
- Use descriptive alt text
- Choose appropriate image formats
- Ensure images support your learning objectives

### 5. Text Content

Rich text content with formatting options.

#### Formatting Features
- **Markdown Support**: Rich formatting with Markdown syntax
- **HTML Support**: Advanced formatting options
- **Link Integration**: External and internal links
- **Code Syntax**: Programming code highlighting

#### Content Types
- Lesson text and explanations
- Instructions and guidelines
- Reading materials
- Reference documentation

#### Best Practices
- Use clear, concise language
- Break text into digestible sections
- Include headings and bullet points
- Add relevant links and references

See the [Markdown Formatting Guide](markdown-guide.md) for detailed syntax information.

### 6. HTML Content

Custom HTML for advanced content presentation.

#### Use Cases
- Interactive demonstrations
- Custom layouts and designs
- Embedded third-party content
- Advanced formatting needs

#### Features
- **Full HTML Support**: Complete HTML/CSS/JavaScript
- **Responsive Design**: Mobile-friendly content
- **External Resources**: Link to CSS and JS files
- **Security**: Sanitized to prevent malicious code

#### Best Practices
- Test content on multiple devices
- Ensure accessibility compliance
- Use semantic HTML structure
- Optimize for loading speed

### 7. Meeting Sessions

Schedule and manage live sessions with students.

#### Meeting Types
- **Video Conferences**: Zoom, Google Meet, Microsoft Teams
- **Webinars**: Large group presentations
- **Office Hours**: One-on-one student meetings
- **Group Sessions**: Small group discussions

#### Configuration
- **Meeting Platform**: Choose video conferencing tool
- **Date and Time**: Schedule with timezone support
- **Duration**: Estimated session length
- **Access Links**: Automatic link generation
- **Recording**: Optional session recording

#### Features
- **Calendar Integration**: Add to student calendars
- **Reminder Notifications**: Email reminders before sessions
- **Attendance Tracking**: Monitor student participation
- **Recording Access**: Post-session video access

### 8. Slide Shows

Create interactive presentations within your course.

#### Slide Show Features
- **Custom Templates**: Choose from available designs
- **Multi-slide Support**: Create comprehensive presentations
- **Transition Effects**: Smooth slide transitions
- **Navigation Controls**: Student-controlled progression
- **Progress Tracking**: Monitor slide completion

#### Slide Types
- **Title Slides**: Course and section introductions
- **Content Slides**: Main learning material
- **Quiz Slides**: Interactive questions
- **Summary Slides**: Key takeaway reviews

For detailed slideshow creation instructions, see [Slideshow Setup Guide](slideshow-setup.md).

## Resource Management

### Adding Resources to Sections

1. **Navigate to Section**: Open the target course section
2. **Add Resource**: Click "Add New Resource"
3. **Select Type**: Choose from the 8 resource types
4. **Configure Resource**: Set up type-specific options
5. **Set Properties**: Name, description, visibility
6. **Save and Test**: Verify resource works correctly

### Resource Properties

#### Common Properties
- **Name**: Clear, descriptive title
- **Description**: Brief explanation of resource purpose
- **Order**: Position within section
- **Visibility**: Public/hidden status
- **Prerequisites**: Required prior completion

#### Advanced Properties
- **Downloadable**: Allow students to download content
- **Mandatory**: Required for section completion
- **Time Tracking**: Monitor time spent on resource
- **Completion Criteria**: Define when resource is "complete"

### Progress Tracking

#### Student Progress
- **Resource Completion**: Individual resource status
- **Section Progress**: Overall section completion percentage
- **Course Progress**: Total course advancement
- **Time Tracking**: Time spent on each resource

#### Instructor Analytics
- **Engagement Metrics**: Most/least popular resources
- **Completion Rates**: Resource completion statistics
- **Time Analysis**: Average time spent per resource
- **Student Performance**: Individual and group progress

## Content Organization Best Practices

### Pedagogical Structure

#### Learning Progression
1. **Introduction**: Course and section overview
2. **Core Content**: Main learning materials
3. **Practice**: Interactive exercises and quizzes
4. **Review**: Summary and key takeaways
5. **Assessment**: Evaluate understanding

#### Resource Sequencing
- Start with overview materials (text/video)
- Provide detailed content (PDFs, audio)
- Include interactive elements (quizzes, discussions)
- End with practice and assessment

### Technical Considerations

#### File Management
- **Naming Convention**: Use consistent, descriptive names
- **File Organization**: Group related files logically
- **Size Optimization**: Keep files reasonably sized
- **Format Standardization**: Use consistent file formats

#### Performance Optimization
- Optimize large files before uploading
- Use progressive loading for video content
- Implement caching for frequently accessed resources
- Monitor resource loading times

### Accessibility

#### Universal Design
- Provide alternative formats for all media
- Include captions for video content
- Add transcripts for audio resources
- Use descriptive link text and alt attributes

#### Mobile Compatibility
- Test resources on mobile devices
- Ensure responsive design for all content
- Optimize file sizes for mobile connections
- Consider mobile-specific navigation

## Common Resource Issues

### Upload Problems
- **File Size**: Check maximum upload limits
- **Format Support**: Verify file format compatibility
- **Permissions**: Ensure proper upload permissions
- **Storage Space**: Check available storage capacity

### Playback Issues
- **Browser Compatibility**: Test across different browsers
- **Plugin Requirements**: Ensure necessary plugins are available
- **Network Issues**: Consider connection speed requirements
- **Device Limitations**: Test on various devices

### Access Problems
- **Visibility Settings**: Check resource visibility configuration
- **Prerequisites**: Verify prerequisite completion
- **Enrollment Status**: Confirm student enrollment
- **Technical Permissions**: Check system access rights

## Next Steps

Now that you understand resource management:
- [Markdown Formatting Guide](markdown-guide.md) - Learn rich text formatting
- [Slideshow Setup](slideshow-setup.md) - Create interactive presentations
- [Certificate Customization](certificate-customization.md) - Configure completion rewards