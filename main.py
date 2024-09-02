import os
import utlis
import json
from aws import AwsManager
from content_analysis import ContentAnalyzer
from audio_analysis import Audio_Analysis


class InterviewAnalyzer:
    def __init__(self, video):
        
        self.video_name = video.split('.')[0]
        self.AwsManager = AwsManager(video)
        self.ContentAnalyzer = ContentAnalyzer() 
        self.AudioAnalyzer =  Audio_Analysis()
        self.output_folder = "output"
        self.data = None
        self.current_folder = self.create_output_dir(self.output_folder)
        self.conversation =None
        self.spk0_content=None
        self.spk1_content = None
        self.spk0_time = None
        self.spk1_time = None
        self.sentence_wpm = None
        self.content_result = {}
        self.input_folder = 'input'
        self.sentence_duration = None
        self.final_result ={}
        

        

    def run(self):
        self.AwsManager.upload_video_to_s3()
        self.AwsManager.transcription()
        self.data = self.AwsManager.save_output(self.current_folder)
        self.conversation, self.spk0_content, self.spk1_content, self.spk0_time, self.spk1_time,self.sentence_wpm ,self.sentence_duration= utlis.extract_video_data(self.data, self.video_name, self.current_folder)
        self.content_result = self.ContentAnalyzer.run(self.spk0_content,self.spk1_content)
        self.audio_result = self.AudioAnalyzer.run(self.input_folder,self.video_name,self.sentence_wpm, self.sentence_duration, self.spk1_content)
        self.save_results()
        return self.content_result, self.audio_result
    

    def save_results(self):
        self.final_result['content_score']= self.content_result
        self.final_result['audio_score'] = self.audio_result
        final_result_file = f'{self.current_folder}/{self.video_name}_results.txt'
        with open(final_result_file, 'w') as file:
            file.write(json.dumps(self.final_result, indent=4))

    def create_output_dir(self, output_folder): 
        file_cnt = 0
        existing_folders = os.listdir(output_folder)
        filtered_folders = [folder for folder in existing_folders if folder.startswith(f"{self.video_name}")]
        sorted_folders = sorted(filtered_folders, reverse=True)

        print(sorted_folders)

        if len(sorted_folders) > 0:
            cnt = (int)(sorted_folders[0].split('_')[-1])
            file_cnt = cnt+1

        current_folder = os.path.join(output_folder, f"{self.video_name}_{file_cnt}")

        os.makedirs(current_folder,exist_ok=True)
        print(f"Folder {current_folder}")
        
        return current_folder

        





if __name__ == "__main__":
    video = 'better-video.mp4'
    
    interview_analyzer  = InterviewAnalyzer(video)
    content_result, audio_result = interview_analyzer.run()
    print(content_result,audio_result)
    


    