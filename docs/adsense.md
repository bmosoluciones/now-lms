# AdSense Integration

NOW-LMS includes comprehensive Google AdSense integration that allows administrators to monetize free courses while providing a premium, ad-free experience for paid course users.

## Overview

The AdSense integration supports 8 specific Google-recommended ad sizes with strategic placement throughout the platform:

- **Leaderboard (728×90)** - Top-performing banner format
- **Medium Rectangle (300×250)** - Embeddable within content
- **Large Rectangle (336×280)** - High-inventory large rectangle
- **Mobile Banner (300×50)** - Mobile-friendly banner
- **Wide Skyscraper (160×600)** - Sidebar placement
- **Skyscraper (120×600)** - Traditional sidebar ad
- **Large Skyscraper (300×600)** - Large sidebar format
- **Billboard (970×250)** - Large top placement

## Business Logic

Ads are strategically displayed only when:

1. **Global ads are enabled** by administrators
2. **Course is free** (not paid)

This ensures a non-intrusive monetization strategy that respects paid course users while generating revenue from free content.

## Configuration

### Accessing AdSense Settings

1. Log in as an administrator
2. Navigate to **Settings** → **AdSense Configuration**
3. Configure your AdSense integration

### Basic Setup

1. **Publisher ID**: Enter your Google AdSense publisher ID (pub-XXXXXXXXXXXXXXXXX)
2. **Meta Tag**: Add your AdSense verification meta tag if required
3. **Enable Meta Tag**: Check if you want to include the meta tag in your site's header
4. **Show Ads Globally**: Master switch to enable/disable all ads across the platform

### Ad Code Configuration

For each ad size, you can configure specific AdSense code:

#### Leaderboard (728×90)

Best for header/footer placement. Ideal for desktop users.

```html
<script
    async
    src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXXX"
    crossorigin="anonymous"
></script>
<!-- Leaderboard -->
<ins
    class="adsbygoogle"
    style="display:inline-block;width:728px;height:90px"
    data-ad-client="ca-pub-XXXXXXXXXXXXXXXXX"
    data-ad-slot="XXXXXXXXXX"
></ins>
<script>
    ;(adsbygoogle = window.adsbygoogle || []).push({})
</script>
```

#### Medium Rectangle (300×250)

Embeddable within content. Used in course sidebars.

```html
<script
    async
    src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXXX"
    crossorigin="anonymous"
></script>
<!-- Medium Rectangle -->
<ins
    class="adsbygoogle"
    style="display:inline-block;width:300px;height:250px"
    data-ad-client="ca-pub-XXXXXXXXXXXXXXXXX"
    data-ad-slot="XXXXXXXXXX"
></ins>
<script>
    ;(adsbygoogle = window.adsbygoogle || []).push({})
</script>
```

#### Large Rectangle (336×280)

High-inventory format. Used after resource descriptions.

```html
<script
    async
    src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXXX"
    crossorigin="anonymous"
></script>
<!-- Large Rectangle -->
<ins
    class="adsbygoogle"
    style="display:inline-block;width:336px;height:280px"
    data-ad-client="ca-pub-XXXXXXXXXXXXXXXXX"
    data-ad-slot="XXXXXXXXXX"
></ins>
<script>
    ;(adsbygoogle = window.adsbygoogle || []).push({})
</script>
```

#### Mobile Banner (300×50)

Optimized for mobile devices.

#### Skyscraper Formats

Vertical ads ideal for sidebar placement:

- **Wide Skyscraper (160×600)**
- **Skyscraper (120×600)**
- **Large Skyscraper (300×600)**

#### Billboard (970×250)

Large format for prominent placement.

## Ad Placement

### Course Pages

- **Medium Rectangle (300×250)** ads appear in the course sidebar for free courses
- Ads are clearly labeled with "Publicidad" for transparency

### Resource Pages

- **Large Rectangle (336×280)** ads appear after resource descriptions for free courses
- Strategic placement that doesn't interfere with learning content

### Global Settings

- Ads only display when globally enabled AND the course is free
- All ads respect the `not curso.pagado` condition

## ads.txt Compliance

NOW-LMS automatically generates a compliant `ads.txt` file at `/ads.txt` that meets Google's requirements:

- Proper `text/plain; charset=utf-8` content-type
- Correct format: `google.com, pub-{your-publisher-id}, DIRECT, f08c47fec0942fa0`
- Graceful handling of missing publisher IDs

### Verifying ads.txt

1. In AdSense settings, click **"Verificar archivo ads.txt"**
2. This will open your site's ads.txt file in a new tab
3. Verify it contains your publisher ID in the correct format

## Theme Compatibility

The AdSense integration works across all NOW-LMS themes:

- Cambridge
- Classic
- Corporative
- Finance
- Harvard
- Ocean Blue
- Oxford
- Rose Pink

All theme template overrides have been updated to include the same strategic ad placement.

## Template Functions

The following Jinja2 functions are available in templates:

### Global Functions

- `adsense_enabled()` - Check if ads are globally enabled
- `ad_leaderboard()` - Get leaderboard ad code
- `ad_medium_rectangle()` - Get medium rectangle ad code
- `ad_large_rectangle()` - Get large rectangle ad code
- `ad_mobile_banner()` - Get mobile banner ad code
- `ad_wide_skyscraper()` - Get wide skyscraper ad code
- `ad_skyscraper()` - Get skyscraper ad code
- `ad_large_skyscraper()` - Get large skyscraper ad code
- `ad_billboard()` - Get billboard ad code

### Error Handling

All functions return empty strings when:

- Ads are disabled globally
- Ad content is missing or empty
- Database connectivity issues occur

## Best Practices

### Content Guidelines

1. **Respect User Experience**: Ads only appear on free content
2. **Clear Labeling**: All ads are labeled as "Publicidad"
3. **Strategic Placement**: Ads don't interfere with learning content
4. **Responsive Design**: Ad codes should include responsive units when possible

### Google AdSense Policies

1. Ensure your content complies with [Google AdSense Content Policies](https://support.google.com/adsense/answer/1348688)
2. Follow [Google AdSense Program Policies](https://support.google.com/adsense/answer/48182)
3. Maintain appropriate content-to-ad ratios
4. Don't encourage clicks or interactions with ads

### Performance Optimization

1. Use async loading for all ad scripts
2. Consider lazy loading for below-the-fold ads
3. Monitor Core Web Vitals impact
4. Test ad performance across different devices

## Troubleshooting

### Ads Not Displaying

1. Verify that **Show Ads Globally** is enabled
2. Ensure the course is free (not paid)
3. Check that ad codes are properly configured
4. Verify your AdSense account is approved

### ads.txt Issues

1. Check that your publisher ID is correctly entered
2. Verify the ads.txt file is accessible at your domain root
3. Ensure proper DNS and hosting configuration

### Theme Issues

1. Verify the theme supports AdSense integration
2. Check that theme overrides include updated templates
3. Clear any template caches

## Migration Notes

For existing NOW-LMS installations:

1. The AdSense integration adds new database fields automatically
2. No manual database migrations are required for alpha releases
3. Existing AdSense configurations are preserved
4. New ad size fields default to empty strings

## Support

For technical support with AdSense integration:

1. Check this documentation first
2. Verify your Google AdSense account status
3. Review Google's AdSense Help Center
4. Contact NOW-LMS support for platform-specific issues

---

**Note**: This feature requires an approved Google AdSense account. Ad revenue and performance depend on factors outside of NOW-LMS control, including content quality, traffic volume, and AdSense policies.
