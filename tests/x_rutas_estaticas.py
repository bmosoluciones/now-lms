# Copyright 2021 -2023 William José Moreno Reyes
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
#
# Contributors:
# - William José Moreno Reyes


"""
url_map: 2024-02-05

 <Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
 <Rule '/static/flask_mde/<filename>' (HEAD, OPTIONS, GET) -> flask_mde.static>,
 <Rule '/category/new' (HEAD, POST, OPTIONS, GET) -> category.new_category>,
 <Rule '/category/list' (HEAD, OPTIONS, GET) -> category.categories>,
 <Rule '/category/<ulid>/delete' (HEAD, OPTIONS, GET) -> category.delete_category>,
 <Rule '/category/<ulid>/edit' (HEAD, POST, OPTIONS, GET) -> category.edit_category>,
 <Rule '/certificate/new' (HEAD, POST, OPTIONS, GET) -> certificate.new_certificate>,
 <Rule '/certificate/list' (HEAD, OPTIONS, GET) -> certificate.certificados>,
 <Rule '/certificate/<ulid>/delete' (HEAD, OPTIONS, GET) -> certificate.delete_certificate>,
 <Rule '/certificate/<ulid>/edit' (HEAD, POST, OPTIONS, GET) -> certificate.edit_certificate>,
 <Rule '/course/<course_code>/view' (HEAD, OPTIONS, GET) -> course.curso>,
 <Rule '/course/<course_code>/enroll' (HEAD, OPTIONS, GET) -> course.course_enroll>,
 <Rule '/course/<course_code>/take' (HEAD, OPTIONS, GET) -> course.tomar_curso>,
 <Rule '/course/<course_code>/moderate' (HEAD, OPTIONS, GET) -> course.moderar_curso>,
 <Rule '/course/<course_code>/admin' (HEAD, OPTIONS, GET) -> course.administrar_curso>,
 <Rule '/course/new_curse' (HEAD, POST, OPTIONS, GET) -> course.nuevo_curso>,
 <Rule '/course/<course_code>/edit' (HEAD, POST, OPTIONS, GET) -> course.editar_curso>,
 <Rule '/course/<course_code>/new_seccion' (HEAD, POST, OPTIONS, GET) -> course.nuevo_seccion>,
 <Rule '/course/<course_code>/<seccion>/edit' (HEAD, POST, OPTIONS, GET) -> course.editar_seccion>,
 <Rule '/course/<course_code>/seccion/increment/<indice>' (HEAD, OPTIONS, GET) -> course.incrementar_indice_seccion>,
 <Rule '/course/<course_code>/seccion/decrement/<indice>' (HEAD, OPTIONS, GET) -> course.reducir_indice_seccion>,
 <Rule '/course/resource/<cource_code>/<seccion_id>/<task>/<resource_index>' (HEAD, OPTIONS, GET) -> course.modificar_orden_recurso>,
 <Rule '/course/<curso_id>/delete_recurso/<seccion>/<id_>' (HEAD, OPTIONS, GET) -> course.eliminar_recurso>,
 <Rule '/course/<curso_id>/delete_seccion/<id_>' (HEAD, OPTIONS, GET) -> course.eliminar_seccion>,
 <Rule '/course/<course_id>/delete_curse' (HEAD, OPTIONS, GET) -> course.eliminar_curso>,
 <Rule '/course/change_curse_status' (HEAD, OPTIONS, GET) -> course.cambiar_estatus_curso>,
 <Rule '/course/change_curse_public' (HEAD, OPTIONS, GET) -> course.cambiar_curso_publico>,
 <Rule '/course/change_curse_seccion_public' (HEAD, OPTIONS, GET) -> course.cambiar_seccion_publico>,
 <Rule '/course/<curso_id>/resource/<resource_type>/<codigo>' (HEAD, OPTIONS, GET) -> course.pagina_recurso>,
 <Rule '/course/<curso_id>/resource/<resource_type>/<codigo>/complete' (HEAD, OPTIONS, GET) -> course.marcar_recurso_completado>,
 <Rule '/course/<curso_id>/alternative/<codigo>/<order>' (HEAD, OPTIONS, GET) -> course.pagina_recurso_alternativo>,
 <Rule '/course/<course_code>/<seccion>/new_resource' (HEAD, OPTIONS, GET) -> course.nuevo_recurso>,
 <Rule '/course/<course_code>/<seccion>/youtube/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_youtube_video>,
 <Rule '/course/<course_code>/<seccion>/text/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_text>,
 <Rule '/course/<course_code>/<seccion>/link/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_link>,
 <Rule '/course/<course_code>/<seccion>/pdf/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_pdf>,
 <Rule '/course/<course_code>/<seccion>/meet/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_meet>,
 <Rule '/course/<course_code>/<seccion>/img/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_img>,
 <Rule '/course/<course_code>/<seccion>/audio/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_audio>,
 <Rule '/course/<course_code>/<seccion>/html/new' (HEAD, POST, OPTIONS, GET) -> course.nuevo_recurso_html>,
 <Rule '/course/<course_code>/files/<recurso_code>' (HEAD, OPTIONS, GET) -> course.recurso_file>,
 <Rule '/course/<course_code>/external_code/<recurso_code>' (HEAD, OPTIONS, GET) -> course.external_code>,
 <Rule '/course/slide_show/<recurso_code>' (HEAD, OPTIONS, GET) -> course.slide_show>,
 <Rule '/course/<course_code>/md_to_html/<recurso_code>' (HEAD, OPTIONS, GET) -> course.markdown_a_html>,
 <Rule '/course/<course_code>/description' (HEAD, OPTIONS, GET) -> course.curso_descripcion_a_html>,
 <Rule '/course/<course_code>/description/<resource>' (HEAD, OPTIONS, GET) -> course.recurso_descripcion_a_html>,
 <Rule '/course/explore' (HEAD, OPTIONS, GET) -> course.lista_cursos>,
 <Rule '/group/new' (HEAD, POST, OPTIONS, GET) -> group.nuevo_grupo>,
 <Rule '/group/set_tutor' (POST, OPTIONS) -> group.agrega_tutor_a_grupo>,
 <Rule '/home' (HEAD, OPTIONS, GET) -> home.pagina_de_inicio>,
 <Rule '/' (HEAD, OPTIONS, GET) -> home.pagina_de_inicio>,
 <Rule '/home/panel' (HEAD, OPTIONS, GET) -> home.panel>,
 <Rule '/message/<ulid>' (HEAD, OPTIONS, GET) -> msg.mensaje>,
 <Rule '/message/new' (HEAD, POST, OPTIONS, GET) -> msg.nuevo_mensaje>,
 <Rule '/program/new' (HEAD, POST, OPTIONS, GET) -> program.nuevo_programa>,
 <Rule '/program/list' (HEAD, OPTIONS, GET) -> program.programas>,
 <Rule '/program/<ulid>/delete' (HEAD, OPTIONS, GET) -> program.delete_program>,
 <Rule '/program/<ulid>/edit' (HEAD, POST, OPTIONS, GET) -> program.edit_program>,
 <Rule '/program/<codigo>/courses' (HEAD, OPTIONS, GET) -> program.programa_cursos>,
 <Rule '/program/<codigo>' (HEAD, OPTIONS, GET) -> program.pagina_programa>,
 <Rule '/program/explore' (HEAD, OPTIONS, GET) -> program.lista_programas>,
 <Rule '/resource/new' (HEAD, POST, OPTIONS, GET) -> resource.new_resource>,
 <Rule '/resource/list' (HEAD, OPTIONS, GET) -> resource.lista_de_recursos>,
 <Rule '/resource/<resource_code>/donwload' (HEAD, OPTIONS, GET) -> resource.descargar_recurso>,
 <Rule '/resource/<ulid>/delete' (HEAD, OPTIONS, GET) -> resource.delete_resource>,
 <Rule '/resource/<ulid>/update' (HEAD, POST, OPTIONS, GET) -> resource.edit_resource>,
 <Rule '/resource/<resource_code>' (HEAD, OPTIONS, GET) -> resource.vista_recurso>,
 <Rule '/resource/explore' (HEAD, OPTIONS, GET) -> resource.lista_recursos>,
 <Rule '/setting/theming' (HEAD, POST, OPTIONS, GET) -> setting.personalizacion>,
 <Rule '/setting/general' (HEAD, POST, OPTIONS, GET) -> setting.configuracion>,
 <Rule '/setting/mail' (HEAD, POST, OPTIONS, GET) -> setting.mail>,
 <Rule '/setting/delete_site_logo' (HEAD, OPTIONS, GET) -> setting.elimina_logo>,
 <Rule '/tag/new' (HEAD, POST, OPTIONS, GET) -> tag.new_tag>,
 <Rule '/tag/list' (HEAD, OPTIONS, GET) -> tag.tags>,
 <Rule '/tag/<ulid>/delete' (HEAD, OPTIONS, GET) -> tag.delete_tag>,
 <Rule '/tag/<ulid>/edit' (HEAD, POST, OPTIONS, GET) -> tag.edit_tag>,
 <Rule '/user/login' (HEAD, POST, OPTIONS, GET) -> user.inicio_sesion>,
 <Rule '/user/logout' (HEAD, OPTIONS, GET) -> user.cerrar_sesion>,
 <Rule '/user/logon' (HEAD, POST, OPTIONS, GET) -> user.crear_cuenta>,
 <Rule '/user/new_user' (HEAD, POST, OPTIONS, GET) -> user.crear_usuario>,
 <Rule '/admin/panel' (HEAD, OPTIONS, GET) -> admin_profile.pagina_admin>,
 <Rule '/admin/users/list' (HEAD, OPTIONS, GET) -> admin_profile.usuarios>,
 <Rule '/admin/users/set_active/<user_id>' (HEAD, OPTIONS, GET) -> admin_profile.activar_usuario>,
 <Rule '/admin/users/set_inactive/<user_id>' (HEAD, OPTIONS, GET) -> admin_profile.inactivar_usuario>,
 <Rule '/admin/users/delete/<user_id>' (HEAD, OPTIONS, GET) -> admin_profile.eliminar_usuario>,
 <Rule '/admin/users/list_inactive' (HEAD, OPTIONS, GET) -> admin_profile.usuarios_inactivos>,
 <Rule '/admin/user/change_type' (HEAD, OPTIONS, GET) -> admin_profile.cambiar_tipo_usario>,
 <Rule '/instructor' (HEAD, OPTIONS, GET) -> instructor_profile.pagina_instructor>,
 <Rule '/instructor/courses_list' (HEAD, OPTIONS, GET) -> instructor_profile.cursos>,
 <Rule '/instructor/group/list' (HEAD, OPTIONS, GET) -> instructor_profile.lista_grupos>,
 <Rule '/group/<ulid>' (HEAD, OPTIONS, GET) -> instructor_profile.grupo>,
 <Rule '/group/remove/<group>/<user>' (HEAD, OPTIONS, GET) -> instructor_profile.elimina_usuario__grupo>,
 <Rule '/group/add' (POST, OPTIONS) -> instructor_profile.agrega_usuario_a_grupo>,
 <Rule '/moderator' (HEAD, OPTIONS, GET) -> moderator_profile.pagina_moderador>,
 <Rule '/student' (HEAD, OPTIONS, GET) -> user_profile.pagina_estudiante>,
 <Rule '/perfil' (HEAD, OPTIONS, GET) -> user_profile.perfil>,
 <Rule '/user/<id_usuario>' (HEAD, OPTIONS, GET) -> user_profile.usuario>,
 <Rule '/perfil/edit/<ulid>' (HEAD, POST, OPTIONS, GET) -> user_profile.edit_perfil>,
 <Rule '/perfil/<ulid>/delete_logo' (HEAD, OPTIONS, GET) -> user_profile.elimina_logo_usuario>,
 <Rule '/_uploads/<setname>/<filename>' (HEAD, OPTIONS, GET) -> _uploads.uploaded_file>])
"""


from collections import namedtuple

Ruta = namedtuple(
    "Ruta",
    [
        # Route to test
        "ruta",
        # Expected HTTP response
        "admin",
        "no_session",
        "user",
        "moderator",
        "instructor",
        # Test text to compare aganist page content
        "texto",
        "como_user",
        "como_moderador",
        "como_instructor",
        "como_admin",
    ],
)

"""
Copy pasta to create a new route to test.

Ruta(
        ruta="",
        no_session=100,
        admin=100,
        user=100,
        moderator=100,
        instructor=100,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
"""

rutas_estaticas = [
    # <---------------------------------------------------------------------> #
    # Home page
    # <---------------------------------------------------------------------> #
    Ruta(
        ruta="/home",
        admin=200,
        no_session=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[
            "NOW LMS".encode("utf-8"),
            "Aplicación para gestión del aprendizaje.".encode("utf-8"),
            "NOW LMS".encode("utf-8"),
            "Sistema de aprendizaje en linea.".encode("utf-8"),
            "Welcome! This is your first course.".encode("utf-8"),
        ],
        como_user=[b"Dania", b"Mendez"],
        como_moderador=[b"Abner", b"Romero"],
        como_instructor=[b"Nemesio", b"Reyes"],
        como_admin=[
            "Cerrar Sesión".encode("utf-8"),
            "Administración".encode("utf-8"),
            b"System",
            b"Administrator",
            "Manual de Administración".encode("utf-8"),
        ],
    ),
    # <---------------------------------------------------------------------> #
    # Keep in the same order that the url_map:
    #     >>> from now_lms import app
    #     >>> app.url_map
    # <---------------------------------------------------------------------> #
    Ruta(
        ruta="/category/new",
        no_session=302,
        admin=200,
        user=403,
        moderator=403,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/category/list",
        no_session=302,
        admin=200,
        user=403,
        moderator=403,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/category/01HNP0TTQNTR03J7ZQHR09YMJK/edit",  # Hard coded ULID in test data creation
        no_session=302,
        admin=200,
        user=403,
        moderator=403,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/category/01HNP0TTQNTR03J7ZQHR09YMJK/delete",
        no_session=302,
        admin=302,  # Delete return a redirect
        user=403,
        moderator=403,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/certificate/new",
        no_session=302,
        admin=200,
        user=403,
        moderator=403,
        instructor=403,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[
            b"Crear nuevo Certificado.",
            b"Certificado",
            b"Descripcion",
            b"Crear Certificado",
            b"""<button class="w-10 btn btn-lg btn-primary btn-block" type="submit">Crear Certificado</button>""",
        ],
    ),
    Ruta(
        ruta="/certificate/list",
        no_session=302,
        admin=200,
        user=403,
        moderator=403,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[
            b"Lista de Certificados Disponibles.",
            b"Lista de certificados disponibles en el sistema.",
            b"Certficado Test",
            b"Nuevo Certificado",
        ],
        como_instructor=[],
        como_admin=[
            b"Lista de Certificados Disponibles.",
            b"Lista de certificados disponibles en el sistema.",
            b"Certficado Test",
            b"Nuevo Certificado",
        ],
    ),
    Ruta(
        ruta="/certificate/01HNP0TTQNTR03J7ZQHR09YMKK/edit",
        no_session=302,
        admin=200,
        user=403,
        moderator=403,
        instructor=403,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[
            b"Editar Certificado.",
            b"Certficado Test",
            b"Actualizar Certificado",
            b"Habilitado",
            b"Certificado Test",
        ],
    ),
    Ruta(
        ruta="/certificate/01HNP0TTQNTR03J7ZQHR09YMKK/delete",
        no_session=302,
        admin=302,
        user=403,
        moderator=403,
        instructor=403,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/now/view",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[b"Inscribirse al Curso"],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
]
