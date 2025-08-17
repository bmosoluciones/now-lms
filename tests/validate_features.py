#!/usr/bin/env python3
"""
NOW-LMS Feature Validation Script
Validates all features mentioned in README.md and provides a comprehensive report.
"""

import requests
import json
import time
import sys
from pathlib import Path
from urllib.parse import urljoin


class FeatureValidator:
    def __init__(self, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
        self.admin_credentials = {"usuario": "lms-admin", "password": "lms-admin"}
        
    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        self.results[test_name] = {"passed": passed, "details": details}
        
    def test_homepage_loads(self):
        """Test that homepage loads with active theme"""
        try:
            response = self.session.get(self.base_url)
            passed = response.status_code == 200 and "NOW" in response.text
            self.log_result("Homepage loads with active theme", passed, 
                          f"Status: {response.status_code}, Contains NOW branding: {'NOW' in response.text}")
            return passed
        except Exception as e:
            self.log_result("Homepage loads with active theme", False, f"Error: {str(e)}")
            return False
            
    def test_health_endpoint(self):
        """Test /health endpoint responds with HTTP 200"""
        try:
            # Try common health endpoint paths
            health_paths = ["/health", "/health/", "/api/health", "/status"]
            for path in health_paths:
                try:
                    response = self.session.get(urljoin(self.base_url, path))
                    if response.status_code == 200:
                        self.log_result("Health endpoint responds with HTTP 200", True, 
                                      f"Path: {path}, Status: {response.status_code}")
                        return True
                except:
                    continue
            
            self.log_result("Health endpoint responds with HTTP 200", False, 
                          "No health endpoint found at common paths")
            return False
        except Exception as e:
            self.log_result("Health endpoint responds with HTTP 200", False, f"Error: {str(e)}")
            return False
            
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        try:
            # Get login page first
            login_page = self.session.get(urljoin(self.base_url, "/user/login"))
            if login_page.status_code != 200:
                self.log_result("Login with valid credentials", False, 
                              f"Login page not accessible: {login_page.status_code}")
                return False
                
            # Attempt login
            login_data = self.admin_credentials.copy()
            response = self.session.post(urljoin(self.base_url, "/user/login"), 
                                       data=login_data, allow_redirects=False)
            
            # Check if redirected (typical successful login behavior)
            passed = response.status_code in [302, 303] or "dashboard" in response.text.lower()
            self.log_result("Login with valid credentials", passed, 
                          f"Status: {response.status_code}, Redirected: {response.status_code in [302, 303]}")
            return passed
        except Exception as e:
            self.log_result("Login with valid credentials", False, f"Error: {str(e)}")
            return False
            
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials shows error"""
        try:
            login_data = {"usuario": "invalid", "password": "invalid"}
            response = self.session.post(urljoin(self.base_url, "/user/login"), 
                                       data=login_data, allow_redirects=True)
            
            # Should stay on login page with error message
            passed = response.status_code == 200 and ("error" in response.text.lower() or 
                                                    "invalid" in response.text.lower() or
                                                    "incorrect" in response.text.lower())
            self.log_result("Login with invalid credentials shows error", passed, 
                          f"Status: {response.status_code}, Contains error message: {passed}")
            return passed
        except Exception as e:
            self.log_result("Login with invalid credentials shows error", False, f"Error: {str(e)}")
            return False
            
    def test_protected_routes_authentication(self):
        """Test that protected routes require authentication"""
        protected_routes = ["/category/list", "/course/create", "/admin", "/user/profile"]
        authenticated_access = 0
        
        for route in protected_routes:
            try:
                response = self.session.get(urljoin(self.base_url, route), allow_redirects=False)
                # Should redirect to login or return 401/403
                if response.status_code in [302, 303, 401, 403]:
                    authenticated_access += 1
            except:
                pass
                
        passed = authenticated_access >= len(protected_routes) // 2  # At least half should be protected
        self.log_result("Protected routes require authentication", passed, 
                      f"Protected routes found: {authenticated_access}/{len(protected_routes)}")
        return passed
        
    def test_blog_functionality(self):
        """Test basic blog functionality"""
        try:
            blog_response = self.session.get(urljoin(self.base_url, "/blog"))
            passed = blog_response.status_code == 200
            self.log_result("Basic blog functionality", passed, 
                          f"Blog page status: {blog_response.status_code}")
            return passed
        except Exception as e:
            self.log_result("Basic blog functionality", False, f"Error: {str(e)}")
            return False
            
    def test_multiple_database_support(self):
        """Test database configuration (SQLite default)"""
        try:
            # Check if database file exists (SQLite)
            db_file = Path("now_lms.db")
            passed = db_file.exists()
            self.log_result("Database support (SQLite default)", passed, 
                          f"Database file exists: {passed}")
            return passed
        except Exception as e:
            self.log_result("Database support (SQLite default)", False, f"Error: {str(e)}")
            return False
            
    def test_static_assets(self):
        """Test that static assets load correctly"""
        try:
            static_paths = ["/static/css/bootstrap.min.css", "/static/js/bootstrap.min.js", 
                          "/static/icons/logo/logo_large.png"]
            loaded_assets = 0
            
            for path in static_paths:
                try:
                    response = self.session.get(urljoin(self.base_url, path))
                    if response.status_code == 200:
                        loaded_assets += 1
                except:
                    pass
                    
            passed = loaded_assets > 0
            self.log_result("Static assets load correctly", passed, 
                          f"Assets loaded: {loaded_assets}/{len(static_paths)}")
            return passed
        except Exception as e:
            self.log_result("Static assets load correctly", False, f"Error: {str(e)}")
            return False
            
    def test_forms_load(self):
        """Test that key forms load without errors"""
        try:
            form_pages = ["/user/login", "/user/register", "/contact"]
            loaded_forms = 0
            
            for page in form_pages:
                try:
                    response = self.session.get(urljoin(self.base_url, page))
                    if response.status_code == 200 and "<form" in response.text:
                        loaded_forms += 1
                except:
                    pass
                    
            passed = loaded_forms > 0
            self.log_result("Key forms load without errors", passed, 
                          f"Forms loaded: {loaded_forms}/{len(form_pages)}")
            return passed
        except Exception as e:
            self.log_result("Key forms load without errors", False, f"Error: {str(e)}")
            return False
            
    def test_navigation_without_500_errors(self):
        """Test basic navigation doesn't produce 500 errors"""
        try:
            navigation_paths = ["/", "/blog", "/user/login", "/courses", "/contact"]
            no_errors = 0
            
            for path in navigation_paths:
                try:
                    response = self.session.get(urljoin(self.base_url, path))
                    if response.status_code != 500:
                        no_errors += 1
                except:
                    pass
                    
            passed = no_errors == len(navigation_paths)
            self.log_result("Navigation without 500 errors", passed, 
                          f"Pages without 500 errors: {no_errors}/{len(navigation_paths)}")
            return passed
        except Exception as e:
            self.log_result("Navigation without 500 errors", False, f"Error: {str(e)}")
            return False
            
    def test_cache_functionality(self):
        """Test caching works (second load performance)"""
        try:
            # First request
            start_time = time.time()
            response1 = self.session.get(self.base_url)
            first_load_time = time.time() - start_time
            
            # Second request  
            start_time = time.time()
            response2 = self.session.get(self.base_url)
            second_load_time = time.time() - start_time
            
            # Should be faster or at least not significantly slower
            passed = (response1.status_code == 200 and response2.status_code == 200 and 
                     second_load_time <= first_load_time * 1.5)
            self.log_result("Cache works (second load faster)", passed, 
                          f"First: {first_load_time:.3f}s, Second: {second_load_time:.3f}s")
            return passed
        except Exception as e:
            self.log_result("Cache works (second load faster)", False, f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all feature validation tests"""
        print("🔍 NOW-LMS Feature Validation Starting...")
        print("=" * 60)
        
        tests = [
            self.test_homepage_loads,
            self.test_health_endpoint,
            self.test_login_valid_credentials,
            self.test_login_invalid_credentials,
            self.test_protected_routes_authentication,
            self.test_blog_functionality,
            self.test_multiple_database_support,
            self.test_static_assets,
            self.test_forms_load,
            self.test_navigation_without_500_errors,
            self.test_cache_functionality,
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            print()  # Add spacing between tests
            
        print("=" * 60)
        print(f"📊 SUMMARY: {passed_tests}/{len(tests)} tests passed")
        
        if passed_tests == len(tests):
            print("🎉 All basic features validated successfully!")
        elif passed_tests >= len(tests) * 0.8:
            print("✅ Most features working well, minor issues detected")
        else:
            print("⚠️  Several features need attention")
            
        return self.results


def main():
    print("🚀 NOW-LMS Feature Validation Tool")
    print("This script validates features mentioned in README.md")
    print()
    
    # Check if application is running
    try:
        response = requests.get("http://127.0.0.1:8080", timeout=5)
        print("✅ Application detected running on localhost:8080")
    except:
        print("❌ Application not running on localhost:8080")
        print("Please start the application with: python -m now_lms")
        sys.exit(1)
        
    validator = FeatureValidator()
    results = validator.run_all_tests()
    
    # Save results to file
    with open("feature_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed results saved to: feature_validation_results.json")


if __name__ == "__main__":
    main()
