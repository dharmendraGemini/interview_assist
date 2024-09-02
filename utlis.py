
import os
import json

def extract_video_data(data, video_name, current_folder):


    # print("data is --->",data)
    conversation, spk0_time, spk1_time, sentence_wpm,sentence_duration = conversation_data(data, video_name, current_folder)
   
    spk0_content = {}
    spk1_content = {}

    
    for key,val in conversation.items():
        if val['speaker'] == 'spk_0':
            spk0_content[key] = val['transcript']
        else:
            spk1_content[key] = val['transcript']
            
    # print("conversation -->",conversation)  
    print(spk0_content)
    print(spk1_content)
    
    return conversation, spk0_content, spk1_content, spk0_time, spk1_time,sentence_wpm ,sentence_duration

def conversation_data(data, video_name, current_folder):
    sentence_duration = {}
    sentence_wpm = {}
    spk0_time = 0
    spk1_time = 0
    req_data = data["results"]["audio_segments"]
    
    candidate_wpm = {
        'wpm':0,
        'transript':''
    }
    spk = 'spk_0'
    conversation = {}
    flag = False
    text = ''
    serial_number = 1
    index = 0
    for val in req_data:
        
        
        
        # pprint(val)
        if val['speaker_label'] == "spk_0":
            spk0_time += float(val['end_time']) - float(val['start_time'])
        if val['speaker_label'] == "spk_1":
            curr_time = (float(val['end_time']) - float(val['start_time']))/60
            spk1_time += float(val['end_time']) - float(val['start_time'])
            sentence_cnt = len(val['transcript'].split())
            candidate_wpm = {
                'wpm': sentence_cnt/curr_time ,
                'transript':val['transcript']
            }
            sentence_wpm[index] = candidate_wpm
            sentence_duration[index] = {}
            sentence_duration[index]['start_time'] = float(val['start_time'])
            sentence_duration[index]['end_time'] = float(val['end_time'])
            sentence_duration[index]['transcript'] = val['transcript']
            index+=1


        if spk !=  val['speaker_label']:
            conversation[serial_number] = {
                "speaker": spk,
                "transcript": text
            }
            # print(spk, text)
            # print("check 1-->",conversation[serial_number])
            serial_number+=1
            text= ''
            spk = val['speaker_label']
            flag = True
            # print("after change-->",spk)
        if spk == val['speaker_label']:
            # print(" spk check-->",spk)
            text += val['transcript']
            spk = val['speaker_label']
            flag = False

    
    if flag == False:
        conversation[serial_number] = {
                "speaker": spk,
                "transcript": text
            }
    # print("conversation ---->",conversation)


    conversation_file = f'{video_name}_conversation.txt'
    output_file = os.path.join(current_folder,conversation_file)
    with open(output_file, 'w') as file:
        file.write(json.dumps(conversation, indent=4))

    return conversation, spk0_time, spk1_time,sentence_wpm ,sentence_duration
def ideal_answer():
    # text = "JavaScript handles asynchronous operations, such as promises and timers, using the event loop. When a promise or timer is encountered, the synchronous code continues to execute, while the asynchronous operation is deferred. Once the operation is completed, the event loop pushes the callback to the call stack, ensuring that it runs after the current execution context is cleared. This allows JavaScript to manage non-blocking, asynchronous behavior efficiently."
    # text = "An interpreter is a program that directly executes instructions written in a programming language without requiring them to be compiled into machine code. It translates high-level code into an intermediate form, executing it line by line. This allows for easier debugging and immediate execution of code."
    text = 'The CALCULATE function in Power BI changes the data context to apply specific filters to an expression. It helps you get results based on certain conditions. Think of it as a way to ask Power BI to “recalculate” something with new rules.'
    return text
                               
            
    