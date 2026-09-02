import json
import os

import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from ragas import evaluate
from ragas.metrics import RubricsScore
from ragas.llms import llm_factory

from prompts import EVALUATION_CRITERIA
from dx_sol_suggest.core.pipeline import make_agent

load_dotenv()


def build_prompt(user_input: dict) -> str:
    return f"""
    あなたはDXコンサルタントです。
    
    業界/業種:
    {user_input["department"]}
    
    状況:
    {user_input["situation"]}
    
    課題:
    {user_input["problems"]}
    
    業務量:
    {user_input["workload"]}
    
    制約:
    {user_input["constraints"]}
    
    DX提案を出力してください
    """


def call_agent(user_input: dict) -> str:
    agent = make_agent()
    response = agent.invoke(
        {"messages": [{"role": "user", "content": build_prompt(user_input)}]}
    )
    return str(response["messages"][-1].content)


if __name__ == "__main__":
    with open("eval/case.json", encoding="utf-8") as f:
        test_cases = json.load(f)

    client = AsyncOpenAI(api_key=os.getenv("OPEN_API_KEY"))

    judge_llm = llm_factory("gpt-4o", client=client)

    metrics = []

    for key, item in EVALUATION_CRITERIA.items():
        metrics.append(RubricsScore(name=key, rubrics=item["rubrics"], llm=judge_llm))

    all_results = []
    errors = 0

    for test_case in test_cases[:2]:
        try:
            question = build_prompt(test_case)
            answer = call_agent(test_case)

            eval_dataset = Dataset.from_dict(
                {
                    "user_input": [question],
                    "response": [answer],
                }
            )

            result = evaluate(eval_dataset, metrics=metrics)

            row = {
                "id": test_case["case_id"],
                "user_input": question,
                "response": answer,
            }

            for metric_name in EVALUATION_CRITERIA:
                row[metric_name] = float(result[metric_name][0])

            row["average"] = sum(row[m] for m in EVALUATION_CRITERIA) / len(
                EVALUATION_CRITERIA
            )

            all_results.append(row)
        except Exception as e:
            errors += 1
            print(f"ERROR {e}")

    df = pd.DataFrame(all_results)
    num_summary = {"n": len(df), "errors": errors}
    metrics_summary = df.drop(["id", "user_input", "response"], axis=1).mean().to_dict()

    os.makedirs("outputs", exist_ok=True)

    df.to_csv("outputs/results.csv", index=False, encoding="utf-8-sig")

    with open("outputs/results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    with open("outputs/summary.json", "w", encoding="utf-8") as f:
        json.dump(num_summary | metrics_summary, f, ensure_ascii=False, indent=2)

    score_columns = ["id", *EVALUATION_CRITERIA.keys(), "average"]
    print(df[score_columns])
    print(
        f"\nSaved {len(all_results)} results to outputs/results.csv and outputs/results.json"
    )
