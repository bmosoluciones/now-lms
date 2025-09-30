# Copyright 2021 - 2023 BMO Soluciones, S.A.
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

import inspect




def test_importable(session_basic_db_setup):
    """El proyecto debe poder importarse sin errores."""
    assert session_basic_db_setup


def test_cli(session_basic_db_setup):
    runner = session_basic_db_setup.test_cli_runner()
    runner.invoke(args=["info", "path"])
    runner.invoke(args=["info", "system"])
    runner.invoke(args=["info", "course", "now"])
    runner.invoke(args=["database"])


def test_flask_instance(session_basic_db_setup):
    from flask import Flask

    assert isinstance(session_basic_db_setup, Flask)


def test_sqlalchemy_instance(session_basic_db_setup):
    from flask_sqlalchemy import SQLAlchemy

    from now_lms import database

    assert isinstance(database, SQLAlchemy)


def test_alembic_instance(session_basic_db_setup):
    from flask_alembic import Alembic

    from now_lms import alembic

    assert isinstance(alembic, Alembic)


def test_login_manager_instance(session_basic_db_setup):
    from flask_login import LoginManager

    from now_lms import administrador_sesion

    assert isinstance(administrador_sesion, LoginManager)


def test_flask_form_classes(session_basic_db_setup):
    from flask_wtf import FlaskForm

    import now_lms.forms as forms

    form_classes = [
        cls
        for name, cls in inspect.getmembers(forms, inspect.isclass)
        if cls.__module__ == forms.__name__ and issubclass(cls, FlaskForm)
    ]

    assert form_classes, "No se encontraron formularios que hereden de FlaskForm."

    for cls in form_classes:
        assert issubclass(cls, FlaskForm), f"{cls.__name__} no hereda de FlaskForm"


def test_base_table_inheritance(session_basic_db_setup):
    from flask_login import UserMixin

    from now_lms import Usuario
    from now_lms.db import BaseTabla, database

    assert issubclass(Usuario, UserMixin)
    assert issubclass(Usuario, BaseTabla)
    assert issubclass(Usuario, database.Model)


# Source: https://gist.github.com/allysonsilva/85fff14a22bbdf55485be947566cc09e
MARKDOWN_EXAMPLE = """
# Headers

```
# h1 Heading 8-)
## h2 Heading
### h3 Heading
#### h4 Heading
##### h5 Heading
###### h6 Heading

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------
```

# h1 Heading 8-)
## h2 Heading
### h3 Heading
#### h4 Heading
##### h5 Heading
###### h6 Heading

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------

------

# Emphasis

```
Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~

**This is bold text**

__This is bold text__

*This is italic text*

_This is italic text_

~~Strikethrough~~
```

Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~

**This is bold text**

__This is bold text__

*This is italic text*

_This is italic text_

~~Strikethrough~~

------

# Lists

```
1. First ordered list item
2. Another item
⋅⋅* Unordered sub-list.
1. Actual numbers don't matter, just that it's a number
⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses

1. Make my changes
    1. Fix bug
    2. Improve formatting
        - Make the headings bigger
2. Push my commits to GitHub
3. Open a pull request
    * Describe my changes
    * Mention all the members of my team
        * Ask for feedback

+ Create a list by starting a line with `+`, `-`, or `*`
+ Sub-lists are made by indenting 2 spaces:
  - Marker character change forces new list start:
    * Ac tristique libero volutpat at
    + Facilisis in pretium nisl aliquet
    - Nulla volutpat aliquam velit
+ Very easy!
```

1. First ordered list item
2. Another item
⋅⋅* Unordered sub-list.
1. Actual numbers don't matter, just that it's a number
⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses

1. Make my changes
    1. Fix bug
    2. Improve formatting
        - Make the headings bigger
2. Push my commits to GitHub
3. Open a pull request
    * Describe my changes
    * Mention all the members of my team
        * Ask for feedback

+ Create a list by starting a line with `+`, `-`, or `*`
+ Sub-lists are made by indenting 2 spaces:
  - Marker character change forces new list start:
    * Ac tristique libero volutpat at
    + Facilisis in pretium nisl aliquet
    - Nulla volutpat aliquam velit
+ Very easy!

------

# Task lists

```
- [x] Finish my changes
- [ ] Push my commits to GitHub
- [ ] Open a pull request
- [x] @mentions, #refs, [links](), **formatting**, and <del>tags</del> supported
- [x] list syntax required (any unordered or ordered list supported)
- [x] this is a complete item
- [ ] this is an incomplete item
```

- [x] Finish my changes
- [ ] Push my commits to GitHub
- [ ] Open a pull request
- [x] @mentions, #refs, [links](), **formatting**, and <del>tags</del> supported
- [x] list syntax required (any unordered or ordered list supported)
- [ ] this is a complete item
- [ ] this is an incomplete item

"""


def test_clean_markdown():
    from now_lms.misc import markdown_to_clean_html

    markdown_to_clean_html(MARKDOWN_EXAMPLE)
