import cv2
import numpy as np
from fer import FER
import dlib
from imutils import face_utils
from scipy.spatial import distance as dist
import json

class VideoAnalyzer:
    def __init__(self, shape_predictor_path='shape_predictor_68_face_landmarks.dat'):
        # Initialize detectors
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(shape_predictor_path)  # Assuming you have this downloaded
        self.fer_detector = FER(mtcnn=True)
        self.normalized_score = None

    def analyze_video(self, video_path):
        # Open the video file
        cap = cv2.VideoCapture(video_path)

        # Get video details
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Initialize cumulative variables
        total_movement_counts = []
        total_blink_counts = 0
        total_emotion_counts = {'angry': 0, 'disgust': 0, 'fear': 0, 'happy': 0, 'sad': 0, 'surprise': 0, 'neutral': 0}

        # Process the whole video
        start_frame = 0
        end_frame = total_frames

        movement_counts, blink_counts, emotion_counts = self.analyze_clip(cap, start_frame, end_frame)
        
        total_movement_counts.extend(movement_counts)
        total_blink_counts += blink_counts
        for emotion, count in emotion_counts.items():
            total_emotion_counts[emotion] += count

        # Calculate cumulative statistics
        avg_movement_rate = np.mean(total_movement_counts) if total_movement_counts else 0
        total_frames_analyzed = sum(total_emotion_counts.values())
        emotion_percentages = {emotion: (count / total_frames_analyzed) * 100 for emotion, count in total_emotion_counts.items()} if total_frames_analyzed > 0 else {emotion: 0 for emotion in total_emotion_counts}

        sorted_emotions = sorted(emotion_percentages.items(), key=lambda x: x[1], reverse=True)
        dominant_emotion, dominant_emotion_percentage = sorted_emotions[0] if sorted_emotions else ('neutral', 0)
        second_dominant_emotion, second_dominant_emotion_percentage = sorted_emotions[1] if len(sorted_emotions) > 1 else ('neutral', 0)

        # Generate detailed description based on dominant emotion
        description, confidence_score = self.generate_description(dominant_emotion, dominant_emotion_percentage, second_dominant_emotion, second_dominant_emotion_percentage, avg_movement_rate, total_blink_counts, total_frames_analyzed, fps)

        # Output results
        video_result = {
            "confidence_score": confidence_score,
            "average_eye_movement_rate": self.normalized_score ,
            "dominant_facial_expression": dominant_emotion,
            "second_dominant_facial_expression": second_dominant_emotion
        }

        # Save results to a JSON file
        # with open('video_analysis_results.json', 'w') as f:
        #     json.dump({"video_score": video_result}, f, indent=4)

        # print(f"Results saved to video_analysis_results.json")

        return video_result

    def analyze_clip(self, cap, start_frame, end_frame):
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        movement_counts = []
        blink_counts = 0
        emotion_counts = {'angry': 0, 'disgust': 0, 'fear': 0, 'happy': 0, 'sad': 0, 'surprise': 0, 'neutral': 0}
        prev_left_eye_center = None
        prev_right_eye_center = None

        for frame_idx in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = self.detector(gray, 0)

            for rect in rects:
                shape = self.predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
                left_eye_center, right_eye_center, ear = self.calculate_eyeball_movement(shape)

                if prev_left_eye_center is not None and prev_right_eye_center is not None:
                    left_movement = dist.euclidean(prev_left_eye_center, left_eye_center)
                    right_movement = dist.euclidean(prev_right_eye_center, right_eye_center)
                    movement_counts.append(left_movement + right_movement)

                    if ear < 0.21:  # Threshold for blinking
                        blink_counts += 1

                prev_left_eye_center = left_eye_center
                prev_right_eye_center = right_eye_center

            # Emotion detection
            result = self.fer_detector.detect_emotions(frame)
            for face in result:
                emotions = face['emotions']
                top_emotion = max(emotions, key=emotions.get)
                emotion_counts[top_emotion] += 1

        return movement_counts, blink_counts, emotion_counts

    def calculate_eyeball_movement(self, landmarks):
        left_eye = landmarks[42:48]
        right_eye = landmarks[36:42]
        left_eye_center = left_eye.mean(axis=0).astype("int")
        right_eye_center = right_eye.mean(axis=0).astype("int")
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        return left_eye_center, right_eye_center, ear

    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def generate_description(self, dominant_emotion, dominant_emotion_percentage, second_dominant_emotion, second_dominant_emotion_percentage, avg_movement_rate, total_blink_counts, total_frames_analyzed, fps):
        description = ""
        confidence_score = 8  # Default confidence score

        # Normalizing the eye movement rate
        max_movement_rate = 10  # Assuming 10 as the maximum expected eye movement rate
        normalized_movement_rate = np.clip(avg_movement_rate / max_movement_rate, 0, 1)

        # Scale normalized rate to a score from 1-10
        self.normalized_score  = normalized_movement_rate * 10

        if dominant_emotion == 'neutral':
            description = (
                f"The candidate's predominant emotional state is neutral, accounting for {dominant_emotion_percentage:.2f}% of the video. "
                f"However, there were also noticeable frames where the second most dominant emotion, {second_dominant_emotion}, "
                f"was observed with {second_dominant_emotion_percentage:.2f}% presence. This indicates that while the overall demeanor "
                f"appears neutral, there are instances where other emotions were also present."
            )
        elif dominant_emotion in ['fear', 'disgust']:
            description = (
                f"The candidate appears quite uneasy with a dominant emotional state of {dominant_emotion} "
                f"at {dominant_emotion_percentage:.2f}%. There is some evidence of nervousness "
                f"indicated by eye movements and blinking. Overall, the candidate's demeanor suggests a higher "
                f"level of anxiety."
            )
            confidence_score -= 2
        elif dominant_emotion == 'happy':
            description = (
                f"The candidate seems positive with a dominant emotional state of {dominant_emotion} "
                f"at {dominant_emotion_percentage:.2f}%. The eye movement and blinking are within normal ranges, "
                f"indicating that the candidate is calm and composed throughout the video."
            )
            confidence_score += 2
        elif dominant_emotion == 'sad':
            description = (
                f"The candidate appears to be experiencing a dominant emotional state of sadness at {dominant_emotion_percentage:.2f}%. "
                f"Eye movement and blink rate are moderate, which might indicate that the candidate is feeling down or reflective."
            )
            confidence_score -= 1
        elif dominant_emotion == 'surprise':
            description = (
                f"The candidate shows a dominant emotional state of surprise at {dominant_emotion_percentage:.2f}%. "
                f"Eye movements and blink rate might be heightened, reflecting a state of astonishment or unexpectedness."
            )
        else:
            description = (
                f"The candidate shows a mixed emotional state with no overwhelmingly dominant emotion. Eye movement and blink rate "
                f"are moderate, suggesting that while the candidate might not be extremely anxious, there are "
                f"slight signs of nervousness. The overall demeanor is neutral."
            )

        # Analyze nervousness based on eye movement and blink counts
        if avg_movement_rate > 2 or total_blink_counts > (20 * (total_frames_analyzed / fps / 60)):
            description += (
                " The eye movement and blink count suggest some level of nervousness, adding to the overall "
                "impression of anxiety or unease."
            )
            confidence_score -= 1

        return description, confidence_score
