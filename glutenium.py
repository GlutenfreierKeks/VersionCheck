# --- Imports ---
import minescript
import customtkinter as ctk
import threading
import time
import math
import json
import os
import keyboard
from pynput import mouse
import tkinter as tk


CONFIG_FILE = "mc_tools_config.json"

# === Config ===
config = {
    "aim_enabled": False,
    "crystal_enabled": False,
    "auto_totem_enabled": False,
    "auto_anchor_enabled": False,
    "double_anchor_enabled": False,
    "triggerbot_enabled": False,
    "staff_detector_enabled": False,

    "staff_list": [],

    # Cooldowns
    "aim_cooldown": 0.03,
    "crystal_cooldown": 0.05,
    "auto_totem_cooldown": 0.1,
    "auto_anchor_cooldown": 0.05,
    "double_anchor_cooldown": 0.05,
    "triggerbot_cooldown": 0.4,

    # Keybinds (none = "")
    "keybinds": {
    "aim": "",
    "crystal": "",
    "auto_totem": "",
    "auto_anchor": "",
    "double_anchor": "",
    "triggerbot": "",
    "staff_detector": ""
    },


    # GUI key
    "gui_key": "",


    # Extra options
    "chat_feedback": False,
    "toggle_sound": False,


    # Double anchor trigger key default
    "double_anchor_key": "shift",
}

# --- Neue Config-Option ---
def update_anchor_trigger(choice):
    config["anchor_trigger"] = choice.lower()
    save_config()


# === Globale Variablen ===
right_click_held = False
anchor_action_pending = False
double_anchor_action_pending = False
sword_slot_before_anchor = None
last_totem_pop_time = 0
manual_slot_change = False
last_checked_slot = None
last_trigger_attack = 0

# === Config Handling ===
def load_config():
    global config
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"[!] Fehler beim Laden der Config: {e}")

def save_config():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[!] Fehler beim Speichern der Config: {e}")


def disable_all_modules():
    for key in ["aim_enabled", "crystal_enabled", "auto_totem_enabled", "auto_anchor_enabled", "double_anchor_enabled", "triggerbot_enabled"]:
        config[key] = False
    save_config()

def disable_all_modules():
    for key in [
        "aim_enabled",
        "crystal_enabled",
        "auto_totem_enabled",
        "auto_anchor_enabled",
        "double_anchor_enabled",
        "triggerbot_enabled",
        "staff_detector_enabled"
    ]:
        config[key] = False
    save_config()

    # GUI Buttons aktualisieren
    try:
        aim_btn.configure(text="Start Aim Assist")
        crystal_btn.configure(text="Start Crystal Place")
        auto_totem_btn.configure(text="Start Auto Totem")
        auto_anchor_btn.configure(text="Start Auto Anchor")
        double_anchor_btn.configure(text="Start Double Anchor")
        triggerbot_btn.configure(text="Start Trigger Bot")
        staff_btn.configure(text="Start Staff Detector")
    except Exception as e:
        print(f"[!] Error while changing buttons: {e}")

# === Staff Detector ===
def staff_detector_loop():
    while True:
        if config.get("staff_detector_enabled", False):
            try:
                for p in minescript.players():  # Spieler in Render Distance
                    name = getattr(p, "name", "").lower()
                    if name in [s.lower() for s in config.get("staff_list", [])]:
                        # Staff entdeckt – sofort alle Module aus
                        print(f"[!!!] Staff in Render Distance: {name} – EVERY MODULE OFF!")
                        disable_all_modules()
                        time.sleep(5)  # kurz warten, um Spam zu verhindern
            except Exception as e:
                print(f"[!] ERROR WITH STAFF DETECTOR: {e}")
        time.sleep(1.0)

# === Helfer ===
def get_selected_hotbar_slot():
    inventory = minescript.player_inventory()
    for itemstack in inventory:
        if getattr(itemstack, "selected", False):
            return getattr(itemstack, "slot", 0)
    return 0

def find_item_in_hotbar(keywords):
    inventory = minescript.player_inventory()
    for itemstack in inventory:
        slot = getattr(itemstack, "slot", -1)
        item_name = getattr(itemstack, "item", "").lower()
        if 0 <= slot <= 8:
            for keyword in keywords:
                if keyword in item_name:
                    return slot
    return None

def find_totem_in_hotbar():
    for item in minescript.player_inventory():
        if 0 <= getattr(item, "slot", -1) <= 8 and "totem" in getattr(item, "item", "").lower():
            return item.slot
    return None

def has_totem_in_offhand():
    for item in minescript.player_inventory():
        if getattr(item, "slot", -1) == 40 and "totem" in getattr(item, "item", "").lower():
            return True
    return False

def has_totem_in_mainhand():
    hand = getattr(minescript.player_hand_items(), "main_hand", None)
    return hand and "totem" in getattr(hand, "item", "").lower()

def get_health():
    player = minescript.player()
    return getattr(player, "health", 20), getattr(player, "absorption", 0)

def put_totem_in_offhand():
    if has_totem_in_offhand():
        return
    totem_slot = find_totem_in_hotbar()
    if totem_slot is None:
        return
    original_slot = get_selected_hotbar_slot()
    minescript.player_inventory_select_slot(totem_slot)
    start_time = time.time()
    while not has_totem_in_offhand() and time.time() - start_time < 0.5:
        minescript.player_press_swap_hands(True)
        time.sleep(0.05)
        minescript.player_press_swap_hands(False)
        time.sleep(0.05)
    minescript.player_inventory_select_slot(original_slot)

def put_totem_in_mainhand():
    global last_totem_pop_time
    if has_totem_in_mainhand():
        return
    hotbar_slot = find_totem_in_hotbar()
    if hotbar_slot is not None:
        minescript.player_inventory_select_slot(hotbar_slot)
        last_totem_pop_time = time.time()
        time.sleep(0.05)

# === Aim Assist ===
def calculate_yaw_pitch(src, dst):
    dx, dy, dz = dst[0]-src[0], dst[1]-src[1], dst[2]-src[2]
    yaw = math.degrees(math.atan2(-dx, dz)) % 360
    distance = math.sqrt(dx**2 + dz**2)
    pitch = -math.degrees(math.atan2(dy-1, distance))
    return yaw, pitch

def aim_assist_loop():
    while True:
        if config["aim_enabled"]:
            player = minescript.player()
            target = minescript.player_get_targeted_entity(max_distance=50)
            if target:
                yaw, pitch = calculate_yaw_pitch(player.position, target.position)
                minescript.player_set_orientation(yaw, pitch)
        time.sleep(config.get("aim_cooldown", 0.03))

# === Crystal Place ===
def has_crystal_in_hand():
    hands = minescript.player_hand_items()
    return any(hand_item and "crystal" in getattr(hand_item, "item", "").lower() for hand_item in [hands.main_hand, hands.off_hand])

def crystal_place_loop():
    while True:
        if config["crystal_enabled"] and right_click_held and has_crystal_in_hand():
            minescript.player_press_use(True)
            minescript.player_press_use(False)
            minescript.player_press_attack(True)
            minescript.player_press_attack(False)
            minescript.player_press_use(True)
            minescript.player_press_use(False)
        time.sleep(config.get("crystal_cooldown", 0.05))

# === Auto Totem (inkl. Double-Hand) ===
def auto_totem_loop():
    global last_totem_pop_time, manual_slot_change, last_checked_slot
    while True:
        if not config["auto_totem_enabled"]:
            time.sleep(0.05)
            continue

        health, absorption = get_health()
        current_slot = get_selected_hotbar_slot()
        if last_checked_slot is not None and current_slot != last_checked_slot:
            manual_slot_change = True
        last_checked_slot = current_slot

        # Offhand priorisieren
        if not has_totem_in_offhand():
            put_totem_in_offhand()

        # Mainhand bei low HP oder kurz nach Totem-Pop
        if not manual_slot_change and (health + absorption <= 6 or time.time() - last_totem_pop_time < 1):
            put_totem_in_mainhand()

        if has_totem_in_mainhand() and has_totem_in_offhand():
            manual_slot_change = False

        time.sleep(config.get("auto_totem_cooldown", 0.1))

# === Trigger Bot ===
def triggerbot_loop():
    global last_trigger_attack
    while True:
        if config.get("triggerbot_enabled", False):
            target = minescript.player_get_targeted_entity(max_distance=4.5)  # normale Hit-Range
            if target:
                now = time.time()
                if now - last_trigger_attack >= config.get("triggerbot_cooldown", 0.4):
                    minescript.player_press_attack(True)
                    minescript.player_press_attack(False)
                    last_trigger_attack = now
        time.sleep(0.01)

# === Auto Anchor / Double Anchor ===
def has_sword_in_mainhand():
    hand = getattr(minescript.player_hand_items(), "main_hand", None)
    return hand and "sword" in getattr(hand, "item", "").lower()

def on_anchor_click(x, y, button, pressed):
    global anchor_action_pending, sword_slot_before_anchor
    if button == mouse.Button.right and pressed and config["auto_anchor_enabled"]:
        if has_sword_in_mainhand():
            sword_slot_before_anchor = get_selected_hotbar_slot()
            anchor_action_pending = True

# --- Globale Variable ---
sword_slot_before_anchor = None

# --- Maus Listener ---
def on_right_click(x, y, button, pressed):
    global right_click_held, anchor_action_pending, double_anchor_action_pending, sword_slot_before_anchor
    if button != mouse.Button.right:
        return

    right_click_held = pressed
    if not pressed:
        return

    trigger = config.get("anchor_trigger", "sword")  # kann "sword" oder "respawn anchor" sein
    hand_item = getattr(minescript.player_hand_items(), "main_hand", None)
    hand_name = getattr(hand_item, "item", "").lower() if hand_item else ""

    if right_click_held:
        if trigger == "sword" and "sword" in hand_name:
            sword_slot_before_anchor = get_selected_hotbar_slot()
            anchor_action_pending = True
        elif trigger == "respawn anchor" and "respawn_anchor" in hand_name:
            sword_slot_before_anchor = get_selected_hotbar_slot()
            anchor_action_pending = True

    trigger_key = config.get("double_anchor_key", "shift")

    # --- Auto Anchor ---
    if config["auto_anchor_enabled"]:
        if config.get("anchor_trigger", "sword") == "sword" and "sword" in hand_name:
            sword_slot_before_anchor = get_selected_hotbar_slot()
            anchor_action_pending = True
        elif config.get("anchor_trigger", "anchor") == "anchor" and "respawn_anchor" in hand_name:
            sword_slot_before_anchor = get_selected_hotbar_slot()
            anchor_action_pending = True

    # --- Double Anchor ---
    if config.get("double_anchor_enabled", False) and keyboard.is_pressed(trigger_key):
        if config.get("anchor_trigger", "sword") == "sword" and "sword" in hand_name:
            sword_slot_before_anchor = get_selected_hotbar_slot()
            double_anchor_action_pending = True
        elif config.get("anchor_trigger", "anchor") == "anchor" and "respawn_anchor" in hand_name:
            sword_slot_before_anchor = get_selected_hotbar_slot()
            anchor_action_pending = True

mouse.Listener(on_click=on_right_click).start()

# --- Auto Anchor Loop ---
def auto_anchor_loop():
    global anchor_action_pending, sword_slot_before_anchor
    while True:
        if anchor_action_pending:
            anchor_action_pending = False

            anchor_slot = find_item_in_hotbar(["respawn_anchor"])
            glow_slot = find_item_in_hotbar(["glowstone"])
            totem_slot = find_item_in_hotbar(["totem"])

            if anchor_slot is not None:
                minescript.player_inventory_select_slot(anchor_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.05)

            if glow_slot is not None:
                minescript.player_inventory_select_slot(glow_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.05)

            if totem_slot is not None:
                minescript.player_inventory_select_slot(totem_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.05)

            if sword_slot_before_anchor is not None:
                minescript.player_inventory_select_slot(sword_slot_before_anchor)
        time.sleep(config.get("auto_anchor_cooldown", 0.05))

# --- Double Anchor Loop ---
def double_anchor_loop():
    global double_anchor_action_pending, sword_slot_before_anchor
    while True:
        if double_anchor_action_pending:
            double_anchor_action_pending = False

            anchor_slot = find_item_in_hotbar(["respawn_anchor"])
            glow_slot = find_item_in_hotbar(["glowstone"])
            totem_slot = find_item_in_hotbar(["totem"])

            # Platzieren Anchor + Glowstone + Totem + zurück
            if anchor_slot:
                minescript.player_inventory_select_slot(anchor_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.025)
            if glow_slot:
                minescript.player_inventory_select_slot(glow_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.025)
            if anchor_slot:
                minescript.player_inventory_select_slot(anchor_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.025)
            if glow_slot:
                minescript.player_inventory_select_slot(glow_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.025)
            if totem_slot:
                minescript.player_inventory_select_slot(totem_slot)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                time.sleep(0.025)
            if sword_slot_before_anchor is not None:
                minescript.player_inventory_select_slot(sword_slot_before_anchor)

        time.sleep(config.get("double_anchor_cooldown", 0.05))


def update_double_anchor_key(choice):
    config["double_anchor_key"] = choice
    save_config()

def find_item_slot_in_hotbar(keywords):
    for item in minescript.player_inventory():
        if 0 <= getattr(item, "slot", -1) <= 8:
            item_name = getattr(item, "item", "").lower()
            if any(keyword in item_name for keyword in keywords):
                return item.slot
    return None

def on_double_anchor_click(x, y, button, pressed):
    global double_anchor_action_pending, sword_slot_before_anchor
    if button == mouse.Button.right and pressed and config.get("double_anchor_enabled", False):
        trigger_key = config.get("double_anchor_key", "shift")
        if has_sword_in_mainhand() and keyboard.is_pressed(trigger_key):
            sword_slot_before_anchor = get_selected_hotbar_slot()
            double_anchor_action_pending = True

# === GUI ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
app = ctk.CTk()
app.geometry("680x760")
app.title("Glutenium")

# ----------------------------
# Fancy glowing loading screen
# ----------------------------
def show_loading_screen(duration_ms: int = 800, title: str = "Glutenium"):
    """
    Non-blocking glowing loading overlay.
    duration_ms: wie lange das Overlay angezeigt wird (ms)
    """
    overlay = tk.Toplevel(app)
    overlay.overrideredirect(True)  # kein Fensterrahmen
    overlay.attributes("-topmost", True)

    # Position & Größe passend zum Hauptfenster
    app.update_idletasks()
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    overlay.geometry(f"{w}x{h}+{x}+{y}")

    # Hintergrund-Frame mit leichtem Pulsieren
    bg = tk.Frame(overlay, bg="#0f1724")
    bg.place(relwidth=1, relheight=1)

    # Container für Labels und Fortschritt
    container = tk.Frame(bg, bg="#0f1724")
    container.place(relx=0.5, rely=0.5, anchor="center")

    # Titel-Label mit animiertem Glow
    title_label = tk.Label(container, text=title, font=("Segoe UI", 32, "bold"), fg="#9be7ff", bg="#0f1724")
    title_label.pack(pady=(0, 8))

    # Untertitel + animierte Punkte
    sub_label_text = tk.StringVar(value="Loading")
    sub_label = tk.Label(container, textvariable=sub_label_text, font=("Segoe UI", 14), fg="#cfefff", bg="#0f1724")
    sub_label.pack()

    # Fortschrittsleiste
    bar_frame = tk.Frame(container, bg="#12202a", height=8)
    bar_frame.pack(pady=(12, 0), fill="x", padx=20)
    bar_fill = tk.Frame(bar_frame, bg="#2dd4bf", width=1, height=8)
    bar_fill.place(x=0, y=0)

    start_time = time.time()
    dot_state = [0]
    glow_state = [0]
    direction = [1]

    def animate():
        elapsed = (time.time() - start_time) * 1000
        frac = min(1.0, elapsed / max(1, duration_ms))

        # Fortschrittsleiste
        total_w = bar_frame.winfo_width() or (w - 40)
        fill_w = max(2, int(total_w * frac))
        bar_fill.configure(width=fill_w)

        # Animierte Punkte
        dot_state[0] = (dot_state[0] + 1) % 60
        dots = (dot_state[0] // 15) % 4
        sub_label_text.set("Loading" + "." * dots)

        # Glow-Effekt Titel
        glow_state[0] += direction[0] * 0.06
        if glow_state[0] >= 1.0:
            glow_state[0] = 1.0
            direction[0] = -1
        elif glow_state[0] <= 0.0:
            glow_state[0] = 0.0
            direction[0] = 1
        base = (15, 23, 36)
        accent = (45, 212, 191)
        mix = glow_state[0] * 0.7
        r = int((1 - mix) * base[0] + mix * accent[0])
        g = int((1 - mix) * base[1] + mix * accent[1])
        b = int((1 - mix) * base[2] + mix * accent[2])
        hexcol = f"#{r:02x}{g:02x}{b:02x}"
        title_label.configure(fg=hexcol)

        # Overlay entfernen, wenn fertig
        if elapsed < duration_ms:
            overlay.after(30, animate)
        else:
            try:
                overlay.destroy()
            except Exception:
                pass

    overlay.update_idletasks()
    animate()

title_label = ctk.CTkLabel(app, text="Glutenium", font=ctk.CTkFont(size=28, weight="bold"))
title_label.pack(pady=20)

tabview = ctk.CTkTabview(app, width=640, height=660, corner_radius=15)
show_loading_screen(duration_ms=700, title="Glutenium")
tabview.pack(padx=20, pady=10, fill="both", expand=True)
tab_modules = tabview.add("Modules")
tab_settings = tabview.add("Settings")
tab_keybinds = tabview.add("Keybinds")

# --- Module Buttons ---
def toggle_and_save(key, button, text_on, text_off):
    config[key] = not config[key]
    button.configure(text=text_off if config[key] else text_on)
    save_config()

def toggle_and_save(key, button, text_on, text_off):
    config[key] = not config[key]
    button.configure(text=text_off if config[key] else text_on)
    save_config()
    # Feedback & sound
    module_name = key.replace("_enabled", "").replace("_", " ").title()
    if config.get("chat_feedback", False):
        try:
        # try to send an in-game chat message if function exists
            if hasattr(minescript, "player_send_chat"):
                minescript.player_send_chat(f"{module_name} {'enabled' if config[key] else 'disabled'}")
            else:
                print(f"[ChatFeedback] {module_name} {'enabled' if config[key] else 'disabled'}")
        except Exception:
            print(f"[ChatFeedback] {module_name} {'enabled' if config[key] else 'disabled'}")
    

aim_btn = ctk.CTkButton(tab_modules, text="Start Aim Assist", command=lambda: toggle_and_save("aim_enabled", aim_btn, "Start Aim Assist", "Stop Aim Assist"), height=40)
aim_btn.pack(pady=6, fill="x")
crystal_btn = ctk.CTkButton(tab_modules, text="Start Crystal Place", command=lambda: toggle_and_save("crystal_enabled", crystal_btn, "Start Crystal Place", "Stop Crystal Place"), height=40)
crystal_btn.pack(pady=6, fill="x")
auto_totem_btn = ctk.CTkButton(tab_modules, text="Start Auto Totem", command=lambda: toggle_and_save("auto_totem_enabled", auto_totem_btn, "Start Auto Totem", "Stop Auto Totem"), height=40)
auto_totem_btn.pack(pady=6, fill="x")
auto_anchor_btn = ctk.CTkButton(tab_modules, text="Start Auto Anchor", command=lambda: toggle_and_save("auto_anchor_enabled", auto_anchor_btn, "Start Auto Anchor", "Stop Auto Anchor"), height=40)
auto_anchor_btn.pack(pady=6, fill="x")
double_anchor_btn = ctk.CTkButton(tab_modules, text="Start Double Anchor", command=lambda: toggle_and_save("double_anchor_enabled", double_anchor_btn, "Start Double Anchor", "Stop Double Anchor"), height=40)
double_anchor_btn.pack(pady=6, fill="x")
triggerbot_btn = ctk.CTkButton(tab_modules, text="Start Trigger Bot", command=lambda: toggle_and_save("triggerbot_enabled", triggerbot_btn, "Start Trigger Bot", "Stop Trigger Bot"), height=40)
triggerbot_btn.pack(pady=6, fill="x")


staff_btn = ctk.CTkButton(
    tab_modules,
    text="Start Staff Detector",
    command=lambda: toggle_and_save("staff_detector_enabled", staff_btn, "Start Staff Detector", "Stop Staff Detector"),
    height=40
)
staff_btn.pack(pady=6, fill="x")


module_key_labels = {}

keybind_frame = ctk.CTkScrollableFrame(tab_keybinds)
keybind_frame.pack(fill='both', expand=True, padx=10, pady=10)

ctk.CTkLabel(keybind_frame, text="Module Keybinds", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(4,8), anchor='w')


def update_key_label(module):
    val = config.get("keybinds", {}).get(module, "")
    text = val if val else "Not set"
    module_key_labels[module].configure(text=text)


def set_key_for_module(module):
    # Open a small dialog and listen for next key press in a thread
    dialog = tk.Toplevel(app)
    dialog.title(f"Set key for {module}")
    dialog.geometry("300x100")
    tk.Label(dialog, text=f"Press the key you want to bind to {module}").pack(pady=10)
    status = tk.Label(dialog, text="waiting for key...", fg="orange")
    status.pack()

    def listen():
        try:
            event = keyboard.read_event()
            # wait for first down event
            while event.event_type != 'down':
                event = keyboard.read_event()
            keyname = event.name
            config.setdefault('keybinds', {})[module] = keyname
            save_config()
            app.after(0, update_key_label, module)
            app.after(0, dialog.destroy)
        except Exception as e:
            print(f"[!] Fehler beim Setzen des Keys: {e}")
            app.after(0, dialog.destroy)

    threading.Thread(target=listen, daemon=True).start()


def reset_key_for_module(module):
    config.setdefault('keybinds', {})[module] = ""
    save_config()
    update_key_label(module)


for module in config.get('keybinds', {}).keys():
    row = ctk.CTkFrame(keybind_frame, fg_color='transparent')
    row.pack(fill='x', pady=4)
    ctk.CTkLabel(row, text=module.replace('_', ' ').title(), width=120, anchor='w').pack(side='left', padx=(6,12))
    lbl = ctk.CTkLabel(row, text=(config['keybinds'].get(module) or "Not set"))
    lbl.pack(side='left', padx=6)
    module_key_labels[module] = lbl
    set_btn = ctk.CTkButton(row, text='Set', width=60, command=lambda m=module: set_key_for_module(m))
    set_btn.pack(side='right', padx=6)
    reset_btn = ctk.CTkButton(row, text='Reset', width=60, command=lambda m=module: reset_key_for_module(m))
    reset_btn.pack(side='right')

# --- GUI key row ---
ctk.CTkLabel(keybind_frame, text="").pack(pady=6)
ctk.CTkLabel(keybind_frame, text="GUI Toggle Key", font=ctk.CTkFont(size=14)).pack(anchor='w')
gui_row = ctk.CTkFrame(keybind_frame, fg_color='transparent')
gui_row.pack(fill='x', pady=4)

gui_key_label = ctk.CTkLabel(gui_row, text=(config.get('gui_key') or "Not set"))
gui_key_label.pack(side='left', padx=6)

def set_gui_key():
    dialog = tk.Toplevel(app)
    dialog.title("Set GUI key")
    dialog.geometry("300x100")
    tk.Label(dialog, text="Press the key you want to toggle the GUI").pack(pady=10)

    def listen():
        try:
            event = keyboard.read_event()
            while event.event_type != 'down':
                event = keyboard.read_event()
            keyname = event.name
            config['gui_key'] = keyname
            save_config()
            app.after(0, lambda: gui_key_label.configure(text=keyname))
            app.after(0, dialog.destroy)
        except Exception as e:
            print(f"[!] Fehler beim Setzen der GUI-Taste: {e}")
            app.after(0, dialog.destroy)

    threading.Thread(target=listen, daemon=True).start()

ctk.CTkButton(gui_row, text='Set GUI Key', width=120, command=set_gui_key).pack(side='right')
ctk.CTkButton(gui_row, text='Reset', width=80, command=lambda: (config.update({'gui_key': ''}), save_config(), gui_key_label.configure(text='Not set'))).pack(side='right', padx=6)

# --- Chat Feedback & Toggle Sound checkboxes ---
options_frame = ctk.CTkFrame(keybind_frame, fg_color='transparent')
options_frame.pack(fill='x', pady=8)

chat_var = tk.BooleanVar(value=config.get('chat_feedback', False))
sound_var = tk.BooleanVar(value=config.get('toggle_sound', False))

def on_chat_change():
    config['chat_feedback'] = chat_var.get()
    save_config()

def on_sound_change():
    config['toggle_sound'] = sound_var.get()
    save_config()

ctk.CTkCheckBox(options_frame, text='Chat Feedback on toggle', variable=chat_var, command=on_chat_change).pack(anchor='w', pady=4)
ctk.CTkCheckBox(options_frame, text='Toggle sound (on module on/off)', variable=sound_var, command=on_sound_change).pack(anchor='w')

# === Keyboard Listener ===
# Central keyboard hook will watch for configured keys and toggle modules / GUI

def toggle_module_by_name(module):
    mapping = {
        'aim': ('aim_enabled', aim_btn, 'Start Aim Assist', 'Stop Aim Assist'),
        'crystal': ('crystal_enabled', crystal_btn, 'Start Crystal Place', 'Stop Crystal Place'),
        'auto_totem': ('auto_totem_enabled', auto_totem_btn, 'Start Auto Totem', 'Stop Auto Totem'),
        'auto_anchor': ('auto_anchor_enabled', auto_anchor_btn, 'Start Auto Anchor', 'Stop Auto Anchor'),
        'double_anchor': ('double_anchor_enabled', double_anchor_btn, 'Start Double Anchor', 'Stop Double Anchor'),
        'triggerbot': ('triggerbot_enabled', triggerbot_btn, 'Start Trigger Bot', 'Stop Trigger Bot'),
        'staff_detector': ('staff_detector_enabled', staff_btn, 'Start Staff Detector', 'Stop Staff Detector')
    }
    if module not in mapping:
        return
    key, btn, t_on, t_off = mapping[module]
    config[key] = not config.get(key, False)
    try:
        btn.configure(text=t_off if config[key] else t_on)
    except Exception:
        pass
    save_config()

    # Feedback nur als print
    print(f"[GLUTENIUM] {module.title()} {'ENABLED' if config[key] else 'DISABLED'}")



def on_key_event(e):
    # only respond to down events
    if e.event_type != 'down':
        return
    name = e.name
    # GUI toggle
        # GUI toggle (with fancy loader when opening)
    if config.get('gui_key') and name == config.get('gui_key'):
        try:
            if app.state() == 'normal':
                app.withdraw()
            else:
                # show loader then bring up GUI (non-blocking)
                show_loading_screen(duration_ms=600, title="Glutenium")
                app.deiconify()
                app.lift()
        except Exception:
            pass
        return

    # Per-module binds
    for module, keyname in config.get('keybinds', {}).items():
        if keyname and name == keyname:
            toggle_module_by_name(module)
            return


def start_keyboard_hook():
    try:
        keyboard.hook(on_key_event)
        # keep the thread alive
        keyboard.wait()
    except Exception as e:
        print(f"[!] Keyboard hook failed: {e}")

# === Remaining initialisation & threads ===
# Load config, update UI states and start background loops
load_config()

# Update module button text according to loaded config
if config.get("aim_enabled"): aim_btn.configure(text="Stop Aim Assist")
if config.get("crystal_enabled"): crystal_btn.configure(text="Stop Crystal Place")
if config.get("auto_totem_enabled"): auto_totem_btn.configure(text="Stop Auto Totem")
if config.get("auto_anchor_enabled"): auto_anchor_btn.configure(text="Stop Auto Anchor")
if config.get("double_anchor_enabled"): double_anchor_btn.configure(text="Stop Double Anchor")
if config.get("triggerbot_enabled"): triggerbot_btn.configure(text="Stop Trigger Bot")
if config.get("staff_detector_enabled"): staff_btn.configure(text="Stop Staff Detector")

# Update key labels
for m in config.get('keybinds', {}).keys():
    update_key_label(m)
if config.get('gui_key'):
    gui_key_label.configure(text=config.get('gui_key'))
else:
    gui_key_label.configure(text='Not set')

# Start keyboard hook in background
threading.Thread(target=start_keyboard_hook, daemon=True).start()

# === Staff List Management ===
ctk.CTkLabel(tab_settings, text="Staff Detector Names:").pack(pady=(10,0))

staff_entry = ctk.CTkEntry(tab_settings, placeholder_text="Enter Staff Name")
staff_entry.pack(pady=5, fill="x")

def add_staff_name():
    name = staff_entry.get().strip()
    if name and name not in config["staff_list"]:
        config["staff_list"].append(name)
        save_config()
        update_staff_listbox()
    staff_entry.delete(0, "end")

def remove_staff_name():
    selection = staff_listbox.curselection()
    if selection:
        index = selection[0]
        name = config["staff_list"][index]
        config["staff_list"].remove(name)
        save_config()
        update_staff_listbox()

def update_staff_listbox():
    staff_listbox.delete(0, tk.END)
    for name in config["staff_list"]:
        staff_listbox.insert(tk.END, name)

add_btn = ctk.CTkButton(tab_settings, text="Add", command=add_staff_name)
add_btn.pack(pady=2, fill="x")

remove_btn = ctk.CTkButton(tab_settings, text="Remove", command=remove_staff_name)
remove_btn.pack(pady=2, fill="x")

staff_listbox = tk.Listbox(tab_settings, height=6, bg="#2b2b2b", fg="white", selectbackground="#3a7ebf")
staff_listbox.pack(pady=5, fill="both", expand=False)

update_staff_listbox()
# --- Double Anchor Key Dropdown ---
anchor_keys = ["shift", "ctrl", "alt", "f", "caps lock"]
double_anchor_key_dropdown = ctk.CTkOptionMenu(tab_modules, values=anchor_keys, command=update_double_anchor_key)
double_anchor_key_dropdown.set(config.get("double_anchor_key", "shift"))
double_anchor_key_dropdown.pack(pady=10, fill="x")

# === Threads starten ===
load_config()
if config["aim_enabled"]: aim_btn.configure(text="Stop Aim Assist")
if config["crystal_enabled"]: crystal_btn.configure(text="Stop Crystal Place")
if config["auto_totem_enabled"]: auto_totem_btn.configure(text="Stop Auto Totem")
if config["auto_anchor_enabled"]: auto_anchor_btn.configure(text="Stop Auto Anchor")
if config.get("double_anchor_enabled", False): double_anchor_btn.configure(text="Stop Double Anchor")
if config.get("triggerbot_enabled", False): triggerbot_btn.configure(text="Stop Trigger Bot")

threading.Thread(target=aim_assist_loop, daemon=True).start()
threading.Thread(target=crystal_place_loop, daemon=True).start()
threading.Thread(target=auto_totem_loop, daemon=True).start()
threading.Thread(target=auto_anchor_loop, daemon=True).start()
threading.Thread(target=double_anchor_loop, daemon=True).start()
threading.Thread(target=triggerbot_loop, daemon=True).start()
threading.Thread(target=staff_detector_loop, daemon=True).start()


# === Settings Tab Widgets ===
def make_cooldown_slider(parent, key, label, from_=0.01, to=0.2, step=0.01):
    slider_frame = ctk.CTkFrame(parent, fg_color="transparent")
    slider_frame.pack(pady=6, fill="x")

    label_widget = ctk.CTkLabel(slider_frame, text=label, font=ctk.CTkFont(size=14))
    label_widget.pack(anchor="w")

    value_label = ctk.CTkLabel(slider_frame, text=f"{config[key]:.2f}s")
    value_label.pack(anchor="e")

    def on_change(value):
        config[key] = round(float(value), 3)
        value_label.configure(text=f"{config[key]:.2f}s")
        save_config()

    slider = ctk.CTkSlider(
        slider_frame, from_=from_, to=to, number_of_steps=int((to-from_)/step),
        command=on_change
    )
    slider.set(config[key])
    slider.pack(fill="x")

    

# --- Cooldown Sliders ---
make_cooldown_slider(tab_settings, "aim_cooldown", "Aim Cooldown", 0.01, 0.1, 0.01)
make_cooldown_slider(tab_settings, "crystal_cooldown", "Crystal Cooldown", 0.01, 0.2, 0.01)
make_cooldown_slider(tab_settings, "auto_totem_cooldown", "Auto Totem Cooldown", 0.01, 0.2, 0.01)
make_cooldown_slider(tab_settings, "auto_anchor_cooldown", "Auto Anchor Cooldown", 0.01, 0.2, 0.01)
make_cooldown_slider(tab_settings, "double_anchor_cooldown", "Double Anchor Cooldown", 0.01, 0.2, 0.01)
make_cooldown_slider(tab_settings, "triggerbot_cooldown", "Trigger Bot Cooldown", 0.1, 1.0, 0.05)

# --- Anchor Trigger Dropdown ---
def update_anchor_trigger(choice):
    config["anchor_trigger"] = choice.lower()
    save_config()

anchor_trigger_dropdown = ctk.CTkOptionMenu(
    tab_modules,
    values=["Sword", "Respawn Anchor"],
    command=update_anchor_trigger
)
anchor_trigger_dropdown.set(config.get("anchor_trigger", "sword").capitalize())
anchor_trigger_dropdown.pack(pady=10, fill="x")

# --- Theme Dropdown ---
def change_theme(choice):
    ctk.set_appearance_mode(choice.lower())
    config["theme"] = choice.lower()
    save_config()

theme_dropdown = ctk.CTkOptionMenu(
    tab_settings,
    values=["Dark", "Light", "System"],
    command=change_theme
)
theme_dropdown.set(config.get("theme", "Dark").capitalize())
theme_dropdown.pack(pady=20, fill="x")

app.protocol("WM_DELETE_WINDOW", lambda: (save_config(), app.destroy()))
app.mainloop()
