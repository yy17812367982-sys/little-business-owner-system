import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

from ai_reliability import AIServiceUnavailable, request_ai_text


class AIRequestReliabilityTests(unittest.TestCase):
    def test_stable_flash_model_is_inside_bounded_attempt_window(self):
        source = Path("pythonapp.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        assignments = {
            target.id: ast.literal_eval(node.value)
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "MODEL_CANDIDATES_PRO"
        }

        self.assertIn("gemini-2.5-flash", assignments["MODEL_CANDIDATES_PRO"][:3])

    def test_report_defaults_have_a_one_minute_maximum_window(self):
        source = Path("pythonapp.py").read_text(encoding="utf-8")

        self.assertIn('AI_REQUEST_TIMEOUT_MS", "30000"', source)
        self.assertIn('AI_MAX_MODEL_ATTEMPTS", "2"', source)
        self.assertIn("thinking_budget=0", source)
        self.assertIn("max_output_tokens=4096", source)

    def test_returns_first_non_empty_response(self):
        calls = []

        def generate_content(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text="  report ready  ")

        result = request_ai_text(generate_content, ["model-a"], "prompt", object())

        self.assertEqual(result, "  report ready  ")
        self.assertEqual(len(calls), 1)
        self.assertIn("config", calls[0])

    def test_empty_response_falls_back_to_next_model(self):
        responses = iter([SimpleNamespace(text=""), SimpleNamespace(text="report")])

        result = request_ai_text(
            lambda **_: next(responses),
            ["model-a", "model-b"],
            "prompt",
            object(),
        )

        self.assertEqual(result, "report")

    def test_timeouts_stop_after_bounded_attempts_and_are_retryable(self):
        calls = []

        def generate_content(**kwargs):
            calls.append(kwargs)
            raise TimeoutError("provider request timed out")

        with self.assertRaises(AIServiceUnavailable) as raised:
            request_ai_text(
                generate_content,
                ["one", "two", "three", "four"],
                "prompt",
                object(),
                max_attempts=3,
            )

        self.assertEqual(len(calls), 3)
        self.assertEqual(raised.exception.code, "AI_TIMEOUT")
        self.assertIn("retry", raised.exception.user_message.lower())

    def test_public_error_does_not_expose_provider_details(self):
        secret_detail = "403 model-x internal-project-id"

        with self.assertRaises(AIServiceUnavailable) as raised:
            request_ai_text(
                lambda **_: (_ for _ in ()).throw(RuntimeError(secret_detail)),
                ["model-x"],
                "prompt",
                object(),
            )

        self.assertNotIn(secret_detail, raised.exception.user_message)
        self.assertIn(secret_detail, raised.exception.last_error)


if __name__ == "__main__":
    unittest.main()
