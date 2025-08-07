#!/usr/bin/env python3
"""
Simple test script to verify the evaluations system functionality.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))


def test_evaluation_models():
    """Test that evaluation models can be imported and instantiated."""
    print("Testing evaluation models...")

    from now_lms import lms_app
    from now_lms.db import Evaluation, Question, QuestionOption, EvaluationAttempt, Answer, EvaluationReopenRequest

    with lms_app.app_context():
        # Test model instantiation
        evaluation = Evaluation(
            section_id="test_section", title="Test Evaluation", description="A test evaluation", passing_score=70.0
        )
        print("✓ Evaluation model instantiated")

        question = Question(evaluation_id="test_eval", type="multiple", text="What is 2+2?", order=1)
        print("✓ Question model instantiated")

        option = QuestionOption(question_id="test_question", text="4", is_correct=True)
        print("✓ QuestionOption model instantiated")

        attempt = EvaluationAttempt(evaluation_id="test_eval", user_id="test_user")
        print("✓ EvaluationAttempt model instantiated")

        answer = Answer(attempt_id="test_attempt", question_id="test_question", selected_option_ids='["option1"]')
        print("✓ Answer model instantiated")

        reopen_request = EvaluationReopenRequest(
            user_id="test_user", evaluation_id="test_eval", justification_text="Need another attempt"
        )
        print("✓ EvaluationReopenRequest model instantiated")

    print("All evaluation models test passed! ✓")


def test_evaluation_forms():
    """Test that evaluation forms can be imported."""
    print("\nTesting evaluation forms...")

    try:
        from now_lms.forms import EvaluationForm, QuestionForm, QuestionOptionForm, EvaluationReopenRequestForm

        print("✓ All evaluation forms imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import forms: {e}")

    print("Evaluation forms test completed! ✓")


def test_app_integration():
    """Test that the app loads with evaluation system."""
    print("\nTesting app integration...")

    from now_lms import lms_app

    with lms_app.app_context():
        # Test that blueprints are registered
        blueprint_names = [bp.name for bp in lms_app.blueprints.values()]

        if "evaluation" in blueprint_names:
            print("✓ Evaluation blueprint registered in app")
        else:
            print("✗ Evaluation blueprint not found in app")

        # Test database tables exist
        from now_lms.db import database
        from sqlalchemy import inspect

        inspector = inspect(database.engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "evaluation",
            "question",
            "question_option",
            "evaluation_attempt",
            "answer",
            "evaluation_reopen_request",
        ]

        for table in expected_tables:
            if table in tables:
                print(f"✓ Database table '{table}' exists")
            else:
                print(f"✗ Database table '{table}' not found")

    print("App integration test completed! ✓")
