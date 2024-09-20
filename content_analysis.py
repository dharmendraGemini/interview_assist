import os
import json
import utlis
from pprint import pprint
from groq import Groq
from dotenv import load_dotenv
from utlis import combined_data

class ContentAnalyzer:
    def __init__(self):
        load_dotenv('.env')
        self.client = Groq(api_key=os.getenv("api_key"))
        self.grammar_errors = {}
        self.grammar_score = None
        self.repetition_score = None
        self.content_similarity_result = {}
        self.ideal_ans = utlis.ideal_answer()
        self.ans_validation_score = None
        self.clarity = None
        self.coherence = None
        self.optimal_repetition = None
        self.content_result = {}
        self.question_wise_data = utlis.combined_data()




    def run(self, spk0_content, spk1_content):
        self.grammar_errors = self.grammar_check(spk1_content)
        self.content_result['grammar_score'] = self.calculate_grammar_score(spk1_content)
      
        self.content_similarity_result = self.content_similarity(self.ideal_ans, spk0_content, spk1_content)
        self.content_result['ans_validation_score'] = self.content_similarity_result['similarity_score']
        self.content_result['clarity'] = self.content_similarity_result['clarity_score']
        self.content_result['coherence'] = self.content_similarity_result['coherence_score']
        self.content_result['optimal_repetetion'] = self.calculate_repetition_score(spk1_content)
        

        return self.content_result

    def question_wise_result(self):
        # for i in self.question_wise_data:
        pass



    def _request_groq_completion(self, model, messages, temperature=0.0, max_tokens=2000, top_p=1):
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=False,
                stop=None,
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Failed to get a response from Groq API: {str(e)}")

    def grammar_check(self, speaker_text):
        messages = [
            {
                "role": "system",
                "content": "You are an English Grammar checker AI bot."
            },
            {
                "role": "user",
                "content": f"""
                Your task is to check for significant grammatical errors, excluding punctuation errors, and identify any repetitions in the following sentences. 
                Each sentence is indexed by a unique number and consider one unique indexed value at a time for {speaker_text}.

                transcript:
                {speaker_text}

                For each sentence, return the grammatical errors that a good speaker would typically avoid. Highlight the sentence with the error, specify the type of grammatical error, and provide the count of such errors. Also, identify any repetitive parts in the sentence, both in meaning and sentence structure.

                Based on the identified errors and repetitions, assign an English grammar quality score out of 5 using the following criteria:

                - 5/5: Ideal English speaker with minimal to no errors.
                - 4/5: Fluent English speaker with minor errors that do not hinder comprehension.
                - 3/5: Understandable but with noticeable errors and repetition that may affect clarity.
                - Less than 2/5: Significant grammatical errors that make comprehension difficult

                Note:
                - Please provide the final response in JSON format only. No additional text or explanations are needed.
                - Provide the results for each sentence separately.
                - Include a count of the significant grammatical errors and a count of repetitive words that a good speaker should avoid.
                - Include an overall English grammar quality score.

                Output Response:
                {{
                    "grammar_quality_score": English grammar quality score out of 10,
                    "total_significant_errors": Total number of significant grammatical errors,
                    "total_repetitions": Total number of repetitive words,
                    "sentences": {{
                        "number": {{
                            "sentence": "The full sentence with the error.",
                            "errors": [
                                {{
                                    "error_type": "Type of grammatical error",
                                    "count": Number of occurrences
                                }}
                            ],
                            "repetitive_parts": [
                                "List of repeated words or phrases"
                            ]
                        }}
                    }},
                }}
                """
            }
        ]
        
        response_text = self._request_groq_completion(model="llama3-70b-8192", messages=messages)
        print('grammar check')
        pprint(response_text)
        return json.loads(response_text)

    def content_similarity(self, ideal_answer, question, candidate_answer):
        messages = [
            {
                "role": "system",
                "content": "You are a content similarity checker AI bot of an interview."
            },
            {
                "role": "user",
                "content": f"""
                Evaluate the content similarity between the ideal answer and the candidate's answer.
                Question: {question}
                Ideal answer: {ideal_answer}
                Candidate's answer: {candidate_answer}

                The task is to compare the relevance of the candidate's response to the ideal answer, focusing on the alignment of key concepts, completeness, clarity, coherence, and accuracy.
                Provide a content similarity score out of ten, where ten indicates a perfect match and one indicates no relevance. 
                Return the response only in JSON format as follows:
                {{
                    "similarity_score": "<score>",
                    "clarity_score":"<score>",
                    "consistency_score":"<score>",
                    "coherence_score":"<score>"
                }}
                
                where:
                "clarity_score": Ensure the text is clear and easy to understand. This involves checking for ambiguous phrases and ensuring the message is straightforward.
                "consistency_score": Check for consistent use of tense, point of view, and terminology throughout the text.
                "coherence_score": Look at how well the ideas flow together. Each sentence and paragraph should logically connect to the next.
                Note:
                - Please provide the final response in JSON format only. No additional text or explanations are needed.
                """
            }
        ]
        
        response_text = self._request_groq_completion(model="llama3-70b-8192", messages=messages)
        print('content similarity-->')
        pprint(response_text)
        return json.loads(response_text)

    def calculate_grammar_score(self, spk1_content):
        text = ''.join(spk1_content.values())
        total_words = len(text.split())

        grammatical_errors = self.grammar_errors['total_significant_errors']
        repetitions = self.grammar_errors['total_repetitions']

        weight_grammar = 4
        weight_repetition = 2

        weighted_errors = (grammatical_errors * weight_grammar) + (repetitions * weight_repetition)
        max_possible_errors = total_words * (weight_grammar + weight_repetition)
        score = 10 - (weighted_errors / max_possible_errors * 10)
        return max(0, min(10, score))

    def calculate_repetition_score(self,  spk1_content):
        text = ''.join(spk1_content.values())
        total_words = len(text.split())

        repetition_ratio = (self.grammar_errors['total_repetitions'] / total_words) * 100

        if repetition_ratio <= 3:
            final_score = 10
        elif repetition_ratio <= 5:
            final_score = 9
        elif repetition_ratio <= 8:
            final_score = 7.5
        elif repetition_ratio <= 10:
            final_score = 6
        elif repetition_ratio <= 12:
            final_score = 4.5
        else:
            final_score = 3

        return final_score
