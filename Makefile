CC = gcc
CFLAGS = -Wall -Wextra -O2

TARGET = c_engine/log_analyzer
SRC = c_engine/main.c
LOG ?= data/server.log

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

run: $(TARGET)
	./$(TARGET) $(LOG)
	.venv/bin/python python/report.py

clean:
	rm -f $(TARGET) results/results.json results/report.html results/charts/*.png