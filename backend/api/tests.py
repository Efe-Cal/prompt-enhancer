from django.test import TestCase

from .shared_utils import parse_llm_response_markdown, EnhancedPromptResponse

# Create your tests here.


class ParseLlmResponseMarkdownTests(TestCase):
	def test_parses_heading_label(self):
		response = "## Improved Prompt\nWrite a haiku about sunrise."
		self.assertEqual(parse_llm_response_markdown(response), "Write a haiku about sunrise.")

	def test_parses_bold_wrapped_heading_label(self):
		response = "**## Improved Prompt**\nWrite a limerick about coding."
		self.assertEqual(parse_llm_response_markdown(response), "Write a limerick about coding.")

	def test_parses_bold_heading_variant(self):
		response = "**# Improved Prompt**\nGenerate a polite support reply."
		self.assertEqual(parse_llm_response_markdown(response), "Generate a polite support reply.")

	def test_parses_list_label_with_inline_value(self):
		response = "- Improved Prompt: Summarize this text in 3 bullets."
		self.assertEqual(parse_llm_response_markdown(response), "Summarize this text in 3 bullets.")

	def test_parses_bold_list_label_with_inline_value(self):
		response = "**- Improved Prompt:** Summarize this text in 1 sentence."
		self.assertEqual(parse_llm_response_markdown(response), "Summarize this text in 1 sentence.")

	def test_parses_bold_label_inline_value(self):
		response = "**Improved Prompt:** Build a study plan for 2 weeks."
		self.assertEqual(parse_llm_response_markdown(response), "Build a study plan for 2 weeks.")

	def test_parses_fenced_block_content(self):
		response = "- Improved Prompt:\n```markdown\nCreate a clean API spec for this feature.\n```"
		self.assertEqual(parse_llm_response_markdown(response), "Create a clean API spec for this feature.")

	def test_returns_none_when_marker_has_no_content(self):
		response = "- Improved Prompt:\n```markdown\n```"
		self.assertIsNone(parse_llm_response_markdown(response))


class EnhancedPromptResponseTests(TestCase):
	def test_parses_with_both_fields(self):
		obj = EnhancedPromptResponse(analysis="Some analysis", improved_prompt="Better prompt")
		self.assertEqual(obj.analysis, "Some analysis")
		self.assertEqual(obj.improved_prompt, "Better prompt")

	def test_parses_without_analysis_field(self):
		"""analysis is optional – a missing field must not raise a ValidationError."""
		obj = EnhancedPromptResponse(improved_prompt="Better prompt")
		self.assertIsNone(obj.analysis)
		self.assertEqual(obj.improved_prompt, "Better prompt")
