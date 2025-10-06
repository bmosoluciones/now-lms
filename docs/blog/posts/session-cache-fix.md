# Session Cache Fix

## Problem Description

The system was exhibiting erratic session behavior:

- Navigation was not smooth
- Sometimes showed the login page
- When trying to log in, showed a message that there was already an active session
- After logging in and refreshing the page, sometimes showed the login button, sometimes showed the user menu

## Root Cause

The issue was caused by **cache key collision** between authenticated and anonymous users.

### How Flask-Caching Works

When using `@cache.cached(unless=condition)`:
- The `unless` parameter only controls whether to **WRITE** to cache
- It does NOT control whether to **READ** from cache
- All requests use the same cache key (e.g., `view//home`)

### The Problem Flow

1. **Anonymous user visits `/home`**
   - Cache MISS
   - Generates page with login button
   - **Caches it with key `view//home`**

2. **Authenticated user visits `/home`**
   - `unless` returns True (don't cache for authenticated users)
   - Checks cache first
   - **FINDS cached anonymous version**
   - Shows login button instead of user menu! ❌

3. **Authenticated user refreshes**
   - Sometimes gets fresh page (with user menu)
   - Sometimes gets cached page (with login button)
   - **Erratic behavior!** ❌

## Solution

Use **authentication-aware cache keys** instead of relying on `unless` parameter.

### New Cache Key Function

```python
def cache_key_with_auth_state() -> str:
    """Generate cache key that includes authentication state.
    
    This ensures authenticated and anonymous users get different cached versions
    of the same page.
    """
    from flask import request
    
    # Include authentication state in the cache key
    auth_state = "auth" if (current_user and current_user.is_authenticated) else "anon"
    
    # Build key from request path and auth state
    key = f"view/{request.path}/{auth_state}"
    
    # Include query parameters if present
    if request.query_string:
        key += f"?{request.query_string.decode('utf-8')}"
    
    return key
```

### Cache Keys Now Generated

| User State | Page | Cache Key |
|------------|------|-----------|
| Anonymous | `/home` | `view//home/anon` |
| Authenticated | `/home` | `view//home/auth` |
| Anonymous | `/course/explore?page=2` | `view//course/explore/anon?page=2` |
| Authenticated | `/course/explore?page=2` | `view//course/explore/auth?page=2` |

### Updated Decorator Usage

**Before:**
```python
@home.route("/home")
@cache.cached(timeout=90, unless=no_guardar_en_cache_global)
def pagina_de_inicio() -> str:
    ...
```

**After:**
```python
@home.route("/home")
@cache.cached(timeout=90, key_prefix=cache_key_with_auth_state)
def pagina_de_inicio() -> str:
    ...
```

## Files Changed

1. **`now_lms/cache.py`**
   - Added `cache_key_with_auth_state()` function
   - Kept `no_guardar_en_cache_global()` for backward compatibility

2. **`now_lms/vistas/home.py`**
   - Updated home page cache decorator

3. **`now_lms/vistas/courses.py`**
   - Updated 5 course view cache decorators

4. **`now_lms/vistas/resources.py`**
   - Updated 2 resource view cache decorators

5. **`now_lms/vistas/programs.py`**
   - Updated 2 program view cache decorators

6. **`tests/test_session_cache_fix.py`**
   - Added comprehensive tests for the fix

## Testing

### Unit Tests

```bash
pytest tests/test_session_cache_fix.py -v
```

Tests verify:
- Cache keys differ for authenticated vs anonymous users
- Cache keys include query parameters
- Login/logout flow works correctly
- No cache collisions between user states

### Integration Tests

```bash
pytest tests/test_cache_invalidation.py tests/test_negative_simple.py -v
```

All existing cache tests still pass.

### Manual Testing

1. Visit home page as anonymous user → Should see login button
2. Login → Should see user menu
3. Refresh page → Should STILL see user menu (not login button)
4. Logout → Should see login button
5. Refresh page → Should STILL see login button (not user menu)

## Benefits

✅ **Smooth navigation** - No more flickering between authenticated/anonymous states

✅ **Consistent session** - Users always see the correct state for their authentication

✅ **Better performance** - Can still cache pages, but separately per auth state

✅ **Security** - Prevents authenticated content from being cached for anonymous users

## Backward Compatibility

The `no_guardar_en_cache_global()` function is kept for backward compatibility, but is no longer used in the main codebase. It can be removed in a future version after verifying no plugins or custom code depend on it.

## Future Improvements

1. Consider adding user-specific cache keys for highly personalized content
2. Add cache warming for common pages
3. Monitor cache hit rates for different authentication states
4. Consider Redis-based session storage for better scalability
