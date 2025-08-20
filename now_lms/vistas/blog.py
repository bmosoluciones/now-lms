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

"""Blog views."""

import re

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime, timezone

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, func, or_

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, BlogComment, BlogPost, BlogTag, database, select
from now_lms.forms import BlogCommentForm, BlogPostForm, BlogTagForm
from now_lms.logs import log

# Route constants
ROUTE_BLOG_POST = "blog.blog_post"
ROUTE_BLOG_ADMIN_INDEX = "blog.admin_blog_index"

blog = Blueprint("blog", __name__, template_folder=DIRECTORIO_PLANTILLAS)


def create_slug(title):
    """Create a URL-friendly slug from title."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def ensure_unique_slug(title, post_id=None):
    """Ensure slug is unique by appending number if needed."""
    base_slug = create_slug(title)
    slug = base_slug
    counter = 1

    while True:
        query = database.select(BlogPost).filter(BlogPost.slug == slug)
        if post_id:
            query = query.filter(BlogPost.id != post_id)

        if not database.session.execute(query).scalars().first():
            break

        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


# Public blog routes
@blog.route("/blog")
def blog_index():
    """Public blog index page."""
    page = request.args.get("page", 1, type=int)
    tag_slug = request.args.get("tag")
    author_id = request.args.get("author")

    query = select(BlogPost).filter(BlogPost.status == "published")

    if tag_slug:
        tag = database.session.execute(select(BlogTag).filter(BlogTag.slug == tag_slug)).scalar_one_or_none()
        if tag:
            query = query.filter(BlogPost.tags.contains(tag))

    if author_id:
        query = query.filter(BlogPost.author_id == author_id)

    query = query.order_by(BlogPost.published_at.desc())

    pagination = database.paginate(
        query,
        page=page,
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    # Get all tags for filter
    tags = database.session.execute(database.select(BlogTag).order_by(BlogTag.name)).scalars().all()

    return render_template(
        "blog/public_index.html",
        posts=pagination.items,
        pagination=pagination,
        tags=tags,
        current_tag=tag_slug,
        current_author=author_id,
    )


@blog.route("/blog/<slug>")
def blog_post(slug):
    """Display a single blog post."""
    post = database.session.execute(
        database.select(BlogPost).filter(and_(BlogPost.slug == slug, BlogPost.status == "published"))
    ).scalar_one_or_none()
    if not post:
        abort(404)

    # Get comments for this post
    comments = (
        database.session.execute(
            database.select(BlogComment)
            .filter(and_(BlogComment.post_id == post.id, BlogComment.status == "visible"))
            .order_by(BlogComment.timestamp)
        )
        .scalars()
        .all()
    )

    # Comment form
    comment_form = BlogCommentForm() if current_user.is_authenticated and post.allow_comments else None

    return render_template("blog/post_detail.html", post=post, comments=comments, comment_form=comment_form)


@blog.route("/blog/<slug>/comments", methods=["POST"])
@login_required
def add_comment(slug):
    """Add a comment to a blog post."""
    post = database.session.execute(
        database.select(BlogPost).filter(and_(BlogPost.slug == slug, BlogPost.status == "published"))
    ).scalar_one_or_none()
    if not post:
        abort(404)

    if not post.allow_comments:
        flash("Los comentarios están deshabilitados para esta entrada.", "warning")
        return redirect(url_for(ROUTE_BLOG_POST, slug=slug))

    form = BlogCommentForm()
    if form.validate_on_submit() or request.method == "POST":
        comment = BlogComment(post_id=post.id, user_id=current_user.usuario, content=form.content.data, status="visible")
        database.session.add(comment)

        # Update comment count
        post.comment_count = (
            database.session.execute(
                database.select(func.count(BlogComment.id)).filter(
                    and_(BlogComment.post_id == post.id, BlogComment.status == "visible")
                )
            ).scalar()
            + 1
        )

        database.session.commit()
        flash("Comentario agregado exitosamente.", "success")
    else:
        flash("Error al agregar el comentario.", "error")

    return redirect(url_for(ROUTE_BLOG_POST, slug=slug))


@blog.route("/blog/comments/<comment_id>/flag", methods=["POST"])
@login_required
def flag_comment(comment_id):
    """Flag a comment as inappropriate."""
    comment = database.session.get(BlogComment, comment_id)
    if not comment:
        abort(404)

    comment.status = "flagged"
    database.session.commit()

    flash("Comentario marcado como inapropiado.", "info")
    return redirect(url_for(ROUTE_BLOG_POST, slug=comment.post.slug))


# Admin blog routes
@blog.route("/admin/blog")
@login_required
@perfil_requerido("admin")
def admin_blog_index():
    """Admin blog management index."""
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "all")

    query = select(BlogPost)

    if status_filter != "all":
        query = query.filter(BlogPost.status == status_filter)

    query = query.order_by(BlogPost.timestamp.desc())

    pagination = database.paginate(
        query,
        page=page,
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template(
        "blog/admin_index.html", posts=pagination.items, pagination=pagination, current_status=status_filter
    )


@blog.route("/admin/blog/posts/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def admin_create_post():
    """Create a new blog post."""
    form = BlogPostForm()

    # Set initial status based on user role
    if current_user.tipo == "admin":
        form.status.data = "published"
    else:
        form.status.data = "pending"
        # Instructors can only create drafts or pending posts
        form.status.choices = [("draft", "Borrador"), ("pending", "Pendiente")]

    if form.validate_on_submit() or request.method == "POST":
        slug = ensure_unique_slug(form.title.data)

        post = BlogPost(
            title=form.title.data,
            slug=slug,
            content=form.content.data,
            author_id=current_user.usuario,
            status=form.status.data,
            allow_comments=form.allow_comments.data,
        )

        if form.status.data == "published":
            post.published_at = datetime.now(timezone.utc)

        database.session.add(post)
        database.session.flush()

        # Handle tags
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(",") if name.strip()]
            for tag_name in tag_names:
                tag_slug = create_slug(tag_name)
                tag = database.session.execute(select(BlogTag).filter(BlogTag.slug == tag_slug)).scalars().first()
                if not tag:
                    # Only admins can create new tags
                    if current_user.tipo == "admin":
                        tag = BlogTag(name=tag_name, slug=tag_slug)
                        database.session.add(tag)
                        database.session.flush()

                if tag and tag not in post.tags:
                    post.tags.append(tag)

        database.session.commit()
        log.info(f"Blog post created: {post.title} by {current_user.usuario}")
        flash("Entrada de blog creada exitosamente.", "success")

        if current_user.tipo == "admin":
            return redirect(url_for(ROUTE_BLOG_ADMIN_INDEX))
        else:
            return redirect(url_for("blog.instructor_blog_index"))

    return render_template("blog/post_form.html", form=form, title="Nueva Entrada")


@blog.route("/admin/blog/posts/<post_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def admin_edit_post(post_id):
    """Edit a blog post."""
    post = database.session.get(BlogPost, post_id)
    if not post:
        abort(404)

    # Check permissions
    if current_user.tipo != "admin" and post.author_id != current_user.usuario:
        abort(403)

    form = BlogPostForm(obj=post)

    # Set form choices based on user role
    if current_user.tipo != "admin":
        form.status.choices = [("draft", "Borrador"), ("pending", "Pendiente")]

    # Pre-populate tags
    tag_names = [tag.name for tag in post.tags]
    form.tags.data = ", ".join(tag_names)

    if form.validate_on_submit() or request.method == "POST":
        post.title = form.title.data
        post.slug = ensure_unique_slug(form.title.data, post.id)
        post.content = form.content.data
        post.allow_comments = form.allow_comments.data

        # Only allow status change if admin or if changing to pending
        if current_user.tipo == "admin" or (form.status.data == "pending" and post.status == "draft"):
            old_status = post.status
            post.status = form.status.data

            # Set published_at if publishing for first time
            if form.status.data == "published" and old_status != "published":
                post.published_at = datetime.now(timezone.utc)

        # Clear existing tags
        post.tags.clear()

        # Handle tags
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(",") if name.strip()]
            for tag_name in tag_names:
                tag_slug = create_slug(tag_name)
                tag = database.session.execute(select(BlogTag).filter(BlogTag.slug == tag_slug)).scalars().first()
                if not tag and current_user.tipo == "admin":
                    tag = BlogTag(name=tag_name, slug=tag_slug)
                    database.session.add(tag)
                    database.session.flush()

                if tag:
                    post.tags.append(tag)

        database.session.commit()
        log.info(f"Blog post updated: {post.title} by {current_user.usuario}")
        flash("Entrada de blog actualizada exitosamente.", "success")

        if current_user.tipo == "admin":
            return redirect(url_for(ROUTE_BLOG_ADMIN_INDEX))
        else:
            return redirect(url_for("blog.instructor_blog_index"))

    return render_template("blog/post_form.html", form=form, title="Editar Entrada", post=post)


@blog.route("/admin/blog/posts/<post_id>/approve", methods=["POST"])
@login_required
@perfil_requerido("admin")
def approve_post(post_id):
    """Approve a pending blog post."""
    post = database.session.get(BlogPost, post_id)
    if not post:
        abort(404)

    post.status = "published"
    post.published_at = datetime.now(timezone.utc)
    database.session.commit()

    flash(f"Entrada '{post.title}' aprobada y publicada.", "success")
    return redirect(url_for(ROUTE_BLOG_ADMIN_INDEX))


@blog.route("/admin/blog/posts/<post_id>/ban", methods=["POST"])
@login_required
@perfil_requerido("admin")
def ban_post(post_id):
    """Ban a blog post."""
    post = database.session.get(BlogPost, post_id)
    if not post:
        abort(404)

    post.status = "banned"
    database.session.commit()

    flash(f"Entrada '{post.title}' ha sido baneada.", "warning")
    return redirect(url_for(ROUTE_BLOG_ADMIN_INDEX))


# Tag management routes
@blog.route("/admin/blog/tags")
@login_required
@perfil_requerido("admin")
def admin_tags():
    """Manage blog tags."""
    page = request.args.get("page", 1, type=int)

    pagination = database.paginate(
        database.select(BlogTag).order_by(BlogTag.name),
        page=page,
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    form = BlogTagForm()

    return render_template("blog/admin_tags.html", tags=pagination.items, pagination=pagination, form=form)


@blog.route("/admin/blog/tags", methods=["POST"])
@login_required
@perfil_requerido("admin")
def create_tag():
    """Create a new blog tag."""
    form = BlogTagForm()

    if form.validate_on_submit() or request.method == "POST":
        slug = create_slug(form.name.data)

        # Check if tag already exists
        existing_tag = (
            database.session.execute(select(BlogTag).filter(or_(BlogTag.name == form.name.data, BlogTag.slug == slug)))
            .scalars()
            .first()
        )

        if existing_tag:
            flash("Una etiqueta con ese nombre ya existe.", "error")
        else:
            tag = BlogTag(name=form.name.data, slug=slug)
            database.session.add(tag)
            database.session.commit()
            flash("Etiqueta creada exitosamente.", "success")

    return redirect(url_for("blog.admin_tags"))


@blog.route("/admin/blog/tags/<tag_id>", methods=["DELETE"])
@login_required
@perfil_requerido("admin")
def delete_tag(tag_id):
    """Delete a blog tag."""
    tag = database.session.get(BlogTag, tag_id)
    if not tag:
        abort(404)

    database.session.delete(tag)
    database.session.commit()

    flash(f"Etiqueta '{tag.name}' eliminada.", "info")
    return redirect(url_for("blog.admin_tags"))


# Comment management routes
@blog.route("/admin/blog/comments/<comment_id>/ban", methods=["POST"])
@login_required
@perfil_requerido("admin")
def ban_comment(comment_id):
    """Ban a comment."""
    comment = database.session.get(BlogComment, comment_id)
    if not comment:
        abort(404)

    # Check permissions - admin or post author
    if current_user.tipo != "admin" and comment.post.author_id != current_user.usuario:
        abort(403)

    comment.status = "banned"

    # Update comment count
    comment.post.comment_count = database.session.execute(
        select(func.count(BlogComment.id)).filter(
            and_(BlogComment.post_id == comment.post_id, BlogComment.status == "visible")
        )
    ).scalar()

    database.session.commit()

    flash("Comentario baneado.", "warning")
    return redirect(url_for(ROUTE_BLOG_POST, slug=comment.post.slug))


@blog.route("/admin/blog/comments/<comment_id>", methods=["DELETE"])
@login_required
@perfil_requerido("admin")
def delete_comment(comment_id):
    """Delete a comment."""
    comment = database.session.get(BlogComment, comment_id)
    if not comment:
        abort(404)

    # Check permissions - admin or post author
    if current_user.tipo != "admin" and comment.post.author_id != current_user.usuario:
        abort(403)

    post_slug = comment.post.slug
    database.session.delete(comment)

    # Update comment count
    post = comment.post
    post.comment_count = database.session.execute(
        select(func.count(BlogComment.id)).filter(and_(BlogComment.post_id == post.id, BlogComment.status == "visible"))
    ).scalar()

    database.session.commit()

    flash("Comentario eliminado.", "info")
    return redirect(url_for(ROUTE_BLOG_POST, slug=post_slug))


# Instructor blog routes
@blog.route("/instructor/blog")
@login_required
@perfil_requerido("instructor")
def instructor_blog_index():
    """Instructor blog management index."""
    page = request.args.get("page", 1, type=int)

    if current_user.tipo == "admin":
        query = select(BlogPost)
    else:
        query = select(BlogPost).filter(BlogPost.author_id == current_user.usuario)

    query = query.order_by(BlogPost.timestamp.desc())

    pagination = database.paginate(
        query,
        page=page,
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template("blog/instructor_index.html", posts=pagination.items, pagination=pagination)
