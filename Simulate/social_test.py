from llm_respond import LLM
import csv
import re
import json
import os
from tqdm import tqdm

class StudentSocialTestPipeline:
    def __init__(self, ses="low", performance="50",number = 5,quality = "low", model="gpt-4.1-mini", temperature=0.7, max_tokens=512,base_path=""):
        self.ses = ses
        self.performance = performance
        self.number = number
        self.quality = quality
        self.recommendation = LLM(model=model, temperature=temperature, max_tokens=max_tokens)
        self.post_student = LLM(model=model, temperature=temperature, max_tokens=max_tokens)
        
        # File paths with SES and performance in filenames
        self.base_path = base_path
        self.slide_file = self.base_path + "high_school_slide_only.json"
        self.output_files = {
            'pre': self.base_path + f"post_with_llm_{ses}_{performance}.csv",
            'rec': self.base_path + f"parent_recommend_with_llm_{ses}_{performance}.csv",
            'post': self.base_path + f"paren_teacher_post_with_llm_{ses}_{performance}.csv"
        }
        
        # Load slides data once
        with open(self.slide_file, "r", encoding="utf-8") as f:
            self.slides_data = json.load(f)
    
    
    def get_post_profile(self):
        """Generate post-test profile"""
        return """
        You are a high school student taking an artificial intelligence test.
        Your socioeconomic status (SES) is: {ses}
        Your academic performance in AI is represented by an accuracy score of {performance}%:
            0% means you get all answers wrong
            100% means you get all answers correct
        This score affects how likely you are to answer correctly and how confident you feel:
            Higher accuracy → higher correctness + higher confidence
            Lower accuracy → lower correctness + lower confidence

        Your Task
            You will receive AI-related test questions (multiple-choice or fill-in-the-blank).
            For each question:
                Use your past answers and teacher-provided materials to make a new attempt.
                Provide an answer based on what you've learned.
                Explain why you chose that answer.
                Report your confidence level on a scale of 0–100:
                    0 = not confident at all
                    100 = completely confident

        Response format (must follow this structure):
            <explanation> Your explanation here. </explanation>
            <answer> Your answer here. (e.g., "A" for multiple choice, or a specific word/phrase for fill-in-the-blank) </answer>
            <confidence> A number between 0 and 100. </confidence>

        Examples:
            <explanation> I chose A because supervised learning involves labeled data. </explanation>
            <answer> A </answer>
            <confidence> 75 </confidence>
        """.format(ses=self.ses, performance=self.performance)
    
    def get_recommendation_profile(self, candidate_materials=""):
        """Generate recommendation profile"""
        prompt = """
        You are a teacher in society (e.g., working in educational services or private tutoring) who supports high school students in learning Artificial Intelligence (AI). Your task is to generate appropriate learning materials for a student based on their background and the specified number and quality of resources to be provided.

        1. Student Background  
            - Socioeconomic status (SES): {ses}  
            - Academic accuracy in AI: {performance}%

        2. Resource Requirements (Predefined)  
            - Number of materials to provide: {number}  
            - Desired quality level of materials: {quality} (one of low, middle, high)

        3. Your Task  
            - Based on the student's background and the predefined number and quality of resources, write a brief explanation for your recommendation.  
            - Then, generate exactly {number} learning resources, with content and depth appropriate to the specified quality level `{quality}`.  
            - You may draw from your own teaching experience and the candidate materials listed below.  
            - Do not exceed the number of materials specified.

        4. Candidate Materials  
        {candidate_materials}

        5. Response Format  
        <explanation> Your reasoning here. </explanation>  
        <materials>  
        Material X: short summary  
        ...  
        </materials>
        """.format(ses=self.ses, performance=self.performance, number=self.number, quality=self.quality, candidate_materials=candidate_materials)
        return prompt

    
    def extract_response_fields(self, response, fields):
        """Extract fields from response using regex"""
        results = {}
        for field in fields:
            pattern = rf"<{field}>(.*?)</{field}>"
            match = re.search(pattern, response, re.DOTALL if field == 'materials' else 0)
            results[field] = match.group(1).strip() if match else ""
        return results

    def get_slide(self, materials):
        lines = materials.strip().split('\n')
        slides = []
        for line in lines:
            match = re.match(r"(slide \d+):", line.strip())
            if match:
                slides.append(match.group(1))
        return slides

    def get_all_materials(self, lecture_id):
        """Get all materials for a lecture"""
        lecture_key = f"lecture {lecture_id}"
        lecture_data = self.slides_data.get(lecture_key, {})
        
        if not lecture_data:
            return ""
            
        sorted_slides = sorted(lecture_data.items(), key=lambda x: int(x[0].replace("slide ", "")))
        return "\n".join(f"{key}: {value}" for key, value in sorted_slides)
    
    def count_total_rows(self, input_file):
        """Count total rows in CSV file for progress bar"""
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return sum(1 for _ in reader)
    
    def process_csv_stage(self, input_file, output_file, process_func, new_fields, stage_name):
        """Generic CSV processing function with progress bar"""
        # Read completed records
        completed_set = set()
        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    completed_set.add((row["lecture"], row["question"]))
        
        # Count total rows for progress bar
        total_rows = self.count_total_rows(input_file)
        
        # Process records
        with open(output_file, "a", newline="", encoding="utf-8") as outfile:
            with open(input_file, "r", encoding="utf-8") as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames + new_fields
                # Add SES and performance columns if they don't exist
                if "ses" not in fieldnames:
                    fieldnames = fieldnames + ["ses", "performance"]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
                
                if os.stat(output_file).st_size == 0:
                    writer.writeheader()
                
                # Create progress bar
                pbar = tqdm(total=total_rows, desc=f"{stage_name} Processing", unit="rows")
                
                processed_count = 0
                for row in reader:
                    key = (row["lecture"], row["question"])
                    if key in completed_set:
                        pbar.update(1)
                        continue
                    
                    # Add SES and performance to row
                    row["ses"] = self.ses
                    row["performance"] = self.performance
                    
                    # Process the row
                    new_data = process_func(row)
                    row.update(new_data)
                    
                    writer.writerow(row)
                    outfile.flush()
                    
                    processed_count += 1
                    pbar.set_postfix({
                        'Lecture': row['lecture'], 
                        'Question': row['question'],
                        'Processed': processed_count
                    })
                    pbar.update(1)
                
                pbar.close()
    

    
    def process_recommendation(self, row):
        """Process recommendation stage"""
        candidate_materials = self.get_all_materials(row['lecture'])
        profile = self.get_recommendation_profile(candidate_materials=candidate_materials)
        
        history = f"""
        The student's history records are as follows:
        Question: {row["contents"]}
        Student answer: {row["post_response"]}(The confidence level on a scale of 0–100:0 = not confident at all,100 = completely confident)
        Correct answer: {row["correct_answer"]}
        """
        
        prompt = [
            {"role": "system", "content": profile},
            {"role": "user", "content": history}
        ]
        
        response = self.recommendation.chat(prompt)
        fields = self.extract_response_fields(response, ["materials"])
        

        return {
            "parent_materials": fields["materials"],
            "parent_recommendation": response
        }
    
    def process_post_test(self, row):
        """Process post-test stage"""
        # Skip if no recommendation was made
        
        # Get materials content
        materials_content =  row["parent_materials"]
        
        profile = self.get_post_profile()
        question_format = f"""
        The student's history records are as follows:
        Question: {row["contents"]}
        Student answer: {row["post_response"]}
        The materials provided by the teacher are:
        Materials recommended: {materials_content}
        """
        
        prompt = [
            {"role": "system", "content": profile},
            {"role": "user", "content": question_format}
        ]
        
        response = self.post_student.chat(prompt)
        fields = self.extract_response_fields(response, ["answer", "confidence"])
        
        return {
            "parent_post_llm_answer": fields["answer"],
            "parent_post_llm_confidence": fields["confidence"],
            "parent_post_response": response
        }
    
    def run_pipeline(self):
        """Run the complete pipeline with progress bars"""
        print(f"开始运行学生测试流水线 - SES: {self.ses}, Performance: {self.performance}")
        print("=" * 60)
        
        
        
        print("\n阶段 1: 推荐材料...")
        self.process_csv_stage(
            self.output_files['pre'],
            self.output_files['rec'],
            self.process_recommendation,
            ["parent_materials", "parent_recommendation"],
            "Recommendation"
        )
        
        print("\n阶段 2: 后测试...")
        self.process_csv_stage(
            self.output_files['rec'],
            self.output_files['post'],
            self.process_post_test,
            ["parent_post_llm_answer", "parent_post_llm_confidence", "parent_post_response"],
            "Post-test"
        )
        
        print("\n" + "=" * 60)
        print("流水线完成！")
        print(f"结果文件保存在:")
        print(f"  家庭推荐材料: {self.output_files['rec']}")
        print(f"  家庭后测试: {self.output_files['post']}")

# Usage
if __name__ == "__main__":

    import pandas as pd

    # 读取 CSV 文件
    df = pd.read_csv("D:/中国科学技术大学 硕士/bdaa/task/fairagent/faircode/gpt4.1data/parent_rec.csv")  # 替换成你的实际文件路径

    # 构建字典：以 (SES, Ability) 为键，对应的 Number 和 Quality 为值
    lookup_dict = {
        (row['SES'], row['Ability']): {
            'Number': int(row['Number']),
            'Quality': row['Quality']
        }
        for _, row in df.iterrows()
    }
    # Example usage with different SES and performance combinations
    sess = ["low", "middle", "high"]
    performances = [10,20,30,40,50,60,70,80,90]

    base_path = "" # Adjust base path you create

    for ses in sess:
        for performance in performances:
            # Get number and quality from lookup_dict
            key = (ses, performance)
            if key not in lookup_dict:
                print(f"No data found for SES: {ses}, Performance: {performance}")
                continue
            number = lookup_dict[key]['Number']
            quality = lookup_dict[key]['Quality']
            print(f"Running pipeline for SES: {ses}, Performance: {performance}")
            pipeline = StudentSocialTestPipeline(ses=ses, performance=performance, number=number, quality=quality)
            pipeline.run_pipeline()
    
    # You can also run with different parameters:
    # pipeline_high = StudentTestPipeline(ses="high", performance="80")
    # pipeline_high.run_pipeline()
    
    # pipeline_medium = StudentTestPipeline(ses="medium", performance="65")
    # pipeline_medium.run_pipeline()