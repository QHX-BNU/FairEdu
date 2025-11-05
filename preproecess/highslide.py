import json

# 原始 JSON 文件路径
data_path = ""# Adjust base path you create for dataset

input_file = data_path + "slide_all.json"

# 新的 JSON 文件路径
output_file = data_path + "high_school_slide_only.json"

# 读取原始 JSON 文件
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取 high school 项的内容
high_school_data = data.get("high school", {})

# 将提取的内容写入新的 JSON 文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(high_school_data, f, indent=4, ensure_ascii=False)

print(f"已将 high school 内容保存到 {output_file}")
