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
# Contributors:
# - William José Moreno Reyes

from unittest import TestCase
import pytest


class TestBasicos(TestCase):
    def setUp(self):
        from now_lms import app

        self.app = app
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.app_context().push()

    def test_importable(self):
        """El proyecto debe poder importarse sin errores."""

        assert self.app

    def test_cli(self):
        self.app.test_cli_runner()


class TestInstanciasDeClases(TestCase):
    def setUp(self):
        from now_lms import app

        self.app = app
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.app_context().push()

    def test_Flask(self):
        from flask import Flask

        self.assertIsInstance(self.app, Flask)

    def test_SQLAlchemy(self):
        from now_lms import database
        from flask_sqlalchemy import SQLAlchemy

        self.assertIsInstance(database, SQLAlchemy)

    def test_Alembic(self):
        from now_lms import alembic
        from flask_alembic import Alembic

        self.assertIsInstance(alembic, Alembic)

    def test_Login(self):
        from now_lms import administrador_sesion
        from flask_login import LoginManager

        self.assertIsInstance(administrador_sesion, LoginManager)

    def test_FlaskForm(self):
        from flask_wtf import FlaskForm
        from now_lms.forms import LoginForm, LogonForm, CurseForm, CursoRecursoVideoYoutube, CursoSeccionForm

        assert issubclass(LoginForm, FlaskForm)
        assert issubclass(CurseForm, FlaskForm)
        assert issubclass(LogonForm, FlaskForm)
        assert issubclass(CursoRecursoVideoYoutube, FlaskForm)
        assert issubclass(CursoSeccionForm, FlaskForm)

    def test_BaseTable(self):
        from now_lms.db import BaseTabla, database
        from flask_login import UserMixin
        from now_lms import Usuario

        assert issubclass(Usuario, UserMixin)
        assert issubclass(Usuario, BaseTabla)
        assert issubclass(Usuario, database.Model)
