import unittest
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stegano.audio import decode_sleepy_alarm, diagnose_sleepy_alarm
ROOT=Path(__file__).resolve().parents[1]
SLEEPY_FLAG='ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'


def _synthetic_ask(flag, sample_rate=48_000, baud=50.0, carrier=8_000.0):
 bits = ' '.join(f'{ord(character):08b}' for character in flag)
 symbols = [0 if symbol == ' ' else int(symbol) + 1 for symbol in bits]
 samples_per_symbol = round(sample_rate / baud)
 sample_indices = np.arange(len(symbols) * samples_per_symbol)
 levels = np.repeat(np.asarray([0.08, 0.35, 0.72])[symbols], samples_per_symbol)
 signal = levels * np.sin(2 * np.pi * carrier * sample_indices / sample_rate)
 return signal[:, None], sample_rate, samples_per_symbol


class TestSleepyAlarm(unittest.TestCase):
 def test_official_reference_assisted_flag(self):
  result=decode_sleepy_alarm(ROOT/'data/sleepy_alarm/morning_n_breakfast.mp3',ROOT/'data/sleepy_alarm/morning_n_breakfast_original.mp3')
  self.assertTrue(result['reference_assisted'])
  self.assertTrue(result['format_valid'])
  self.assertEqual(result['decoded_text'],SLEEPY_FLAG)
  self.assertEqual(result['character_count'],39)
  self.assertEqual(result['symbol_count'],350)
  self.assertEqual(result['separator_count'],38)

 def test_reference_overlap_inside_early_symbol_preserves_prefix(self):
  target, sample_rate, samples_per_symbol = _synthetic_ask(SLEEPY_FLAG)
  reference = np.zeros_like(target)
  overlap_start = samples_per_symbol + samples_per_symbol // 2

  def align_with_mid_symbol_start(target_audio, sr, reference_audio, ref_sr):
   self.assertEqual(sr, sample_rate)
   self.assertEqual(ref_sr, sample_rate)
   return (
    target_audio[overlap_start:],
    reference_audio[overlap_start:],
    {'lag_samples': overlap_start, 'correlation': 1.0, 'target_start_sample': overlap_start},
   )

  with patch('stegano.audio.sf.read', side_effect=[(target, sample_rate), (reference, sample_rate)]), \
       patch('stegano.audio._align', side_effect=align_with_mid_symbol_start):
   decoded = diagnose_sleepy_alarm('target.mp3', 'reference.mp3')

  result = decoded['result']
  diagnostics = decoded['diagnostics']
  expected_symbols = list(' '.join(f'{ord(character):08b}' for character in SLEEPY_FLAG))
  self.assertEqual(result['decoded_text'],SLEEPY_FLAG)
  self.assertEqual(result['symbol_count'],350)
  self.assertEqual(result['separator_count'],38)
  self.assertEqual(result['character_count'],39)
  self.assertEqual(result['alignment']['target_start_sample'],overlap_start)
  self.assertEqual(diagnostics['symbol_labels'][:16],expected_symbols[:16])
  self.assertAlmostEqual(diagnostics['amplitude_levels'][0],0.35,places=6)
