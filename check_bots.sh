#!/bin/bash

# Имя процесса, который ищет скрипт (т.е. ваш бот)
# Если ваши боты запускаются с аргументами, используйте часть команды, например "my_bot.py"
BOT_PROCESS_NAME="python"

echo "--- Начинаем проверку 16 сессий Screen ---"
echo "Ищем процесс: $BOT_PROCESS_NAME"
echo "------------------------------------------"

# Получаем список сессий screen. Извлекаем только PID и имя сессии.
# Используем grep -v "Sockets" для исключения последней строки
screen -ls | grep -oE '[0-9]+\.[a-zA-Z0-9]+' | while read SESSION_INFO; do
    # Разделяем PID и имя
    PID=$(echo "$SESSION_INFO" | cut -d'.' -f1)
    NAME=$(echo "$SESSION_INFO" | cut -d'.' -f2)

    # Проверяем дерево процессов (pstree) на наличие искомого процесса
    # Используем grep -q, чтобы просто проверить наличие и не выводить весь pstree
    if pstree -p "$PID" | grep -q "$BOT_PROCESS_NAME"; then
        echo -e "[✅ АКТИВЕН ] Сессия $NAME (PID: $PID)"
    else
        echo -e "[❌ УПАЛ! ] Сессия $NAME (PID: $PID)"
        echo "   --- Вероятно, внутри только shell. Для проверки: screen -r $NAME"
    fi
done

echo "------------------------------------------"
echo "Проверка завершена."