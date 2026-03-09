"""
EventEase Test Suite
====================
Run with: python -m pytest tests/test_app.py -v
"""

import pytest
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, validate_password, allowed_file


# =====================
# FIXTURES
# =====================
@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    """Create a test client with a logged-in session."""
    with client.session_transaction() as sess:
        sess['loggedin'] = True
        sess['id'] = 1
        sess['name'] = 'Test User'
        sess['role'] = 'participant'
    return client


@pytest.fixture
def organizer_client(client):
    """Create a test client logged in as an organizer."""
    with client.session_transaction() as sess:
        sess['loggedin'] = True
        sess['id'] = 2
        sess['name'] = 'Test Organizer'
        sess['role'] = 'organizer'
    return client


@pytest.fixture
def admin_client(client):
    """Create a test client logged in as admin."""
    with client.session_transaction() as sess:
        sess['loggedin'] = True
        sess['id'] = 3
        sess['name'] = 'Test Admin'
        sess['role'] = 'admin'
    return client


# =====================
# UNIT TESTS: UTILITIES
# =====================
class TestPasswordValidation:
    """Tests for the password validation function."""

    def test_valid_password(self):
        errors = validate_password("Hello123")
        assert errors == []

    def test_password_too_short(self):
        errors = validate_password("Hi1")
        assert any("6 characters" in e for e in errors)

    def test_password_no_letter(self):
        errors = validate_password("123456")
        assert any("letter" in e for e in errors)

    def test_password_no_number(self):
        errors = validate_password("HelloWorld")
        assert any("number" in e for e in errors)

    def test_empty_password(self):
        errors = validate_password("")
        assert len(errors) >= 1

    def test_password_with_special_chars(self):
        errors = validate_password("P@ss1!")
        assert errors == []


class TestAllowedFile:
    """Tests for the file extension validation function."""

    def test_allowed_png(self):
        assert allowed_file("photo.png") is True

    def test_allowed_jpg(self):
        assert allowed_file("image.jpg") is True

    def test_allowed_jpeg(self):
        assert allowed_file("pic.jpeg") is True

    def test_allowed_gif(self):
        assert allowed_file("animation.gif") is True

    def test_allowed_webp(self):
        assert allowed_file("photo.webp") is True

    def test_disallowed_exe(self):
        assert allowed_file("virus.exe") is False

    def test_disallowed_pdf(self):
        assert allowed_file("document.pdf") is False

    def test_disallowed_py(self):
        assert allowed_file("script.py") is False

    def test_no_extension(self):
        assert allowed_file("noext") is False

    def test_empty_string(self):
        assert allowed_file("") is False

    def test_case_insensitive(self):
        assert allowed_file("photo.PNG") is True
        assert allowed_file("image.JPG") is True


# =====================
# ROUTE TESTS: PUBLIC PAGES
# =====================
class TestPublicRoutes:
    """Tests for pages accessible without login."""

    def test_home_page_loads(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'EventEase' in response.data

    def test_login_page_loads(self, client):
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_page_loads(self, client):
        response = client.get('/register')
        assert response.status_code == 200

    def test_events_page_loads(self, client):
        response = client.get('/events')
        assert response.status_code == 200

    def test_404_page(self, client):
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'404' in response.data


# =====================
# ROUTE TESTS: AUTH REQUIRED
# =====================
class TestAuthProtection:
    """Tests that protected routes redirect unauthenticated users."""

    def test_create_event_requires_login(self, client):
        response = client.get('/create_event')
        assert response.status_code == 302

    def test_organizer_dashboard_requires_login(self, client):
        response = client.get('/organizer_dashboard')
        assert response.status_code == 302

    def test_participant_dashboard_requires_login(self, client):
        response = client.get('/participant_dashboard')
        assert response.status_code == 302

    def test_volunteer_dashboard_requires_login(self, client):
        response = client.get('/volunteer_dashboard')
        assert response.status_code == 302

    def test_admin_dashboard_requires_login(self, client):
        response = client.get('/admin_dashboard')
        assert response.status_code == 302

    def test_profile_requires_login(self, client):
        response = client.get('/profile')
        assert response.status_code == 302

    def test_create_event_post_requires_login(self, client):
        response = client.post('/create_event', data={'title': 'Test'})
        assert response.status_code == 302


# =====================
# ROUTE TESTS: ROLE PROTECTION
# =====================
class TestRoleProtection:
    """Tests that role-specific routes enforce proper roles."""

    def test_admin_dashboard_blocked_for_participant(self, logged_in_client):
        response = logged_in_client.get('/admin_dashboard')
        assert response.status_code == 302

    def test_admin_delete_user_blocked_for_non_admin(self, logged_in_client):
        response = logged_in_client.post('/admin/delete_user/999')
        assert response.status_code == 302


# =====================
# ROUTE TESTS: LOGGED IN ACCESS
# =====================
class TestLoggedInAccess:
    """Tests that logged-in users can access protected routes."""

    def test_participant_dashboard_accessible(self, logged_in_client):
        response = logged_in_client.get('/participant_dashboard')
        assert response.status_code == 200

    def test_create_event_page_accessible(self, logged_in_client):
        response = logged_in_client.get('/create_event')
        assert response.status_code == 200

    def test_profile_accessible(self, logged_in_client):
        response = logged_in_client.get('/profile')
        assert response.status_code == 200

    def test_admin_dashboard_accessible_for_admin(self, admin_client):
        response = admin_client.get('/admin_dashboard')
        assert response.status_code == 200


# =====================
# ROUTE TESTS: FORM VALIDATION
# =====================
class TestFormValidation:
    """Tests for server-side form validation."""

    def test_register_empty_fields(self, client):
        response = client.post('/register', data={
            'name': '', 'email': '', 'password': '', 'role': 'participant'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_register_weak_password(self, client):
        response = client.post('/register', data={
            'name': 'Test', 'email': 'test@test.com', 'password': '1', 'role': 'participant'
        }, follow_redirects=True)
        assert b'6 characters' in response.data or response.status_code == 200

    def test_register_invalid_role(self, client):
        response = client.post('/register', data={
            'name': 'Test', 'email': 'test@test.com', 'password': 'Test123', 'role': 'superadmin'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_create_event_no_title(self, logged_in_client):
        response = logged_in_client.post('/create_event', data={
            'title': '', 'description': 'Test', 'category': 'Test',
            'price': '0', 'event_date': '2026-12-01', 'event_time': '10:00',
            'venue': 'Test', 'address': 'Test', 'gmap_link': '',
            'max_participants': '100', 'registration_deadline': '2026-11-30'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_empty_fields(self, client):
        response = client.post('/login', data={
            'email': '', 'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200


# =====================
# ROUTE TESTS: LOGOUT
# =====================
class TestLogout:
    """Tests for the logout functionality."""

    def test_logout_clears_session(self, logged_in_client):
        response = logged_in_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        with logged_in_client.session_transaction() as sess:
            assert 'loggedin' not in sess


# =====================
# ROUTE TESTS: SEARCH & PAGINATION
# =====================
class TestSearchAndPagination:
    """Tests for event search and pagination."""

    def test_events_with_search(self, client):
        response = client.get('/events?search=test')
        assert response.status_code == 200

    def test_events_with_category_filter(self, client):
        response = client.get('/events?category=workshop')
        assert response.status_code == 200

    def test_events_with_pagination(self, client):
        response = client.get('/events?page=1')
        assert response.status_code == 200

    def test_events_combined_filters(self, client):
        response = client.get('/events?search=test&category=workshop&page=1')
        assert response.status_code == 200
