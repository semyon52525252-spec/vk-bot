import os

FILE_PATH = '/storage/emulated/0/Download/BOT_SEMYON_LP.py'

# Что ищем и на что меняем (чтобы починить отступы)
FIXES = {
    "    if low.startswith('ракета'):\n        parts = text.split()\n        if len(parts) >= 3: play_rocket(peer_id, from_id, parts[2], float(parts[1]), mid)\n        return":
    "    if low.startswith('ракета'):\n        parts = text.split()\n        if len(parts) >= 3: play_rocket(peer_id, from_id, parts[2], float(parts[1]), mid)\n        return",
    
    "    if low.startswith('слоты'):\n        parts = text.split()\n        if len(parts) >= 2: play_slots(peer_id, from_id, parts[1], mid)\n        return":
    "    if low.startswith('слоты'):\n        parts = text.split()\n        if len(parts) >= 2: play_slots(peer_id, from_id, parts[1], mid)\n        return",
    
    "    if low.startswith('монетка'):\n        parts = text.split()\n        if len(parts) >= 3: play_coin(peer_id, from_id, parts[1], parts[2], mid)\n        return":
    "    if low.startswith('монетка'):\n        parts = text.split()\n        if len(parts) >= 3: play_coin(peer_id, from_id, parts[1], parts[2], mid)\n        return"
}

if not os.path.exists(FILE_PATH):
    print(f"❌ Файл {FILE_PATH} не найден!")
else:
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        code = f.read()

    fixed_count = 0
    # Ищем кривые отступы (например, если перед if стоят лишние пробелы, 
    # или наоборот их нет там, где надо)
    # Для простоты мы просто проверим, есть ли правильные блоки, 
    # и если нет — принудительно вставим их в конец функции handle_command.
    
    # Но проще: просто перезапишем файл с правильными блоками
    if "if low.startswith('ракета'):" not in code:
        print("⚠️ Блок ракеты не найден. Возможно, файл уже поврежден.")
    else:
        # Заменяем все возможные варианты отступов на правильный
        code = code.replace("    if low.startswith('ракета'):", "    if low.startswith('ракета'):")
        code = code.replace("if low.startswith('ракета'):", "    if low.startswith('ракета'):")
        
        code = code.replace("    if low.startswith('слоты'):", "    if low.startswith('слоты'):")
        code = code.replace("if low.startswith('слоты'):", "    if low.startswith('слоты'):")
        
        code = code.replace("    if low.startswith('монетка'):", "    if low.startswith('монетка'):")
        code = code.replace("if low.startswith('монетка'):", "    if low.startswith('монетка'):")

        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(code)
        print("✅ Отступы исправлены!")

print("\nТеперь запусти скрипт-курьер для GitHub (тот, что с токеном), и потом нажми 'Пересобрать' на Bothost.")