import time
import json
import threading
from pynput import keyboard

tally = {}
seconds_typed = 0.0
session_start = 0.0
last_keystroke = 0.0
lock = threading.Lock()

def load_tally():
    global tally, seconds_typed
    try:
        with open('tally.json', 'r') as f:
            data = json.load(f)
            raw_tally = data.get('keys', {})
            
            tally = {}
            for k, v in raw_tally.items():
                new_k = k
                if new_k.startswith('Key.'):
                    new_k = new_k.replace('Key.', '')
                    if new_k.endswith('_l') or new_k.endswith('_r'):
                        new_k = new_k[:-2]
                tally[new_k] = tally.get(new_k, 0) + v
                
            seconds_typed = data.get('seconds_typed', 0.0)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

def save_tally():
    with lock:
        current_session = 0.0
        if session_start > 0:
            current_session = (last_keystroke - session_start)
        
        sorted_tally = dict(sorted(tally.items()))
        
        with open('tally.json', 'w') as f:
            json.dump({"keys": sorted_tally, "seconds_typed": seconds_typed + current_session}, f, indent=4)

def periodic_save():
    while True:
        time.sleep(10)
        save_tally()

def on_press(key):
    global session_start, last_keystroke, seconds_typed
    
    if hasattr(key, 'char') and key.char:
        k = key.char
    elif hasattr(key, 'name') and key.name:
        k = key.name
        if k.endswith('_r') or k.endswith('_l'):
            k = k[:-2]
    else:
        k = str(key).replace('Key.', '')
        
    now = time.time()
    
    with lock:
        if last_keystroke == 0.0:
            session_start = now
        elif now - last_keystroke > 300:
            seconds_typed += (last_keystroke - session_start)
            session_start = now
            
        last_keystroke = now
        tally[k] = tally.get(k, 0) + 1

load_tally()
threading.Thread(target=periodic_save, daemon=True).start()

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()