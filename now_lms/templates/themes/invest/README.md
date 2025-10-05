# Invest Theme A professional finance-inspired theme for NOW LMS with a green color palette that evokes trust, growth, and
prosperity. ## Theme Overview The Invest theme is designed with financial education and professional development in mind. It
features: - **Color Palette**: Green shades representing money, growth, and stability - Primary: `#2E7D32` (Forest Green) -
Secondary: `#43A047` (Emerald) - Accent: `#66BB6A` (Light Green) - Background: `#FAFFFE` (Pale Green) - **Typography**: -
Headings: Montserrat (professional, modern) - Body: Roboto (clean, readable) - **Design Elements**: - Gradient backgrounds for
visual interest - Financial icons (cash, coins, growth charts) - Card-based layouts with hover effects - Professional,
trustworthy aesthetic ## Files Structure ``` invest/ ├── header.j2 # HTML head tags and metadata ├── js.j2 # JavaScript
libraries and custom scripts ├── local_style.j2 # Theme CSS reference ├── navbar.j2 # Navigation bar with white text on green
gradient ├── notify.j2 # Alert/notification components ├── pagination.j2 # Pagination controls styled for invest theme ├──
overrides/ │ └── home.j2 # Custom home page with financial messaging └── README.md # This file ``` ## Static Assets The theme's
CSS is located in `now_lms/static/themes/invest/`: - `theme.css` - Full CSS with comments - `theme.min.css` - Minified version
for production ## Features ### Hero Section - Green gradient background (#2E7D32 to #43A047) - Professional messaging focused
on investment in education - Call-to-action buttons with high contrast - Cash/coin icon as visual element ### Feature Cards -
Clean, card-based layout - Icons representing: Growth, Certification, Flexibility - Hover effects with enhanced shadows -
Professional color scheme ### Navigation - White text on green gradient for high visibility - Smooth hover effects - Responsive
mobile menu ### Forms and Interactions - Green focus states matching theme colors - Consistent button styling - Professional
progress indicators ## Usage To activate the Invest theme: 1. Log in as an administrator 2. Navigate to Administration →
Settings → Theme 3. Select "invest" from the theme dropdown 4. Save changes ## Color Variables The theme uses CSS custom
properties for easy customization: ```css --money-primary: #2E7D32; --money-secondary: #43A047; --money-accent: #66BB6A;
--money-light: #F1F8F4; --money-background: #FAFFFE; --money-text: #1B5E20; ``` ## Browser Support - Modern browsers (Chrome,
Firefox, Safari, Edge) - Responsive design for mobile, tablet, and desktop - Graceful degradation for older browsers ##
Customization To customize colors, edit the `:root` section in `theme.css`: ```css :root { --money-primary: #2E7D32; /* Change
to your preferred primary color */ /* ... other variables ... */ } ``` ## Testing The Money theme includes automated tests:
```bash python -m pytest tests/test_endtoend.py::test_theme_functionality_comprehensive -v python -m pytest
tests/test_endtoend.py::test_theme_custom_pages -v ``` Both tests verify: - Theme files are accessible - CSS loads correctly -
Home page override works - Theme switching functions properly ## Credits - Designed for NOW LMS - Color palette inspired by
financial institutions and growth metaphors - Icons from Bootstrap Icons
