import os
import sys
import time
import shutil
import unittest
import tempfile
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from voice.states import VoiceState
from voice.text_shortener import prepare_spoken_text
from voice.providers.fake_provider import FakeTTSProvider
from voice.voice_manager import VoiceManager


class MockAudioPlayer:
    def __init__(self, playback_duration: float = 0.04, should_fail: bool = False):
        self.playback_duration = playback_duration
        self.should_fail = should_fail
        self._is_playing = False
        self._stop_event = threading.Event()
        self.played_files = []

    def is_playing(self) -> bool:
        return self._is_playing

    def play(self, audio_file_path: str, on_started=None, on_finished=None, on_error=None) -> bool:
        self.stop()
        if self.should_fail:
            if on_error:
                on_error("MockAudioPlayer simulated error")
            return False

        self.played_files.append(audio_file_path)
        self._stop_event.clear()
        self._is_playing = True

        def _worker():
            if on_started and not self._stop_event.is_set():
                on_started()
            self._stop_event.wait(timeout=self.playback_duration)
            self._is_playing = False
            if not self._stop_event.is_set() and on_finished:
                on_finished()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        self._is_playing = False


class TestTextShortener(unittest.TestCase):
    def test_strip_markdown(self):
        md = "## Header\nThis is **bold** and *italic* with a [link](http://example.com)."
        spoken = prepare_spoken_text(md)
        self.assertNotIn("#", spoken)
        self.assertNotIn("**", spoken)
        self.assertNotIn("*", spoken)
        self.assertNotIn("http://", spoken)
        self.assertIn("Header", spoken)
        self.assertIn("This is bold and italic with a link.", spoken)

    def test_code_block_replacement(self):
        text = "Here is the code:\n```python\nprint('hello')\n```\nDone."
        spoken = prepare_spoken_text(text)
        self.assertNotIn("print('hello')", spoken)
        self.assertIn("I've prepared the code.", spoken)
        self.assertIn("Done.", spoken)

    def test_inline_code_preservation(self):
        text = "Run `python main.py` to start."
        spoken = prepare_spoken_text(text)
        self.assertEqual(spoken, "Run python main dot py to start.")

    def test_sentence_boundary_truncation(self):
        long_text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        spoken = prepare_spoken_text(long_text, max_chars=40)
        self.assertTrue(spoken.endswith("."))
        self.assertLessEqual(len(spoken), 40)

    def test_spoken_text_keeps_only_two_sentences(self):
        spoken = prepare_spoken_text("First sentence. Second sentence. Third sentence.")
        self.assertEqual(spoken, "First sentence. Second sentence.")


class TestVoiceManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="levi_voice_test_")
        self.fake_provider = FakeTTSProvider(delay_seconds=0.01)
        self.mock_player = MockAudioPlayer(playback_duration=0.04)
        self.manager = VoiceManager(
            provider=self.fake_provider,
            audio_player=self.mock_player,
            cache_dir=self.temp_dir,
        )

    def tearDown(self):
        self.manager.cleanup()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initial_state_idle(self):
        self.assertEqual(self.manager.get_state(), VoiceState.IDLE)
        self.assertFalse(self.manager.is_speaking())

    def test_speak_lifecycle(self):
        req_id = self.manager.speak("Hello. I am LEVI.")
        self.assertIsNotNone(req_id)
        time.sleep(0.12)
        self.assertEqual(self.manager.get_state(), VoiceState.IDLE)
        self.assertEqual(len(self.fake_provider.synthesize_calls), 1)

    def test_stop_speaking_cancels_playback(self):
        self.manager.speak("This is a long message that should be canceled.")
        time.sleep(0.01)
        self.manager.stop_speaking()
        self.assertEqual(self.manager.get_state(), VoiceState.IDLE)
        self.assertFalse(self.manager.is_speaking())

    def test_concurrency_policy_latest_utterance_wins(self):
        req1 = self.manager.speak("First utterance.")
        time.sleep(0.005)
        req2 = self.manager.speak("Second utterance replaces the first.")
        self.assertNotEqual(req1, req2)
        time.sleep(0.12)
        self.assertEqual(self.manager.get_state(), VoiceState.IDLE)

    def test_provider_failure_fallback_to_idle(self):
        failing_provider = FakeTTSProvider(should_fail=True, delay_seconds=0.0)
        manager = VoiceManager(
            provider=failing_provider,
            audio_player=self.mock_player,
            cache_dir=self.temp_dir,
        )
        manager.speak("Test failure handling.")
        time.sleep(0.12)
        self.assertEqual(manager.get_state(), VoiceState.IDLE)
        manager.cleanup()


if __name__ == "__main__":
    unittest.main()
