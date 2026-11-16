#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>

typedef struct
{
    int total;
    int info;
    int warning;
    int error;
    int unknown;
    double error_rate;
} LogStats;

typedef struct
{
    char message[256];
    int count;
} ErrorEntry;

typedef struct
{
    char minute[6];
    int total;
    int errors;
} TimeBucket;

void sort_error(ErrorEntry errors[], int count) // sort errors: little->many
{
    for (int i = 0; i < count - 1; i++)
    {
        for (int j = 0; j < count - i - 1; j++)
        {
            if (errors[j].count < errors[j + 1].count)
            {
                ErrorEntry tmp = errors[j];
                errors[j] = errors[j + 1];
                errors[j + 1] = tmp;
            }
        }
    }
}

void add_error(ErrorEntry **errors, int *count, int *capacity, const char *message) // Find most popular errors
{
    // 1. Ищем дубликат среди уже записанных ошибок
    for (int i = 0; i < *count; i++)
    {
        if (strcmp((*errors)[i].message, message) == 0)
        {
            (*errors)[i].count++;
            return;
        }
    }

    // 2. Если выделенная память закончилась — увеличиваем вместимость в 2 раза
    if (*count >= *capacity)
    {
        int new_cap = (*capacity == 0) ? 8 : (*capacity * 2);
        ErrorEntry *tmp = realloc(*errors, new_cap * sizeof(ErrorEntry));
        if (tmp == NULL)
        {
            perror("Memory allocation failed for errors");
            return;
        }
        *errors = tmp;
        *capacity = new_cap;
    }

    // 3. Добавляем новую уникальную ошибку
    strcpy((*errors)[*count].message, message);
    (*errors)[*count].count = 1;
    (*count)++;
}

void add_timeline(TimeBucket **timeline, int *timeline_count, int *timeline_capacity, const char *minute, int is_error) // check active for minutes
{
    // 1. Проверяем, есть ли уже такая минута в массиве
    for (int i = 0; i < *timeline_count; i++)
    {
        if (strcmp((*timeline)[i].minute, minute) == 0)
        {
            if (is_error == 1)
            {
                (*timeline)[i].errors++;
            }
            (*timeline)[i].total++;
            return;
        }
    }

    // 2. Если место в динамическом массиве закончилось — расширяем в 2 раза через realloc
    if (*timeline_count >= *timeline_capacity)
    {
        int new_cap = (*timeline_capacity == 0) ? 16 : (*timeline_capacity * 2);
        TimeBucket *tmp = realloc(*timeline, new_cap * sizeof(TimeBucket));
        if (tmp == NULL)
        {
            perror("Memory allocation failed for timeline");
            return;
        }
        *timeline = tmp;
        *timeline_capacity = new_cap;
    }

    // 3. Записываем новую минуту
    strcpy((*timeline)[*timeline_count].minute, minute);
    (*timeline)[*timeline_count].total = 1;
    (*timeline)[*timeline_count].errors = is_error;
    (*timeline_count)++;
}

void print_json_escaped(FILE *out, const char *str) // write string symbol to symbol for json
{
    for (int i = 0; str[i] != '\0'; i++)
    {
        if (str[i] == '"' || str[i] == '\\')
        {
            fprintf(out, "\\%c", str[i]);
        }
        else
        {
            fprintf(out, "%c", str[i]);
        }
    }
}

int export_to_json(const char *output_path, const char *log_file, LogStats stats, ErrorEntry errors[], int unique_count, TimeBucket timeline[], int timeline_count)
{
    mkdir("results", 0755); // Создаём папку results автоматически, если её ещё нет

    FILE *out = fopen(output_path, "w");
    if (out == NULL)
    {
        perror("Error creating JSON file");
        return 1;
    }

    fprintf(out, "{\n");

    // 1. Имя проанализированного файла
    fprintf(out, "  \"file\": \"");
    print_json_escaped(out, log_file);
    fprintf(out, "\",\n");

    // 2. Общая статистика и уровни событий
    fprintf(out, "  \"total_records\": %d,\n", stats.total);
    fprintf(out, "  \"levels\": {\n");
    fprintf(out, "    \"info\": %d,\n", stats.info);
    fprintf(out, "    \"warning\": %d,\n", stats.warning);
    fprintf(out, "    \"error\": %d,\n", stats.error);
    fprintf(out, "    \"unknown\": %d\n", stats.unknown);
    fprintf(out, "  },\n");
    fprintf(out, "  \"error_rate\": %.2f,\n", stats.error_rate);

    // 3. Массив самых частых ошибок (топ-10)
    fprintf(out, "  \"top_errors\": [\n");
    int top_limit = unique_count < 10 ? unique_count : 10;
    for (int i = 0; i < top_limit; i++)
    {
        fprintf(out, "    {\"message\": \"");
        print_json_escaped(out, errors[i].message);
        fprintf(out, "\", \"count\": %d}", errors[i].count);

        if (i < top_limit - 1)
        {
            fprintf(out, ",");
        }
        fprintf(out, "\n");
    }
    fprintf(out, "  ],\n");

    // 4. Поминутная хронология событий
    fprintf(out, "  \"timeline\": [\n");
    for (int i = 0; i < timeline_count; i++)
    {
        fprintf(out, "    {\"minute\": \"%s\", \"total\": %d, \"errors\": %d}",
                timeline[i].minute, timeline[i].total, timeline[i].errors);

        if (i < timeline_count - 1)
        {
            fprintf(out, ",");
        }
        fprintf(out, "\n");
    }
    fprintf(out, "  ]\n");

    fprintf(out, "}\n");
    fclose(out);
    return 0;
}

int main(int argc, char *argv[])
{
    LogStats stats = {0};

    // Указатели на динамические массивы
    ErrorEntry *unique_errors = NULL;
    TimeBucket *timeline = NULL;

    int unique_count = 0;
    int unique_capacity = 0;
    int timeline_count = 0;
    int timeline_capacity = 0;

    if (argc < 2) // check file`s path
    {
        printf("Usage: %s <path_to_log>\n", argv[0]);
        return 1;
    }

    FILE *file = fopen(argv[1], "r");
    if (file == NULL)
    {
        perror("Error opening file");
        return 1;
    }

    char buffer[1024];
    char message[256];
    char date[16];
    char time[16];
    char level[16];
    while (fgets(buffer, sizeof(buffer), file) != NULL) // calculate and check strings
    {
        stats.total++;
        int fields = sscanf(buffer, "%15s %15s %15s %255[^\n]", date, time, level, message);
        if (fields != 4)
        {
            stats.unknown++;
            continue;
        }

        char minute[6];
        strncpy(minute, time, 5);
        minute[5] = '\0';

        if (strcmp(level, "INFO") == 0)
        {
            stats.info++;
            add_timeline(&timeline, &timeline_count, &timeline_capacity, minute, 0);
        }
        else if (strcmp(level, "WARNING") == 0)
        {
            stats.warning++;
            add_timeline(&timeline, &timeline_count, &timeline_capacity, minute, 0);
        }
        else if (strcmp(level, "ERROR") == 0)
        {
            stats.error++;
            add_error(&unique_errors, &unique_count, &unique_capacity, message);
            add_timeline(&timeline, &timeline_count, &timeline_capacity, minute, 1);
        }
        else
        {
            stats.unknown++;
        }
    }

    if (stats.total > 0)
    {
        stats.error_rate = (double)stats.error / stats.total * 100.0;
    }

    fclose(file);

    sort_error(unique_errors, unique_count);

    printf("Total lines: %d\n", stats.total);
    printf("INFO: %d, WARNINGS: %d, ERRORS: %d, UNKNOWN: %d\n", stats.info, stats.warning, stats.error, stats.unknown);
    printf("Error rate: %.1f%%\n", stats.error_rate);

    if (unique_count > 0)
    {
        printf("Most frequent errors:\n");
        for (int i = 0; i < unique_count && i < 5; i++)
        {
            printf("%d. %s (%d)\n", i + 1, unique_errors[i].message, unique_errors[i].count);
        }
    }

    if (timeline_count > 0)
    {
        printf("Timeline:\n");
        for (int i = 0; i < timeline_count; i++)
        {
            printf("%s -> total: %d, errors: %d\n", timeline[i].minute, timeline[i].total, timeline[i].errors);
        }
    }

    if (export_to_json("results/results.json", argv[1], stats, unique_errors, unique_count, timeline, timeline_count) == 0)
    {
        printf("\n[OK] Results exported to results/results.json\n");
    }

    // Освобождаем выделенную динамическую память
    free(unique_errors);
    free(timeline);

    return 0;
}