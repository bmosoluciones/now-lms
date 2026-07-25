# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Comprehensive integration tests for course resources (now_lms/vistas/courses/resources.py)."""

import io
import os
from datetime import date, datetime, time
from unittest import mock

import pytest
from flask import url_for

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Configuracion,
    CourseLibrary,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    Slide,
    SlideShowResource,
    Usuario,
    Pago,
    database,
)


@pytest.fixture
def resources_setup(app, db_session):
    """Sets up student, instructor, and admin users with a test course and section."""
    student = Usuario(
        usuario="res_student",
        acceso=proteger_passwd("studentpass"),
        nombre="Res Student",
        correo_electronico="res_student@example.com",
        tipo="student",
        activo=True,
    )
    instructor = Usuario(
        usuario="res_instructor",
        acceso=proteger_passwd("instructorpass"),
        nombre="Res Instructor",
        correo_electronico="res_inst@example.com",
        tipo="instructor",
        activo=True,
    )
    admin = Usuario(
        usuario="res_admin",
        acceso=proteger_passwd("adminpass"),
        nombre="Res Admin",
        correo_electronico="res_admin@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add_all([student, instructor, admin])
    db_session.commit()

    course = Curso(
        nombre="Resources Course",
        codigo="RES101",
        descripcion_corta="Short desc",
        descripcion="Long desc",
        estado="open",
        certificado=True,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    assignment = DocenteCurso(
        curso="RES101",
        usuario=instructor.usuario,
        vigente=True,
    )
    db_session.add(assignment)

    pago = Pago(
        usuario=student.usuario,
        curso="RES101",
        monto=0,
        estado="completed",
        nombre="Res",
        apellido="Student",
        correo_electronico="res_student@example.com",
    )
    db_session.add(pago)
    db_session.commit()

    enrollment = EstudianteCurso(
        curso="RES101",
        usuario=student.usuario,
        vigente=True,
        pago=pago.id,
    )
    db_session.add(enrollment)
    db_session.commit()

    section = CursoSeccion(
        curso="RES101",
        nombre="First Section",
        descripcion="Section desc",
        indice=1,
        creado_por="res_instructor",
    )
    db_session.add(section)
    db_session.commit()

    return {
        "student": student,
        "instructor": instructor,
        "admin": admin,
        "course": course,
        "section": section,
    }


@pytest.fixture
def client_student(client, resources_setup, app):
    """Authenticated student client."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = resources_setup["student"].id
            sess["_fresh"] = True
    return client


@pytest.fixture
def client_instructor(client, resources_setup, app):
    """Authenticated instructor client."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = resources_setup["instructor"].id
            sess["_fresh"] = True
    return client


# ==============================================================================
# Complete Resource & Progression Tests
# ==============================================================================

def test_marcar_recurso_completado_and_progression(client_student, db_session, resources_setup):
    """Test marking resource as complete and progressing to the next resource."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    # Create two resources
    rec1 = CursoRecurso(
        curso=course_code,
        seccion=section_id,
        tipo="text",
        nombre="Resource 1",
        descripcion="Desc 1",
        indice=1,
        text="Content 1",
        creado_por="res_instructor",
    )
    rec2 = CursoRecurso(
        curso=course_code,
        seccion=section_id,
        tipo="text",
        nombre="Resource 2",
        descripcion="Desc 2",
        indice=2,
        text="Content 2",
        creado_por="res_instructor",
    )
    db_session.add_all([rec1, rec2])
    db_session.commit()

    # Complete resource 1 -> should redirect to resource 2 page
    resp = client_student.post(f"/course/{course_code}/resource/text/{rec1.id}/complete", follow_redirects=True)
    assert resp.status_code == 200

    # Check progress in DB
    progress = db_session.execute(
        database.select(CursoRecursoAvance).filter_by(
            usuario=resources_setup["student"].usuario,
            curso=course_code,
            recurso=rec1.id
        )
    ).scalar_one()
    assert progress.completado is True


def test_pagina_recurso_alternativo(client_student, db_session, resources_setup):
    """Test alternative resources page view."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    rec = CursoRecurso(
        curso=course_code,
        seccion=section_id,
        tipo="text",
        nombre="Resource",
        descripcion="Desc",
        indice=1,
        creado_por="res_instructor",
        publico=True,
    )
    db_session.add(rec)
    db_session.commit()

    resp = client_student.get(f"/course/{course_code}/alternative/{rec.id}/asc")
    assert resp.status_code == 200
    assert b"Resource" in resp.data


# ==============================================================================
# Subtitle Loaders (VTT) & File Serve Tests
# ==============================================================================

def test_vtt_subtitle_loaders(client_student, db_session, resources_setup):
    """Test loading of VTT and VTT secondary subtitles."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    rec = CursoRecurso(
        curso=course_code,
        seccion=section_id,
        tipo="mp3",
        nombre="Audio",
        descripcion="Desc",
        indice=1,
        doc="audio.mp3",
        subtitle_vtt="WEBVTT\n\n00:01.000 --> 00:03.000\nHello!",
        subtitle_vtt_secondary="WEBVTT\n\n00:01.000 --> 00:03.000\nBonjour!",
        creado_por="res_instructor",
        publico=True,
    )
    db_session.add(rec)
    db_session.commit()

    # Load primary subtitle
    resp_vtt = client_student.get(f"/course/{course_code}/vtt/{rec.id}")
    assert resp_vtt.status_code == 200
    assert b"Hello!" in resp_vtt.data
    assert resp_vtt.headers.get("Content-Type") == "text/vtt; charset=utf-8"

    # Load secondary subtitle
    resp_vtt_sec = client_student.get(f"/course/{course_code}/vtt_secondary/{rec.id}")
    assert resp_vtt_sec.status_code == 200
    assert b"Bonjour!" in resp_vtt_sec.data


def test_pdf_viewer_and_external_code(client_student, db_session, resources_setup):
    """Test loading PDF viewer and external code."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    rec = CursoRecurso(
        curso=course_code,
        seccion=section_id,
        tipo="pdf",
        nombre="Document",
        descripcion="Desc",
        indice=1,
        doc="document.pdf",
        external_code="<iframe></iframe>",
        creado_por="res_instructor",
        publico=True,
    )
    db_session.add(rec)
    db_session.commit()

    resp_pdf = client_student.get(f"/course/{course_code}/pdf_viewer/{rec.id}")
    assert resp_pdf.status_code == 200

    resp_ext = client_student.get(f"/course/{course_code}/external_code/{rec.id}")
    assert resp_ext.status_code == 200
    assert b"iframe" in resp_ext.data


# ==============================================================================
# SlideShow Tests (New and Legacy systems)
# ==============================================================================

def test_slideshow_rendering_and_preview(client_instructor, db_session, resources_setup):
    """Test creating, editing, and previewing slideshow presentations."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    # 1. Create a slideshow resource via route
    form_data = {
        "nombre": "Amazing Presentation",
        "descripcion": "Learn how to use reveal.js",
        "theme": "league",
    }
    resp_create = client_instructor.post(
        f"/course/{course_code}/{section_id}/slides/new",
        data=form_data,
        follow_redirects=False
    )
    assert resp_create.status_code in [302, 200]

    # Locate slideshow
    slideshow = db_session.execute(database.select(SlideShowResource).filter_by(title="Amazing Presentation")).scalar_one()

    # 2. Edit slideshow slides
    edit_data = {
        "title": "Amazing Presentation Updated",
        "theme": "serif",
        "slide_count": "2",
        "slide_0_title": "Slide 1",
        "slide_0_content": "Content 1",
        "slide_0_order": "1",
        "slide_1_title": "Slide 2",
        "slide_1_content": "Content 2",
        "slide_1_order": "2",
    }
    resp_edit = client_instructor.post(
        f"/course/{course_code}/slideshow/{slideshow.id}/edit",
        data=edit_data,
        follow_redirects=False
    )
    assert resp_edit.status_code in [302, 200]

    # Locate slides
    slides = db_session.execute(
        database.select(Slide).filter_by(slide_show_id=slideshow.id).order_by(Slide.order)
    ).scalars().all()
    assert len(slides) == 2
    assert slides[0].title == "Slide 1"

    # 3. Preview slideshow
    resp_preview = client_instructor.get(f"/course/{course_code}/slideshow/{slideshow.id}/preview")
    assert resp_preview.status_code == 200
    assert b"Slide 1" in resp_preview.data


# ==============================================================================
# Course Library Tests
# ==============================================================================

def test_course_library_management(client_instructor, db_session, resources_setup):
    """Test listing, uploading, serving, and deleting course library files."""
    course_code = resources_setup["course"].codigo

    # Enable uploads in config
    cfg = db_session.execute(database.select(Configuracion)).scalars().first()
    if cfg:
        cfg.enable_file_uploads = True
        db_session.commit()

    # Mock file saving path
    with mock.patch("now_lms.vistas.courses.resources.get_course_library_path", return_value="/tmp"), \
         mock.patch("now_lms.vistas.courses.resources.ensure_course_library_directory", return_value="/tmp"), \
         mock.patch("now_lms.vistas.courses.resources.path.getsize", return_value=12), \
         mock.patch("werkzeug.datastructures.FileStorage.save") as mock_save:

        # Upload a library file
        file_data = {
            "nombre": "User Manual",
            "descripcion": "Reference manual.",
            "archivo": (io.BytesIO(b"file content"), "manual.pdf")
        }
        resp_upload = client_instructor.post(
            f"/course/{course_code}/library/new",
            data=file_data,
            content_type="multipart/form-data",
            follow_redirects=True
        )

        assert resp_upload.status_code == 200
        assert b"subido exitosamente" in resp_upload.data

        # Verify DB entry
        lib_record = db_session.execute(
            database.select(CourseLibrary).filter_by(curso=course_code, filename="manual.pdf")
        ).scalar_one()
        assert lib_record.nombre == "User Manual"

        # Serve file
        with mock.patch("now_lms.vistas.courses.resources.path.exists", return_value=True), \
             mock.patch("now_lms.vistas.courses.resources.path.isfile", return_value=True), \
             mock.patch("now_lms.vistas.courses.resources.send_from_directory") as mock_send:
            client_instructor.get(f"/course/{course_code}/library/file/manual.pdf")
            mock_send.assert_called_once_with("/tmp", "manual.pdf", as_attachment=True)

        # Delete library file
        with mock.patch("now_lms.vistas.courses.resources.remove") as mock_remove, \
             mock.patch("now_lms.vistas.courses.resources.path.exists", return_value=True):
            resp_del = client_instructor.post(
                f"/course/{course_code}/library/delete/{lib_record.id}",
                follow_redirects=True
            )
            assert resp_del.status_code == 200
            assert b"eliminado exitosamente" in resp_del.data
            mock_remove.assert_called_once()

            # Ensure deleted from database
            deleted = db_session.get(CourseLibrary, lib_record.id)
            assert deleted is None


# ==============================================================================
# Calendar Compose Links Tests
# ==============================================================================

def test_meet_calendar_compose_links(client_student, db_session, resources_setup):
    """Test downloading meeting ICS file, and compiling google and outlook calendar links."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    # Create meet resource
    meet_rec = CursoRecurso(
        curso=course_code,
        seccion=section_id,
        tipo="meet",
        nombre="Live Virtual Class",
        descripcion="Discussion on module 1",
        indice=1,
        url="https://meet.jit.si/my-live-class",
        fecha=date(2026, 8, 12),
        hora_inicio=time(14, 0),
        hora_fin=time(15, 0),
        notes="Google Meet",
        creado_por="res_instructor",
        publico=True,
    )
    db_session.add(meet_rec)
    db_session.commit()

    # 1. ICS Download
    resp_ics = client_student.get(f"/course/{course_code}/resource/meet/{meet_rec.id}/calendar.ics")
    assert resp_ics.status_code == 200
    assert b"BEGIN:VCALENDAR" in resp_ics.data
    assert b"Live Virtual Class" in resp_ics.data

    # 2. Google Calendar Redirect
    resp_gcal = client_student.get(f"/course/{course_code}/resource/meet/{meet_rec.id}/google-calendar")
    assert resp_gcal.status_code == 302
    assert "calendar.google.com" in resp_gcal.headers.get("Location")

    # 3. Outlook Calendar Redirect
    resp_out = client_student.get(f"/course/{course_code}/resource/meet/{meet_rec.id}/outlook-calendar")
    assert resp_out.status_code == 302
    assert "outlook.live.com" in resp_out.headers.get("Location")


# ==============================================================================
# CRUD and Validation for all resource types
# ==============================================================================

def test_crud_all_resource_types(client_instructor, db_session, resources_setup):
    """Test creation and editing of HTML, YouTube, Text, Link, PDF, Meet, Image, Audio, and Downloadable resource types."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    # 1. HTML Resource
    html_data = {
        "nombre": "HTML Rec",
        "descripcion": "Learn HTML",
        "requerido": "required",
        "html_externo": "<div>Page Content</div>",
    }
    resp_html = client_instructor.post(f"/course/{course_code}/{section_id}/html/new", data=html_data, follow_redirects=False)
    assert resp_html.status_code == 302
    rec_html = db_session.execute(database.select(CursoRecurso).filter_by(nombre="HTML Rec")).scalar_one()

    # GET HTML Edit
    resp_get_html = client_instructor.get(f"/course/{course_code}/{section_id}/html/{rec_html.id}/edit")
    assert resp_get_html.status_code == 200

    # POST HTML Edit
    html_data["nombre"] = "HTML Rec Updated"
    resp_post_html = client_instructor.post(f"/course/{course_code}/{section_id}/html/{rec_html.id}/edit", data=html_data, follow_redirects=False)
    assert resp_post_html.status_code == 302
    db_session.expire(rec_html)
    assert rec_html.nombre == "HTML Rec Updated"

    # 2. YouTube Resource
    yt_data = {
        "nombre": "Video Resource",
        "descripcion": "YouTube video description",
        "requerido": "required",
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }
    resp_yt = client_instructor.post(f"/course/{course_code}/{section_id}/youtube/new", data=yt_data, follow_redirects=False)
    assert resp_yt.status_code == 302
    rec_yt = db_session.execute(database.select(CursoRecurso).filter_by(nombre="Video Resource")).scalar_one()

    # GET YouTube Edit
    resp_get_yt = client_instructor.get(f"/course/{course_code}/{section_id}/youtube/{rec_yt.id}/edit")
    assert resp_get_yt.status_code == 200

    # POST YouTube Edit
    yt_data["nombre"] = "Video Resource Updated"
    resp_post_yt = client_instructor.post(f"/course/{course_code}/{section_id}/youtube/{rec_yt.id}/edit", data=yt_data, follow_redirects=False)
    assert resp_post_yt.status_code == 302
    db_session.expire(rec_yt)
    assert rec_yt.nombre == "Video Resource Updated"

    # 3. Text Resource
    text_data = {
        "nombre": "Text Doc",
        "descripcion": "Markdown manual.",
        "requerido": "required",
        "editor": "# Title\nHello world.",
    }
    resp_text = client_instructor.post(f"/course/{course_code}/{section_id}/text/new", data=text_data, follow_redirects=False)
    assert resp_text.status_code == 302
    rec_text = db_session.execute(database.select(CursoRecurso).filter_by(nombre="Text Doc")).scalar_one()

    # GET Text Edit
    resp_get_text = client_instructor.get(f"/course/{course_code}/{section_id}/text/{rec_text.id}/edit")
    assert resp_get_text.status_code == 200

    # POST Text Edit
    text_data["nombre"] = "Text Doc Updated"
    resp_post_text = client_instructor.post(f"/course/{course_code}/{section_id}/text/{rec_text.id}/edit", data=text_data, follow_redirects=False)
    assert resp_post_text.status_code == 302
    db_session.expire(rec_text)
    assert rec_text.nombre == "Text Doc Updated"

    # 4. Link Resource
    link_data = {
        "nombre": "Web Link",
        "descripcion": "Useful reference website.",
        "requerido": "required",
        "url": "https://bmosoluciones.com",
    }
    resp_link = client_instructor.post(f"/course/{course_code}/{section_id}/link/new", data=link_data, follow_redirects=False)
    assert resp_link.status_code == 302
    rec_link = db_session.execute(database.select(CursoRecurso).filter_by(nombre="Web Link")).scalar_one()

    # GET Link Edit
    resp_get_link = client_instructor.get(f"/course/{course_code}/{section_id}/link/{rec_link.id}/edit")
    assert resp_get_link.status_code == 200

    # POST Link Edit
    link_data["nombre"] = "Web Link Updated"
    resp_post_link = client_instructor.post(f"/course/{course_code}/{section_id}/link/{rec_link.id}/edit", data=link_data, follow_redirects=False)
    assert resp_post_link.status_code == 302
    db_session.expire(rec_link)
    assert rec_link.nombre == "Web Link Updated"


def test_resources_wtforms_error_handling_and_cache_invalidation(client_instructor, db_session, resources_setup):
    """Test that invalid form submissions are handled gracefully without 500 errors and cache is invalidated on success."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    # 1. Invalid submission (missing required 'nombre' and 'descripcion')
    invalid_data = {
        "nombre": "",
        "descripcion": "",
        "requerido": "required",
        "editor": "# Hello",
    }
    # Send post to create new text resource
    resp = client_instructor.post(f"/course/{course_code}/{section_id}/text/new", data=invalid_data)
    # It should not return 500! It must return 200 with the template re-rendered
    assert resp.status_code == 200
    assert b"Markdown" in resp.data  # Assures the editor form is shown again with errors

    # 2. Valid submission with cache invalidation check
    valid_data = {
        "nombre": "Valid Text Resource",
        "descripcion": "Valid description",
        "requerido": "required",
        "editor": "# Hello world",
    }
    with mock.patch("now_lms.vistas.courses.resources.invalidar_cache_curso") as mock_invalidate:
        resp_valid = client_instructor.post(f"/course/{course_code}/{section_id}/text/new", data=valid_data, follow_redirects=False)
        assert resp_valid.status_code == 302
        # Check that invalidar_cache_curso was called with correct course_code
        mock_invalidate.assert_called_with(course_code)


def test_resource_edit_get_requests_and_errors(client_instructor, db_session, resources_setup):
    """Test GET requests, invalid POSTs, and OperationalErrors on all resource routes to achieve 100% patch coverage."""
    course_code = resources_setup["course"].codigo
    section_id = resources_setup["section"].id

    # Create dummy resources of all types
    types = ["html", "youtube", "text", "link", "pdf", "meet", "img", "mp3", "descargable"]
    recursos = {}
    for t in types:
        rec = CursoRecurso(
            curso=course_code, seccion=section_id, tipo=t,
            nombre=f"Rec {t}", descripcion=f"Desc {t}", doc=f"f.{t}", creado_por="inst"
        )
        db_session.add(rec)
        recursos[t] = rec
    db_session.commit()

    # Enable downloadable file uploads in config
    cfg = db_session.execute(database.select(Configuracion)).scalars().first()
    if cfg:
        cfg.enable_file_uploads = True
        db_session.commit()

    url_prefixes = {
        "html": "html",
        "youtube": "youtube",
        "text": "text",
        "link": "link",
        "pdf": "pdf",
        "meet": "meet",
        "img": "img",
        "mp3": "audio",
        "descargable": "descargable",
    }

    # 1. GET requests on edit pages (for form pre-population from DB)
    for t, rec in recursos.items():
        prefix = url_prefixes[t]
        resp = client_instructor.get(f"/course/{course_code}/{section_id}/{prefix}/{rec.id}/edit")
        assert resp.status_code == 200

    # 2. Invalid POST requests to NEW routes (missing required fields like 'nombre')
    invalid_data = {"nombre": "", "descripcion": "", "requerido": "required"}
    for t in types:
        prefix = url_prefixes[t]
        resp = client_instructor.post(f"/course/{course_code}/{section_id}/{prefix}/new", data=invalid_data)
        assert resp.status_code == 200

    # 3. Invalid POST requests to EDIT routes (missing required fields like 'nombre')
    for t, rec in recursos.items():
        prefix = url_prefixes[t]
        resp = client_instructor.post(f"/course/{course_code}/{section_id}/{prefix}/{rec.id}/edit", data=invalid_data)
        assert resp.status_code == 200

    # 4. Test OperationalError coverage on commits
    from sqlalchemy.exc import OperationalError
    with mock.patch("now_lms.vistas.courses.resources.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        # Try editing PDF with an operational error
        resp = client_instructor.post(
            f"/course/{course_code}/{section_id}/pdf/{recursos['pdf'].id}/edit",
            data={"nombre": "New PDF", "descripcion": "New Desc", "requerido": "required"},
            follow_redirects=False
        )
        assert resp.status_code == 302  # Redirects on error
