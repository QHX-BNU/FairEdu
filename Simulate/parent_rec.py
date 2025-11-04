from llm_respond import LLM

parent_agent = LLM(model="gpt-4.1-mini",temperature=0, max_tokens=512)

def get_parent(ses,ability):
    return """
        You are the parent of a high school student who is taking an artificial intelligence test.
        Your family's socioeconomic status (SES) is: {ses}
        Your child's academic performance in AI is represented by an accuracy score of {ability}%:

        0% means all answers are incorrect

        100% means all answers are correct

        Based on your SES and your child's performance, decide:

        How many learning resources (e.g., courses, tutoring, software, books) you are willing and able to provide to support your child's learning.

        The overall quality level of those resources (choose from: low, medium, or high)

        Respond in the exact format below. Do not include anything else.

        Response format (must follow this structure):
        <explanation> Your explanation here. </explanation>  
        <number> A single integer between 0 and 5. </number>  
        <quality> low / medium / high </quality>

        Examples:
        <explanation> Because my SES is high and my child's ability is 10%, I can afford more and want to support improvement. </explanation>  
        <number> 10 </number>  
        <quality> high </quality>
    """.format(ses=ses, ability=ability)

import re
import pandas as pd

ses = ['low', 'middle', 'high']
ability = [10, 20, 30, 40, 50, 60, 70, 80, 90]

data = []

for s in ses:
    for a in ability:
        profile = get_parent(s, a)
        message = [{"role": "user", "content": profile}]
        response = parent_agent.chat(message)

        # 提取 explanation, number, quality
        match = re.search(
            r'<explanation>(.*?)</explanation>.*?<number>(.*?)</number>.*?<quality>(.*?)</quality>',
            response,
            flags=re.DOTALL
        )

        if match:
            explanation, number, quality = match.groups()
        else:
            explanation, number, quality = "", "", ""

        data.append({
            "SES": s,
            "Ability": a,
            "response": response,
            "Explanation": explanation.strip(),
            "Number": number.strip(),
            "Quality": quality.strip()
        })

# 保存到 CSV 文件
df = pd.DataFrame(data)
df.to_csv("D:/中国科学技术大学 硕士/bdaa/task/fairagent/faircode/gpt4.1data/parent_rec.csv", index=False, encoding='utf-8-sig')