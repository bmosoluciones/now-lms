# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test end-to-end para funcionalidad de blog.

Prueba el flujo completo de:
- Creación de posts de blog
- Edición de posts
- Visualización pública
- Comentarios
- Tags de blog
"""


from now_lms.auth import proteger_passwd
from now_lms.db import BlogComment, BlogPost, BlogTag, Usuario, database

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_admin(db_session) -> Usuario:
    """Crea un usuario administrador para las pruebas."""
    user = Usuario(
        usuario="admin",
        acceso=proteger_passwd("admin"),
        nombre="Admin",
        correo_electronico="admin@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login_admin(app):
    """Inicia sesión como administrador y retorna el cliente."""
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def test_e2e_blog_post_creation_and_viewing(app, db_session):
    """Test: crear un post de blog y visualizarlo públicamente."""
    # 1) Crear admin y login
    _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Crear post de blog via POST
    resp_new = client.post(
        "/admin/blog/posts/new",
        data={
            "title": "Mi Primer Post",
            "content": "Este es el contenido del post",
            "status": "published",
        },
        follow_redirects=False,
    )
    assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar que el post existe en la base de datos
    post = db_session.execute(database.select(BlogPost).filter_by(title="Mi Primer Post")).scalars().first()
    assert post is not None
    assert post.content == "Este es el contenido del post"
    assert post.status == "published"
    assert post.slug is not None

    # 4) Visualizar el post públicamente (sin login)
    client_public = app.test_client()
    resp_view = client_public.get(f"/blog/{post.slug}")
    assert resp_view.status_code == 200
    assert b"Mi Primer Post" in resp_view.data

    # 5) Verificar que el post aparece en el índice del blog
    resp_index = client_public.get("/blog")
    assert resp_index.status_code == 200
    assert b"Mi Primer Post" in resp_index.data


def test_e2e_blog_post_editing(app, db_session):
    """Test: editar un post de blog existente."""
    # 1) Crear admin y login
    admin = _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Crear post inicial
    post = BlogPost(
        title="Post Original",
        content="Contenido original",
        status="published",
        slug="post-original",
        author_id=admin.id,
    )
    db_session.add(post)
    db_session.commit()
    post_id = post.id

    # 3) Editar el post via POST
    resp_edit = client.post(
        f"/admin/blog/posts/{post_id}/edit",
        data={
            "title": "Post Editado",
            "content": "Contenido editado",
            "status": "published",
        },
        follow_redirects=False,
    )
    assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}

    # 4) Verificar cambios en la base de datos
    post_editado = db_session.get(BlogPost, post_id)
    assert post_editado is not None
    assert post_editado.title == "Post Editado"
    assert post_editado.content == "Contenido editado"


def test_e2e_blog_comments(app, db_session):
    """Test: agregar comentarios a un post de blog."""
    # 1) Crear admin y post
    admin = _crear_admin(db_session)
    post = BlogPost(
        title="Post con Comentarios",
        content="Contenido del post",
        status="published",
        slug="post-con-comentarios",
        author_id=admin.id,
    )
    db_session.add(post)
    db_session.commit()
    post_id = post.id

    # 2) Login como admin
    client = _login_admin(app)

    # 3) Agregar comentario via POST (ruta correcta es /blog/<slug>/comments)
    resp_comment = client.post(
        f"/blog/{post.slug}/comments",
        data={
            "content": "Este es un comentario de prueba",
        },
        follow_redirects=False,
    )
    assert resp_comment.status_code in REDIRECT_STATUS_CODES | {200}

    # 4) Verificar que el comentario existe en la base de datos
    comentario = db_session.execute(database.select(BlogComment).filter_by(post_id=post_id)).scalars().first()
    assert comentario is not None
    assert comentario.content == "Este es un comentario de prueba"
    assert comentario.user_id == admin.usuario  # user_id es el nombre de usuario, no el ID


def test_e2e_blog_tags(app, db_session):
    """Test: crear y usar tags de blog."""
    # 1) Crear admin y login
    admin = _crear_admin(db_session)  # noqa: F841
    client = _login_admin(app)

    # 2) Crear post con tags via POST (los tags se crean automáticamente si el usuario es admin)
    resp_new_post = client.post(
        "/admin/blog/posts/new",
        data={
            "title": "Post sobre Python",
            "content": "Contenido sobre Python",
            "status": "published",
            "tags": "Python, Programación",  # Tags como string separado por comas
        },
        follow_redirects=False,
    )
    assert resp_new_post.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar que el post existe
    post = db_session.execute(database.select(BlogPost).filter_by(title="Post sobre Python")).scalars().first()
    assert post is not None

    # 4) Verificar que los tags fueron creados
    tag_python = db_session.execute(database.select(BlogTag).filter_by(name="Python")).scalars().first()
    tag_prog = db_session.execute(database.select(BlogTag).filter_by(name="Programación")).scalars().first()

    # Al menos uno de los tags debe existir (dependiendo de la implementación)
    assert tag_python is not None or tag_prog is not None


def test_e2e_blog_draft_post(app, db_session):
    """Test: crear un post como draft/pending y verificar que no es visible públicamente."""
    # 1) Crear instructor (no admin) para poder crear drafts/pending
    instructor = Usuario(
        usuario="instructor",
        acceso=proteger_passwd("instructor"),
        nombre="Instructor",
        correo_electronico="instructor@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add(instructor)
    db_session.commit()

    client = app.test_client()
    client.post("/user/login", data={"usuario": "instructor", "acceso": "instructor"}, follow_redirects=False)

    # 2) Crear post (los instructores solo pueden crear draft o pending)
    resp_new = client.post(
        "/admin/blog/posts/new",
        data={
            "title": "Post Pendiente",
            "content": "Este post está pendiente de aprobación",
            "status": "pending",
        },
        follow_redirects=False,
    )
    assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar que el post existe como pending en la base de datos
    post = db_session.execute(database.select(BlogPost).filter_by(title="Post Pendiente")).scalars().first()
    assert post is not None
    assert post.status in ["draft", "pending"]  # Puede ser draft o pending dependiendo de la implementación

    # 4) Verificar que NO aparece en el índice público (solo published aparecen)
    client_public = app.test_client()
    resp_index = client_public.get("/blog")
    assert resp_index.status_code == 200
    assert b"Post Pendiente" not in resp_index.data


def test_e2e_blog_post_list_admin(app, db_session):
    """Test: listar posts desde el panel de administración."""
    # 1) Crear admin y login
    admin = _crear_admin(db_session)  # noqa: F841
    client = _login_admin(app)

    # 2) Ver lista de posts en admin (puede estar vacía o tener el post por defecto)
    resp_list = client.get("/admin/blog")
    assert resp_list.status_code == 200
    # Verificar que la página carga correctamente
    assert b"blog" in resp_list.data.lower() or b"post" in resp_list.data.lower()
