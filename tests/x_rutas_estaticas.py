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
url_map: 2024-02-10:

 <Rule '/category/new' (POST, OPTIONS, HEAD, GET) -> category.new_category>,
 <Rule '/category/list' (OPTIONS, HEAD, GET) -> category.categories>,
 <Rule '/category/<ulid>/delete' (OPTIONS, HEAD, GET) -> category.delete_category>,
 <Rule '/category/<ulid>/edit' (POST, OPTIONS, HEAD, GET) -> category.edit_category>,
 <Rule '/certificate/new' (POST, OPTIONS, HEAD, GET) -> certificate.new_certificate>,
 <Rule '/certificate/list' (OPTIONS, HEAD, GET) -> certificate.certificados>,
 <Rule '/certificate/<ulid>/delete' (OPTIONS, HEAD, GET) -> certificate.delete_certificate>,
 <Rule '/certificate/<ulid>/edit' (POST, OPTIONS, HEAD, GET) -> certificate.edit_certificate>,
 <Rule '/course/<course_code>/view' (OPTIONS, HEAD, GET) -> course.curso>,
 <Rule '/course/<course_code>/enroll' (OPTIONS, HEAD, GET) -> course.course_enroll>,
 <Rule '/course/<course_code>/take' (OPTIONS, HEAD, GET) -> course.tomar_curso>,
 <Rule '/course/<course_code>/moderate' (OPTIONS, HEAD, GET) -> course.moderar_curso>,
 <Rule '/course/<course_code>/admin' (OPTIONS, HEAD, GET) -> course.administrar_curso>,
 <Rule '/course/new_curse' (POST, OPTIONS, HEAD, GET) -> course.nuevo_curso>,
 <Rule '/course/<course_code>/edit' (POST, OPTIONS, HEAD, GET) -> course.editar_curso>,
 <Rule '/course/<course_code>/new_seccion' (POST, OPTIONS, HEAD, GET) -> course.nuevo_seccion>,
 <Rule '/course/<course_code>/<seccion>/edit' (POST, OPTIONS, HEAD, GET) -> course.editar_seccion>,
 <Rule '/course/<course_code>/seccion/increment/<indice>' (OPTIONS, HEAD, GET) -> course.incrementar_indice_seccion>,
 <Rule '/course/<course_code>/seccion/decrement/<indice>' (OPTIONS, HEAD, GET) -> course.reducir_indice_seccion>,
 <Rule '/course/resource/<cource_code>/<seccion_id>/<task>/<resource_index>' (OPTIONS, HEAD, GET) -> course.modificar_orden_recurso>,
 <Rule '/course/<curso_code>/delete_recurso/<seccion>/<id_>' (OPTIONS, HEAD, GET) -> course.eliminar_recurso>,
 <Rule '/course/<curso_id>/delete_seccion/<id_>' (OPTIONS, HEAD, GET) -> course.eliminar_seccion>,
 <Rule '/course/change_curse_status' (OPTIONS, HEAD, GET) -> course.cambiar_estatus_curso>,
 <Rule '/course/change_curse_public' (OPTIONS, HEAD, GET) -> course.cambiar_curso_publico>,
 <Rule '/course/change_curse_seccion_public' (OPTIONS, HEAD, GET) -> course.cambiar_seccion_publico>,
 <Rule '/course/<curso_id>/resource/<resource_type>/<codigo>' (OPTIONS, HEAD, GET) -> course.pagina_recurso>,
 <Rule '/course/<curso_id>/resource/<resource_type>/<codigo>/complete' (OPTIONS, HEAD, GET) -> course.marcar_recurso_completado>,
 <Rule '/course/<curso_id>/alternative/<codigo>/<order>' (OPTIONS, HEAD, GET) -> course.pagina_recurso_alternativo>,
 <Rule '/course/<course_code>/<seccion>/new_resource' (OPTIONS, HEAD, GET) -> course.nuevo_recurso>,
 <Rule '/course/<course_code>/<seccion>/youtube/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_youtube_video>,
 <Rule '/course/<course_code>/<seccion>/text/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_text>,
 <Rule '/course/<course_code>/<seccion>/link/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_link>,
 <Rule '/course/<course_code>/<seccion>/pdf/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_pdf>,
 <Rule '/course/<course_code>/<seccion>/meet/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_meet>,
 <Rule '/course/<course_code>/<seccion>/img/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_img>,
 <Rule '/course/<course_code>/<seccion>/audio/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_audio>,
 <Rule '/course/<course_code>/<seccion>/html/new' (POST, OPTIONS, HEAD, GET) -> course.nuevo_recurso_html>,
 <Rule '/course/<course_code>/delete_logo' (OPTIONS, HEAD, GET) -> course.elimina_logo>,
 <Rule '/course/<course_code>/files/<recurso_code>' (OPTIONS, HEAD, GET) -> course.recurso_file>,
 <Rule '/course/<course_code>/external_code/<recurso_code>' (OPTIONS, HEAD, GET) -> course.external_code>,
 <Rule '/course/slide_show/<recurso_code>' (OPTIONS, HEAD, GET) -> course.slide_show>,
 <Rule '/course/<course_code>/md_to_html/<recurso_code>' (OPTIONS, HEAD, GET) -> course.markdown_a_html>,
 <Rule '/course/<course_code>/description' (OPTIONS, HEAD, GET) -> course.curso_descripcion_a_html>,
 <Rule '/course/<course_code>/description/<resource>' (OPTIONS, HEAD, GET) -> course.recurso_descripcion_a_html>,
 <Rule '/course/explore' (OPTIONS, HEAD, GET) -> course.lista_cursos>,
 <Rule '/group/new' (POST, OPTIONS, HEAD, GET) -> group.nuevo_grupo>,
 <Rule '/group/set_tutor' (POST, OPTIONS) -> group.agrega_tutor_a_grupo>,
 <Rule '/home' (OPTIONS, HEAD, GET) -> home.pagina_de_inicio>,
 <Rule '/' (OPTIONS, HEAD, GET) -> home.pagina_de_inicio>,
 <Rule '/home/panel' (OPTIONS, HEAD, GET) -> home.panel>,
 <Rule '/message/<ulid>' (OPTIONS, HEAD, GET) -> msg.mensaje>,
 <Rule '/message/new' (POST, OPTIONS, HEAD, GET) -> msg.nuevo_mensaje>,
 <Rule '/program/new' (POST, OPTIONS, HEAD, GET) -> program.nuevo_programa>,
 <Rule '/program/list' (OPTIONS, HEAD, GET) -> program.programas>,
 <Rule '/program/<ulid>/delete' (OPTIONS, HEAD, GET) -> program.delete_program>,
 <Rule '/program/<ulid>/edit' (POST, OPTIONS, HEAD, GET) -> program.edit_program>,
 <Rule '/program/<codigo>/courses' (OPTIONS, HEAD, GET) -> program.programa_cursos>,
 <Rule '/program/<codigo>' (OPTIONS, HEAD, GET) -> program.pagina_programa>,
 <Rule '/program/explore' (OPTIONS, HEAD, GET) -> program.lista_programas>,
 <Rule '/resource/new' (POST, OPTIONS, HEAD, GET) -> resource.new_resource>,
 <Rule '/resource/list' (OPTIONS, HEAD, GET) -> resource.lista_de_recursos>,
 <Rule '/resource/<resource_code>/donwload' (OPTIONS, HEAD, GET) -> resource.descargar_recurso>,
 <Rule '/resource/<ulid>/delete' (OPTIONS, HEAD, GET) -> resource.delete_resource>,
 <Rule '/resource/<ulid>/update' (POST, OPTIONS, HEAD, GET) -> resource.edit_resource>,
 <Rule '/resource/<resource_code>' (OPTIONS, HEAD, GET) -> resource.vista_recurso>,
 <Rule '/resource/explore' (OPTIONS, HEAD, GET) -> resource.lista_recursos>,
 <Rule '/setting/theming' (POST, OPTIONS, HEAD, GET) -> setting.personalizacion>,
 <Rule '/setting/general' (POST, OPTIONS, HEAD, GET) -> setting.configuracion>,
 <Rule '/setting/mail' (POST, OPTIONS, HEAD, GET) -> setting.mail>,
 <Rule '/setting/delete_site_logo' (OPTIONS, HEAD, GET) -> setting.elimina_logo>,
 <Rule '/tag/new' (POST, OPTIONS, HEAD, GET) -> tag.new_tag>,
 <Rule '/tag/list' (OPTIONS, HEAD, GET) -> tag.tags>,
 <Rule '/tag/<ulid>/delete' (OPTIONS, HEAD, GET) -> tag.delete_tag>,
 <Rule '/tag/<ulid>/edit' (POST, OPTIONS, HEAD, GET) -> tag.edit_tag>,
 <Rule '/user/login' (POST, OPTIONS, HEAD, GET) -> user.inicio_sesion>,
 <Rule '/user/logout' (OPTIONS, HEAD, GET) -> user.cerrar_sesion>,
 <Rule '/user/logon' (POST, OPTIONS, HEAD, GET) -> user.crear_cuenta>,
 <Rule '/user/new_user' (POST, OPTIONS, HEAD, GET) -> user.crear_usuario>,
 <Rule '/admin/panel' (OPTIONS, HEAD, GET) -> admin_profile.pagina_admin>,
 <Rule '/admin/users/list' (OPTIONS, HEAD, GET) -> admin_profile.usuarios>,
 <Rule '/admin/users/set_active/<user_id>' (OPTIONS, HEAD, GET) -> admin_profile.activar_usuario>,
 <Rule '/admin/users/set_inactive/<user_id>' (OPTIONS, HEAD, GET) -> admin_profile.inactivar_usuario>,
 <Rule '/admin/users/delete/<user_id>' (OPTIONS, HEAD, GET) -> admin_profile.eliminar_usuario>,
 <Rule '/admin/users/list_inactive' (OPTIONS, HEAD, GET) -> admin_profile.usuarios_inactivos>,
 <Rule '/admin/user/change_type' (OPTIONS, HEAD, GET) -> admin_profile.cambiar_tipo_usario>,
 <Rule '/instructor' (OPTIONS, HEAD, GET) -> instructor_profile.pagina_instructor>,
 <Rule '/instructor/courses_list' (OPTIONS, HEAD, GET) -> instructor_profile.cursos>,
 <Rule '/instructor/group/list' (OPTIONS, HEAD, GET) -> instructor_profile.lista_grupos>,
 <Rule '/group/<ulid>' (OPTIONS, HEAD, GET) -> instructor_profile.grupo>,
 <Rule '/group/remove/<group>/<user>' (OPTIONS, HEAD, GET) -> instructor_profile.elimina_usuario__grupo>,
 <Rule '/group/add' (POST, OPTIONS) -> instructor_profile.agrega_usuario_a_grupo>,
 <Rule '/moderator' (OPTIONS, HEAD, GET) -> moderator_profile.pagina_moderador>,
 <Rule '/student' (OPTIONS, HEAD, GET) -> user_profile.pagina_estudiante>,
 <Rule '/perfil' (OPTIONS, HEAD, GET) -> user_profile.perfil>,
 <Rule '/user/<id_usuario>' (OPTIONS, HEAD, GET) -> user_profile.usuario>,
 <Rule '/perfil/edit/<ulid>' (POST, OPTIONS, HEAD, GET) -> user_profile.edit_perfil>,
 <Rule '/perfil/<ulid>/delete_logo' (OPTIONS, HEAD, GET) -> user_profile.elimina_logo_usuario>,
 <Rule '/http/error/<code>' (OPTIONS, HEAD, GET) -> error.error_page>,
 <Rule '/_uploads/<setname>/<filename>' (OPTIONS, HEAD, GET) -> _uploads.uploaded_file>])
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
        ruta="/instructor/courses_list",
        no_session=302,
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
    Ruta(
        ruta="/course/now/view?inspect=True",
        no_session=200,
        admin=200,
        user=403,
        moderator=403,
        instructor=403,
        texto=[],
        como_user=[b"Inscribirse al Curso"],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/test/view",  # Test course
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
    Ruta(
        ruta="/course/now/enroll",
        no_session=302,
        admin=200,
        user=200,
        moderator=403,
        instructor=403,
        texto=[],
        como_user=[b"Inscribirse al Curso"],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/now/take",
        no_session=302,
        admin=302,
        user=200,
        moderator=403,
        instructor=403,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/now/moderate",
        no_session=302,
        admin=200,
        user=403,
        moderator=200,
        instructor=403,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/now/admin",
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
        ruta="/course/new_curse",
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
        ruta="/course/now/edit",
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
        ruta="/course/now/new_seccion",
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
        ruta="/course/now/01HPB1MZXBHZETC4ZH0HV4G39Q/edit",
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
        ruta="/course/now/seccion/increment/1",
        no_session=302,
        admin=302,
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
        ruta="/course/now/seccion/decrement/2",
        no_session=302,
        admin=302,
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
        ruta="/course/resource/now/01HPB1MZXBHZETC4ZH0HV4G39Q/increment/1",
        no_session=302,
        admin=302,
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
        ruta="/course/resource/now/01HPB1MZXBHZETC4ZH0HV4G39Q/decrement/2",
        no_session=302,
        admin=302,
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
        ruta="/course/now/delete_recurso/01HPB1MZXBHZETC4ZH0HV4G39Q/01HPB3AP3QNVK9ES6JGG5YK7CH",
        no_session=302,
        admin=302,
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
        ruta="/course/change_curse_status?curse=now&status=draft",
        no_session=302,
        admin=302,
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
        ruta="/course/change_curse_public?curse=now",
        no_session=302,
        admin=302,
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
        ruta="/course/change_curse_seccion_public?course_code=now&codigo=01HPB1MZXBHZETC4ZH0HV4G39Q",
        no_session=302,
        admin=302,
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
        ruta="/course/now/delete_seccion/01HPB1MZXBHZETC4ZH0HV4G39Q",
        no_session=302,
        admin=302,
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
        ruta="/course/test/resource/mp3/01HNZYDA9WKT2FHCBZSFV7JQBR",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/pdf/01HNZYDQV2K1FWNKH0R04JTSNV",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/meet/01HNZYDXSJJ1EC28QW22YNHSGX",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/text/01HNZYETGNYGVYN79JB9STQHAM",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/img/01HNZYECPY2SKBM09GFA4TFWN2",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/html/01HNZYFK9SX5GE6CEKC4DSSZHD",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/link/01HNZYFZWX2HF6354B5SV4V8V8",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/slides/01HNZYGGKNNDG4NJ949971GMJM",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/youtube/01HNZYGXRRWXJ8GXVXYZY8S994",
        no_session=403,
        admin=200,
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
        ruta="/course/test/resource/mp3/01HNZYDA9WKT2FHCBZSFV7JQBR/complete",
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
        ruta="/course/test/alternative/01HNZYECPY2SKBM09GFA4TFWN2/asc",
        no_session=302,
        admin=200,
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
        ruta="/course/test/alternative/01HNZYECPY2SKBM09GFA4TFWN2/desc",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/new_resource",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/youtube/new",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/text/new",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/link/new",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/pdf/new",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/meet/new",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/img/new",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/audio/new",
        no_session=302,
        admin=200,
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
        ruta="/course/test/01HNZY7Y81RR4EFMDQX8F2XWHE/html/new",
        no_session=302,
        admin=200,
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
        ruta="/course/now/delete_logo",
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
        ruta="/course/test/files/01HNZYECPY2SKBM09GFA4TFWN2",
        no_session=302,
        admin=200,
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
        ruta="/course/test/external_code/01HNZYFK9SX5GE6CEKC4DSSZHD",
        no_session=302,
        admin=200,
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
        ruta="/course/test/md_to_html/01HNZYETGNYGVYN79JB9STQHAM",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/now/description",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/test/description/01HNZYETGNYGVYN79JB9STQHAM",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/course/explore",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/group/new",
        no_session=302,
        admin=200,
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
        ruta="/home/panel",
        no_session=302,
        admin=200,
        user=302,
        moderator=302,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/message/01HPMH3TYC30S59FG7B9Z23FSS",
        no_session=302,
        admin=200,
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
        ruta="/program/new",
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
        ruta="/program/list",
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
        ruta="/program/P000",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[b"Programing 101"],
        como_user=[b"Programing 101"],
        como_moderador=[b"Programing 101"],
        como_instructor=[b"Programing 101"],
        como_admin=[b"Programing 101"],
    ),
    Ruta(
        ruta="/program/P000/courses",
        no_session=302,
        admin=200,
        user=403,
        moderator=403,
        instructor=403,
        texto=[b"Lista de Cursos del Programa."],
        como_user=[b"Lista de Cursos del Programa."],
        como_moderador=[b"Lista de Cursos del Programa."],
        como_instructor=[b"Lista de Cursos del Programa."],
        como_admin=[b"Lista de Cursos del Programa."],
    ),
    Ruta(
        ruta="/program/explore",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/program/01HNZXEMSWTSBM4PNSY4R9VMN6/edit",
        no_session=302,
        admin=200,
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
        ruta="/program/01HNZXEMSWTSBM4PNSY4R9VMN6/delete",
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
        ruta="/resource/new",
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
        ruta="/resource/list",
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
        ruta="/resource/01HNZXA1BX9B297CYAAA4MK93V/donwload",
        no_session=302,
        admin=200,
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
        ruta="/resource/01HNZXA1BX9B297CYAAA4MK93V/update",
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
        ruta="/resource/01HNZXA1BX9B297CYAAA4MK93V",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/resource/explore",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/resource/01HNZXA1BX9B297CYAAA4MK93V/delete",
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
        ruta="/setting/theming",
        no_session=302,
        admin=200,
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
        ruta="/setting/general",
        no_session=302,
        admin=200,
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
        ruta="/setting/mail",
        no_session=302,
        admin=200,
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
        ruta="/setting/delete_site_logo",
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
        ruta="/tag/new",
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
        ruta="/tag/list",
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
        ruta="/tag/01HNP0TTQNTR03J7ZQHR09YMJJ/edit",
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
        ruta="/tag/01HNP0TTQNTR03J7ZQHR09YMJJ/delete",
        no_session=302,
        admin=302,
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
        ruta="/user/login",
        no_session=200,
        admin=302,
        user=302,
        moderator=302,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/user/logout",
        no_session=302,
        admin=302,
        user=302,
        moderator=302,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/user/logon",
        no_session=200,
        admin=200,
        user=200,
        moderator=200,
        instructor=200,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/user/new_user",
        no_session=302,
        admin=302,
        user=302,
        moderator=302,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/perfil",
        no_session=302,
        admin=302,
        user=302,
        moderator=302,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/admin/users/list",
        no_session=302,
        admin=302,
        user=302,
        moderator=302,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
    Ruta(
        ruta="/setting/adsense",
        no_session=302,
        admin=302,
        user=302,
        moderator=302,
        instructor=302,
        texto=[],
        como_user=[],
        como_moderador=[],
        como_instructor=[],
        como_admin=[],
    ),
]
