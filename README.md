# Paper
## Title: Beyond Parity: A Framework for Context-Aware and Equitable Outcome Evaluation of LLMs in Education

## Abstract
As Large Language Models (LLMs) are increasingly integrated into educational technology, ensuring their fairness is paramount. Traditional fairness evaluation, primarily based on statistical parity, is fundamentally inadequate for education. It aims for equality by removing sensitive attributes like socioeconomic status, yet this approach fails to account for the core principle of educational equity: providing differentiated support based on individual backgrounds to achieve common learning goals. Consequently, models passing traditional "equality-based" metrics may still produce inequitable outcomes in real-world educational environments. To address this critical gap, we propose a novel two-dimensional framework for evaluating LLM fairness in education **Contextual Fairness and Equitable Outcomes (CF-EO)**. The **Contextual Fairness** dimension evaluates whether an LLM leverages learner backgrounds to dynamically tailor pedagogical actions such as resource , while the \textbf{Equitable Outcomes} dimension assesses whether the LLM's pedagogical actions lead to fair learning results across diverse learner groups. To validate this framework, we introduce **RealEdu** (**Real**istic **Edu**cational Simulator), an LLM-powered simulator that generates diverse learner personas with unique backgrounds to model learning processes in real-world environments where learners' backgrounds may influence their outcomes. Our experiments in RealEdu reveal a critical finding: while an LLM passes traditional metrics, CF-EO systematically uncovers equity violations undetectable by parity-based methods—demonstrating that ignoring contextual adaptation reproduces inequality.  This research provides a more comprehensive and contextually-grounded approach to LLM fairness evaluation, contributing significantly to the development of more equitable and responsible AI-powered educational tools.

## Methodology
![realedu](https://github.com/user-attachments/assets/da89a29c-1848-4223-a452-585e62a3fe27)

# How to run the code
## Download dataset
You can download the dataset in https://github.com/songlinxu/ClassroomSimulacra/tree/main/dataset.
And then you can download two files —— "slide_all.json" and "test_all.json" —— to the [dataset folder](./dataset/).

## Adjust your dataset path in code
- [highslide.py](./preproecess/highslide.py) In line 4, You should set `data_path` to the folder where "slide_all.json" and "test_all.json" are stored
- [hightest.py](./preproecess/highslide.py) In line 5, You should set `data_path` to the folder where "slide_all.json" and "test_all.json" are stored
- [sch]
