# Tests de NOW LMS

Documentación de la suite de pruebas unitarias.

## Filosofía de testing

Esta suite de tests está diseñada con los siguientes principios:

1. **Simplicidad**: Tests fáciles de leer y entender, sin código mágico
2. **Independencia**: Cada test es completamente independiente
3. **Velocidad**: Todos los tests usan base de datos en memoria
4. **Mantenibilidad**: Código explícito que facilita modificaciones

## Estructura

```
tests/
├── __init__.py           # Paquete de tests
├── conftest.py           # Fixtures de pytest (simples y claras)
├── test_basicos.py       # Tests básicos de la aplicación
├── test_auth.py          # Tests de autenticación
├── test_modelos.py       # Tests de modelos de base de datos
└── test_multipledb.py    # Tests especiales para PostgreSQL/MySQL
```

## Ejecutar tests

### Todos los tests
```bash
pytest tests/
```

### Tests específicos
```bash
pytest tests/test_auth.py
pytest tests/test_modelos.py::test_crear_usuario
```

### Con cobertura
```bash
pytest tests/ --cov=now_lms
```

### Modo verbose
```bash
pytest tests/ -v
```

## Fixtures disponibles

En `conftest.py` están definidas las fixtures básicas:

- **`app`**: Aplicación Flask con base de datos en memoria
- **`client`**: Cliente HTTP para hacer requests
- **`db_session`**: Sesión de base de datos (con todas las tablas creadas)

## Escribir nuevos tests

### Estructura básica

```python
def test_algo_especifico(app, db_session):
    """Descripción clara de lo que se está probando."""
    from now_lms.db import Modelo
    
    # 1. Crear datos necesarios
    objeto = Modelo(campo="valor")
    db_session.add(objeto)
    db_session.commit()
    
    # 2. Ejecutar la acción a probar
    resultado = hacer_algo(objeto)
    
    # 3. Verificar el resultado esperado
    assert resultado == esperado
    
    # 4. La limpieza es automática (db se destruye al final)
```

### Reglas importantes

1. **Cada test crea sus propios datos** - No asumas que existen datos previos
2. **No dependas de otros tests** - Tests deben poder ejecutarse en cualquier orden
3. **Nombres descriptivos** - El nombre del test debe indicar qué se está probando
4. **Docstrings claros** - Explica brevemente qué hace el test
5. **Una validación por test** - Cada test debe verificar una sola cosa

### Ejemplo completo

```python
def test_crear_usuario_con_email_duplicado_falla(app, db_session):
    """No se debe permitir crear dos usuarios con el mismo email."""
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd
    from sqlalchemy.exc import IntegrityError
    
    # Crear primer usuario
    user1 = Usuario(
        usuario="user1",
        acceso=proteger_passwd("pass123"),
        nombre="Usuario Uno",
        correo_electronico="test@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user1)
    db_session.commit()
    
    # Intentar crear segundo usuario con mismo email
    user2 = Usuario(
        usuario="user2",
        acceso=proteger_passwd("pass456"),
        nombre="Usuario Dos",
        correo_electronico="test@example.com",  # Email duplicado
        tipo="student",
        activo=True,
    )
    
    # Debe fallar con IntegrityError
    with pytest.raises(IntegrityError):
        db_session.add(user2)
        db_session.commit()
```

## Tests de múltiples bases de datos

El archivo `test_multipledb.py` es especial:

- Solo se ejecuta en entorno CI (`CI=True`)
- Solo se ejecuta si `DATABASE_URL` apunta a PostgreSQL o MySQL
- Se usa para validar compatibilidad con diferentes motores de base de datos

Los tests normales siempre usan SQLite en memoria, que es rápido y suficiente para validación de lógica.

## Convenciones de código

- **Imports al inicio de la función**: Para mayor claridad sobre dependencias
- **Comentarios explícitos**: Cuando sea necesario explicar por qué algo se hace así
- **Assertions simples**: `assert x == y` mejor que condiciones complejas
- **Sin fixtures complejas**: Preferir crear datos explícitamente en cada test

## Depuración de tests

### Ver output detallado
```bash
pytest tests/test_auth.py -v -s
```

### Ver traceback completo
```bash
pytest tests/ --tb=long
```

### Ejecutar solo tests que fallaron
```bash
pytest tests/ --lf
```

### Stop en primer fallo
```bash
pytest tests/ -x
```

## Buenas prácticas

### ✅ Hacer

- Tests simples y directos
- Nombres descriptivos
- Una cosa por test
- Datos explícitos en cada test
- Limpieza automática (fixtures de pytest)

### ❌ Evitar

- Tests que dependen de otros tests
- Fixtures complicadas o mágicas
- Datos compartidos entre tests
- Tests que modifican estado global
- Múltiples assertions no relacionadas en un test

## Métricas actuales

- **Tests totales**: 10 pasando
- **Tiempo de ejecución**: ~2.6 segundos
- **Cobertura**: Tests básicos de funcionalidad core

## Recursos

- [Pytest documentation](https://docs.pytest.org/)
- [Testing Flask applications](https://flask.palletsprojects.com/en/latest/testing/)
- [SQLAlchemy testing](https://docs.sqlalchemy.org/en/latest/orm/session_basics.html#session-frequently-asked-questions)
