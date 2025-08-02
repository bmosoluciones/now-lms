# Slideshow Setup Guide

This comprehensive guide covers creating custom slide shows in NOW-LMS, from basic presentations to advanced interactive content.

## Overview

Slideshows in NOW-LMS provide an interactive way to present course content with navigation controls, progress tracking, and engaging visual elements. Students can progress through slides at their own pace while the system tracks their progress.

## Slideshow Architecture

### Components

```
Slideshow Resource
├── Slideshow Configuration
│   ├── Template Selection
│   ├── Navigation Settings
│   └── Progress Tracking
├── Individual Slides
│   ├── Slide Content
│   ├── Slide Type
│   └── Transition Effects
└── Student Interface
    ├── Navigation Controls
    ├── Progress Indicator
    └── Completion Tracking
```

### Slideshow Types

#### Linear Presentations
- Sequential slide progression
- Students follow predetermined path
- Suitable for step-by-step tutorials

#### Non-Linear Presentations
- Students can jump between slides
- Menu-driven navigation
- Good for reference materials

#### Interactive Presentations
- Include quizzes and exercises
- Branching based on responses
- Enhanced engagement

## Creating a Slideshow

### Step 1: Add Slideshow Resource

1. **Navigate to Course Section**
2. **Add New Resource** → Select "Slide Shows"
3. **Configure Basic Settings**:
   - Resource name
   - Description
   - Visibility settings

### Step 2: Choose Slideshow Template

NOW-LMS offers several built-in templates:

#### Professional Template
```
Style: Clean, corporate design
Colors: Blue and white theme
Fonts: Sans-serif, readable
Best For: Business presentations, formal courses
```

#### Academic Template
```
Style: Traditional academic layout
Colors: Dark blue and cream
Fonts: Serif for headings, sans-serif for body
Best For: University courses, scholarly content
```

#### Creative Template
```
Style: Modern, colorful design
Colors: Vibrant, customizable palette
Fonts: Contemporary font combinations
Best For: Creative courses, engaging content
```

#### Minimal Template
```
Style: Clean, distraction-free
Colors: Monochrome with accent colors
Fonts: Simple, readable typography
Best For: Focus on content, technical subjects
```

### Step 3: Configure Slideshow Settings

#### Navigation Options
```
Linear Navigation: True/False
- True: Students must complete slides in order
- False: Allow jumping between slides

Show Slide Numbers: True/False
- Display current slide and total count

Progress Bar: True/False
- Visual progress indicator

Navigation Controls: Enabled/Disabled
- Previous/Next buttons
- Menu/Table of contents
```

#### Timing Settings
```
Auto-advance: True/False
- Automatically move to next slide

Auto-advance Delay: Seconds
- Time before auto-advancing

Minimum Time per Slide: Seconds
- Required viewing time before allowing progression
```

#### Completion Tracking
```
Track Progress: True/False
- Monitor which slides students have viewed

Require All Slides: True/False
- Students must view all slides for completion

Completion Criteria: Percentage
- Minimum percentage of slides to view
```

## Slide Types and Content

### 1. Title Slides

Use for course introductions and section headers.

#### Content Structure
```markdown
# Main Title
## Subtitle
### Author/Instructor Information

![Logo or image](logo.png)
```

#### Best Practices
- Keep titles concise and descriptive
- Use high-quality images
- Include course or section context
- Consider branding elements

### 2. Content Slides

Main instructional content with text, images, and media.

#### Text Content
```markdown
## Slide Title

Key points:
- Important concept 1
- Important concept 2
- Important concept 3

Additional details and explanations...
```

#### Mixed Media Content
```markdown
## Slide Title

![Relevant image](content-image.png)

**Key Concept**: Explanation of the concept

> Important quote or highlight

See also: [Related resource](link-to-resource)
```

### 3. List Slides

Present information in organized, digestible formats.

#### Bullet Points
```markdown
## Key Benefits

- **Benefit 1**: Detailed explanation
- **Benefit 2**: Detailed explanation  
- **Benefit 3**: Detailed explanation
```

#### Numbered Steps
```markdown
## Process Overview

1. **Step 1**: Description of first step
2. **Step 2**: Description of second step
3. **Step 3**: Description of third step
```

### 4. Image Slides

Visual content with minimal text overlay.

#### Full-Screen Images
```markdown
![Alt text](large-image.jpg)

## Optional Caption
Brief description or context
```

#### Image with Annotations
```markdown
## Diagram Explanation

![Process diagram](diagram.png)

**Key Components:**
- Component A: Function
- Component B: Function
- Component C: Function
```

### 5. Code Slides

Display programming code with syntax highlighting.

#### Code Examples
```markdown
## Code Example

```python
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count

# Usage
scores = [85, 92, 78, 96, 88]
average = calculate_average(scores)
print(f"Average score: {average}")
```

**Explanation**: This function calculates the average of a list of numbers.
```

#### Code Comparisons
```markdown
## Before vs After

**Before:**
```python
# Inefficient approach
result = []
for i in range(len(data)):
    result.append(data[i] * 2)
```

**After:**
```python
# More efficient approach
result = [x * 2 for x in data]
```
```

### 6. Quiz Slides

Interactive questions to test understanding.

#### Multiple Choice
```markdown
## Quiz Question

**Which of the following is correct?**

A) Option 1
B) Option 2  
C) Option 3
D) Option 4

<details>
<summary>Click for answer</summary>
**Answer: C** - Explanation of why option C is correct.
</details>
```

#### True/False
```markdown
## True or False

**Statement**: Python is a compiled programming language.

<details>
<summary>Click for answer</summary>
**False** - Python is an interpreted language, not compiled.
</details>
```

### 7. Summary Slides

Conclude sections with key takeaways.

#### Key Points Summary
```markdown
## Section Summary

**What we covered:**
✓ Concept 1
✓ Concept 2  
✓ Concept 3

**Next steps:**
→ Practice exercises
→ Additional readings
→ Assignment preparation
```

#### Review Questions
```markdown
## Review Questions

Before moving on, can you answer these questions?

1. What is the main purpose of...?
2. How would you implement...?
3. When should you use...?

If you can't answer these, review the previous slides.
```

## Custom Slideshow Templates

### Creating Custom Templates

#### Template Structure
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{slideshow_title}}</title>
    <link rel="stylesheet" href="custom-style.css">
</head>
<body>
    <div class="slideshow-container">
        <div class="slide-content">
            {{slide_content}}
        </div>
        <div class="navigation">
            {{navigation_controls}}
        </div>
        <div class="progress">
            {{progress_indicator}}
        </div>
    </div>
    <script src="slideshow.js"></script>
</body>
</html>
```

#### CSS Customization
```css
/* Custom slideshow styles */
.slideshow-container {
    font-family: 'Your Font', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 100vh;
}

.slide-content {
    padding: 40px;
    max-width: 800px;
    margin: 0 auto;
}

.slide-content h1 {
    font-size: 2.5em;
    margin-bottom: 20px;
    text-align: center;
}

.slide-content h2 {
    font-size: 2em;
    color: #ffd700;
    border-bottom: 2px solid #ffd700;
    padding-bottom: 10px;
}

.navigation {
    position: fixed;
    bottom: 20px;
    right: 20px;
}

.nav-button {
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid white;
    color: white;
    padding: 10px 20px;
    margin: 0 5px;
    border-radius: 25px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.nav-button:hover {
    background: white;
    color: #667eea;
}

.progress-bar {
    position: fixed;
    top: 0;
    left: 0;
    height: 4px;
    background: #ffd700;
    transition: width 0.3s ease;
}
```

#### JavaScript Functionality
```javascript
// Custom slideshow functionality
class CustomSlideshow {
    constructor() {
        this.currentSlide = 0;
        this.totalSlides = document.querySelectorAll('.slide').length;
        this.initializeNavigation();
        this.updateProgress();
    }

    initializeNavigation() {
        // Add event listeners for navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight') this.nextSlide();
            if (e.key === 'ArrowLeft') this.previousSlide();
        });
    }

    nextSlide() {
        if (this.currentSlide < this.totalSlides - 1) {
            this.currentSlide++;
            this.showSlide();
            this.updateProgress();
        }
    }

    previousSlide() {
        if (this.currentSlide > 0) {
            this.currentSlide--;
            this.showSlide();
            this.updateProgress();
        }
    }

    showSlide() {
        // Hide all slides
        document.querySelectorAll('.slide').forEach(slide => {
            slide.style.display = 'none';
        });
        
        // Show current slide
        document.querySelectorAll('.slide')[this.currentSlide].style.display = 'block';
    }

    updateProgress() {
        const progress = ((this.currentSlide + 1) / this.totalSlides) * 100;
        document.querySelector('.progress-bar').style.width = progress + '%';
        
        // Send progress to LMS
        this.reportProgress(progress);
    }

    reportProgress(progress) {
        // API call to update student progress
        fetch('/api/slideshow/progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                slideshow_id: this.slideshowId,
                progress: progress,
                current_slide: this.currentSlide
            })
        });
    }
}

// Initialize slideshow when page loads
document.addEventListener('DOMContentLoaded', () => {
    new CustomSlideshow();
});
```

### Template Configuration File

Create a template configuration to define settings:

```json
{
    "template_name": "Custom Professional",
    "template_id": "custom_professional",
    "version": "1.0",
    "description": "Professional slideshow template with custom branding",
    "author": "Your Name",
    "settings": {
        "colors": {
            "primary": "#667eea",
            "secondary": "#764ba2",
            "accent": "#ffd700",
            "text": "#ffffff"
        },
        "fonts": {
            "headings": "Roboto, sans-serif",
            "body": "Open Sans, sans-serif"
        },
        "features": {
            "auto_advance": false,
            "progress_bar": true,
            "slide_numbers": true,
            "navigation_arrows": true,
            "keyboard_navigation": true
        },
        "animations": {
            "slide_transition": "fade",
            "transition_duration": "0.3s"
        }
    },
    "files": {
        "template": "template.html",
        "styles": "style.css",
        "script": "script.js"
    }
}
```

## Advanced Features

### Interactive Elements

#### Embedded Videos
```markdown
## Video Demonstration

<video controls width="100%">
    <source src="demo-video.mp4" type="video/mp4">
    Your browser does not support the video tag.
</video>

**Key points from the video:**
- Point 1
- Point 2
```

#### Interactive Diagrams
```html
<div class="interactive-diagram">
    <svg width="400" height="300">
        <circle cx="200" cy="150" r="50" fill="#667eea" 
                onclick="showInfo('circle')" class="clickable"/>
        <rect x="100" y="100" width="80" height="60" fill="#764ba2" 
              onclick="showInfo('rectangle')" class="clickable"/>
    </svg>
    <div id="info-display"></div>
</div>
```

#### Progressive Disclosure
```markdown
## Complex Topic

**Level 1**: Basic explanation

<details>
<summary>More Details</summary>

**Level 2**: Intermediate explanation

<details>
<summary>Advanced Details</summary>

**Level 3**: Advanced explanation with technical details

</details>
</details>
```

### Branching Slideshows

Create conditional navigation based on student responses:

```javascript
class BranchingSlideshow extends CustomSlideshow {
    handleQuizResponse(answer) {
        if (answer === 'correct') {
            this.jumpToSlide('advanced_content');
        } else {
            this.jumpToSlide('review_content');
        }
    }

    jumpToSlide(slideId) {
        const targetSlide = document.getElementById(slideId);
        if (targetSlide) {
            this.currentSlide = Array.from(document.querySelectorAll('.slide')).indexOf(targetSlide);
            this.showSlide();
            this.updateProgress();
        }
    }
}
```

## Best Practices

### Content Design

#### Slide Density
- **One concept per slide**: Avoid information overload
- **6x6 rule**: Maximum 6 bullet points, 6 words each
- **Visual hierarchy**: Use headings, spacing, and emphasis effectively

#### Visual Design
- **Consistent style**: Use same fonts, colors, and layout
- **High contrast**: Ensure readability
- **Quality images**: Use high-resolution, relevant images
- **White space**: Don't overcrowd slides

### Navigation Design

#### User Experience
- **Clear controls**: Make navigation obvious
- **Feedback**: Show current position and progress
- **Accessibility**: Support keyboard navigation
- **Mobile-friendly**: Ensure touch-friendly controls

#### Progress Tracking
- **Meaningful metrics**: Track completion and time spent
- **Clear requirements**: Communicate completion criteria
- **Flexible pacing**: Allow students to control progression

### Technical Considerations

#### Performance
- **Optimize images**: Compress for web delivery
- **Lazy loading**: Load slides as needed
- **Caching**: Cache static resources
- **Responsive design**: Work on all device sizes

#### Accessibility
- **Alt text**: Provide for all images
- **Keyboard navigation**: Support arrow keys and tab
- **Screen readers**: Use semantic HTML
- **Color contrast**: Meet WCAG guidelines

## Troubleshooting

### Common Issues

#### Slides Not Displaying
- **Check file paths**: Ensure all resources are accessible
- **Validate HTML**: Check for syntax errors
- **Test JavaScript**: Verify script functionality
- **Browser compatibility**: Test across different browsers

#### Navigation Problems
- **JavaScript errors**: Check browser console for errors
- **Event listeners**: Verify click/keyboard handlers
- **Progress tracking**: Ensure API calls are working
- **CSS conflicts**: Check for style conflicts

#### Performance Issues
- **Large images**: Optimize file sizes
- **Too many slides**: Consider breaking into multiple presentations
- **Complex animations**: Simplify transitions
- **Memory usage**: Monitor browser performance

## Integration with NOW-LMS

### Progress Tracking Integration

The slideshow automatically integrates with NOW-LMS progress tracking:

```javascript
// Progress is automatically reported to the LMS
function reportSlideProgress(slideIndex, totalSlides) {
    const progress = (slideIndex + 1) / totalSlides * 100;
    
    // This function is provided by NOW-LMS
    LMS.updateResourceProgress({
        resource_id: slideshow.resourceId,
        progress_percentage: progress,
        completed: progress >= slideshow.completionThreshold
    });
}
```

### Completion Criteria

Configure how slideshow completion is determined:

- **All slides viewed**: Student must view every slide
- **Percentage-based**: Student must view X% of slides
- **Time-based**: Student must spend minimum time
- **Quiz-based**: Student must answer embedded questions

## Next Steps

Now that you understand slideshow creation:
- [Certificate Customization](certificate-customization.md) - Design completion certificates
- [Forum and Messaging](forum-messaging.md) - Encourage discussion of slideshow content
- [Markdown Formatting](markdown-guide.md) - Enhance slide content with rich formatting