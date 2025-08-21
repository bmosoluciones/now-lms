# Session Fixtures Usage Guide

This guide shows how to use the new session-scoped pytest fixtures for better test performance.

## Available Session Fixtures

1. **session_basic_db_setup**: Minimal database setup with basic configuration and certificates
2. **session_full_db_setup**: Full database setup with users, courses, and test data  
3. **session_full_db_setup_with_examples**: Full setup including example data
4. **isolated_db_session**: Function-scoped session for modifying data while using session fixtures

## Usage Examples

### Read-only tests with basic setup
```python
def test_basic_functionality(session_basic_db_setup):
    """Test that only needs basic database setup."""
    with session_basic_db_setup.app_context():
        from now_lms import database
        from now_lms.db import Configuracion, select
        
        # Read configuration data
        configs = database.session.execute(select(Configuracion)).scalars().all()
        assert len(configs) > 0
```

### Read-only tests with full data
```python  
def test_user_functionality(session_full_db_setup):
    """Test that needs users and courses."""
    with session_full_db_setup.app_context():
        from now_lms import database
        from now_lms.db import Usuario, Curso, select
        
        # Read users and courses
        users = database.session.execute(select(Usuario)).scalars().all()
        courses = database.session.execute(select(Curso)).scalars().all()
        
        assert len(users) >= 1
        assert len(courses) >= 1
```

### Tests that need to modify data
```python
def test_data_modification(isolated_db_session):
    """Test that modifies data but rolls back changes."""
    from now_lms.db import Usuario, select
    from now_lms.auth import proteger_passwd
    
    # Get initial count
    initial_count = len(isolated_db_session.execute(select(Usuario)).scalars().all())
    
    # Add a user (will be rolled back automatically)
    new_user = Usuario(
        usuario="test_user",
        acceso=proteger_passwd("password"),
        nombre="Test",
        apellido="User",
        activo=True
    )
    isolated_db_session.add(new_user)
    isolated_db_session.flush()
    
    # Verify user was added
    new_count = len(isolated_db_session.execute(select(Usuario)).scalars().all())
    assert new_count == initial_count + 1
    
    # Changes will be automatically rolled back after test
```

## Important Notes

1. **Cannot mix session and function fixtures**: Do not use session fixtures (like `session_full_db_setup`) and function fixtures (like `app`, `db_session`) in the same test.

2. **Session fixtures are shared**: Session fixtures are created once per test session and shared across all tests that use them.

3. **Use isolated_db_session for data modification**: When you need to modify data in tests that use session fixtures, use the `isolated_db_session` fixture which provides automatic rollback.

4. **Performance benefit**: Session fixtures significantly improve test performance for read-only tests by avoiding repeated database setup/teardown.

5. **Independent databases**: Session fixtures use completely separate database files from function fixtures, ensuring no interference.

## Performance Comparison

- **Function fixtures**: Each test creates and destroys a fresh database (~0.5-1s per test)
- **Session fixtures**: Database created once per session, shared across tests (~0.1s per test after initial setup)

For test suites with many read-only tests, this can provide significant performance improvements.