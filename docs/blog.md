# Blog

The NOW LMS includes an integrated blog system that allows administrators and content creators to publish articles, announcements, and educational content.

## Blog Features

- **Article Publishing**: Create and publish blog posts with rich text formatting
- **Category Organization**: Organize posts by categories for better navigation
- **User-Friendly URLs**: SEO-friendly URLs for blog posts and categories
- **Public Access**: Blog content is publicly accessible to all visitors
- **Feature Toggle**: Blog functionality can be enabled/disabled via admin settings

## Blog Management

### Accessing the Blog System

- **Public View**: `/blog` - Public blog listing page
- **Admin Access**: Available through the admin dashboard for content management

### Configuration

The blog system can be enabled or disabled through the admin configuration:

- **Setting**: `enable_blog` in the site configuration
- **Default**: Disabled by default (like other optional features)

### Content Organization

- **Posts**: Individual blog articles with title, content, publication date
- **Categories**: Organizational structure for grouping related posts
- **Public Visibility**: All published content is visible to site visitors

## Technical Implementation

- **Routes**: Blog functionality is implemented in the blog blueprint
- **Templates**: Blog-specific templates for listing and viewing posts
- **Database**: Integrated with the main LMS database structure
- **Cache**: Blog content benefits from the application's caching system
