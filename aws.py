import os
import json
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError




class S3VideoManager:
    def __init__(
            self, 
            video, 
            local_video_folder='input', 
            bucket_name='interview-performance-analysis', 
            s3_video_folder='videos', 
            s3_output_folder='transcribed_files'
        ):
        
        #load env variables
        load_dotenv('.env')

        #initialize aws credentials
        self.access_key = os.getenv("aws_access_key_id")
        self.secret_key = os.getenv("aws_secret_access_key")
        self.session_token = os.getenv("aws_session_token")
        self.region = os.getenv("aws_region")

        #boto3 clients
        self.transcribe_client = boto3.client(
            'transcribe',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            aws_session_token=self.session_token,
            region_name=self.region
        )
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            aws_session_token=self.session_token,
            region_name=self.region
        )



        # Define file paths and path keys
        self.local_video_folder = local_video_folder
        self.video = video
        self.local_file_path = os.path.join(self.local_video_folder, self.video)
        self.bucket_name = bucket_name
        self.s3_video_folder = s3_video_folder
        self.s3_output_folder = s3_output_folder
        self.video_name = video.split('.')[0]
        self.s3_video_key = f'{self.s3_video_folder}/{self.video}'
        self.s3_output_file_key = f'{self.s3_output_folder}/{self.video_name}.txt'
        print(self.s3_output_file_key)

    def upload_video_to_s3(self):
        
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=self.s3_video_key)
            print(f'Video already exists in s3://{self.bucket_name}/{self.s3_video_key}')
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Upload video to S3 if it does not exist
                try:
                    self.s3_client.upload_file(self.local_file_path, self.bucket_name, self.s3_video_key)
                    print(f'Successfully uploaded {self.local_file_path} to s3://{self.bucket_name}/{self.s3_video_key}')
                except Exception as upload_error:
                    print(f'Error uploading file: {upload_error}')
            elif error_code == '400':
                print(f'Bad Request: Please check the bucket name, key, and permissions. Error: {e}')
            else:
                print(f'Error checking file existence: {e}') 
    def transcription(self):
        media_file_uri = f's3://{self.bucket_name}/{self.s3_video_key}'
        try:
            transcription_job = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=f'interview-performance-analysis-{self.video_name}',
                Media={'MediaFileUri': media_file_uri},
                MediaFormat='mp4',
                LanguageCode='en-US',
                OutputBucketName=self.bucket_name,
                OutputKey=self.s3_output_file_key,
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 2
                }
            )
            print("Transcription job started successfully:", transcription_job)
            while True:
                job = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=transcription_job['TranscriptionJob']['TranscriptionJobName']
                )
                if job['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                    break

            print(job['TranscriptionJob']['TranscriptionJobStatus'])
            if job['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                print(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
        except Exception as e:
            print("Error starting transcription job:", e)
        
        
            
    def save_output(self,current_folder):
        print(f"Bucket: {self.bucket_name}, Key: {self.s3_output_file_key}")
        
        # Fetch the file from S3
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.s3_output_file_key)
        print(response)
        
        # Read and decode the file content
        file_content = response['Body'].read().decode('utf-8')
        data = json.loads(file_content)
        
        # Define output directory and video folder
        raw_file = f'{self.video_name}_raw.txt'
        output_file = os.path.join(current_folder,raw_file)
        with open(output_file, 'w') as file:
            file.write(json.dumps(data, indent=4))

        return data                                 

def main():
    video_manager = S3VideoManager(video='better-video.mp4')
    video_manager.upload_video_to_s3()
    video_manager.transcription()


