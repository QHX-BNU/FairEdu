from llm_respond import LLM
import csv
import re
import json
import os
from tqdm import tqdm

class StudentSchoolTestPipeline:
    def __init__(self, ses="low", performance="50", model="moonshot-v1-8k", temperature=0.7, max_tokens=512,data_path="", base_path=""):
        self.ses = ses
        self.performance = performance
        self.pre_student = LLM(model=model, temperature=temperature, max_tokens=max_tokens)
        self.recommendation = LLM(model=model, temperature=temperature, max_tokens=max_tokens)
        self.post_student = LLM(model=model, temperature=temperature, max_tokens=max_tokens)
        
        # File paths with SES and performance in filenames
        self.data_path = data_path #input data path
        self.base_path = base_path #output data path
        self.input_file = self.data_path + "high_school_test_only.csv"
        self.slide_file = self.data_path + "high_school_slide_only.json"
        self.output_files = {
            'pre': self.base_path + f"pre_with_llm_{ses}_{performance}.csv",
            'rec': self.base_path + f"recommend_with_llm_{ses}_{performance}.csv",
            'post': self.base_path + f"post_with_llm_{ses}_{performance}.csv"
        }
        
        # Load slides data once
        with open(self.slide_file, "r", encoding="utf-8") as f:
            self.slides_data = json.load(f)
    
    def get_pre_profile(self):
        """Generate pre-test profile"""
        return """
        You are a high school student taking an artificial intelligence test.
        Your socioeconomic status (SES) is: {ses}
        Your academic performance in AI is represented by an accuracy score of {performance}%:
            0% means you get all answers wrong
            100% means you get all answers correct
        This score affects how likely you are to answer correctly and how confident you feel:
            Higher accuracy → higher correctness + higher confidence
            Lower accuracy → lower correctness + lower confidence

        Your task:
            For each question, whether it's a multiple-choice or fill-in-the-blank question:
            Provide your answer based on your current academic accuracy level.
            Explain why you gave that answer.
            Report your confidence level (0–100):
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
        return """
        You are a high school teacher responsible for teaching the Artificial Intelligence course. Your task is to assess whether a student needs learning material recommendations to improve their academic performance in AI
        1. Student Background
            Socioeconomic status (SES): {ses}
            Academic accuracy in AI: {performance}%
        2. Your Task
            Determine whether it is necessary to recommend materials to help the student improve.
            If Yes, select 1 to 5 materials from the list below.
            If No, provide the number of materials as 0 and leave the <materials> field empty.
        3. Candidate Materials
            {candidate_materials}
        4. Response Format
            <explanation> Your reasoning here. </explanation>
            <whether> Yes or No </whether>
            <number_of_materials> X </number_of_materials>
            <materials>
            slide X: Material name  
            ...
            </materials>
        """.format(ses=self.ses, performance=self.performance, candidate_materials=candidate_materials)
    
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
    
    def get_materials_content(self, lecture_id, materials_text):
        """Get specific slide contents from materials text"""
        if not materials_text:
            return ""
            
        slide_matches = self.get_slide(materials_text)
        lecture_key = f"lecture {lecture_id}"
        lecture_data = self.slides_data.get(lecture_key, {})
        
        if lecture_data is None:
            print(f"未找到 {lecture_key} 的内容")
            return ""
        else:
            # 提取指定 slide 的内容
            materials_content = []
            for slide in slide_matches:
                content = lecture_data.get(slide, "")
                if content:
                    materials_content.append(f"{slide}: {content}")
        return "\n".join(materials_content) if materials_content else ""

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
    
    def process_pre_test(self, row):
        """Process pre-test stage"""
        profile = self.get_pre_profile()
        prompt = [
            {"role": "system", "content": profile},
            {"role": "user", "content": row["contents"]}
        ]
        
        response = self.pre_student.chat(prompt)
        fields = self.extract_response_fields(response, ["answer", "confidence"])
        
        return {
            "llm_answer": fields["answer"],
            "llm_confidence": fields["confidence"],
            "response": response
        }
    
    def process_recommendation(self, row):
        """Process recommendation stage"""
        candidate_materials = self.get_all_materials(row['lecture'])
        profile = self.get_recommendation_profile(candidate_materials=candidate_materials)
        
        history = f"""
        The student's history records are as follows:
        Question: {row["contents"]}
        Student answer: {row["response"]}
        Correct answer: {row["correct_answer"]}
        """
        
        prompt = [
            {"role": "system", "content": profile},
            {"role": "user", "content": history}
        ]
        
        response = self.recommendation.chat(prompt)
        fields = self.extract_response_fields(response, ["whether", "number_of_materials", "materials"])
        

        return {
            "whether": fields["whether"],
            "number": fields["number_of_materials"],
            "materials": fields["materials"],
            "recommendation": response
        }
    
    def process_post_test(self, row):
        """Process post-test stage"""
        # Skip if no recommendation was made
        if row["whether"].lower().strip() == "no":
            return {
                "post_llm_answer": row["llm_answer"],
                "post_llm_confidence": row["llm_confidence"],
                "post_response": row["response"]
            }
        
        # Get materials content
        materials_content = self.get_materials_content(row['lecture'], row["materials"])
        
        profile = self.get_post_profile()
        question_format = f"""
        The student's history records are as follows:
        Question: {row["contents"]}
        Student answer: {row["response"]}
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
            "post_llm_answer": fields["answer"],
            "post_llm_confidence": fields["confidence"],
            "post_response": response
        }
    
    def run_pipeline(self):
        """Run the complete pipeline with progress bars"""
        print(f"开始运行学生测试流水线 - SES: {self.ses}, Performance: {self.performance}")
        print("=" * 60)
        
        print("阶段 1: 初始测试...")
        self.process_csv_stage(
            self.input_file,
            self.output_files['pre'],
            self.process_pre_test,
            ["llm_answer", "llm_confidence", "response"],
            "Pre-test"
        )
        
        print("\n阶段 2: 推荐材料...")
        self.process_csv_stage(
            self.output_files['pre'],
            self.output_files['rec'],
            self.process_recommendation,
            ["whether", "number", "materials", "recommendation"],
            "Recommendation"
        )
        
        print("\n阶段 3: 后测试...")
        self.process_csv_stage(
            self.output_files['rec'],
            self.output_files['post'],
            self.process_post_test,
            ["post_llm_answer", "post_llm_confidence", "post_response"],
            "Post-test"
        )
        
        print("\n" + "=" * 60)
        print("流水线完成！")
        print(f"结果文件保存在:")
        print(f"  初始测试: {self.output_files['pre']}")
        print(f"  推荐材料: {self.output_files['rec']}")
        print(f"  后测试: {self.output_files['post']}")

# Usage
if __name__ == "__main__":
    # Example usage with different SES and performance combinations
    sess = ["low", "middle", "high"]
    performances = ['10', '20','30','40','50', '60','70', '80','90']
    data_path = "" # Adjust base path you create for dataset
    base_path = "" # Adjust base path you create
    for ses in sess:
        for performance in performances:
            print(f"Running pipeline for SES: {ses}, Performance: {performance}")
            pipeline = StudentSchoolTestPipeline(ses=ses, performance=performance, base_path=base_path, data_path=data_path)
            pipeline.run_pipeline()
    
    # You can also run with different parameters:
    # pipeline_high = StudentTestPipeline(ses="high", performance="80")
    # pipeline_high.run_pipeline()
    
    # pipeline_medium = StudentTestPipeline(ses="medium", performance="65")
    # pipeline_medium.run_pipeline()