import unittest
from backend.providers.prompt import parse_enhancer_answer
class PromptEnhancerTests(unittest.TestCase):
 def test_t2i_parse(self):
  result=parse_enhancer_answer('<think>draft</think> text {"rewritten_prompt":"clean whiteboard fox","wh_ratio":"16:9"}','t2i');self.assertTrue(result.parse_ok);self.assertEqual((result.rewritten_prompt,result.wh_ratio),('clean whiteboard fox','16:9'))
 def test_edit_parse(self):
  result=parse_enhancer_answer('{"rewritten_prompt":"change coat","ratio_follow":"<image1>"}','edit');self.assertEqual(result.ratio_follow,'<image1>')
 def test_fallback(self):
  result=parse_enhancer_answer('plain answer','t2i');self.assertFalse(result.parse_ok);self.assertEqual(result.rewritten_prompt,'plain answer')
