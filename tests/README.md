# Comprehensive Route Testing

This directory contains comprehensive tests that visit all views exposed by the Flask app to ensure users do not encounter 404 or 500 errors.

## Test Files

### test_all_routes_comprehensive.py
This is the main comprehensive route testing implementation that:

- **Automatically discovers all routes** using Flask's URL map (discovers all 207 routes)
- **Categorizes routes** into static vs dynamic routes  
- **Tests different user roles**: anonymous, admin, regular user, instructor, moderator
- **Handles dynamic routes** with sample parameters from test data
- **Focuses on preventing 500 server errors** while allowing expected 404s for missing resources
- **Skips problematic routes** that require special setup or have known issues

**Test scenarios:**
- `test_discover_all_routes`: Verifies route discovery works
- `test_static_routes_anonymous_user`: Tests all static routes with anonymous user
- `test_static_routes_admin_user`: Tests all static routes with admin privileges  
- `test_static_routes_regular_user`: Tests all static routes with regular user
- `test_dynamic_routes_with_sample_data`: Tests dynamic routes with sample parameters
- `test_error_handling_routes`: Tests custom error pages (403, 404, 405, 500)
- `test_common_public_routes`: Tests critical public routes

### test_vistas.py
Contains traditional route testing using the manually-maintained static routes list in `x_rutas_estaticas.py`:

- `test_visit_views_anonymous_using_static_list`: Tests routes with anonymous user against expected response codes
- `test_visit_views_admin_using_static_list`: Tests routes with admin user against expected response codes

### x_rutas_estaticas.py
Manually-maintained list of static routes with expected response codes for different user roles. This provides more detailed expected behavior testing but requires manual maintenance.

## Running the Tests

```bash
# Run all comprehensive route tests
python -m pytest tests/test_all_routes_comprehensive.py -v

# Run traditional static route tests  
python -m pytest tests/test_vistas.py::test_visit_views_anonymous_using_static_list -v
python -m pytest tests/test_vistas.py::test_visit_views_admin_using_static_list -v

# Run all route-related tests
python -m pytest tests/test_vistas.py tests/test_all_routes_comprehensive.py -v
```

## Key Features

### Route Discovery
- Uses Flask's `app.url_map.iter_rules()` to automatically discover all routes
- No manual route maintenance required
- Automatically adapts to new routes added to the application

### Smart Route Skipping
Routes are intelligently skipped if they:
- Require valid JWT tokens (`/user/check_mail/<token>`)
- Need specific file paths (`/static/flask_mde/<path:filename>`)
- Have external dependencies (PayPal integration routes)
- Are POST-only and shouldn't be tested with GET
- Have known template/JavaScript dependency issues

### Error Classification
- **500+ errors**: Real server errors that indicate application bugs
- **400-499 errors**: Client errors (often expected for unauthorized access)
- **Template/data errors**: Expected when testing with sample data on dynamic routes

### Sample Data Parameters
Dynamic routes are tested using realistic sample parameters from test data:
```python
SAMPLE_PARAMS = {
    'course_code': 'now',  # Test course code
    'ulid': '01HNZXJRD65A55BJACFEFNZ88D',  # Sample ULID from test data
    'resource_code': '01HNZXA1BX9B297CYAAA4MK93V',  # Sample resource ID
    # ... more parameters
}
```

## Benefits

1. **Prevents server errors**: Ensures no 500 errors occur across the application
2. **Comprehensive coverage**: Tests all routes automatically
3. **Role-based testing**: Verifies proper authorization and redirects
4. **Maintenance-free**: Automatically adapts to new routes
5. **Fast execution**: Efficient testing without external dependencies
6. **Clear reporting**: Detailed logs of what was tested and any issues found

This testing approach ensures the Flask app provides a robust user experience without unexpected server errors or broken pages.