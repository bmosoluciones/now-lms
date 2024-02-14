from collections import namedtuple
from io import BytesIO

Form = namedtuple("form", ["ruta", "data"])

forms = [
    Form(
        ruta="/course/new_curse",
        data={"nombre": "nombre", "codigo": "codigo", "descripcion": "descripcion", "logo": (BytesIO(b"abcdef"), "logo.pdf")},
    ),
    Form(
        ruta="course/test/new_seccion",
        data={
            "nombre": "nombre",
            "descripcion": "descripcion",
        },
    ),
]
