# Python 3.\* Features in NOW-LMS

NOW-LMS requires Python 3.11+ and takes advantage of modern Python language features for better code quality, performance, and maintainability.

## Implemented Features

### Python 3.5 Features

#### 1. Extended Unpacking (PEP 448)

**Location**: `now_lms/config/__init__.py`

Used for cleaner list and set creation with starred expressions:

```python
# Before
VALORES_TRUE = {"1", "true", "yes", "on", "development", "dev"}

# After
VALORES_TRUE = {*["1", "true", "yes", "on"], *["development", "dev"]}

# Environment variable lists with extended unpacking
DEBUG_VARS = ["DEBUG", "CI", "DEV", "DEVELOPMENT"]
FRAMEWORK_VARS = ["FLASK_ENV", "DJANGO_DEBUG", "NODE_ENV"]
GENERIC_VARS = ["ENV", "APP_ENV"]

DESARROLLO = any(
    str(environ.get(var, "")).strip().lower() in VALORES_TRUE
    for var in [*DEBUG_VARS, *FRAMEWORK_VARS, *GENERIC_VARS]
)
```

**Location**: `now_lms/misc.py`

Organized HTML tags with logical grouping:

```python
# Before - Long flat list
HTML_TAGS = ["a", "abbr", "acronym", "b", "blockquote", ...]

# After - Grouped with extended unpacking
HTML_TAGS = [
    # Basic formatting
    *["a", "abbr", "acronym", "b", "blockquote", "br", "code"],
    # List and definition tags
    *["dd", "del", "div", "dl", "dt", "em"],
    # Headers and content
    *["h1", "h2", "h3", "hr", "i", "img"],
    # Lists and paragraphs
    *["li", "ol", "p", "pre", "s", "strong", "sub", "sup"],
    # Tables
    *["table", "tbody", "td", "th", "thead", "tr", "ul"],
]
```

**Benefits**:

- More readable code organization
- Cleaner list and set concatenation
- Better logical grouping of related items

### Python 3.6 Features

#### 1. f-strings (PEP 498)

**Location**: `now_lms/misc.py`

Replaced string concatenation with f-strings for URL parameter building:

```python
# Before
argumentos = argumentos + "&" + key + "=" + value

# After
argumentos = f"{argumentos}&{key}={value}"
```

**Location**: `now_lms/db/initial_data.py`

Updated example code to use secrets module with f-strings:

```python
# Example code in course content now demonstrates modern Python practices
```

**Benefits**:

- More readable string formatting
- Better performance than .format() or % formatting
- Easier to maintain and debug

#### 2. Numeric Literal Underscores (PEP 515)

**Location**: `now_lms/auth.py`

Added underscores to large numbers for better readability:

```python
# Before
iterations=480000

# After
iterations=480_000  # Python 3.6+ - Numeric literal underscores for readability

# Password reset and confirmation tokens
expiration_time = datetime.now(timezone.utc) + timedelta(seconds=36_000)  # 10 hours
expiration_time = datetime.now(timezone.utc) + timedelta(seconds=3_600)   # 1 hour
```

**Benefits**:

- Improved readability of large numbers
- Easier to spot errors in numeric literals
- Self-documenting time constants

#### 3. Variable Annotations (PEP 526)

**Location**: `now_lms/misc.py`

Added type annotations to module-level constants:

```python
# Before
TIPOS_DE_USUARIO: list = ["admin", "user", "instructor", "moderator"]
ICONOS_RECURSOS: dict = {...}

# After
TIPOS_DE_USUARIO: list[str] = ["admin", "user", "instructor", "moderator"]
ICONOS_RECURSOS: dict[str, str] = {...}
CURSO_NIVEL: dict[int, str] = {...}
GENEROS: dict[str, str] = {...}
```

**Location**: `now_lms/misc.py` - HTMLCleaner class

Added instance variable annotations:

```python
class HTMLCleaner(HTMLParser):
    """HTML parser for extracting clean text content."""

    # Python 3.6+ - Variable annotations for instance attributes
    textos: list[str]

    def __init__(self):
        super().__init__()
        self.textos = []
```

**Location**: `now_lms/config/__init__.py`

Improved configuration dictionary typing:

```python
# Before
CONFIGURACION: Dict = {}

# After
CONFIGURACION: dict[str, str | bool | Path] = {}
```

**Benefits**:

- Better IDE support and autocomplete
- Clearer code documentation
- Enhanced type checking capabilities

#### 4. secrets Module (PEP 506)

**Location**: `now_lms/db/initial_data.py`

Replaced random module with secrets for security-critical operations:

```python
# Before
import random
secret_number = random.randint(1, 10)

# After
import secrets
secret_number = secrets.randbelow(10) + 1  # 1-10 range
```

**Benefits**:

- Cryptographically strong random number generation
- Better security practices in example code
- Suitable for security-sensitive applications

### Python 3.7 Features

#### 1. Data Classes (PEP 557)

**Location**: `now_lms/misc.py`

Converted NamedTuple classes to dataclasses for better functionality:

```python
# Before
from typing import NamedTuple

class EstiloLocal(NamedTuple):
    navbar: dict
    texto: dict
    logo: dict
    buttom: dict

class EstiloAlterta(NamedTuple):
    icono: dict
    clase: dict

# After
from dataclasses import dataclass

@dataclass
class EstiloLocal:
    """Customizable style configuration.

    Python 3.7+ dataclass provides better functionality than NamedTuple:
    - Mutable fields for runtime configuration updates
    - Default values and field validation
    - Rich comparison and hashing support
    """
    navbar: dict[str, str]
    texto: dict[str, str]
    logo: dict[str, str]
    buttom: dict[str, str]

@dataclass
class EstiloAlterta:
    """Alert style configuration.

    Python 3.7+ dataclass replaces NamedTuple for better flexibility:
    - Allows runtime modification of alert styles
    - Better IDE support and introspection
    - Cleaner initialization and validation
    """
    icono: dict[str, str]
    clase: dict[str, str]
```

**Benefits**:

- Mutable fields allow runtime configuration changes
- Better default value support
- Enhanced IDE support and introspection
- More powerful than NamedTuple for configuration objects
- Built-in **repr**, **eq**, and **hash** methods

### Python 3.8 Features

#### 1. Positional-Only Parameters (`/`)

**Location**: `now_lms/auth.py`

Used in critical authentication functions to prevent keyword argument misuse:

```python
def proteger_passwd(clave, /):
    """Protege contraseña con argon2. Solo acepta argumentos posicionales."""

def validar_acceso(usuario_id, acceso, /):
    """Verifica inicio de sesión. Solo acepta argumentos posicionales."""
```

**Location**: `now_lms/bi.py`

Extended to business logic functions for API safety:

```python
def asignar_curso_a_instructor(curso_codigo: str | None, /, usuario_id: str | None = None):
    """Course assignment requires positional course code parameter."""

def cambia_tipo_de_usuario_por_id(id_usuario: str | None, /, nuevo_tipo: str | None = None, usuario: str | None = None):
    """User type changes require positional user ID parameter."""
```

**Benefits**:

- Prevents accidental keyword argument usage in security-critical functions
- Makes API intentions clearer
- Protects against future parameter name changes
- Enforces correct parameter order in business logic

#### 2. Assignment Expressions (Walrus Operator `:=`)

**Location**: `now_lms/cache_utils.py`

Used to simplify file operations and reduce redundant computations:

```python
# Before
temp_base = tempfile.gettempdir()
cache_dir = os.path.join(temp_base, "now_lms_cache")
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir, mode=0o700, exist_ok=True)

# After
if not os.path.exists(cache_dir := os.path.join(tempfile.gettempdir(), "now_lms_cache")):
    os.makedirs(cache_dir, mode=0o700, exist_ok=True)
```

**Benefits**:

- Reduces variable scope and improves readability
- Eliminates redundant computations
- Makes file path operations more concise

### Python 3.9 Features

#### 1. Native Type Hinting for Generics

**Locations**: `now_lms/misc.py`, `now_lms/mail.py`, `now_lms/bi.py`

Replaced old-style `Union` types with modern union operator:

```python
# Before
from typing import Union
def func(param: Union[str, None]) -> Union[dict, None]:

# After
def func(param: str | None) -> dict | None:
```

**Latest additions in `now_lms/bi.py`**:

- All business logic functions now use `str | None` instead of `Union[None, str]`
- Multi-type unions like `str | int | None` for flexible ID parameters

**Benefits**:

- More readable type hints
- Consistent with modern Python style
- Better IDE support
- Reduced import overhead

### Python 3.10 Features

#### 1. Structural Pattern Matching (`match`)

**Location**: `now_lms/vistas/home.py`

Replaced long if-elif chains with pattern matching for user role handling:

```python
# Before
if current_user.tipo == "admin":
    # admin logic
elif current_user.tipo == "student":
    # student logic
elif current_user.tipo == "instructor":
    # instructor logic
else:
    # default

# After
match current_user.tipo:
    case "admin":
        # admin logic
    case "student":
        # student logic
    case "instructor":
        # instructor logic
    case _:
        # default
```

**Location**: `now_lms/mail.py`

String-to-boolean conversion:

```python
# Before
if MAIL_USE_SSL == "FALSE":
    MAIL_USE_SSL = False
elif MAIL_USE_SSL == "TRUE":
    MAIL_USE_SSL = True

# After
match MAIL_USE_SSL:
    case "FALSE":
        MAIL_USE_SSL = False
    case "TRUE":
        MAIL_USE_SSL = True
```

**Location**: `now_lms/vistas/messages.py`

User role-based access control with pattern matching:

```python
# Before
if current_user.tipo == "instructor":
    course_codes = [dc.curso for dc in get_instructor_courses()]
elif current_user.tipo == "moderator":
    course_codes = [mc.curso for mc in get_moderator_courses()]
else:  # admin
    course_codes = [c.codigo for c in get_all_courses()]

# After
match current_user.tipo:
    case "instructor":
        course_codes = [dc.curso for dc in get_instructor_courses()]
    case "moderator":
        course_codes = [mc.curso for mc in get_moderator_courses()]
    case _:  # admin
        course_codes = [c.codigo for c in get_all_courses()]
```

**Location**: `now_lms/vistas/evaluations.py`

Question type evaluation with pattern matching:

```python
# Before
if question.type == "boolean":
    # Handle boolean questions
    if answer.selected_option_ids:
        selected_ids = json.loads(answer.selected_option_ids)
        # ... validation logic
elif question.type == "multiple":
    # Handle multiple choice questions
    if answer.selected_option_ids:
        selected_ids = json.loads(answer.selected_option_ids)
        # ... validation logic

# After
match question.type:
    case "boolean":
        # Handle boolean questions
        if answer.selected_option_ids:
            selected_ids = json.loads(answer.selected_option_ids)
            # ... validation logic
    case "multiple":
        # Handle multiple choice questions
        if answer.selected_option_ids:
            selected_ids = json.loads(answer.selected_option_ids)
            # ... validation logic
```

**Benefits**:

- More readable than long if-elif chains
- Pattern matching is more powerful and extensible
- Better performance for multiple comparisons
- Enhanced code structure for role-based logic
- Clearer intent in question type handling

### Python 3.11 Features

#### 1. Improved Typing with `Self`

**Location**: `now_lms/db/__init__.py`

Used `Self` return type annotation for methods that return the instance:

```python
from typing import Self

class ForoMensaje(database.Model, BaseTabla):
    def get_thread_root(self) -> Self:
        """Retorna el mensaje raíz del hilo."""
        if self.parent_id:
            return self.parent.get_thread_root()
        return self
```

**Benefits**:

- More accurate type hints for methods returning self
- Better IDE support and type checking
- Self-documenting code

## Type Hints Guidelines

### Overview

NOW-LMS extensively uses type hints across all Flask routes and business logic to ensure code reliability and better developer experience. Type hints are mandatory for all public functions, especially Flask route handlers.

### Flask Route Type Hints

#### Required Imports for Type Hints

Before implementing type hints in Flask routes, ensure you have the necessary imports:

```python
# Required for type hints
from __future__ import annotations

# Flask imports
from flask import Blueprint, render_template, redirect, request, jsonify, abort
from werkzeug.wrappers import Response

# Alternative Response import (both are equivalent)
# from flask import Response

# For error handling with status codes
from flask import Response as FlaskResponse  # when distinguishing from werkzeug Response
```

The `Response` type used in route return annotations comes from **Werkzeug** (`werkzeug.wrappers.Response`) or **Flask** (`flask.Response`) - both are equivalent since Flask re-exports Werkzeug's Response class.

#### 1. Basic Route Return Types

Flask routes in NOW-LMS follow consistent type hint patterns for return values:

**Simple HTML Template Routes**:

```python
@home.route("/")
def pagina_de_inicio() -> str:
    """Homepage route returning rendered template."""
    return render_template("index.html")
```

**Routes with Conditional Redirects**:

```python
@home.route("/home/panel")
@login_required
def panel() -> str | Response:
    """User panel - may redirect or return template."""
    if not current_user.is_authenticated:
        return redirect("/user/login")
    return render_template("panel.html")
```

**API Routes Returning JSON**:

```python
@blog.route("/blog/count_view/<post_id>", methods=["POST"])
def count_view(post_id: int) -> tuple[Response, int]:
    """API endpoint returning JSON response with status code."""
    # Logic here
    return jsonify({"status": "success"}), 200
```

**Complex Routes with Multiple Return Types**:

```python
@course.route("/course/<course_code>/payment")
def payment_page(course_code: str) -> str | Response | tuple[FlaskResponse, int]:
    """Payment page with multiple possible return scenarios."""
    if not course_exists(course_code):
        return abort(404)  # tuple[FlaskResponse, int]
    if user_already_enrolled():
        return redirect("/course/" + course_code)  # Response
    return render_template("payment.html")  # str
```

#### 2. Route Parameter Type Hints

All route parameters must have explicit type annotations:

**String Parameters**:

```python
@course.route("/course/<course_code>")
def curso(course_code: str) -> str:
    """Course view with string parameter."""
    # course_code is automatically validated as str by Flask
```

**Integer Parameters**:

```python
@evaluation.route("/evaluation/<int:evaluation_id>/take")
def take_evaluation(evaluation_id: int) -> str | Response:
    """Evaluation page with integer parameter."""
    # evaluation_id is validated and converted to int by Flask
```

**Multiple Parameters**:

```python
@course.route("/course/<course_code>/resource/<resource_code>")
def pagina_recurso(course_code: str, resource_code: str) -> str:
    """Resource page with multiple string parameters."""
    # Both parameters are required and typed
```

#### 3. HTTP Method Handling

Routes accepting multiple HTTP methods should handle type hints consistently:

**GET/POST Routes**:

```python
@course.route("/course/new_curse", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_curso() -> str | Response:
    """Create new course - GET shows form, POST processes it."""
    form = CurseForm()
    if form.validate_on_submit():
        # Process form and redirect
        return redirect("/course/list")
    # Show form template
    return render_template("course_form.html", form=form)
```

**AJAX/API Endpoints**:

```python
@course.route("/course/<course_code>/mark_complete", methods=["POST"])
@login_required
def marcar_recurso_completado(course_code: str, resource_code: str) -> Response:
    """AJAX endpoint for marking resources complete."""
    # Always returns Response (JSON or redirect)
    return jsonify({"status": "success"})
```

#### 4. Complex Return Type Scenarios

**File Downloads and Responses**:

```python
@course.route("/course/<course_code>/resource/<resource_code>/file")
def recurso_file(course_code: str, resource_code: str) -> Response:
    """File download endpoint."""
    # send_from_directory() returns Response
    return send_from_directory(upload_folder, filename)
```

**Calendar and Export Routes**:

```python
@calendar.route("/calendar/export.ics")
def export_ics() -> Response:
    """Export calendar in ICS format."""
    ics_content = generate_ics()
    response = make_response(ics_content)
    response.headers["Content-Type"] = "text/calendar"
    return response
```

**Error Handling with Status Codes**:

```python
@admin.route("/admin/debug")
def debug_config() -> tuple[FlaskResponse, int]:
    """Debug endpoint returning specific status codes."""
    if not current_user.is_admin():
        return abort(403)  # Returns tuple[FlaskResponse, int]
    return jsonify(debug_info), 200
```

#### 5. Authentication and Authorization Decorators

Type hints work seamlessly with authentication decorators:

```python
@course.route("/admin/course/<course_code>/manage")
@login_required
@perfil_requerido("instructor")
def administrar_curso(course_code: str) -> str:
    """Course management page for instructors."""
    # Decorators don't affect type hints
    return render_template("course_admin.html")
```

#### 6. Helper Function Type Hints

Helper functions used in routes should also be properly typed:

```python
def check_course_access(course_code: str, user) -> bool:
    """Check if user can access course."""
    # Returns boolean for access check
    return user.can_access_course(course_code)

def get_user_resource_progress(course_id: str, user_id: str | None = None) -> dict[int, dict[str, bool]]:
    """Get user progress data."""
    # Complex nested return type for progress tracking
    return {section_id: {"completed": bool, "accessible": bool}}
```

### Best Practices for Flask Route Type Hints

#### 1. Return Type Consistency

- Use `str` for routes that always return rendered templates
- Use `Response` for routes that always return redirects, JSON, or files
- Use `str | Response` for routes that may return templates OR redirects
- Use `tuple[FlaskResponse, int]` for routes that may return error codes

#### 2. Parameter Validation

- Always annotate route parameters with their expected types
- Use Flask's built-in converters (`<int:id>`, `<float:price>`) when possible
- Validate parameter types match the route converter

#### 3. Error Handling

- Consider error scenarios in return type annotations
- Use `abort()` for HTTP errors (returns `tuple[FlaskResponse, int]`)
- Handle `None` cases explicitly in type hints

#### 4. Form Processing

- Type hint form-processing routes as `str | Response`
- GET requests typically return `str` (template)
- POST requests typically return `Response` (redirect) on success

#### 5. AJAX and API Consistency

- API endpoints should return `Response` or `tuple[Response, int]`
- Use consistent JSON response structures
- Type hint any data serialization functions

### Common Type Hint Patterns

```python
# Template-only routes
def simple_page() -> str: ...

# Routes with conditional logic
def dynamic_page() -> str | Response: ...

# API endpoints
def api_endpoint() -> Response: ...
def api_with_status() -> tuple[Response, int]: ...

# File downloads
def download_file() -> Response: ...

# Error handlers
def error_handler() -> tuple[FlaskResponse, int]: ...

# Complex multi-scenario routes
def complex_route() -> str | Response | tuple[FlaskResponse, int]: ...
```

### Integration with Flask Ecosystem

Type hints work seamlessly with Flask extensions:

```python
# Flask-Login integration
@login_required
def protected_route() -> str | Response: ...

# Flask-WTF forms
def form_route() -> str | Response:
    form = MyForm()
    if form.validate_on_submit():
        return redirect("/success")  # Response
    return render_template("form.html", form=form)  # str

# Flask-SQLAlchemy queries with proper typing
def user_detail(user_id: int) -> str | Response:
    user = database.session.get(Usuario, user_id)
    if not user:
        return abort(404)  # tuple[FlaskResponse, int]
    return render_template("user.html", user=user)  # str
```

## Code Quality Impact

### Linting and Formatting

All modernized code passes:

- **Black**: Python code formatter with line length 127
- **Flake8**: Linting with project-specific rules
- **mypy**: Type checking (when available)
- **ruff**: Fast Python linter

### Testing

All features are validated by:

- Unit tests continue to pass
- Integration tests validate functionality
- Route testing ensures no regressions

## Future Opportunities

### Additional Python 3.5-3.7 Features to Consider

1. **More Data Classes**: Convert additional configuration and data transfer objects
2. **Extended Unpacking**: Apply to more function calls and data structure operations
3. **Context Variables (PEP 567)**: For request-scoped data in web applications
4. **Built-in breakpoint() (PEP 553)**: Replace any remaining debug patterns

### Additional Python 3.8+ Features to Consider

1. **Assignment Expressions (Walrus Operator)**: Look for file processing and validation patterns where assignment+check is common
2. **More Positional-Only Parameters**: Apply to other core functions like database operations
3. **Exception Groups**: For handling multiple concurrent errors in file uploads or batch operations
4. **Parenthesized Context Managers**: For file operations and database transactions

### Performance Benefits

- **Pattern Matching**: Better performance than if-elif chains for multiple comparisons
- **Native Type Hints**: Reduced import overhead
- **Walrus Operator**: Eliminates redundant computations
- **Data Classes**: Better performance than NamedTuple for mutable objects
- **Extended Unpacking**: More efficient than manual list concatenation
- **f-strings**: Faster than .format() or % formatting

## Migration Guidelines

When modernizing additional code:

1. **Prioritize Safety**: Always test changes thoroughly
2. **Focus on Readability**: Only apply features where they improve code clarity
3. **Maintain Compatibility**: Ensure all team members use Python 3.11+
4. **Document Changes**: Update this file when adding new features
5. **Progressive Enhancement**: Implement features incrementally rather than all at once

## References

- [Python 3.5 Release Notes](https://docs.python.org/3/whatsnew/3.5.html)
- [Python 3.6 Release Notes](https://docs.python.org/3/whatsnew/3.6.html)
- [Python 3.7 Release Notes](https://docs.python.org/3/whatsnew/3.7.html)
- [Python 3.8 Release Notes](https://docs.python.org/3/whatsnew/3.8.html)
- [Python 3.9 Release Notes](https://docs.python.org/3/whatsnew/3.9.html)
- [Python 3.10 Release Notes](https://docs.python.org/3/whatsnew/3.10.html)
- [Python 3.11 Release Notes](https://docs.python.org/3/whatsnew/3.11.html)
