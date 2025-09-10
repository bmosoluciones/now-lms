# Overview

NOW-LMS is a comprehensive Learning Management System built with Python Flask that provides a complete online education platform. The system supports course creation and management, user authentication, payments, certifications, evaluations, master classes, and a blog system. It's designed to be simple to install, use, configure, and maintain while offering features comparable to commercial platforms like Thinkific and Teachable.

The platform supports multiple user roles (students, instructors, moderators, administrators), flexible course structures with required/optional/alternative resources, and various content types including videos, audio with subtitle support, documents, and interactive evaluations.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Python Flask microframework with modular blueprint architecture
- **ORM**: SQLAlchemy for database abstraction and management
- **Database Migrations**: Flask-Alembic for schema versioning and updates
- **Authentication**: Flask-Login with Argon2 password hashing for security
- **Authorization**: Role-based access control with decorators for different user types

## Frontend Architecture
- **UI Framework**: Bootstrap 5 for responsive design and components
- **JavaScript**: Alpine.js for reactive frontend interactions
- **Templating**: Jinja2 templates with a flexible theming system (13 built-in themes)
- **Static Assets**: NPM-managed frontend dependencies with build optimization
- **Internationalization**: Flask-Babel for multi-language support

## Data Storage Solutions
- **Primary Database**: SQLAlchemy with support for SQLite (development), PostgreSQL, and MySQL/MariaDB
- **File Uploads**: Flask-Reuploaded for handling course resources, images, and documents
- **Caching**: Configurable caching system supporting Redis, Memcached, or filesystem-based cache

## Content Management
- **Course Structure**: Hierarchical organization with courses, sections, and resources
- **Resource Types**: Support for videos, audio (with VTT subtitles), PDFs, images, evaluations, and external links
- **Learning Paths**: Flexible resource requirements (required, optional, alternative) for personalized learning
- **Rich Content**: Markdown support with Flask-MDE for content creation

## Authentication and Authorization
- **User Management**: Multi-role system (admin, instructor, moderator, student)
- **Password Security**: Argon2-CFFI for secure password hashing
- **Session Management**: Flask-Login for user session handling
- **Access Control**: Decorator-based permissions with role-specific route protection
- **Email Verification**: Built-in email verification system with configurable SMTP

## Payment and Monetization
- **Payment Processing**: PayPal integration for course payments
- **Ad Integration**: Google AdSense support with strategic placement (free courses only)
- **Coupon System**: Discount codes and promotional pricing
- **Audit Access**: Preview mode for potential students

## Assessment and Certification
- **Evaluations**: Built-in evaluation system with various question types
- **Certificates**: PDF certificate generation using WeasyPrint
- **Progress Tracking**: Student progress monitoring and completion tracking
- **Calendar Integration**: Event management for scheduled activities

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework and related extensions (Flask-Login, Flask-Mail, Flask-WTF, Flask-Babel)
- **SQLAlchemy**: Database ORM for data persistence and relationships
- **Alembic**: Database migration management
- **Waitress**: WSGI server for production deployment

## Security and Encryption
- **Argon2-CFFI**: Modern password hashing algorithm
- **Cryptography**: Encryption utilities for sensitive data
- **PyJWT**: JSON Web Token handling for secure communications

## Content Processing
- **WeasyPrint**: PDF generation for certificates and reports
- **Markdown**: Content formatting and rich text processing
- **Bleach**: HTML sanitization for user-generated content
- **Python-Slugify**: URL-friendly slug generation

## Payment and External Services
- **PayPal API**: Payment processing integration
- **Redis**: Optional caching and session storage
- **SMTP Services**: Email delivery for notifications and verification

## Development and Deployment
- **pytest**: Comprehensive testing framework with fixtures
- **Prettier**: Frontend code formatting
- **Black/Ruff**: Python code formatting and linting
- **Docker**: Containerization support with OCI images
- **NPM**: Frontend dependency management

## Database Drivers
- **pg8000**: PostgreSQL database connectivity (pure Python)
- **mysql-connector-python**: MySQL/MariaDB support (optional)
- **SQLite**: Built-in support for development and small deployments

## Additional Utilities
- **QRCode**: QR code generation for course sharing
- **python-ulid/cuid2**: Unique identifier generation
- **Requests**: HTTP client for external API integrations
- **Babel**: Internationalization and localization support