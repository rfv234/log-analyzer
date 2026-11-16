import os
import matplotlib

# Переключаем Matplotlib в режим генерации картинок без открытия GUI-окна
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyzer import load_and_analyze


def generate_charts(data, output_dir="results/charts"):
    # 1. Создаём папку results/charts/, если её ещё нет
    os.makedirs(output_dir, exist_ok=True)

    # --- ГРАФИК 1: Распределение событий по уровням (INFO, WARNING, ERROR) ---
    levels = data["levels"]
    categories = ["INFO", "WARNING", "ERROR"]
    values = [levels["info"], levels["warning"], levels["error"]]
    colors = ["#3b82f6", "#f59e0b", "#ef4444"]  # Синий, оранжевый, красный

    plt.figure(figsize=(7, 4.2))
    bars = plt.bar(categories, values, color=colors, width=0.5)

    plt.title("Распределение событий по уровням", fontsize=13, fontweight="bold", pad=12)
    plt.ylabel("Количество записей", fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.locator_params(axis="y", integer=True)

    # Подписываем точные числа над каждым столбцом
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    # Добавляем небольшой запас сверху, чтобы цифра над самым высоким столбцом не упиралась в рамку
    max_val = max(values) if values else 0
    plt.ylim(0, max_val * 1.18 + 1)

    levels_path = os.path.join(output_dir, "levels_distribution.png")
    plt.savefig(levels_path, dpi=150, bbox_inches="tight")
    plt.close()

    # --- ГРАФИК 2: Динамика событий и ошибок по времени ---
    timeline = data["timeline"]
    minutes = [item["minute"] for item in timeline]
    totals = [item["total"] for item in timeline]
    errors = [item["errors"] for item in timeline]

    plt.figure(figsize=(8, 4.2))

    if minutes:
        # Если точек много (> 40), убираем кружки-маркеры и делаем линию тоньше
        many_points = len(minutes) > 40
        marker_style = None if many_points else "o"
        line_w = 1.2 if many_points else 2.0

        plt.plot(
            minutes,
            totals,
            marker=marker_style,
            linestyle="--",
            color="#64748b",
            linewidth=line_w,
            label="Всего событий",
        )
        plt.plot(
            minutes,
            errors,
            marker=marker_style,
            linestyle="-",
            color="#ef4444",
            linewidth=line_w,
            label="Ошибки (ERROR)",
        )
        plt.legend(frameon=True)

        # Оставляем на оси X максимум ~12 подписей, чтобы текст не слипался
        if len(minutes) > 12:
            step = len(minutes) // 12
            plt.xticks(range(0, len(minutes), step), rotation=45)
        elif len(minutes) > 6:
            plt.xticks(rotation=45)
    else:
        plt.text(0.5, 0.5, "Нет данных по времени", ha="center", va="center", fontsize=12)

    plt.title("Активность и всплески ошибок по минутам", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Время (ЧЧ:ММ)", fontsize=10)
    plt.ylabel("Количество событий", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.locator_params(axis="y", integer=True)

    timeline_path = os.path.join(output_dir, "error_timeline.png")
    plt.savefig(timeline_path, dpi=150, bbox_inches="tight")
    plt.close()

    # Возвращаем пути относительно папки results/
    return {
        "levels_chart": "charts/levels_distribution.png",
        "timeline_chart": "charts/error_timeline.png",
    }


if __name__ == "__main__":
    analyzed_data = load_and_analyze()
    chart_paths = generate_charts(analyzed_data)
    print("[OK] Графики успешно сохранены:")
    for name, path in chart_paths.items():
        print(f" - {name}: results/{path}")