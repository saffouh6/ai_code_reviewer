import sys
import unittest
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

PROJECT = Path(os.environ.get("AI_CODE_REVIEWER_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(PROJECT))

from services import groq_service


def fake_client(result="OK"):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=result), finish_reason="stop")]
    )
    return client


class InputValidationTests(unittest.TestCase):
    def test_blank_input_is_rejected_without_api_call(self):
        with patch.object(groq_service, "_create_client") as create_client:
            self.assertIn("kod parçası girin", groq_service.review_code("  \n\t"))
            create_client.assert_not_called()

    def test_valid_input_is_sent_to_service(self):
        client = fake_client()
        with patch.object(groq_service, "_create_client", return_value=client):
            self.assertEqual("OK", groq_service.review_code("print(1)"))
        self.assertIn("print(1)", client.chat.completions.create.call_args.kwargs["messages"][1]["content"])

    def test_exact_limit_is_accepted(self):
        client = fake_client()
        code = "x" * groq_service.MAX_CODE_LENGTH
        with patch.object(groq_service, "_create_client", return_value=client):
            self.assertEqual("OK", groq_service.review_code(code))
        self.assertIn(code, client.chat.completions.create.call_args.kwargs["messages"][1]["content"])

    def test_over_limit_is_rejected_without_api_call(self):
        with patch.object(groq_service, "_create_client") as create_client:
            self.assertIn("çok uzun", groq_service.review_code("x" * (groq_service.MAX_CODE_LENGTH + 1)))
            create_client.assert_not_called()

    def test_streamlit_widget_enforces_and_displays_limit(self):
        app_source = (PROJECT / "app.py").read_text(encoding="utf-8")
        self.assertIn("max_chars=MAX_CODE_LENGTH", app_source)
        self.assertIn("help=f\"En fazla {MAX_CODE_LENGTH:,} karakter girilebilir.\"", app_source)


if __name__ == "__main__":
    unittest.main(verbosity=2)

