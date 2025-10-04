# Finance Theme Un tema moderno con enfoque financiero diseñado específicamente para cursos de finanzas personales y
corporativas en NOW LMS. Este tema captura la esencia profesional del sector financiero con un esquema de colores azul y verde
que transmite confianza y crecimiento. ## Características - **Esquema de Colores Profesional**: Azul financiero (#1E3A8A) y
verde de crecimiento (#10B981) que reflejan estabilidad y prosperidad - **Navegación Estilo Corporativo**: Navegación
horizontal limpia y profesional - **Diseño de Tarjetas de Curso**: Tarjetas elegantes con iconografía relacionada con finanzas
- **Tipografía Profesional**: Fuentes claras y legibles para contenido educativo - **Diseño Responsivo**: Optimizado para todos
los tamaños de pantalla - **Accesibilidad**: Alto contraste y tipografía clara para el aprendizaje - **Elementos Visuales
Financieros**: Iconos y gráficos que evocan el mundo financiero ## Esquema de Colores - Primario: #1E3A8A (Azul Financiero) -
Secundario: #10B981 (Verde Crecimiento) - Acento: #3B82F6 (Azul Claro) - Fondo: #F8FAFC (Gris Muy Claro) - Texto: #1E293B (Gris
Oscuro) ## Mejoras Visuales - Hero section con placeholder para imagen de fondo financiera - Navegación con estilo corporativo
profesional - Efectos hover sutiles - Botones con estilo financiero - Tarjetas de curso con iconografía de finanzas - Diseño
limpio y profesional - Gradientes suaves que transmiten crecimiento ## Estructura del Tema ``` finance/ ├── base.j2 ->
Plantilla base del tema ├── header.j2 -> Archivos CSS y JS personalizados para incluir en el head ├── local_style.j2 -> Estilos
CSS locales con mejoras del tema Finance ├── navbar.j2 -> Barra de navegación con estilo Finance ├── notify.j2 -> Marcado HTML
de notificaciones personalizado ├── pagination.j2 -> Código de paginación personalizado ├── js.j2 -> Bibliotecas JavaScript
personalizadas ├── overrides/ │ └── home.j2 -> [OPCIONAL] Página de inicio personalizada para el sitio └── README.md ``` ##
Requisitos El frontend de NOW LMS requiere Bootstrap 5, por lo que incluye esos recursos en tu header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
``` ## Uso Recomendado Este tema está diseñado específicamente para plataformas educativas que ofrecen cursos de finanzas
personales, inversiones, contabilidad y otros temas relacionados con el sector financiero, proporcionando una experiencia
visual coherente que conecta con los estudiantes interesados en el mundo de las finanzas. ## Internacionalización Todas las
cadenas de texto están marcadas para traducción usando el sistema de internacionalización de Flask-Babel. El idioma base es
español.
