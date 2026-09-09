import json
import os

import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset
from openai import AsyncOpenAI
from ragas import evaluate, RunConfig
from ragas.metrics import AspectCritic, RubricsScore
from ragas.llms import llm_factory

from enums import parse_case_enums
from prompts import EVALUATION_CRITERIA, build_proper_behavior_definition
from dx_sol_suggest.core.pipeline import make_agent

load_dotenv()


def build_structured_prompt(user_input: dict) -> str:
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


def call_agent(content: str) -> str:
    agent = make_agent()
    response = agent.invoke({"messages": [{"role": "user", "content": content}]})
    return str(response["messages"][-1].content)


if __name__ == "__main__":
    with open("eval/test_case.json", encoding="utf-8") as f:
        test_cases = [parse_case_enums(case) for case in json.load(f)]

    client = AsyncOpenAI(api_key=os.getenv("OPEN_API_KEY"))

    judge_llm = llm_factory("gpt-4o", client=client)

    # 全ケース共通の観点は、ループの外で一度だけ構築する
    common_metrics = [
        RubricsScore(name=key, rubrics=item["rubrics"], llm=judge_llm)
        for key, item in EVALUATION_CRITERIA.items()
    ]

    all_results = []
    errors = 0

    for test_case in test_cases[:10]:
        try:
            answer = call_agent(test_case["user_message"])

            eval_dataset = Dataset.from_dict(
                {
                    "user_input": [test_case["user_message"]],
                    "response": [answer],
                }
            )

            # description がケースごとに異なる観点は、ここで都度構築する
            case_metrics = [
                *common_metrics,
                AspectCritic(
                    name="proper_behavior",
                    definition=build_proper_behavior_definition(test_case),
                    llm=judge_llm,
                ),
            ]

            # NOTE: rate_limit_exceeded回避のため並列処理を無効化
            result = evaluate(
                eval_dataset, metrics=case_metrics, run_config=RunConfig(max_workers=1)
            )

            row = {
                "id": test_case["case_id"],
                "user_input": test_case["user_message"],
                "response": answer,
            }

            for metric_name in EVALUATION_CRITERIA:
                row[metric_name] = float(result[metric_name][0])

            row["proper_behavior"] = float(result["proper_behavior"][0])

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

    suffix = "10_trial_prompt_enj"

    df.to_csv(f"outputs/results_{suffix}.csv", index=False, encoding="utf-8-sig")

    with open(f"outputs/results_{suffix}.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    with open(f"outputs/summary_{suffix}.json", "w", encoding="utf-8") as f:
        json.dump(num_summary | metrics_summary, f, ensure_ascii=False, indent=2)

    score_columns = ["id", *EVALUATION_CRITERIA.keys(), "proper_behavior", "average"]
    print(df[score_columns])
    print(
        f"\nSaved {len(all_results)} results to outputs/results.csv and outputs/results.json"
    )
