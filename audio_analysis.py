import librosa
import crepe
import numpy as np
from pydub import AudioSegment

class Audio_Analysis:
  def __init__(self):
    pass

  def get_audio_tone_score(self, sentence_duration, audio_file):
    audio = AudioSegment.from_wav(audio_file)
    scores = []
    for i, data in sentence_duration.items():
        start_time_ms = data['start_time'] * 1000
        end_time_ms = data['end_time'] * 1000
        segment_audio = audio[start_time_ms:end_time_ms]
        temp_file = "temp_segment.wav"
        segment_audio.export(temp_file, format="wav")
        score = self.analyse_tone(temp_file)
        print(f"Segment {i} score: {score}")
        scores.append(score)
    mean_score = np.mean(scores)
    return mean_score

  def analyse_tone(self, audio):
      y, sr = librosa.load(audio)
      rms_energy = librosa.feature.rms(y=y)[0]
      mean_rms_energy = np.mean(rms_energy)
      time, frequency, confidence, _ = crepe.predict(y, sr, viterbi=True)
      mean_pitch = np.mean(frequency[confidence > 0.5])
      S = np.abs(librosa.stft(y))**2
      spectral_energy = np.sum(S, axis=0)
      mean_spectral_energy = np.mean(spectral_energy)
      tone_score = (
          0.4 * (mean_rms_energy / 0.1) +
          0.4 * (mean_pitch / 200) +
          0.3 * (mean_spectral_energy / 1e6)
      )
      tone_score = min(max(tone_score, 0), 1) * 10
      return tone_score

  def get_audio_fluency_score(self, sentence_wpm, spk1_content):
      speech_rates = [v['wpm'] for v in sentence_wpm.values()]
      consistency_score, mean_rate, std_dev = self.calculate_consistency_score(speech_rates)
      overall_wpm, speed, speed_score = self.speech_speed_overall(speech_rates)
      total_filler_words, filler_percentage, filler_score = self.find_filler_words(spk1_content)
      fluency_score = (consistency_score + speed_score + filler_score) / 3
      print(f"Final Combined Score: {fluency_score:.2f} / 10")
      print(f"Consistency Score: {consistency_score:.2f} / 10")
      print(f"Speech Speed Score: {speed_score} / 10")
      print(f"Filler Words Score: {filler_score} / 10")
      print(f"Total Filler Words: {total_filler_words}")
      print(f"Filler Percentage: {filler_percentage:.2f}%")
      print(f"Mean Speech Rate: {mean_rate:.2f} words per minute")
      print(f"Standard Deviation of Speech Rate: {std_dev:.2f}")
      print(f"Overall Words Per Minute (WPM): {overall_wpm:.2f}")
      print(f"Speech Speed Category: {speed}")
      return fluency_score

  def calculate_consistency_score(self, speech_rates):
      values = np.array(speech_rates)
      min_val = np.min(values)
      max_val = np.max(values)
      mean_rate = np.mean(values)
      std_dev = 0
      if min_val == max_val:
          return 10, mean_rate, std_dev
      min_max_scaled = (values - min_val) / (max_val - min_val)
      std_dev = np.std(min_max_scaled)
      consistency_score = 10 * (1 - std_dev)
      return consistency_score, mean_rate, std_dev

  def speech_speed_overall(self, wpm_rates):
      overall_wpm = np.mean(wpm_rates)
      if 70 < overall_wpm <= 150:
          speed = 'Medium'
          speed_score = 10
      elif 150 < overall_wpm <= 200:
          speed = 'Medium to Fast'
          speed_score = 8
      elif overall_wpm <= 70:
          speed = 'Slow'
          speed_score = 5
      else:
          speed = 'Fast'
          speed_score = 5
      return overall_wpm, speed, speed_score


  def find_filler_words(self, text):
      speech_text = ''
      for key,value in text.items():
          speech_text += value
      speech_text = speech_text.split()

      filler_words = ["like", "um", "Um", "Um...", "Um..", "might", "aa", "aaa", "mean", "know", "well", "Well", "Oh", "oh",
                  "really", "basically", "oh", "maybe", "somehow", "Hi..", "Hi...", "Well", "like", "know", "mean"]

      total_filler_words = 0
      for word in filler_words:
          total_filler_words += speech_text.count(word)
      percent = (total_filler_words / max(len(speech_text), 1)) * 100
      score = 0
      if percent <= 5:
        score = 10
      elif percent <= 10:
        score = 8
      elif percent <= 20:
        score = 6
      elif percent <= 30:
        score = 4
      else:
        score = 2
      return total_filler_words, percent, score
