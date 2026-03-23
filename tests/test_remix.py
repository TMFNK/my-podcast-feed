import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(
            "/Users/edis-mac/Documents/03-Eddie-Python-Projects/python/my-podcast-feed-main/scripts"
        )
    ),
)

from remix import _call_llm, generate_script


class RemixTests(unittest.TestCase):
    def test_generate_script_reports_active_env_path_when_api_key_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            old_data_dir = os.environ.get("PODCAST_DATA_DIR")
            old_api_key = os.environ.get("OPENAI_API_KEY")
            os.environ["PODCAST_DATA_DIR"] = str(data_dir)
            os.environ.pop("OPENAI_API_KEY", None)

            try:
                with self.assertRaises(RuntimeError) as ctx:
                    generate_script(
                        articles=[
                            {
                                "title": "Example",
                                "source_name": "Feed",
                                "author": "Author",
                                "published": "2026-03-23T00:00:00+00:00",
                                "content": "Body",
                            }
                        ],
                        config={
                            "hosts": 2,
                            "llm": {
                                "provider": "openai",
                                "api_key_env": "OPENAI_API_KEY",
                                "model": "gpt-4.1",
                            },
                        },
                    )
            finally:
                if old_data_dir is None:
                    os.environ.pop("PODCAST_DATA_DIR", None)
                else:
                    os.environ["PODCAST_DATA_DIR"] = old_data_dir

                if old_api_key is None:
                    os.environ.pop("OPENAI_API_KEY", None)
                else:
                    os.environ["OPENAI_API_KEY"] = old_api_key

            self.assertIn(str(data_dir / ".env"), str(ctx.exception))

    @mock.patch("openai.OpenAI")
    def test_opencode_gpt_models_use_openai_responses_endpoint(self, mock_openai_client):
        response_client = mock.Mock()
        response_client.responses.create.return_value.output_text = '[{"speaker":"A","text":"Hi"}]'
        mock_openai_client.return_value = response_client

        result = _call_llm(
            "opencode",
            "gpt-5.4",
            "test-key",
            "prompt text",
            logger=mock.Mock(),
        )

        self.assertEqual(result, '[{"speaker":"A","text":"Hi"}]')
        mock_openai_client.assert_called_once_with(
            api_key="test-key",
            base_url="https://opencode.ai/zen/v1",
        )
        response_client.responses.create.assert_called_once_with(
            model="gpt-5.4",
            input="prompt text",
            max_output_tokens=8192,
        )

    @mock.patch("openai.OpenAI")
    def test_opencode_prefixed_model_ids_are_normalized(self, mock_openai_client):
        response_client = mock.Mock()
        response_client.responses.create.return_value.output_text = '[{"speaker":"A","text":"Hi"}]'
        mock_openai_client.return_value = response_client

        _call_llm(
            "opencode",
            "opencode/gpt-5.4",
            "test-key",
            "prompt text",
            logger=mock.Mock(),
        )

        response_client.responses.create.assert_called_once_with(
            model="gpt-5.4",
            input="prompt text",
            max_output_tokens=8192,
        )

    @mock.patch("anthropic.Anthropic")
    def test_opencode_claude_models_use_anthropic_messages_endpoint(self, mock_anthropic_client):
        messages_client = mock.Mock()
        messages_client.messages.create.return_value.content = [mock.Mock(text='[{"speaker":"A","text":"Hi"}]')]
        mock_anthropic_client.return_value = messages_client

        result = _call_llm(
            "opencode",
            "claude-sonnet-4-6",
            "test-key",
            "prompt text",
            logger=mock.Mock(),
        )

        self.assertEqual(result, '[{"speaker":"A","text":"Hi"}]')
        mock_anthropic_client.assert_called_once_with(
            api_key="test-key",
            base_url="https://opencode.ai/zen/v1",
        )
        messages_client.messages.create.assert_called_once_with(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": "prompt text"}],
        )

    @mock.patch("openai.OpenAI")
    def test_opencode_openai_compatible_models_use_chat_completions(self, mock_openai_client):
        chat_client = mock.Mock()
        chat_client.chat.completions.create.return_value.choices = [
            mock.Mock(message=mock.Mock(content='[{"speaker":"A","text":"Hi"}]'))
        ]
        mock_openai_client.return_value = chat_client

        result = _call_llm(
            "opencode",
            "glm-5",
            "test-key",
            "prompt text",
            logger=mock.Mock(),
        )

        self.assertEqual(result, '[{"speaker":"A","text":"Hi"}]')
        chat_client.chat.completions.create.assert_called_once_with(
            model="glm-5",
            max_tokens=8192,
            messages=[{"role": "user", "content": "prompt text"}],
        )

    @mock.patch("openai.OpenAI")
    def test_opencode_allows_explicit_api_style_override(self, mock_openai_client):
        response_client = mock.Mock()
        response_client.chat.completions.create.return_value.choices = [
            mock.Mock(message=mock.Mock(content='[{"speaker":"A","text":"Hi"}]'))
        ]
        mock_openai_client.return_value = response_client

        result = _call_llm(
            "opencode",
            "custom-model",
            "test-key",
            "prompt text",
            logger=mock.Mock(),
            provider_options={"api_style": "chat_completions", "base_url": "https://example.com/custom"},
        )

        self.assertEqual(result, '[{"speaker":"A","text":"Hi"}]')
        mock_openai_client.assert_called_once_with(
            api_key="test-key",
            base_url="https://example.com/custom/v1",
        )

    def test_opencode_unknown_models_raise_clear_error(self):
        with self.assertRaises(ValueError) as ctx:
            _call_llm(
                "opencode",
                "gemini-3.1-pro",
                "test-key",
                "prompt text",
                logger=mock.Mock(),
            )

        self.assertIn("Unable to determine OpenCode API style", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
