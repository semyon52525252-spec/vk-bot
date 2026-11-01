import requests, time, random, json, re, os, threading

# ================== НАСТРОЙКИ ==================
TOKEN_MAIN = 'vk1.a.h6kIKn8jmVz3wQtN0HYgcHDmkE_SlKVnXI8pX4y9ALcLEpLO3z04En_o_9xydE5wit9ssxnBzHNgvVfqCtneoChTorV_wZhnOySZ8_jk9SWl-sB3A8Y9nvU0T9IcgWwl1l1Zxdo4bzRnWVsMQTtji-evHxSSSUOhrEMD00IZgXzw2xxBiyIo-19Z7nazTdQrZXyHSuTJsFF5gN0PVGxRCw'
ID_MAIN = 841914988

TOKEN_LOGGER = 'vk1.a.j5SvDCJbvcferRbSX-omtdXBwY3lfH89LNFVWV5udZD6jFTrQkKiyb8JQKoA-1eXeniOeZ12N8hVXnrDGBuTDejspok8tFwgoGC4DC_Y29w5xJ26p9xHcrxln3PDcMvFpYO2e9YgmGGbijXG1kmUJxb5R40dtA5hYIO4TwLf2vL3lDqC1o7DeLvV1oDFD8UJXPQOffegjxOc2O-tkKZFzg'
ID_LOGGER = 831745887

ID_ME = 836631906
API = 'https://api.vk.com/method/'
V = '5.199'
DATA_FILE = 'game_data.json'
lock = threading.Lock()
REPLY_MODE = True 

# ================== БАЗА ДАННЫХ ==================
game_data = {
    'users': {}, 
    'next_bot_id': 100, 
    'pending_buys': {}, 
    'history_logs': [], 
    'groups': set(), 
    'bots': [{'id': ID_MAIN, 'token': TOKEN_MAIN}],
    'dice_duels': {}
}
CURRENT_TOKEN = TOKEN_MAIN
CURRENT_ID = ID_MAIN

def save_data():
    with lock:
        try:
            d = game_data.copy()
            d['groups'] = list(game_data['groups'])
            with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=2)
        except: pass

def load_data():
    global game_data, CURRENT_TOKEN, CURRENT_ID
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                game_data.update(data)
                if 'groups' in data: game_data['groups'] = set(data['groups'])
        except: pass
    if str(ID_ME) not in game_data['users']:
        game_data['users'][str(ID_ME)] = {'bot_id': game_data['next_bot_id'], 'balance': 999999999999999, 'cash': 0, 'banned': False, 'is_dev': True, 'vip': True, 'custom_profile': '', 'god_mode': False, 'cash_to_dm': True, 'logs': False}
        game_data['next_bot_id'] += 1
    else:
        game_data['users'][str(ID_ME)]['is_dev'] = True
        game_data['users'][str(ID_ME)]['vip'] = True
    if game_data['bots']:
        CURRENT_TOKEN = game_data['bots'][0]['token']
        CURRENT_ID = game_data['bots'][0]['id']

# ================== УТИЛИТЫ ==================
def call(method, params, token=None):
    if not token: token = CURRENT_TOKEN
    params['access_token'] = token
    params['v'] = V
    return requests.get(API + method, params=params).json()

def send_bot(peer_id, text, reply_to=None, token=None):
    global REPLY_MODE
    if not token: token = CURRENT_TOKEN
    params = {'peer_id': peer_id, 'message': text, 'random_id': int(time.time() * 1000) % 2147483647}
    if REPLY_MODE and reply_to: params['reply_to'] = reply_to
    r = call('messages.send', params, token)
    return r.get('response') if 'response' in r else None

def send_dm(uid, text, token):
    try: call('messages.send', {'user_id': uid, 'message': text, 'random_id': int(time.time() * 1000) % 2147483647}, token); return True
    except: return False

def get_user_name(uid, token=None):
    if not uid: return 'Неизвестный'
    r = call('users.get', {'user_ids': uid}, token)
    if 'error' not in r and r.get('response') and len(r['response']) > 0:
        return f"{r['response'][0]['first_name']} {r['response'][0]['last_name']}"
    return f'id{uid}'

def get_mentions(text):
    return list(set(int(m) for m in re.findall(r'\[id(\d+)\|', text) + re.findall(r'@id(\d+)', text)))

def get_player_by_bot_id(bot_id_search):
    for vk_id, data in game_data['users'].items():
        if str(data.get('bot_id')).lower() == str(bot_id_search).lower(): return int(vk_id)
    return None

def parse_target(text, mid):
    ids = get_mentions(text)
    if not ids and mid:
        info = call('messages.getById', {'message_ids': mid})
        if 'error' not in info and info.get('response') and info['response'].get('items'):
            items = info['response']['items']
            if len(items) > 0 and items[0].get('reply_message'):
                target_id = items[0]['reply_message']['from_id']
                if target_id != CURRENT_ID: ids = [target_id]
    if ids: return ids[0]
    for word in re.findall(r'\b\w+\b', text):
        if word.lower() in ['себе', 'купить', 'айди', 'перевод', 'выдать', 'забрать', 'бан', 'разбан', 'профиль', 'посмотреть', 'разраб', 'обнулить', 'помощь', 'монетка', 'ракета', 'слоты', 'вип', 'кэш', 'логи', 'лс', 'изменить', 'вид', 'выигрыш', 'обычный', 'рассылка', 'poll', 'написать', 'ссылка', 'добавить', 'передать', 'бот', 'кубики', 'принять']: continue
        vk_id = get_player_by_bot_id(word)
        if vk_id: return vk_id
    return None

def get_player(uid, create=False):
    uid_str = str(uid)
    if uid_str not in game_data['users']:
        if not create: return None
        game_data['users'][uid_str] = {'bot_id': game_data['next_bot_id'], 'balance': 500, 'cash': 0, 'banned': False, 'is_dev': False, 'vip': False, 'cash_to_dm': True, 'logs': False, 'custom_profile': '', 'god_mode': False}
        game_data['next_bot_id'] += 1; save_data()
    return game_data['users'][uid_str]

def format_profile(target_id):
    tp = get_player(target_id)
    if not tp: return '👤 Пользователь не зарегистрирован.'
    if tp.get('custom_profile'):
        prof = tp['custom_profile'].replace('{ник}', get_user_name(target_id)).replace('{баланс}', str(tp['balance'])).replace('{кэш}', str(tp['cash'])).replace('{id_бот}', str(tp['bot_id'])).replace('{id_вк}', str(target_id))
        return prof.replace('\\n', '\n')
    marks = "👺РАЗРАБОТЧИК👺 " if tp.get('is_dev') else ""
    marks += "👑ПРЕМИУМ👑" if tp.get('vip') else ""
    if marks: marks = f"{marks}\n"
    return f'{marks}👤 {get_user_name(target_id)}\n🆔 ID в боте: {tp["bot_id"]}\n💰 Баланс: {tp["balance"]}\n💵 Кэш: {tp["cash"]}'

def add_log(uid, game_name, mult, bet, win):
    p = get_player(uid, create=True)
    if p.get('is_dev'): return 
    game_data['history_logs'].insert(0, {'name': get_user_name(uid), 'game': game_name, 'mult': mult, 'bet': bet, 'win': win})
    game_data['history_logs'] = game_data['history_logs'][:20]; save_data()

def send_log_to_devs(text):
    devs = [int(u) for u, d in game_data['users'].items() if d.get('is_dev')]
    for dev in devs:
        send_dm(dev, text, TOKEN_LOGGER)

def play_rocket(peer, uid, bet_str, mult, mid):
    p = get_player(uid)
    if not p: return send_bot(peer, '❌ Напиши "начать".', reply_to=mid)
    try: bet = p['balance'] if bet_str.lower() in ['ва-банк', 'максимум'] else int(bet_str)
    except: return send_bot(peer, '❌ Ошибка. Пример: ракета 1.5 100', reply_to=mid)
    if bet <= 0 or bet > p['balance']: return send_bot(peer, f'❌ Баланс: {p["balance"]}', reply_to=mid)
    if mult < 1.1 or mult > 100: return send_bot(peer, '❌ Коэф. от 1.1 до 100.', reply_to=mid)
    god = p.get('god_mode', False); r = random.random()
    if god or r < 0.01: crash = 100.0
    else: crash = round(1.0 + 99 * (random.random() ** 5), 2)
    if crash >= mult or god:
        win = int(bet * mult); p['balance'] += win
        send_bot(peer, f'🚀 Краш {crash}\nВыигрыш: +{win}\n💰 {p["balance"]}', reply_to=mid)
        if mult >= 10: send_log_to_devs(f'🔥 Лог: Ракета {mult}x\nВыигрыш: {win}\nИгрок: {get_user_name(uid)}')
    else:
        p['balance'] -= bet; k = 0.10 if p.get('vip') else 0.01
        p['cash'] += int(bet * k) or 1
        send_bot(peer, f'💥 Краш {crash}\nПроигрыш: -{bet}\n💰 {p["balance"]}', reply_to=mid)
    save_data()

def play_slots(peer, uid, bet_str, mid):
    p = get_player(uid)
    if not p: return send_bot(peer, '❌ Напиши "начать".', reply_to=mid)
    try: bet = p['balance'] if bet_str.lower() in ['ва-банк', 'максимум'] else int(bet_str)
    except: return send_bot(peer, '❌ Ошибка. Пример: слоты 100', reply_to=mid)
    if bet <= 0 or bet > p['balance']: return send_bot(peer, f'❌ Баланс: {p["balance"]}', reply_to=mid)
    sym = ['🍒', '🍋', '🍇', '💎', '7️⃣']; res = [random.choice(sym) for _ in range(3)]; res_str = "".join(res)
    god = p.get('god_mode', False); roll = random.random()
    if roll < 0.05 or god:
        win = bet * 3; p['balance'] += (win - bet)
        send_bot(peer, f'Ставка сыграла!\nСтавка ×3\n{res_str}\n💰 Баланс: {p["balance"]}', reply_to=mid)
        send_log_to_devs(f'🔥 Лог: Слоты x3\nВыигрыш: {win}\nИгрок: {get_user_name(uid)}')
    elif roll < 0.25:
        win = bet * 2; p['balance'] += (win - bet)
        send_bot(peer, f'Ставка сыграла!\nСтавка ×2\n{res_str}\n💰 Баланс: {p["balance"]}', reply_to=mid)
    else:
        p['balance'] -= bet; k = 0.10 if p.get('vip') else 0.01
        p['cash'] += int(bet * k) or 1
        send_bot(peer, f'Ставка не сыграла.\nСтавка ×0\n{res_str}\n💰 Баланс: {p["balance"]}', reply_to=mid)
    save_data()

def play_coin(peer, uid, choice, bet_str, mid):
    p = get_player(uid)
    if not p: return send_bot(peer, '❌ Напиши "начать".', reply_to=mid)
    choice = choice.replace('ё', 'е')
    if choice not in ['орел', 'решка']: return send_bot(peer, '🪙 Выбери сторону: монетка орел 100', reply_to=mid)
    try: bet = p['balance'] if bet_str.lower() in ['максимум', 'вб'] else int(bet_str)
    except: return send_bot(peer, '🪙 Укажи сумму.', reply_to=mid)
    if bet <= 0 or bet > p['balance']: return send_bot(peer, f'❌ Баланс: {p["balance"]}', reply_to=mid)
    god = p.get('god_mode', False); roll = random.choice(['орел', 'решка'])
    if roll == choice or god:
        p['balance'] += bet
        send_bot(peer, f'🪙 Выпал {roll.upper()}!\n🎉 Выигрыш: +{bet}\n💰 {p["balance"]}', reply_to=mid)
    else:
        p['balance'] -= bet
        send_bot(peer, f'🪙 Выпал {roll.upper()}!\n💸 Проигрыш: -{bet}\n💰 {p["balance"]}', reply_to=mid)
    save_data()
# ================== ОБРАБОТКА КОМАНД ==================
def handle_command(text, peer_id, from_id, mid):
    global REPLY_MODE, CURRENT_TOKEN, CURRENT_ID
    low = text.lower().strip(); is_dm = (peer_id == from_id); p = get_player(from_id)
    
    if not is_dm: game_data['groups'].add(peer_id); save_data()
    if p and p.get('banned'): return 

    # === ПОМОЩЬ ===
    if low in ['команды', 'помощь']:
        return send_bot(peer_id, '📋 **Команды (для всех):**\nначать, профиль, посмотреть, баланс, снять кэш, передать 100 @юзер\n🎮 ракета 1.5 100, слоты 100, монетка орел 100, кубики 100 @юзер\n🎲 принять кубики, купить айди, подтвердить', reply_to=mid)

    if low in ['команды разработчика', 'помощь разработчика']:
        if not p or (not p.get('is_dev') and from_id != ID_ME): return send_bot(peer_id, '⛔ Нет прав.', reply_to=mid)
        return send_bot(peer_id, '👨‍💻 **Команды разработчика:**\nвыдать @юзер 100\nзабрать @юзер 100\nдать @юзер 100\nвыдать вип @юзер\n/бан @юзер, /разбан @юзер, /кто в бане\n/айди себе <новый_ID>\n/разрабы', reply_to=mid)

    if low in ['команды создателя', 'помощь создателя']:
        if from_id != ID_ME: return send_bot(peer_id, '⛔ Только для создателя.', reply_to=mid)
        return send_bot(peer_id, '👑 **Команды создателя:**\n+бот <токен>, боты, /переключить бота <номер>\n/выигрыш, /рассылка <текст>, /poll\n/написать <peer_id/@юзер> <текст>, /ссылка <peer_id>, /добавить <@юзер>\n/разраб @юзер, /забрать разраба @юзер, /обнулить @юзер\n/replay, /unreplay', reply_to=mid)

    # === КОМАНДЫ СОЗДАТЕЛЯ ===
    if from_id == ID_ME:
        if low.startswith('+бот '):
            new_token = text[5:].strip()
            r = call('users.get', {}, token=new_token)
            if 'error' not in r and r.get('response'):
                new_id = r['response'][0]['id']
                if not any(b['id'] == new_id for b in game_data['bots']):
                    game_data['bots'].append({'id': new_id, 'token': new_token}); save_data()
                    return send_bot(peer_id, f'✅ Бот {get_user_name(new_id)} добавлен!', reply_to=mid)
            return send_bot(peer_id, '❌ Ошибка токена.', reply_to=mid)
            
        if low in ['боты', '/боты']:
            text_out = '🤖 **Список ботов:**\n'
            for i, b in enumerate(game_data['bots']):
                active = " (Активный)" if b['id'] == CURRENT_ID else ""
                text_out += f'{i+1}. {get_user_name(b["id"])}{active}\n'
            return send_bot(peer_id, text_out, reply_to=mid)
            
        if low.startswith('/переключить бота '):
            try:
                num = int(text.split()[-1]) - 1
                if 0 <= num < len(game_data['bots']):
                    CURRENT_ID = game_data['bots'][num]['id']; CURRENT_TOKEN = game_data['bots'][num]['token']
                    return send_bot(peer_id, f'✅ Переключено на {get_user_name(CURRENT_ID)}.', reply_to=mid)
            except: pass
            return send_bot(peer_id, '❌ Неверный номер.', reply_to=mid)

        if low.startswith('/рассылка '):
            msg_text = text[10:].strip(); count = 0
            for uid_str in game_data['users'].keys():
                if int(uid_str) == CURRENT_ID: continue
                if send_dm(int(uid_str), msg_text, TOKEN_LOGGER): count += 1
            for g_id in list(game_data['groups']):
                try: call('messages.send', {'peer_id': g_id, 'message': msg_text, 'random_id': int(time.time() * 1000) % 2147483647}); count += 1
                except: pass
            return send_bot(peer_id, f'✅ Рассылка завершена. Отправлено: {count}', reply_to=mid)

        if low in ['/poll', '.poll']:
            u_list = list(game_data['users'].keys()); g_list = list(game_data['groups'])
            out = f'📊 Юзеры ({len(u_list)}):\n' + '\n'.join([f'id{u}' for u in u_list[:20]]) + f'\n\n💬 Беседы ({len(g_list)}):\n' + '\n'.join([str(g) for g in g_list[:20]])
            return send_bot(peer_id, out, reply_to=mid)

        if low.startswith('/написать '):
            parts = text[10:].strip().split(maxsplit=1)
            if len(parts) < 2: return send_bot(peer_id, 'Формат: /написать <peer_id или @юзер> <текст>', reply_to=mid)
            target_raw = parts[0]; msg_text = parts[1]; target_peer = None
            mentions = get_mentions(target_raw)
            if mentions: target_peer = mentions[0] 
            elif target_raw.isdigit(): target_peer = int(target_raw)
            if target_peer:
                try: call('messages.send', {'peer_id': target_peer, 'message': msg_text, 'random_id': int(time.time() * 1000) % 2147483647}); return send_bot(peer_id, f'✅ Отправлено в {target_peer}', reply_to=mid)
                except: return send_bot(peer_id, '❌ Ошибка.', reply_to=mid)

        if low.startswith('/ссылка '):
            try:
                cid = int(text.split()[-1]) - 2000000000
                return send_bot(peer_id, f'🔗 https://vk.me/join/{cid}', reply_to=mid)
            except: return send_bot(peer_id, 'Формат: /ссылка 2000000000', reply_to=mid)

        if low.startswith('/добавить '):
            return send_bot(peer_id, '⚠️ Бот не может добавлять. Кидай ссылку: /ссылка <id>', reply_to=mid)

        if low.startswith('/разраб '):
            target = parse_target(text, mid)
            if target: 
                get_player(target, True)['is_dev'] = True; save_data()
                send_dm(target, '👨‍💻 Вас назначили разработчиком в этом боте!', TOKEN_LOGGER)
            return send_bot(peer_id, f'✅ {get_user_name(target)} теперь Разработчик!', reply_to=mid)

        if low.startswith('/забрать разраба'):
            target = parse_target(text, mid)
            if target: 
                tp = get_player(target)
                if tp: tp['is_dev'] = False; save_data()
            return send_bot(peer_id, f'✅ Права забраны.', reply_to=mid)

        if low.startswith('/обнулить'):
            target = parse_target(text, mid)
            if target:
                tp = get_player(target, True)
                tp['balance'] = 500; tp['cash'] = 0; tp['banned'] = False; save_data()
            return send_bot(peer_id, f'✅ Аккаунт обнулен.', reply_to=mid)

        if low in ['/unreplay', '.unreplay']:
            REPLY_MODE = False; return send_bot(peer_id, '✅ Реплаи ВЫКЛ.', reply_to=mid)
        if low in ['/replay', '.replay']:
            REPLY_MODE = True; return send_bot(peer_id, '✅ Реплаи ВКЛ.', reply_to=mid)

    # === ИГРА КУБИКИ ===
    if low.startswith('кубики'):
        parts = text.split()
        if len(parts) == 1: return send_bot(peer_id, '🎲 кубики 100 @юзер', reply_to=mid)
        bet = 0
        for part in parts[1:]:
            if part.lower() in ['ва-банк', 'максимум']: bet = 0; break
            if part.isdigit(): bet = int(part); break
        target = parse_target(text, mid)
        if not target: return send_bot(peer_id, 'Укажи @юзер.', reply_to=mid)
        
        p_host = get_player(from_id)
        if not p_host: return send_bot(peer_id, '❌ Напиши "начать".', reply_to=mid)
        if bet <= 0 or bet > p_host['balance']: bet = p_host['balance']
        if bet <= 0: return send_bot(peer_id, '❌ Нет монет.', reply_to=mid)
        
        game_data['dice_duels'][str(peer_id)] = {'host': from_id, 'target': target, 'bet': bet}
        save_data()
        return send_bot(peer_id, f'🎲 {get_user_name(from_id)} вызывает {get_user_name(target)} на "Кубики" на {bet} монет!\nНапишите "принять кубики".', reply_to=mid)

    if low.startswith('принять кубики'):
        duel = game_data['dice_duels'].get(str(peer_id))
        if not duel: return send_bot(peer_id, 'Нет активных вызовов.', reply_to=mid)
        host_id = int(duel['host']); target_id = int(duel['target']); bet = int(duel['bet'])
        if from_id != target_id and from_id != host_id: return send_bot(peer_id, 'Этот вызов не для тебя.', reply_to=mid)
        if host_id == target_id: return send_bot(peer_id, 'Нельзя играть сам с собой.', reply_to=mid)
        
        p_host = get_player(host_id); p_accept = get_player(target_id)
        if p_accept['balance'] < bet: return send_bot(peer_id, f'❌ У {get_user_name(target_id)} мало монет.', reply_to=mid)
            
        r_h = random.randint(1, 6); r_a = random.randint(1, 6)
        text_out = (f'🎲 Кубики:\n{get_user_name(host_id)}: {r_h}\n{get_user_name(target_id)}: {r_a}\n\n')
        if r_h > r_a:
            p_host['balance'] += bet; p_accept['balance'] -= bet
            text_out += f'🏆 Победил {get_user_name(host_id)}!'
        elif r_a > r_h:
            p_accept['balance'] += bet; p_host['balance'] -= bet
            text_out += f'🏆 Победил {get_user_name(target_id)}!'
        else: text_out += '🤝 Ничья!'
            
        del game_data['dice_duels'][str(peer_id)]; save_data()
        return send_bot(peer_id, text_out, reply_to=mid)

    # === ПЕРЕВОДЫ С ЛОГАМИ ===
    if low.startswith('передать '):
        if not p: return send_bot(peer_id, '❌ Напиши "начать".', reply_to=mid)
        amount = next((int(x) for x in re.findall(r'\b\d+\b', text) if not get_player_by_bot_id(x)), 0)
        target = parse_target(text, mid)
        if not target or amount <= 0: return send_bot(peer_id, 'Формат: передать 100 @юзер', reply_to=mid)
        if from_id != ID_ME and target != from_id: return send_bot(peer_id, '⛔ Только себе.', reply_to=mid)
        if p['balance'] < amount: return send_bot(peer_id, '❌ Мало монет.', reply_to=mid)
        
        p['balance'] -= amount; tp = get_player(target, True); tp['balance'] += amount; save_data()
        send_dm(target, f'💸 {get_user_name(from_id)} передал вам {amount} монет!', TOKEN_MAIN)
        
        log_text = f'#перевод\n👤 {get_user_name(from_id)} перевел {get_user_name(target)} {amount} монет!'
        game_data['history_logs'].append(log_text)
        send_log_to_devs(log_text)
        save_data()
        return send_bot(peer_id, f'✅ Передано {amount} {get_user_name(target)}.', reply_to=mid)

    # === ВЫДАЧА И ЗАБРАТЬ ===
    if low.startswith(('выдать', '/выдать', 'дать', '/дать', 'забрать', '/забрать')):
        if not p or not p.get('is_dev'): return send_bot(peer_id, '⛔ Нет прав.', reply_to=mid)
        is_main = (from_id == ID_ME)
        if 'вип' in low:
            target = from_id if 'себе' in low else parse_target(text, mid)
            if not target: return send_bot(peer_id, 'Укажи юзера.', reply_to=mid)
            if not is_main and target != from_id: return send_bot(peer_id, '⛔ Только себе.', reply_to=mid)
            tp = get_player(target, True); tp['vip'] = True; save_data()
            return send_bot(peer_id, f'👑 {get_user_name(target)} ПРЕМИУМ!', reply_to=mid)
        is_take = low.startswith('забрать') or low.startswith('/забрать')
        amount = next((int(x) for x in re.findall(r'\b\d+\b', text) if not get_player_by_bot_id(x)), 0)
        target = from_id if 'себе' in low else parse_target(text, mid)
        if not target: return send_bot(peer_id, 'Укажи юзера.', reply_to=mid)
        if not is_main and target != from_id: return send_bot(peer_id, '⛔ Только себе.', reply_to=mid)
        if amount <= 0: return send_bot(peer_id, 'Укажи сумму.', reply_to=mid)
        tp = get_player(target, create=True); tp['balance'] += (-amount if is_take else amount); save_data()
        return send_bot(peer_id, f'✅ {"Забрано" if is_take else "Выдано"} {amount} у {get_user_name(target)}', reply_to=mid)

    # === МОДЕРАЦИЯ ===
    if low.startswith('/бан'):
        if not p or not p.get('is_dev'): return send_bot(peer_id, '⛔ Нет прав.', reply_to=mid)
        target = parse_target(text, mid)
        if target: get_player(target, True)['banned'] = True; save_data()
        return send_bot(peer_id, f'🚫 Забанен.', reply_to=mid)

    if low.startswith('/разбан'):
        if not p or not p.get('is_dev'): return send_bot(peer_id, '⛔ Нет прав.', reply_to=mid)
        target = parse_target(text, mid)
        if target: 
            tp = get_player(target)
            if tp: tp['banned'] = False; save_data()
        return send_bot(peer_id, f'✅ Разбанен.', reply_to=mid)

    if low in ['/кто в бане', 'кто в бане']:
        banned = [get_user_name(int(u)) for u, d in game_data['users'].items() if d.get('banned')]
        return send_bot(peer_id, '🚫 В бане: ' + (', '.join(banned) if banned else 'никого'), reply_to=mid)

    # === ПОКУПКА И СМЕНА ID ===
    if low.startswith('/айди себе') or low.startswith('.айди себе'):
        if not p or not p.get('is_dev'): return send_bot(peer_id, '⛔ Нет прав.', reply_to=mid)
        parts = text.split(maxsplit=2)
        if len(parts) < 3: return send_bot(peer_id, 'Формат: /айди себе <новый_ID>', reply_to=mid)
        p['bot_id'] = parts[2].strip(); save_data()
        return send_bot(peer_id, f'✅ ID изменен на: {p["bot_id"]}', reply_to=mid)

    if low.startswith('купить айди'):
        if not p: return send_bot(peer_id, '❌ Напиши "начать".', reply_to=mid)
        rand_id = str(random.randint(100000, 999999))
        if random.random() < 0.1: rand_id = random.choice(['777777', '123456', '111111', '999999'])
        game_data['pending_buys'][str(from_id)] = rand_id; save_data()
        return send_bot(peer_id, f'🎲 Выпал ID: {rand_id}\n💰 Цена: 5000\nНапиши "подтвердить".', reply_to=mid)

    if low == 'подтвердить' or low == '/подтвердить':
        pending = game_data['pending_buys'].get(str(from_id))
        if not pending: return send_bot(peer_id, 'Нет активных покупок.', reply_to=mid)
        if p['balance'] < 5000: return send_bot(peer_id, '❌ Мало монет.', reply_to=mid)
        p['balance'] -= 5000; p['bot_id'] = pending
        del game_data['pending_buys'][str(from_id)]; save_data()
        return send_bot(peer_id, f'✅ Куплен ID: {pending}!', reply_to=mid)

    # === ПРОФИЛЬ И БАЗА ===
    if low in ['начать', '/начать']:
        if p: return send_bot(peer_id, f'✅ Твой ID: {p["bot_id"]}', reply_to=mid)
        tp = get_player(from_id, create=True)
        return send_bot(peer_id, f'✅ Успешно!\nID: {tp["bot_id"]}', reply_to=mid)
        
    if low in ['мой профиль', 'профиль']: return send_bot(peer_id, format_profile(from_id), reply_to=mid)
    if low.startswith('посмотреть'):
        target = parse_target(text, mid) or from_id
        return send_bot(peer_id, format_profile(target), reply_to=mid)
        
    if low in ['баланс', '.баланс']:
        if not p: return send_bot(peer_id, '❌ Нет аккаунта.', reply_to=mid)
        return send_bot(peer_id, f'💰 Баланс: {p["balance"]}', reply_to=mid)
        
    if low in ['снять кэш', '/снять кэш']:
        if not p or p['cash'] <= 0: return send_bot(peer_id, '❌ Нет кэша.', reply_to=mid)
        amount = p['cash']; p['balance'] += amount; p['cash'] = 0; save_data()
        return send_bot(peer_id, f'💵 Кэш снят: +{amount}\n💰 {p["balance"]}', reply_to=mid)

    if low in ['/логи', '.логи']:
        logs = game_data.get('history_logs', [])
        if not logs: return send_bot(peer_id, '📭 Логов нет.', reply_to=mid)
        return send_bot(peer_id, '🏆 Логи переводов:\n' + '\n'.join(logs[-10:]), reply_to=mid)

    if low in ['/разрабы', 'разрабы']:
        devs = [get_user_name(int(u)) for u, d in game_data['users'].items() if d.get('is_dev')]
        return send_bot(peer_id, '👨‍💻 Разрабы:\n' + '\n'.join([f'- {d}' for d in devs]), reply_to=mid)

    # === VIP КОМАНДЫ ===
    if low in ['/выигрыш', '.выигрыш']:
        if from_id != ID_ME: return
        p['god_mode'] = not p.get('god_mode', False); save_data()
        return send_bot(peer_id, f'👑 100% выигрыш {"ВКЛ" if p["god_mode"] else "ВЫКЛ"}!', reply_to=mid)

    if p and p.get('vip'):
        if low in ['/отключить переводы', '.отключить переводы']:
            p['cash_to_dm'] = False; save_data(); return send_bot(peer_id, '✅ Уведомления ВЫКЛ.', reply_to=mid)
        if low in ['/включить логи', '.включить логи']:
            p['logs'] = True; save_data(); return send_bot(peer_id, '✅ Логи ВКЛ.', reply_to=mid)
        if low.startswith('/изменить профиль'):
            match = re.search(r'(?:/изменить профиль|\.изменить профиль)\s*(.*)', text, re.IGNORECASE | re.DOTALL)
            if match:
                new_prof = match.group(1).strip()
                if not new_prof:
                    p['custom_profile'] = ''; save_data()
                    return send_bot(peer_id, '✅ Профиль сброшен.', reply_to=mid)
                p['custom_profile'] = new_prof; save_data()
                return send_bot(peer_id, f'✅ Профиль обновлен!', reply_to=mid)

# ================== ЗАПУСК БОТА ==================
def longpoll_bot():
    lp = call('messages.getLongPollServer', {'lp_version': 3})
    if 'error' in lp: return print('❌ Ошибка LongPoll:', lp['error'])
    server, key, ts = lp['response']['server'], lp['response']['key'], lp['response']['ts']
    print(f'✅ Бот {get_user_name(CURRENT_ID)} запущен.')
    while True:
        url = f'https://{server}?act=a_check&key={key}&ts={ts}&wait=25&mode=2&version=3'
        try: data = requests.get(url, timeout=30).json()
        except: time.sleep(5); continue
        if 'failed' in data:
            lp = call('messages.getLongPollServer', {'lp_version': 3})
            if 'error' not in lp: server, key, ts = lp['response']['server'], lp['response']['key'], lp['response']['ts']
            continue
        ts = data.get('ts', ts)
        for upd in data.get('updates', []):
            if upd[0] != 4: continue
            mid, peer_id = upd[1], upd[3]
            info = call('messages.getById', {'message_ids': mid})
            if 'error' not in info and info.get('response') and info['response'].get('items'):
                msg = info['response']['items'][0]
                if msg['from_id'] != CURRENT_ID: 
                    try: handle_command(msg.get('text', '').strip(), peer_id, msg['from_id'], mid)
                    except Exception as e: print("Ошибка:", e)

if __name__ == '__main__':
    load_data()
    longpoll_bot()