import unittest

from ai_filter import is_job_matched


class TestJobVerdictParsing(unittest.TestCase):
    def test_english_matched(self):
        self.assertTrue(
            is_job_matched("Verdict: MATCHED\nReason: Strong Python backend fit.", "en")
        )

    def test_english_rejected(self):
        self.assertFalse(
            is_job_matched("Verdict: REJECTED\nReason: Pure design role.", "en")
        )

    def test_russian_matched(self):
        self.assertTrue(is_job_matched("Вердикт: ПОДХОДИТ\nПричина: Python бот.", "ru"))

    def test_russian_rejected(self):
        self.assertFalse(is_job_matched("Вердикт: НЕ ПОДХОДИТ\nПричина: SMM.", "ru"))


if __name__ == "__main__":
    unittest.main()
