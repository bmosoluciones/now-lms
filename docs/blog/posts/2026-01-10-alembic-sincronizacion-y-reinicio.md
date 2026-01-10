# Alembic: sincronización de revisiones y cómo reiniciar correctamente

Fecha: 2026-01-10

Este artículo explica qué es la tabla `alembic_version`, por qué aparecen errores como “Can't locate revision …”, y cómo corregir problemas de sincronización de migraciones en NOW LMS usando Alembic integrado en la aplicación (Flask-Alembic), tanto en desarrollo como en servidores.

## ¿Qué guarda Alembic?
- **Tabla `alembic_version`**: almacena la(s) revisión(es) actual(es) aplicadas. En la mayoría de usos, una fila; si hay ramas, puede haber varias.
- **Metadatos en archivos de migración**: `revision`, `down_revision`, `branch_labels`, `depends_on` dentro de cada script.
- **No guarda**: un log detallado de pasos ejecutados ni checksums. Por eso editar una migración ya aplicada no es detectado automáticamente.

## Síntomas típicos
- “Can't locate revision identified by 'XXXX'” al intentar `upgrade()` o `downgrade()`.
- Migraciones que no se encuentran pese a que el archivo existe en el repo.
- Reaplicación de migraciones que falla por “table/column already exists”.

## Causas comunes
- **Ubicación incorrecta de scripts**: el proceso no está leyendo `now_lms/migrations` (p. ej., intenta usar un `migrations/` vacío o un paquete instalado sin migraciones).
- **Desfase entre BD y código**: la tabla `alembic_version` apunta a un `revision_id` que no existe en los archivos cargados por ese proceso (otro checkout o wheel sin migraciones).
- **Cambio de IDs**: se editó el `revision`/`down_revision` de una migración ya aplicada (por ejemplo, renombrar un ID amigable a timestamp), rompiendo la cadena.
- **Uso de `alembic.exe`**: este proyecto no incluye `alembic.ini/env.py` para ese CLI; se debe usar Alembic integrado en la app.

## Cómo diagnosticar
Usar el contexto de la app para ver qué scripts Alembic está leyendo:

```python
from now_lms import init_app, alembic
app = init_app()
with app.app_context():
    sd = alembic.script_directory
    print("script_location:", sd.dir)
    print("total revisions:", len(sd.revision_map._revisions))
    print("has 20260109_191123:", "20260109_191123" in sd.revision_map._revisions)
```

Si `script_location` no apunta a `now_lms/migrations`, asegúrate de ejecutar las migraciones bajo el contexto de la app (NOW LMS configura esto automáticamente en la inicialización).

## Soluciones rápidas (según situación)
- **Proceso no encuentra migraciones**: ejecuta migraciones dentro de la app.
  ```bash
  # Windows
  venv\Scripts\python chec.py

  # Linux/Mac
  venv/bin/python chec.py
  ```
  El script `chec.py` crea el contexto de la app y ejecuta `alembic.upgrade()`.

- **Desfase de IDs (renombraste una revisión)**: sincroniza con `stamp` y luego `upgrade`.
  ```python
  from now_lms import init_app, alembic
  app = init_app()
  with app.app_context():
      alembic.stamp("20260110_035505")  # ID correcto en archivos
      alembic.upgrade()
  ```

- **Reaplicar todo en orden** (BD limpia o staging):
  ```python
  from now_lms import init_app, alembic
  app = init_app()
  with app.app_context():
      alembic.downgrade("base")
      alembic.upgrade()
  ```
  Nota: `downgrade("base")` afectará datos si las migraciones definen `downgrade()` destructivos. Úsalo en desarrollo/staging.

## ¿Puedo borrar la tabla `alembic_version`?
Sí, pero entiende el efecto:
- Alembic asumirá que estás en `base`. Si tu esquema ya tiene objetos, `upgrade()` puede fallar por “ya existe”.
- Recomendado: tras borrar, usa `alembic.stamp(<revision>)` para resincronizar al punto correcto y luego `upgrade()`.

Ejemplo seguro:
```python
from now_lms import create_app, alembic
from sqlalchemy import text

app = create_app(app_name="drop_alembic_version", testing=True)
with app.app_context():
    from now_lms.db import database as db
    db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
    db.session.commit()

    # Sincroniza al ID que corresponde a tu esquema
    alembic.stamp("20260110_035505")
    alembic.upgrade()
```

### Último recurso
- Considera borrar la tabla `alembic_version` solo como último recurso cuando:
  - El proceso no puede sincronizarse con `stamp` por diferencias irreconciliables de IDs.
  - Has confirmado en staging que reaplicar migraciones no rompe por objetos existentes.
- Después de borrar, siempre realiza `alembic.stamp(<revision_correcta>)` para alinear el puntero de versión y luego `alembic.upgrade()`.
- En producción, evita esta opción si hay riesgo de pérdida de datos; prioriza crear una nueva migración correctiva o sincronizar con `stamp`.

## Buenas prácticas
- **No edites** migraciones ya aplicadas; crea una nueva que corrija cambios.
- **IDs coherentes**: usa timestamps consistentes en `revision` y referencia esos mismos en `down_revision` posteriores.
- **Contexto de app**: ejecuta Alembic siempre dentro del contexto de NOW LMS para que lea `now_lms/migrations`.
- **Empaquetado**: asegúrate de incluir `now_lms/migrations` en tu distribución (MANIFEST/pyproject) si despliegas como paquete/wheel.
- **Producción**: evita `downgrade("base")`; usa `stamp` y nuevas migraciones. Prueba en staging.

## Verificación rápida
- Versión actual:
  ```python
  from now_lms import init_app
  app = init_app()
  with app.app_context():
      from now_lms.db import database as db
      print(db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar())
  ```
- Columnas/tablas creadas por las últimas migraciones (ejemplos): `cover_image`, `cover_image_ext` en `blog_post`, `mostrar_en_footer` en `static_pages`, y tabla `enlaces_utiles`.

## Ejemplo práctico (Windows)
```bash
# 1) Ejecutar migraciones dentro del contexto de la app
venv\Scripts\python chec.py

# 2) Si hubo renombre de IDs, sincronizar
venv\Scripts\python - <<'PY'
from now_lms import init_app, alembic
app = init_app()
with app.app_context():
    alembic.stamp("20260110_035505")
    alembic.upgrade()
PY

# 3) Ver versión
venv\Scripts\python - <<'PY'
from now_lms import init_app
app = init_app()
with app.app_context():
    from now_lms.db import database as db
    print(db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar())
PY
```

---

Si necesitas un script utilitario (similar a `chec.py`) con modos `reset`, `stamp`, `downgrade_base` y `upgrade`, podemos añadirlo para automatizar estas operaciones sin depender del CLI de Alembic.
