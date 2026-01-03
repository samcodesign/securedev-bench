import json

from .console import success


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
    success(f"\nReports saved to {md_filename} and {json_filename}")
    return markdown_report


def generate_console_report(results: list) -> str:
    """
    Generate a colorized and emoji-enhanced table for console output.
    """
    from colorama import Fore, Style

    def col_width(key, values, min_width):
        """Get max width for a column, given header, values, and min width."""
        return max(min_width, max((len(str(v)) for v in values), default=0), len(key))

    # Prepare all column data
    model_vals = [str(res['model_id']) for res in results]
    task_vals = [str(res['task_id']) for res in results]
    result_vals = [str(res['result']) for res in results]
    sec_vals = [f"{res['security_passed']}/{res['security_total']}" for res in results]
    func_vals = [f"{res['functionality_passed']}/{res['functionality_total']}" for res in results]
    dur_vals = [str(res['duration_seconds']) for res in results]

    # Minimum widths for each column
    min_widths = {
        'Model': 8,
        'Task': 8,
        'Result': 10,
        'Security': 8,
        'Functionality': 14,
        'Duration (s)': 12,
    }

    # Compute widths
    model_width = col_width('Model', model_vals, min_widths['Model'])
    task_width = col_width('Task', task_vals, min_widths['Task'])
    result_width = col_width('Result', result_vals, min_widths['Result']) + 2  # +2 for emoji padding
    security_width = col_width('Security', sec_vals, min_widths['Security'])
    func_width = col_width('Functionality', func_vals, min_widths['Functionality'])
    dur_width = col_width('Duration (s)', dur_vals, min_widths['Duration (s)'])

    # Header and separator
    header = (
        f"{'Model':<{model_width}} "
        f"{'Task':<{task_width}} "
        f"{'Result':<{result_width}} "
        f"{'Security':<{security_width}} "
        f"{'Functionality':<{func_width}} "
        f"{'Duration (s)':<{dur_width}}\n"
    )
    separator = (
        f"{'-'*model_width} "
        f"{'-'*task_width} "
        f"{'-'*result_width} "
        f"{'-'*security_width} "
        f"{'-'*func_width} "
        f"{'-'*dur_width}\n"
    )

    def color_result(result):
        if result == 'SUCCESS':
            return Fore.GREEN, '✅'
        elif result in ('FAILED', 'TESTS_FAILED'):
            return Fore.RED, '❌'
        else:
            return Fore.YELLOW, '⚠️'

    body = ""
    for res in results:
        sec_score = f"{res['security_passed']}/{res['security_total']}"
        func_score = f"{res['functionality_passed']}/{res['functionality_total']}"
        color, emoji = color_result(res['result'])
        result_str = f"{color}{emoji} {res['result']}{Style.RESET_ALL}"
        body += (
            f"{str(res['model_id']):<{model_width}} "
            f"{str(res['task_id']):<{task_width}} "
            f"{result_str:<{result_width}} "
            f"{sec_score:<{security_width}} "
            f"{func_score:<{func_width}} "
            f"{str(res['duration_seconds']):<{dur_width}}\n"
        )
    return header + separator + body
