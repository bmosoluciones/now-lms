# SQLAlchemy Query API Guide

This guide provides comprehensive examples of how to implement the modern SQLAlchemy 2.x query API in the NOW Learning Management System.

## Table of Contents

1. [Basic Imports](#basic-imports)
2. [SELECT Operations](#select-operations)
3. [UPDATE Operations](#update-operations)
4. [DELETE Operations](#delete-operations)
5. [Database Session Operations](#database-session-operations)
6. [Advanced Patterns](#advanced-patterns)
7. [Migration Patterns](#migration-patterns)

## Basic Imports

Always ensure you have the necessary imports for modern SQLAlchemy operations:

```python
from sqlalchemy import func, select, delete, update
from now_lms.db import database, select  # select is pre-imported from db module
```

## SELECT Operations

### Basic Select

```python
# Single record
user = database.session.execute(select(Usuario).filter_by(usuario='john_doe')).scalars().first()

# All records
users = database.session.execute(select(Usuario)).scalars().all()

# With filtering
active_users = database.session.execute(
    select(Usuario).filter(Usuario.activo == True)
).scalars().all()
```

### Select with Order By

```python
# Ordered results
courses = database.session.execute(
    select(Curso).order_by(Curso.nombre.asc())
).scalars().all()

# Multiple order criteria
sections = database.session.execute(
    select(CursoSeccion)
    .filter_by(curso=course_code)
    .order_by(CursoSeccion.indice, CursoSeccion.nombre)
).scalars().all()
```

### Select with Joins

```python
# Inner join
evaluations = database.session.execute(
    select(Evaluation)
    .join(CursoSeccion)
    .filter(CursoSeccion.curso == course_code)
).scalars().all()

# Left outer join
results = database.session.execute(
    select(Curso)
    .outerjoin(DocenteCurso)
    .filter(DocenteCurso.usuario == user_id)
).scalars().all()
```

### Select Specific Columns

```python
# Select only specific columns (not all columns from table)
course_names = database.session.execute(
    select(Curso.codigo, Curso.nombre)
    .filter(Curso.publico == True)
).all()

# With functions
user_count = database.session.execute(
    select(func.count(Usuario.id))
    .filter(Usuario.activo == True)
).scalar()

# Group by with aggregation
course_stats = database.session.execute(
    select(Curso.categoria, func.count(Curso.id))
    .group_by(Curso.categoria)
).all()
```

### Select First or 404 Pattern

```python
# Modern replacement for first_or_404()
from flask import abort

post = database.session.execute(
    select(BlogPost).filter(BlogPost.slug == slug)
).scalars().first()
if not post:
    abort(404)
```

### Count Operations

```python
# Count records
total_courses = database.session.execute(
    select(func.count(Curso.id))
    .filter(Curso.publico == True)
).scalar()

# Count with conditions
active_students = database.session.execute(
    select(func.count(EstudianteCurso.id))
    .filter(EstudianteCurso.vigente == True)
).scalar()
```

### Pagination

```python
# Modern pagination (using database.paginate instead of query().paginate())
posts = database.paginate(
    select(BlogPost).filter(BlogPost.published == True).order_by(BlogPost.fecha.desc()),
    page=page,
    per_page=per_page,
    error_out=False
)
```

### Subqueries and EXISTS

```python
# Subquery
subquery = select(DocenteCurso.curso).filter(DocenteCurso.usuario == user_id)
instructor_courses = database.session.execute(
    select(Curso).filter(Curso.codigo.in_(subquery))
).scalars().all()

# EXISTS
from sqlalchemy import exists
has_course = database.session.execute(
    select(exists().where(
        EstudianteCurso.usuario == user_id,
        EstudianteCurso.curso == course_code
    ))
).scalar()
```

## UPDATE Operations

### Basic Update

```python
# Update single record
database.session.execute(
    update(Usuario)
    .where(Usuario.usuario == user_id)
    .values(ultimo_acceso=datetime.now())
)
database.session.commit()

# Update multiple records
database.session.execute(
    update(Curso)
    .where(Curso.categoria == old_category)
    .values(categoria=new_category)
)
database.session.commit()
```

### Update with Conditions

```python
# Conditional update
database.session.execute(
    update(CursoSeccion)
    .where(
        CursoSeccion.curso == course_code,
        CursoSeccion.publico == False
    )
    .values(publico=True)
)
database.session.commit()
```

### Update Using ORM Objects

```python
# For single record updates, you can still use ORM approach
user = database.session.execute(
    select(Usuario).filter_by(usuario=user_id)
).scalars().first()
if user:
    user.ultimo_acceso = datetime.now()
    database.session.commit()
```

## DELETE Operations

### Basic Delete

```python
# Delete records
database.session.execute(
    delete(Categoria).where(Categoria.id == category_id)
)
database.session.commit()

# Delete with multiple conditions
database.session.execute(
    delete(EstudianteCurso).where(
        EstudianteCurso.usuario == user_id,
        EstudianteCurso.vigente == False
    )
)
database.session.commit()
```

### Delete with Joins (using subquery)

```python
# Delete related records
subquery = select(CursoSeccion.id).filter(CursoSeccion.curso == course_code)
database.session.execute(
    delete(CursoRecurso).where(CursoRecurso.seccion.in_(subquery))
)
database.session.commit()
```

## Database Session Operations

### Core Session Methods

```python
# Add new record
new_user = Usuario(usuario='new_user', email='user@example.com')
database.session.add(new_user)
database.session.commit()

# Add multiple records
database.session.add_all([user1, user2, user3])
database.session.commit()

# Flush (write to database but don't commit transaction)
database.session.add(new_course)
database.session.flush()  # Assigns ID but doesn't commit
# new_course.id is now available

# Commit transaction
database.session.commit()

# Rollback transaction
try:
    database.session.add(new_record)
    database.session.commit()
except Exception:
    database.session.rollback()
    raise
```

### Database Schema Operations

```python
# Drop all tables (development/testing only)
database.drop_all()

# Create all tables
database.create_all()

# Reflect existing database
database.reflect()
```

### Session State Management

```python
# Remove object from session
database.session.expunge(user_object)

# Refresh object from database
database.session.refresh(user_object)

# Merge detached object
merged_user = database.session.merge(detached_user)
database.session.commit()

# Check if object is in session
if user in database.session:
    print("User is in session")
```

## Advanced Patterns

### Complex Filtering

```python
# Multiple OR conditions
from sqlalchemy import or_

courses = database.session.execute(
    select(Curso).filter(
        or_(
            Curso.categoria == 'programming',
            Curso.categoria == 'web-development'
        )
    )
).scalars().all()

# IN clause
valid_statuses = ['active', 'pending', 'trial']
users = database.session.execute(
    select(Usuario).filter(Usuario.status.in_(valid_statuses))
).scalars().all()

# LIKE patterns
search_results = database.session.execute(
    select(Curso).filter(Curso.nombre.like(f'%{search_term}%'))
).scalars().all()
```

### Date and Time Filtering

```python
from datetime import datetime, timedelta

# Date ranges
recent_posts = database.session.execute(
    select(BlogPost).filter(
        BlogPost.fecha >= datetime.now() - timedelta(days=30)
    )
).scalars().all()

# Date comparisons
expired_coupons = database.session.execute(
    select(Coupon).filter(Coupon.fecha_expiracion < datetime.now())
).scalars().all()
```

### Raw SQL When Needed

```python
# For complex queries that are difficult with ORM
result = database.session.execute(
    database.text(
        "SELECT c.nombre, COUNT(ec.id) as student_count "
        "FROM curso c LEFT JOIN estudiante_curso ec ON c.codigo = ec.curso "
        "GROUP BY c.codigo, c.nombre "
        "HAVING COUNT(ec.id) > :min_students"
    ),
    {"min_students": 10}
).fetchall()
```

## Migration Patterns

### Common Migration Patterns from Old to New API

```python
# ❌ OLD (Deprecated)
database.session.query(Usuario).filter_by(usuario=id_usuario).first()

# ✅ NEW (Modern)
database.session.execute(select(Usuario).filter_by(usuario=id_usuario)).scalars().first()

# ❌ OLD (Deprecated)
database.session.query(Curso).all()

# ✅ NEW (Modern)
database.session.execute(select(Curso)).scalars().all()

# ❌ OLD (Deprecated)
database.session.query(func.count(Usuario.id)).scalar()

# ✅ NEW (Modern)
database.session.execute(select(func.count(Usuario.id))).scalar()

# ❌ OLD (Deprecated)
database.session.query(Curso).filter(...).paginate(page=page, per_page=per_page)

# ✅ NEW (Modern)
database.paginate(select(Curso).filter(...), page=page, per_page=per_page)

# ❌ OLD (Deprecated)
database.session.query(Usuario).filter_by(id=user_id).delete()

# ✅ NEW (Modern)
database.session.execute(delete(Usuario).where(Usuario.id == user_id))
```

### Choosing Between .scalars().first() vs .scalar_one_or_none()

```python
# Use .scalars().first() when:
# - You want the first result even if multiple exist
# - Original code used .first()
# - Multiple results are acceptable/expected
result = database.session.execute(
    select(Configuration).filter_by(key='theme')
).scalars().first()

# Use .scalar_one_or_none() when:
# - You expect exactly zero or one result
# - You want an exception if multiple results exist
# - Data integrity requires uniqueness
user = database.session.execute(
    select(Usuario).filter_by(email=email)
).scalar_one_or_none()
```

### Avoid singleton-comparison errors

Incorrect way
```
.filter(DocenteCurso.vigente == True)
```
Correct way

```
.filter(DocenteCurso.vigente.is_(True))
```


## Best Practices

1. **Always use .scalars()** when you want SQLAlchemy model objects
2. **Use .scalar()** for single values (counts, aggregations)
3. **Prefer .scalars().first()** over .scalar_one_or_none() for compatibility
4. **Always commit after modifications** unless in a transaction context
5. **Handle None results** explicitly when using .first()
6. **Use select() for all read operations**
7. **Use update() and delete() for bulk operations**
8. **Import select from now_lms.db** (pre-configured)

## Error Handling

```python
from sqlalchemy.exc import IntegrityError, MultipleResultsFound

try:
    # Operation that might fail
    database.session.execute(
        update(Usuario).where(Usuario.id == user_id).values(email=new_email)
    )
    database.session.commit()
except IntegrityError as e:
    database.session.rollback()
    # Handle duplicate email or other constraint violations
    flash("Email already exists", "error")
except MultipleResultsFound as e:
    # Handle when scalar_one_or_none() finds multiple results
    log.error(f"Multiple results found: {e}")
    raise
```

This guide covers the essential patterns for modern SQLAlchemy 2.x usage in the NOW LMS project. Always prefer the modern syntax for new code and migrate legacy code gradually following these patterns.
