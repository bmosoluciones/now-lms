# Excel Theme Un tema moderno inspirado en Microsoft Excel diseñado específicamente para cursos de Excel en NOW LMS. Este tema
captura la esencia visual de Excel con un esquema de colores verde profesional y elementos de diseño que reflejan la
experiencia de Excel. ## Características - **Esquema de Colores Excel**: Verde profesional (#217346) que refleja la identidad
visual de Microsoft Excel - **Navegación Estilo Pestañas**: Navegación horizontal inspirada en las pestañas de Excel - **Diseño
de Tarjetas de Curso**: Tarjetas limpias con iconografía relacionada con Excel - **Tipografía Profesional**: Fuentes claras y
legibles para contenido educativo - **Diseño Responsivo**: Optimizado para todos los tamaños de pantalla - **Accesibilidad**:
Alto contraste y tipografía clara para el aprendizaje - **Elementos Visuales Excel**: Iconos y gráficos que evocan la
experiencia de Excel ## Esquema de Colores - Primario: #217346 (Verde Excel) - Secundario: #10A037 (Verde Claro) - Acento:
#0B5D2D (Verde Oscuro) - Fondo: #F8F9FA (Gris Claro) - Texto: #212529 (Gris Oscuro) ## Mejoras Visuales - Navegación con
pestañas horizontales - Efectos hover sutiles - Botones con estilo Excel - Tarjetas de curso con iconografía de hojas de
cálculo - Diseño limpio y profesional - Efectos de sombra mínimos ## Estructura del Tema ``` excel/ ├── base.j2 -> Plantilla
base del tema ├── header.j2 -> Archivos CSS y JS personalizados para incluir en el head ├── local_style.j2 -> Estilos CSS
locales con mejoras del tema Excel ├── navbar.j2 -> Barra de navegación con estilo Excel ├── notify.j2 -> Marcado HTML de
notificaciones personalizado ├── pagination.j2 -> Código de paginación personalizado ├── js.j2 -> Bibliotecas JavaScript
personalizadas ├── overrides/ │ └── home.j2 -> [OPCIONAL] Página de inicio personalizada para el sitio └── README.md ``` ##
Requisitos El frontend de NOW LMS requiere Bootstrap 5, por lo que incluye esos recursos en tu header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
``` ## Uso Recomendado Este tema está diseñado específicamente para plataformas educativas que ofrecen cursos de Microsoft
Excel, proporcionando una experiencia visual coherente que conecta con los estudiantes familiarizados con la interfaz de Excel.
## Internacionalización Todas las cadenas de texto están marcadas para traducción usando el sistema de internacionalización de
Flask-Babel. El idioma base es español.
