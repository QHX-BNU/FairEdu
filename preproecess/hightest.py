import json
import csv
import re

data_path = ""# Adjust base path you create for dataset
# 原始 JSON 文件路径
input_file = data_path + "test_all.json"

# 新的 JSON 文件路径
output_file = data_path + "high_school_test_only.json"

# 读取原始 JSON 文件
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取 high school 项的内容
high_school_data = data.get("high school", {})

# 将提取的内容写入新的 JSON 文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(high_school_data, f, indent=4, ensure_ascii=False)

print(f"已将 high school 内容保存到 {output_file}")

# 读取 JSON 文件
with open(output_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 写入 CSV 文件
with open(data_path + "high_school_test_only.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["lecture", "question", "contents", "slide", "correct_answer"])

    for lecture_key, questions in data.items():
        # 提取 lecture 编号中的数字
        lecture_number = re.findall(r'\d+', lecture_key)
        lecture_number = lecture_number[0] if lecture_number else lecture_key

        for question_key, qinfo in questions.items():
            # 提取问题编号数字
            question_number = re.findall(r'\d+', question_key)
            question_number = question_number[0] if question_number else question_key

            contents = qinfo.get("contents", "")
            slide = qinfo.get("slide", "")
            correct_answer = qinfo.get("correct_answer", "")
            writer.writerow([lecture_number, question_number, contents, slide, correct_answer])