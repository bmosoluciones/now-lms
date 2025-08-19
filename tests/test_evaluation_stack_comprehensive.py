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
#

"""Comprehensive tests for Evaluation Stack - Basic version."""


from now_lms.db import (
    Evaluation,
    Question,
    QuestionOption,
    EvaluationAttempt,
    Curso,
    CursoSeccion,
    Usuario,
    database,
)


class TestEvaluationBasicFunctionality:
    """Test basic evaluation model and creation."""

    def test_evaluation_model_exists(self, minimal_db_setup):
        """Test that Evaluation model can be imported and instantiated."""
        # Create course and section first
        course = Curso(
            codigo="EVAL_COURSE",
            nombre="Evaluation Course",
            descripcion_corta="Course for evaluation testing",
            descripcion="Course for evaluation testing",
            estado="open",
        )
        database.session.add(course)
        database.session.commit()

        section = CursoSeccion(
            curso=course.codigo,
            nombre="Test Section",
            descripcion="Section for testing",
            indice=1,
        )
        database.session.add(section)
        database.session.commit()

        evaluation = Evaluation(
            section_id=section.id,
            title="Test Evaluation",
            description="A test evaluation",
            is_exam=False,
            passing_score=70.0,
        )
        assert evaluation is not None
        assert evaluation.title == "Test Evaluation"
        assert evaluation.passing_score == 70.0

    def test_evaluation_with_questions(self, minimal_db_setup):
        """Test evaluation with questions creation."""
        # Create course and section
        course = Curso(
            codigo="QUEST_COURSE",
            nombre="Question Course",
            descripcion_corta="Course for question testing",
            descripcion="Course for question testing",
            estado="open",
        )
        database.session.add(course)
        database.session.commit()

        section = CursoSeccion(
            curso=course.codigo,
            nombre="Question Section",
            descripcion="Section for question testing",
            indice=1,
        )
        database.session.add(section)
        database.session.commit()

        # Create evaluation
        evaluation = Evaluation(
            section_id=section.id,
            title="Question Test Evaluation",
            description="Evaluation with questions",
            is_exam=True,
            passing_score=80.0,
        )
        database.session.add(evaluation)
        database.session.commit()

        # Create question
        question = Question(
            evaluation_id=evaluation.id,
            type="boolean",
            text="Is this a test question?",
            explanation="This is indeed a test question",
            order=1,
        )
        database.session.add(question)
        database.session.commit()

        # Verify question
        retrieved = database.session.execute(database.select(Question).filter_by(evaluation_id=evaluation.id)).scalar_one()

        assert retrieved.text == "Is this a test question?"
        assert retrieved.type == "boolean"

    def test_evaluation_attempt(self, minimal_db_setup):
        """Test student evaluation attempt."""
        # Create user
        user = Usuario(
            usuario="eval_student",
            acceso=b"password123",
            nombre="Eval",
            apellido="Student",
            correo_electronico="evalstudent@test.com",
            tipo="student",
        )
        database.session.add(user)

        # Create course and section
        course = Curso(
            codigo="ATT_COURSE",
            nombre="Attempt Course",
            descripcion_corta="Course for attempt testing",
            descripcion="Course for attempt testing",
            estado="open",
        )
        database.session.add(course)
        database.session.commit()

        section = CursoSeccion(
            curso=course.codigo,
            nombre="Attempt Section",
            descripcion="Section for attempt testing",
            indice=1,
        )
        database.session.add(section)
        database.session.commit()

        # Create evaluation
        evaluation = Evaluation(
            section_id=section.id,
            title="Attempt Test Evaluation",
            description="Evaluation for attempt testing",
            passing_score=75.0,
        )
        database.session.add(evaluation)
        database.session.commit()

        # Create attempt
        attempt = EvaluationAttempt(
            evaluation_id=evaluation.id,
            user_id=user.usuario,
            score=85.0,
            passed=True,
        )
        database.session.add(attempt)
        database.session.commit()

        # Verify attempt
        retrieved = database.session.execute(
            database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation.id, user_id=user.usuario)
        ).scalar_one()

        assert retrieved.score == 85.0
        assert retrieved.passed is True

    def test_question_with_options(self, minimal_db_setup):
        """Test multiple choice question with options."""
        # Create course and section
        course = Curso(
            codigo="OPT_COURSE",
            nombre="Option Course",
            descripcion_corta="Course for option testing",
            descripcion="Course for option testing",
            estado="open",
        )
        database.session.add(course)
        database.session.commit()

        section = CursoSeccion(
            curso=course.codigo,
            nombre="Option Section",
            descripcion="Section for option testing",
            indice=1,
        )
        database.session.add(section)
        database.session.commit()

        # Create evaluation
        evaluation = Evaluation(
            section_id=section.id,
            title="Option Test Evaluation",
            description="Evaluation with multiple choice",
            passing_score=60.0,
        )
        database.session.add(evaluation)
        database.session.commit()

        # Create multiple choice question
        question = Question(
            evaluation_id=evaluation.id,
            type="multiple",
            text="What is 2 + 2?",
            order=1,
        )
        database.session.add(question)
        database.session.commit()

        # Create options
        option1 = QuestionOption(
            question_id=question.id,
            text="3",
            is_correct=False,
        )
        option2 = QuestionOption(
            question_id=question.id,
            text="4",
            is_correct=True,
        )
        database.session.add_all([option1, option2])
        database.session.commit()

        # Verify options
        options = database.session.execute(database.select(QuestionOption).filter_by(question_id=question.id)).scalars().all()

        assert len(options) == 2
        # Check that we have both options (order may vary)
        texts = [opt.text for opt in options]
        correct_flags = [opt.is_correct for opt in options]
        assert "3" in texts
        assert "4" in texts
        assert False in correct_flags
        assert True in correct_flags
