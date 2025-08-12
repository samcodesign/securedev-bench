import json


def generate_markdown_report(results: list) -> str:
    header = "| Model | Task | Result | Security Score | Functionality Score | Duration (s) |\n"
    separator = "|:---|:---|:---|:---|:---|:---|\n"
    body = ""
    for res in results:
        sec_score = f"{res['security_passed']}/{res['security_total']}"
        func_score = f"{res['functionality_passed']}/{res['functionality_total']}"
        body += f"| `{res['model_id']}` | `{res['task_id']}` | **{res['result']}** | {sec_score} | {func_score} | {res['duration_seconds']} |\n"
    return header + separator + body


def save_reports(results: list, base_filename: str = "benchmark_report"):
    json_filename, md_filename = f"{base_filename}.json", f"{base_filename}.md"
    with open(json_filename, "w") as f:
        json.dump(results, f, indent=2)
    markdown_report = generate_markdown_report(results)
    with open(md_filename, "w") as f:
        f.write(markdown_report)
    print(f"\nReports saved to {md_filename} and {json_filename}")
    return markdown_report
