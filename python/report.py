import base64
import html
import os
from datetime import datetime

from analyzer import load_and_analyze
from vizualization import generate_charts


def encode_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        encoded_bytes = base64.b64encode(img_file.read())
        encoded_str = encoded_bytes.decode("utf-8")
        return f"data:image/png;base64,{encoded_str}"


def build_html_report(data, chart_paths, output_path="results/report.html"):
    results_dir = os.path.dirname(output_path)
    os.makedirs(results_dir, exist_ok=True)

    levels = data["levels"]
    rates = data["rates"]
    peak = data["peak_error"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Кодируем оба графика в Base64, чтобы отчёт был полностью автономным
    levels_full_path = os.path.join(results_dir, chart_paths["levels_chart"])
    timeline_full_path = os.path.join(results_dir, chart_paths["timeline_chart"])

    levels_b64 = encode_image_base64(levels_full_path)
    timeline_b64 = encode_image_base64(timeline_full_path)

    # Формируем строку с пиком ошибок
    if peak:
        peak_text = f"{html.escape(peak['minute'])} ({peak['count']} шт.)"
    else:
        peak_text = "Ошибок не зафиксировано"

    # Генерируем строки таблицы для самых частых ошибок
    top_errors = data["top_errors"]
    if top_errors:
        rows_html = ""
        for idx, err in enumerate(top_errors, start=1):
            safe_msg = html.escape(err["message"])
            rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td><code>{safe_msg}</code></td>
                <td><strong>{err['count']}</strong></td>
            </tr>
            """
    else:
        rows_html = """
        <tr>
            <td colspan="3" style="text-align: center; color: #64748b;">Ошибок в логе не обнаружено</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчёт анализа логов — {html.escape(data['file'])}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            margin: 0;
            padding: 32px;
        }}
        .container {{
            max-width: 1050px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid #1e293b;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        h1 {{
            margin: 0 0 8px 0;
            font-size: 26px;
            color: #f8fafc;
        }}
        .meta {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 16px;
        }}
        .card-title {{
            font-size: 13px;
            color: #94a3b8;
            margin-bottom: 6px;
        }}
        .card-value {{
            font-size: 24px;
            font-weight: 700;
        }}
        .info {{ color: #3b82f6; }}
        .warn {{ color: #f59e0b; }}
        .err {{ color: #ef4444; }}
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
            gap: 20px;
            margin-bottom: 28px;
        }}
        .chart-box {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
        }}
        .chart-box img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #1e293b;
            border-radius: 10px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #334155;
        }}
        th {{
            background: #0f172a;
            color: #94a3b8;
            font-size: 13px;
            text-transform: uppercase;
        }}
        code {{
            background: #0f172a;
            padding: 3px 6px;
            border-radius: 4px;
            color: #fca5a5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Отчёт анализа лог-файла</h1>
            <div class="meta">
                Файл: <strong>{html.escape(data['file'])}</strong> • Сформировано: {generated_at}
            </div>
        </header>

        <section class="cards">
            <div class="card">
                <div class="card-title">Всего записей</div>
                <div class="card-value">{data['total_records']}</div>
            </div>
            <div class="card">
                <div class="card-title">INFO</div>
                <div class="card-value info">{levels['info']} ({rates['info']}%)</div>
            </div>
            <div class="card">
                <div class="card-title">WARNING</div>
                <div class="card-value warn">{levels['warning']} ({rates['warning']}%)</div>
            </div>
            <div class="card">
                <div class="card-title">ERROR</div>
                <div class="card-value err">{levels['error']} ({rates['error']}%)</div>
            </div>
            <div class="card">
                <div class="card-title">Пик ошибок</div>
                <div class="card-value" style="font-size: 18px; padding-top: 4px;">{peak_text}</div>
            </div>
        </section>

        <section class="charts">
            <div class="chart-box">
                <img src="{levels_b64}" alt="Распределение уровней">
            </div>
            <div class="chart-box">
                <img src="{timeline_b64}" alt="Хронология ошибок">
            </div>
        </section>

        <section>
            <h2>Самые частые ошибки</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px;">#</th>
                        <th>Сообщение об ошибке</th>
                        <th style="width: 120px;">Повторений</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </section>
    </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    return output_path


if __name__ == "__main__":
    analyzed_data = load_and_analyze()
    charts = generate_charts(analyzed_data)
    report_file = build_html_report(analyzed_data, charts)
    print(f"[OK] Автономный отчёт готов: {report_file}")