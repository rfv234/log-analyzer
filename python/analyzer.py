import json
import os

def load_and_analyze(json_path="results/results.json"):
    if not os.path.exists(json_path): # проверка на существование файла, который создало C-ядро
        raise FileExistsError(f"Файл {json_path} не найден. Сначала запустите C-анализатор.")
    
    with open("results/results.json", "r", encoding="utf-8") as file: # читаем json в обычный словарь Python
        data = json.load(file)

    # проверка наличия всех полей в JSON файле
    required_keys = ['file', 'total_records', 'levels', 'error_rate', 'top_errors', 'timeline']
    for key in required_keys:
        if key not in data:
            raise KeyError(f"в JSON отсутствует обязательно поле: {key}")

    # считаем процентное соотношение для каждого уровня
    total = data["total_records"]
    levels = data["levels"]

    if total > 0:
        data["rates"] = {
            "info": round(levels["info"] / total * 100, 2),
            "warning": round(levels["warning"] / total * 100, 2),
            "error": round(levels["error"] / total * 100, 2),
        }
    else:
        data["rates"] = {"info": 0.0, "warnings": 0.0, "error": 0.0}

    # ищем минуту с наибольшим числом ошибок (пик сбоев)
    timeline = data["timeline"]
    data["peak_error"] = None

    if timeline:
        peak = max(timeline, key=lambda item: item["errors"])
        if peak["errors"] > 0:
            data["peak_error"] = {
                "minute": peak["minute"],
                "count": peak["errors"],
            }

    return data

# краткая сводка для проверки
if __name__ == "__main__":
    analyzed = load_and_analyze()
    print(f"Файл: {analyzed['file']}")
    print(f"Всего записей: {analyzed['total_records']}")
    print(f"Проценты: {analyzed['rates']}")
    print(f"Пик ошибок: {analyzed['peak_error']}")

    


