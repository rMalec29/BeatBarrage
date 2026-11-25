import traceback
import copy
import os
import math
import sys
import glob

# --- CRITICAL FIX FOR PYTHON 3.8+ ON WINDOWS ---
if os.name == 'nt':
    # This forces Python to look in your exact script folder for the Steam DLLs
    os.add_dll_directory(os.path.abspath(os.path.dirname(__file__)))

def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)

# --- CRITICAL WINDOWS DPI FIX FOR SMOOTH RENDERING ---
if os.name == 'nt':
    import ctypes
    from ctypes import wintypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1) # Windows 8.1+
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware() # Windows Vista/7
        except Exception:
            pass

# --- STEAMWORKS INITIALIZATION ---
STEAM_APP_ID = 480 # STRICTLY USE 480 FOR LOCAL TESTING
steam_active = False
try:
    from steamworks import STEAMWORKS
    steamworks = STEAMWORKS()
    steamworks.initialize()
    steam_active = True
    print(">>> STEAMWORKS API INITIALIZED SUCCESSFULLY! <<<")
except Exception as e:
    print("\n" + "!"*50)
    print(" STEAM API FAILED TO INITIALIZE ")
    print(f" EXACT ERROR: {e}")
    print("!"*50 + "\n")
    steamworks = None

try:
    import numpy as np
    np.fromstring = np.frombuffer 

    import pygame
    import soundcard as sc
    import threading
    import random
    import time
    import warnings
    import json
    import base64
    import hashlib
    from cryptography.fernet import Fernet
    
    warnings.filterwarnings("ignore", module="soundcard")

    # --- 0. ADVANCED SAVE SYSTEM, UPGRADES, & CHARMS ---
    SAVE_FILE = "idle_defender_save.dat"
    _SECRET = b"BeatBarrage_S3cr3t_K3y_2024_xQ9!"
    _FKEY = base64.urlsafe_b64encode(hashlib.sha256(_SECRET).digest())
    _CIPHER = Fernet(_FKEY)
    
    DEFAULT_UPGRADES = {
        "bass_dmg": {"level": 1, "cost": 250, "max": 5, "name": "Bass Payload", "desc": "Missile explosion size", "color": (255, 100, 100)},
        "bass_spd": {"level": 1, "cost": 200, "max": 5, "name": "Bass Velocity", "desc": "Missile flight speed", "color": (200, 50, 50)},
        "mid_wid":  {"level": 1, "cost": 300, "max": 4, "name": "Mids Width", "desc": "Laser hit-box size", "color": (100, 255, 100)},
        "mid_rate": {"level": 1, "cost": 350, "max": 4, "name": "Mids Riff Rate", "desc": "Laser fire speed", "color": (50, 200, 50)},
        "hi_arcs":  {"level": 1, "cost": 400, "max": 5, "name": "Highs Arcs", "desc": "Lightning chain jumps", "color": (100, 100, 255)},
        "hi_volt":  {"level": 1, "cost": 300, "max": 5, "name": "Highs Voltage", "desc": "Lightning damage", "color": (50, 50, 200)},
        "maxhp":    {"level": 1, "cost": 250, "max": 10, "name": "Core Max HP", "desc": "Maximum health points", "color": (255, 50, 200)},
        "regen":    {"level": 1, "cost": 300, "max": 10, "name": "Core Regen", "desc": "Passive healing rate", "color": (100, 200, 255)}
    }

    # 20 Unique Charms with Synergies
    ALL_CHARMS = {
        "heavy_needle":  {"name": "Heavy Needle",  "desc": "2x Damage, 0.5x Fire Rate",     "color": (180, 180, 180)},
        "neon_stylus":   {"name": "Neon Stylus",   "desc": "1.5x Fire Rate",                "color": (255, 50, 255)},
        "gold_plated":   {"name": "Gold Plated",   "desc": "+50% Gold Earned",              "color": (255, 215, 0)},
        "subwoofer":     {"name": "Subwoofer",     "desc": "Bass drops have massive AoE",   "color": (255, 80, 80)},
        "tweeter":       {"name": "Tweeter",       "desc": "+50% Crit Chance on Highs",     "color": (100, 120, 255)},
        "copper_wire":   {"name": "Copper Wire",   "desc": "Lightning chains 3 extra",      "color": (210, 120, 60)},
        "amp_shield":    {"name": "Amp Shield",    "desc": "Max HP is Doubled",             "color": (100, 255, 120)},
        "diamond_tip":   {"name": "Diamond Tip",   "desc": "Lasers pierce all enemies",     "color": (100, 255, 255)},
        "cooling_fan":   {"name": "Cooling Fan",   "desc": "Overdrive charges 2x faster",   "color": (180, 240, 255)},
        "rusty_gear":    {"name": "Rusty Gear",    "desc": "Enemy speed -30%",              "color": (160, 110, 60)},
        # New charms
        "bass_drum":     {"name": "Bass Drum",     "desc": "Explosions spawn ring burst",   "color": (255, 60, 60)},
        "echo_chamber":  {"name": "Echo Chamber",  "desc": "Missile trails deal damage",    "color": (80, 200, 255)},
        "phase_shift":   {"name": "Phase Shift",   "desc": "Overdrive freezes enemies 2s",  "color": (200, 140, 255)},
        "static_field":  {"name": "Static Field",  "desc": "Core zaps nearby enemies",      "color": (80, 255, 200)},
        "waveform":      {"name": "Waveform",      "desc": "High beats also fire laser",    "color": (140, 255, 140)},
        "distortion":    {"name": "Distortion",    "desc": "+50% dmg, +25% enemy speed",    "color": (255, 160, 60)},
        "equalizer":     {"name": "Equalizer",     "desc": "Overdrive fires all weapons",   "color": (255, 255, 140)},
        "feedback_loop": {"name": "Feedback Loop", "desc": "Kills restore 10% as credits",  "color": (255, 200, 80)},
        "vinyl_scratch": {"name": "Vinyl Scratch", "desc": "Double vinyls per wave",        "color": (200, 100, 255)},
        "beat_shield":   {"name": "Beat Shield",   "desc": "Every 10 kills: absorb 1 hit",  "color": (140, 200, 255)},
    }

    # Roguelike run perks - picked once per wave clear, lost on death
    PERK_POOL = {
        "overclock":      {"name": "Overclock",       "desc": "Weapon cooldowns -25%",        "color": (255, 200, 50),  "rarity": "common"},
        "resonance":      {"name": "Resonance",       "desc": "Missiles seek lowest HP",      "color": (255, 160, 60),  "rarity": "common"},
        "deep_bass":      {"name": "Deep Bass",       "desc": "Explosion radius +50%",        "color": (255, 100, 100), "rarity": "common"},
        "shredder":       {"name": "Shredder",        "desc": "Laser width doubled",          "color": (100, 255, 120), "rarity": "common"},
        "capacitor":      {"name": "Capacitor",       "desc": "Overdrive charges 3x faster",  "color": (160, 60, 255),  "rarity": "uncommon"},
        "iron_core":      {"name": "Iron Core",       "desc": "+150 Max HP this run",         "color": (160, 160, 255), "rarity": "common"},
        "gold_rush":      {"name": "Gold Rush",       "desc": "+40% credits earned",          "color": (255, 215, 0),   "rarity": "common"},
        "lucky_shot":     {"name": "Lucky Shot",      "desc": "+20% crit chance",             "color": (255, 255, 100), "rarity": "uncommon"},
        "phantom_beat":   {"name": "Phantom Beat",    "desc": "Auto-fires bass every 5s",     "color": (200, 100, 255), "rarity": "uncommon"},
        "tempo_slow":     {"name": "Tempo Down",      "desc": "All enemies -20% speed",       "color": (100, 200, 255), "rarity": "common"},
        "voltaic":        {"name": "Voltaic",         "desc": "+2 lightning chain jumps",     "color": (200, 200, 255), "rarity": "common"},
        "vampire":        {"name": "Vampire",         "desc": "15% damage heals core",        "color": (220, 60, 110),  "rarity": "rare"},
        "chain_reaction": {"name": "Chain Reaction",  "desc": "Explosions deal 2x damage",    "color": (255, 150, 0),   "rarity": "rare"},
        "shield_wall":    {"name": "Shield Wall",     "desc": "One free hit per wave",         "color": (100, 220, 120),  "rarity": "rare"},
        "beat_echo":      {"name": "Beat Echo",       "desc": "Each weapon fires twice",        "color": (255, 100, 200),  "rarity": "rare"},
        # Stackable build perks — designed to go crazy when stacked
        "mass_driver":    {"name": "Mass Driver",     "desc": "+25% explosion radius",          "color": (255, 120, 60),   "rarity": "common"},
        "velocity":       {"name": "Velocity",        "desc": "+30% missile speed",             "color": (180, 255, 100),  "rarity": "common"},
        "crit_storm":     {"name": "Crit Storm",      "desc": "+15% crit chance",               "color": (255, 240, 80),   "rarity": "uncommon"},
        "arc_surge":      {"name": "Arc Surge",       "desc": "+1 lightning chain jump",        "color": (180, 160, 255),  "rarity": "common"},
        "blood_price":    {"name": "Blood Price",     "desc": "+40% dmg, -8% max HP",           "color": (220, 40, 80),    "rarity": "uncommon"},
        "bass_amp":       {"name": "Bass Amp",        "desc": "+20% bass damage",               "color": (255, 80, 80),    "rarity": "common"},
        "laser_lens":     {"name": "Laser Lens",      "desc": "+15% laser width",               "color": (80, 255, 100),   "rarity": "common"},
        "volt_amp":       {"name": "Volt Amp",        "desc": "+30% lightning damage",          "color": (160, 160, 255),  "rarity": "common"},
        "gold_fever":     {"name": "Gold Fever",      "desc": "+25% credits from kills",        "color": (255, 200, 0),    "rarity": "common"},
        "combo_boost":    {"name": "Combo Boost",     "desc": "Max combo +5",                   "color": (0, 220, 255),    "rarity": "uncommon"},
        "berserker":      {"name": "Berserker",       "desc": "+5% dmg per active perk",        "color": (255, 60, 120),   "rarity": "rare"},
        "multishot":      {"name": "Multishot",       "desc": "Bass fires at 2 targets",        "color": (255, 180, 80),   "rarity": "uncommon"},
        "echo_volley":    {"name": "Echo Volley",     "desc": "+1 mid laser per beat",          "color": (80, 200, 130),   "rarity": "uncommon"},
        "overcharge":     {"name": "Overcharge",      "desc": "Overdrive lasts +3s longer",     "color": (255, 255, 180),  "rarity": "uncommon"},
        "glass_cannon":   {"name": "Glass Cannon",    "desc": "+100% dmg, -50% max HP",         "color": (255, 60, 60),    "rarity": "rare"},
        "adrenaline":     {"name": "Adrenaline",      "desc": "+2% dmg per combo level",        "color": (255, 140, 0),    "rarity": "uncommon"},
    }
    RARITY_COLORS = {"common": (180, 180, 180), "uncommon": (80, 210, 100), "rare": (180, 80, 255)}

    def load_progress():
        data = {
            "gold": 0, "vinyls": 0, "upgrades": copy.deepcopy(DEFAULT_UPGRADES), 
            "skins": {"basic": True, "silver": False, "gold": False, "neon": False, "diamond": False, "workshop": False}, 
            "selected_skin": "basic", "current_wave": 1, "difficulty": "NORMAL",
            "player_level": 1, "player_xp": 0, "platinum_records": 0,
            "current_mon_idx": 0, "snap_quad": 1,
            "unlocked_charms": [], "equipped_charms": []
        }
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "rb") as f:
                    encrypted = f.read()
                decrypted = _CIPHER.decrypt(encrypted)
                saved_data = json.loads(decrypted)
                for k in ["gold", "vinyls", "selected_skin", "current_wave", "difficulty", "player_level", "player_xp", "platinum_records", "current_mon_idx", "snap_quad", "unlocked_charms", "equipped_charms"]:
                    if k in saved_data: data[k] = saved_data[k]
                    for k in data["skins"]:
                        if k in saved_data.get("skins", {}): data["skins"][k] = saved_data["skins"][k]
                    for key in data["upgrades"]:
                        if key in saved_data.get("upgrades", {}):
                            data["upgrades"][key]["level"] = saved_data["upgrades"][key].get("level", 1)
                            data["upgrades"][key]["cost"] = saved_data["upgrades"][key].get("cost", data["upgrades"][key]["cost"])
            except: pass
        return data

    save_data = load_progress()
    gold = save_data["gold"]
    vinyls = save_data["vinyls"]
    upgrades = save_data["upgrades"]
    skins = save_data["skins"]
    selected_skin = save_data["selected_skin"]
    current_wave = save_data["current_wave"]
    difficulty = save_data["difficulty"]
    player_level = save_data["player_level"]
    player_xp = save_data["player_xp"]
    platinum_records = save_data["platinum_records"]
    current_mon_idx = save_data["current_mon_idx"]
    snap_quad = save_data["snap_quad"]
    unlocked_charms = save_data["unlocked_charms"]
    equipped_charms = save_data["equipped_charms"]

    def save_progress():
        raw = json.dumps({
                "gold": gold, "vinyls": vinyls, "upgrades": upgrades, "skins": skins, 
                "selected_skin": selected_skin, "current_wave": current_wave, "difficulty": difficulty,
                "player_level": player_level, "player_xp": player_xp, "platinum_records": platinum_records,
                "current_mon_idx": current_mon_idx, "snap_quad": snap_quad,
                "unlocked_charms": unlocked_charms, "equipped_charms": equipped_charms
        }).encode()
        with open(SAVE_FILE, "wb") as f:
            f.write(_CIPHER.encrypt(raw))

    def get_xp_requirement(level):
        return int(50 * (1.3 ** (level - 1)))

    def get_max_charm_slots():
        slots = 0
        if player_level >= 5: slots += 1
        if player_level >= 15: slots += 1
        if player_level >= 30: slots += 1
        return slots

    # --- 1. MULTI-BAND FFT AUDIO ENGINE ---
    current_bass, current_mid, current_high = 0.0, 0.0, 0.0
    roll_bass, roll_mid, roll_high = 0.01, 0.01, 0.01 
    smoothed_vol = 0.0    

    def listen_to_internal_audio():
        global current_bass, current_mid, current_high, smoothed_vol
        while True: 
            try:
                speaker = sc.default_speaker()
                mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
                with mic.recorder(samplerate=44100) as recorder:
                    while True:
                        data = recorder.record(numframes=1024)
                        if data.size > 0:
                            mono_data = data.mean(axis=1) if len(data.shape) > 1 else data
                            smoothed_vol = smoothed_vol * 0.8 + np.max(np.abs(mono_data)) * 0.2
                            fft_data = np.abs(np.fft.rfft(mono_data))
                            
                            current_bass = np.mean(fft_data[1:6])   
                            current_mid = np.mean(fft_data[6:45])   
                            current_high = np.mean(fft_data[45:150]) 
            except Exception:
                time.sleep(1.5)

    threading.Thread(target=listen_to_internal_audio, daemon=True).start()

    # --- 2. WINDOWS DISPLAY & CTYPES CONFIGURATION ---
    pygame.init()
    WIDTH, HEIGHT = 400, 300
    
    monitors = []
    if os.name == 'nt':
        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
            
        def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            monitors.append((lprcMonitor.contents.left, lprcMonitor.contents.top, 
                             lprcMonitor.contents.right - lprcMonitor.contents.left, 
                             lprcMonitor.contents.bottom - lprcMonitor.contents.top))
            return True
            
        MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
        ctypes.windll.user32.EnumDisplayMonitors(0, None, MonitorEnumProc(monitor_enum_proc), 0)
        
    if not monitors: monitors = [(0, 0, 1920, 1080)]
    if current_mon_idx >= len(monitors): current_mon_idx = 0
        
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
    main_surf = pygame.Surface((WIDTH, HEIGHT)) 
    
    HWND = None
    if os.name == 'nt':
        HWND = pygame.display.get_wm_info()['window']

    def set_window_pos(x, y):
        if HWND:
            ctypes.windll.user32.SetWindowPos(HWND, 0, x, y, 0, 0, 0x0015)

    def apply_snap():
        if not HWND: return
        mon_x, mon_y, mon_w, mon_h = monitors[current_mon_idx]
        margin = 20
        if snap_quad == 0:   tx, ty = mon_x + margin, mon_y + margin
        elif snap_quad == 1: tx, ty = mon_x + mon_w - WIDTH - margin, mon_y + margin
        elif snap_quad == 2: tx, ty = mon_x + margin, mon_y + mon_h - HEIGHT - margin
        else:                tx, ty = mon_x + mon_w - WIDTH - margin, mon_y + mon_h - HEIGHT - margin
        set_window_pos(tx, ty)

    def enforce_always_on_top():
        try:
            import win32gui, win32con
            while True:
                try:
                    win32gui.SetWindowPos(HWND, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                except: pass
                time.sleep(0.01)
        except ImportError:
            while True:
                try:
                    if HWND: ctypes.windll.user32.SetWindowPos(HWND, -1, 0, 0, 0, 0, 0x0013)
                except: pass
                time.sleep(0.01)

    threading.Thread(target=enforce_always_on_top, daemon=True).start()
    apply_snap()

    # --- IMAGES, FONTS & WORKSHOP ---
    img_workshop = None
    try:
        img_basic = pygame.image.load(resource_path("turntable_basic.png")).convert_alpha()
        img_silver = pygame.image.load(resource_path("turntable_silver.png")).convert_alpha()
        img_gold = pygame.image.load(resource_path("turntable_gold.png")).convert_alpha()
        img_neon = pygame.image.load(resource_path("turntable_neon.png")).convert_alpha()
        img_diamond = pygame.image.load(resource_path("turntable_diamond.png")).convert_alpha()
        images_loaded = True
        
        # Load Steam Workshop Subscribed Items
        if steam_active:
            workshop_dir = os.path.abspath(os.path.join(resource_path("."), f"../../workshop/content/{STEAM_APP_ID}/"))
            if os.path.exists(workshop_dir):
                # Grab the first custom PNG found in subscribed folders
                custom_skins = glob.glob(os.path.join(workshop_dir, "*/*.png"))
                if custom_skins:
                    img_workshop = pygame.image.load(custom_skins[0]).convert_alpha()
                    skins["workshop"] = True
    except Exception:
        images_loaded = False

    try:
        title_font = pygame.font.Font(resource_path("PressStart2P-Regular.ttf"), 10)
        desc_font = pygame.font.Font(resource_path("PressStart2P-Regular.ttf"), 8)
        skin_desc_font = pygame.font.Font(resource_path("PressStart2P-Regular.ttf"), 6)
        big_font = pygame.font.Font(resource_path("PressStart2P-Regular.ttf"), 16)
        dmg_font = pygame.font.Font(resource_path("PressStart2P-Regular.ttf"), 12)
        crit_font = pygame.font.Font(resource_path("PressStart2P-Regular.ttf"), 14)
    except:
        title_font = pygame.font.SysFont("Courier New", 12, bold=True)
        desc_font = pygame.font.SysFont("Courier New", 10)
        skin_desc_font = pygame.font.SysFont("Courier New", 8, bold=True)
        big_font = pygame.font.SysFont("Courier New", 18, bold=True)
        dmg_font = pygame.font.SysFont("Courier New", 14, bold=True)
        crit_font = pygame.font.SysFont("Courier New", 18, bold=True)

    clock = pygame.time.Clock()

    def draw_button_centered(surface, rect, text, font, bg_color, text_color, border_color=(255,255,255), border_width=2):
        pygame.draw.rect(surface, bg_color, rect)
        if border_width > 0: pygame.draw.rect(surface, border_color, rect, border_width)
        text_surf = font.render(text, False, text_color)
        text_x = rect.x + (rect.width // 2) - (text_surf.get_width() // 2)
        text_y = rect.y + (rect.height // 2) - (text_surf.get_height() // 2)
        surface.blit(text_surf, (text_x, text_y))

    def draw_card_text_centered(surface, rect, text, font, text_color, y_offset):
        text_surf = font.render(text, False, text_color)
        text_x = rect.x + (rect.width // 2) - (text_surf.get_width() // 2)
        surface.blit(text_surf, (text_x, rect.y + y_offset))

    def draw_glow_button(surface, rect, text, font, bg_color, text_color, glow_color, hovered=False, border_width=2):
        glow_size = 6 if hovered else 3
        glow_surf = pygame.Surface((rect.width + glow_size*2, rect.height + glow_size*2), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*glow_color, 100 if hovered else 45), (0, 0, rect.width + glow_size*2, rect.height + glow_size*2))
        surface.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))
        inner_col = tuple(min(255, c + 20) for c in bg_color) if hovered else bg_color
        pygame.draw.rect(surface, inner_col, rect)
        pygame.draw.rect(surface, glow_color, rect, border_width)
        # Auto-fit: shrink to fallback font if text overflows
        max_w = rect.width - 8
        use_font = font if font.size(text)[0] <= max_w else skin_desc_font
        text_surf = use_font.render(text, False, text_color)
        surface.blit(text_surf, (rect.x + (rect.width - text_surf.get_width())//2, rect.y + (rect.height - text_surf.get_height())//2))

    def draw_panel(surface, rect, bg=(14, 14, 22), border=(60, 60, 95), border_width=2):
        # Subtle gradient feel: draw slightly lighter strip at top
        pygame.draw.rect(surface, bg, rect)
        top_strip = pygame.Rect(rect.x, rect.y, rect.width, max(1, rect.height // 4))
        strip_surf = pygame.Surface((top_strip.width, top_strip.height), pygame.SRCALPHA)
        strip_surf.fill((255, 255, 255, 12))
        surface.blit(strip_surf, top_strip.topleft)
        pygame.draw.rect(surface, border, rect, border_width)

    def draw_text_shadow(surface, text, font, color, pos, shadow_color=(0,0,0), offset=1):
        shadow_surf = font.render(text, False, shadow_color)
        surface.blit(shadow_surf, (pos[0] + offset, pos[1] + offset))
        text_surf = font.render(text, False, color)
        surface.blit(text_surf, pos)
        return text_surf.get_width()

    def wrap_text(text, font, max_width):
        words = text.split()
        lines, current = [], []
        for word in words:
            test = " ".join(current + [word])
            if font.size(test)[0] <= max_width:
                current.append(word)
            else:
                if current: lines.append(" ".join(current))
                current = [word]
        if current: lines.append(" ".join(current))
        return lines if lines else [text]

    def draw_text_in_rect(surface, text, font, color, rect, y_start=0, line_height=None):
        lh = line_height or (font.size("A")[1] + 2)
        for i, line in enumerate(wrap_text(text, font, rect.width - 8)):
            surf = font.render(line, False, color)
            surface.blit(surf, (rect.x + 4, rect.y + y_start + i * lh))

    def fit_text(text, preferred_font, fallback_font, max_width):
        if preferred_font.size(text)[0] <= max_width:
            return preferred_font, text
        if fallback_font.size(text)[0] <= max_width:
            return fallback_font, text
        # Truncate with ellipsis
        while len(text) > 1 and fallback_font.size(text + "..")[0] > max_width:
            text = text[:-1]
        return fallback_font, text + ".."

    # --- 3. GAME STATE ---
    app_state = "MAIN_MENU"
    menu_open = False 

    enemies, missiles, particles, shockwaves, super_novas = [], [], [], [], []
    lasers, lightnings, damage_texts, streak_popups = [], [], [], []
    
    combo, streak_count, combo_timer, spawn_timer, shake_intensity, death_timer = 1, 0, 0, 0, 0, 0
    boss_spawned, overdrive_meter, overdrive_active, overdrive_timer = False, 0.0, False, 0
    cooldown_bass, cooldown_mid, cooldown_high, core_angle = 0, 0, 0, 0.0 
    wave_frames, WAVE_DURATION, intermission_timer = 0, 3600, 0
    vinyls_just_earned, xp_just_earned, elite_meter = 0, 0, 0 
    
    player_max_hp = 100.0 + (upgrades["maxhp"]["level"] * 25) - 25
    if "amp_shield" in equipped_charms: player_max_hp *= 2.0
    player_hp = player_max_hp
    base_regen = 0.02

    # Roguelike run state
    run_perks = []
    run_history = []   # [{'wave': N, 'offered': [...], 'picked': str}]
    wave_reward_options = []
    charm_scroll_offset = 0
    phantom_beat_timer = 0
    wave_shield_active = False
    beat_shield_kills = 0
    beat_shield_active = False
    phase_shift_active = False
    phase_shift_timer = 0
    static_field_timer = 0
    equalizer_fired = False

    # --- UI BUTTON DEFINITIONS ---
    btn_continue = pygame.Rect(WIDTH//2 - 75, HEIGHT//2 - 50, 150, 30)
    btn_new_game = pygame.Rect(WIDTH//2 - 75, HEIGHT//2 - 10, 150, 30)
    btn_options  = pygame.Rect(WIDTH//2 - 75, HEIGHT//2 + 30, 150, 30)
    btn_char_select = pygame.Rect(WIDTH//2 - 75, HEIGHT//2 + 70, 150, 30)
    btn_quit_main = pygame.Rect(WIDTH//2 - 75, HEIGHT//2 + 110, 150, 30)
    
    btn_back_opt = pygame.Rect(15, 15, 60, 25)
    btn_mon_prev = pygame.Rect(WIDTH//2 - 90, 85, 30, 30)
    btn_mon_next = pygame.Rect(WIDTH//2 + 60, 85, 30, 30)
    
    qw, qh = 60, 40
    q0_rect = pygame.Rect(WIDTH//2 - qw, 155, qw, qh)
    q1_rect = pygame.Rect(WIDTH//2, 155, qw, qh)
    q2_rect = pygame.Rect(WIDTH//2 - qw, 155 + qh, qw, qh)
    q3_rect = pygame.Rect(WIDTH//2, 155 + qh, qw, qh)
    quad_rects = [q0_rect, q1_rect, q2_rect, q3_rect]

    btn_menu = pygame.Rect(WIDTH - 95, HEIGHT - 35, 85, 25)
    btn_pause = pygame.Rect(WIDTH - 185, HEIGHT - 35, 85, 25)
    btn_close_menu = pygame.Rect(WIDTH - 40, 10, 30, 30)
    
    btn_diff_normal = pygame.Rect(WIDTH//2 - 120, 90, 240, 45)
    btn_diff_hard = pygame.Rect(WIDTH//2 - 120, 145, 240, 45)
    btn_diff_crazy = pygame.Rect(WIDTH//2 - 120, 200, 240, 45)
    btn_back_diff = pygame.Rect(15, 15, 60, 25)

    btn_resume       = pygame.Rect(WIDTH//2 - 60, HEIGHT//2 - 58, 120, 26)
    btn_run_log      = pygame.Rect(WIDTH//2 - 60, HEIGHT//2 - 28, 120, 26)
    btn_restart      = pygame.Rect(WIDTH//2 - 60, HEIGHT//2 +  2, 120, 26)
    btn_quit_to_main = pygame.Rect(WIDTH//2 - 60, HEIGHT//2 + 32, 120, 26)
    btn_back_run_log = pygame.Rect(15, 15, 60, 25)
    run_log_scroll   = 0

    # Garage / Character Select - Adjusted grid for Workshop Slot
    btn_skin_basic = pygame.Rect(25, 45, 110, 80)
    btn_skin_silver = pygame.Rect(145, 45, 110, 80)
    btn_skin_gold = pygame.Rect(265, 45, 110, 80)
    btn_skin_neon = pygame.Rect(25, 135, 110, 80)
    btn_skin_diamond = pygame.Rect(145, 135, 110, 80)
    btn_skin_workshop = pygame.Rect(265, 135, 110, 80) # New Workshop Button
    
    btn_charms_menu = pygame.Rect(WIDTH//2 - 140, 245, 130, 30)
    btn_prestige_garage = pygame.Rect(WIDTH//2 + 10, 245, 130, 30)
    btn_back_char = pygame.Rect(15, 15, 60, 25)
    
    # Charms UI
    btn_back_charms = pygame.Rect(15, 15, 60, 25)
    btn_charm_scroll_up   = pygame.Rect(WIDTH - 30, 65, 20, 20)
    btn_charm_scroll_down = pygame.Rect(WIDTH - 30, 260, 20, 20)
    charm_list_rects = []

    # Wave reward perk card layout (3 cards across)
    _cw, _ch = 116, 130
    _cy = 100
    wave_reward_rects = [
        pygame.Rect(8,            _cy, _cw, _ch),
        pygame.Rect(WIDTH//2 - _cw//2, _cy, _cw, _ch),
        pygame.Rect(WIDTH - 8 - _cw,  _cy, _cw, _ch),
    ]
    
    def get_upgrade_rects():
        rects = {}
        x_cols = [20, 205] 
        y_start = 50 
        row, col = 0, 0
        for key in DEFAULT_UPGRADES.keys():
            rects[key] = pygame.Rect(x_cols[col], y_start + (row * 50), 175, 42)
            col += 1
            if col > 1: col = 0; row += 1
        return rects
    upgrade_rects = get_upgrade_rects()

    def execute_prestige():
        global gold, vinyls, upgrades, player_level, player_xp, current_wave, platinum_records
        platinum_records += 1
        gold = 0
        vinyls = 0
        player_level = 1
        player_xp = 0
        current_wave = 1
        upgrades = copy.deepcopy(DEFAULT_UPGRADES)
        save_progress()

    def start_new_run(chosen_difficulty):
        global gold, upgrades, current_wave, difficulty, player_hp, player_max_hp, combo, streak_count, wave_frames, intermission_timer
        global enemies, missiles, particles, shockwaves, super_novas, lasers, lightnings, streak_popups, damage_texts, boss_spawned
        global overdrive_meter, overdrive_active, player_level, run_perks, wave_reward_options
        global phantom_beat_timer, wave_shield_active, beat_shield_kills, beat_shield_active
        global phase_shift_active, phase_shift_timer, static_field_timer, equalizer_fired, run_history

        difficulty = chosen_difficulty
        current_wave = 1
        wave_frames = 0
        intermission_timer = 0
        combo = 1
        streak_count = 0
        gold = 0
        boss_spawned = False
        overdrive_meter = 0.0
        overdrive_active = False
        run_perks = []
        run_history = []
        wave_reward_options = []
        phantom_beat_timer = 0
        wave_shield_active = False
        beat_shield_kills = 0
        beat_shield_active = False
        phase_shift_active = False
        phase_shift_timer = 0
        static_field_timer = 0
        equalizer_fired = False

        upgrades = copy.deepcopy(DEFAULT_UPGRADES)

        if difficulty == "CRAZY":
            player_level = 30
            for key in upgrades:
                upgrades[key]["level"] = upgrades[key]["max"]

        player_max_hp = 100.0 + (upgrades["maxhp"]["level"] * 25) - 25
        if "amp_shield" in equipped_charms: player_max_hp *= 2.0
        player_hp = player_max_hp

        enemies.clear(); missiles.clear(); particles.clear(); shockwaves.clear(); damage_texts.clear()
        super_novas.clear(); lasers.clear(); lightnings.clear(); streak_popups.clear()

    def push_steam_leaderboard(wave):
        if steam_active and steamworks:
            try:
                # 'True' flag tells Steam to KEEP BEST score only
                steamworks.Users.UploadLeaderboardScore("Highest_Wave", wave, True)
                print(f"Pushed Wave {wave} to Steam Leaderboards!")
            except Exception as e:
                print("Failed to push to Steam Leaderboard.")

    def handle_death():
        global gold, current_wave, upgrades, player_hp, player_max_hp, combo, streak_count, wave_frames, intermission_timer
        global enemies, missiles, shockwaves, super_novas, lasers, lightnings, streak_popups, damage_texts, boss_spawned
        global overdrive_meter, overdrive_active
        
        # --- Push Score to Steam Leaderboards ---
        push_steam_leaderboard(current_wave)

        if difficulty == "HARD":
            gold = 0 
            upgrades = copy.deepcopy(DEFAULT_UPGRADES) 
        else:
            gold = int(gold * 0.75) 
            
        current_wave = 1
        wave_frames = 0
        intermission_timer = 0
        combo = 1
        streak_count = 0
        boss_spawned = False
        overdrive_meter = 0.0
        overdrive_active = False
        
        player_max_hp = 100.0 + (upgrades["maxhp"]["level"] * 25) - 25
        if "amp_shield" in equipped_charms: player_max_hp *= 2.0
        player_hp = player_max_hp
        
        enemies.clear(); missiles.clear(); shockwaves.clear(); streak_popups.clear(); damage_texts.clear()
        super_novas.clear(); lasers.clear(); lightnings.clear()
        save_progress()

    def spawn_particle(x, y, color, speed_mult=1.0, count=10):
        for _ in range(count):
            particles.append({
                'pos': [float(x), float(y)],
                'vel': [random.uniform(-4, 4) * speed_mult, random.uniform(-4, 4) * speed_mult],
                'life': 255, 'color': color
            })

    def spawn_enemy(is_elite=False, e_type="NORMAL"):
        side = random.randint(0, 3)
        if side == 0: x, y = random.randint(0, WIDTH), -40
        elif side == 1: x, y = random.randint(0, WIDTH), HEIGHT + 40
        elif side == 2: x, y = -40, random.randint(0, HEIGHT)
        else: x, y = WIDTH + 40, random.randint(0, HEIGHT)
        
        base_hp = 1 + (current_wave - 1)
        
        if e_type == "GHOST":
            hp = base_hp * 50; speed = 0.2; color = (255, 215, 0, 150); size = 50
        elif e_type == "BOSS":
            hp = base_hp * 30; speed = 0.3; color = (255, 50, 255, 255); size = 60
        elif e_type == "SWARM":
            hp = 1; speed = 2.0 + (current_wave * 0.1); color = (50, 255, 255, 255); size = 12
        elif e_type == "TANK":
            hp = base_hp * 4; speed = 0.5; color = (100, 50, 50, 255); size = 35
        elif is_elite:
            hp = base_hp * 5; speed = 0.6; color = (255, 150, 0, 255); size = 20 + (hp * 1.5) 
        else:
            hp = base_hp; speed = 1.0 + (current_wave * 0.1) 
            color = (max(50, 255 - (hp*15)), 50, min(255, 50 + (hp*25)), 255) 
            size = 18 + (hp * 1.5)
            
        enemies.append({'pos': [float(x), float(y)], 'hp': hp, 'max_hp': hp, 'speed': speed, 'color': color, 'size': min(size, 80), 'type': e_type})

    def unlock_random_charm():
        global unlocked_charms, streak_popups
        available = [c for c in ALL_CHARMS.keys() if c not in unlocked_charms]
        if available:
            new_charm = random.choice(available)
            unlocked_charms.append(new_charm)
            streak_popups.append({'text': f"CHARM UNLOCKED: {ALL_CHARMS[new_charm]['name']}!", 'y': float(HEIGHT//2 - 60), 'life': 250})
            save_progress()
        else:
            streak_popups.append({'text': "ALL CHARMS UNLOCKED!", 'y': float(HEIGHT//2 - 60), 'life': 200})

    def damage_enemy(e, base_amount):
        global gold, combo, combo_timer, shake_intensity, streak_count, streak_popups, platinum_records
        global player_hp, player_max_hp, run_perks, beat_shield_kills
        
        amount = base_amount * (1.0 + (platinum_records * 0.2))
        if overdrive_active: amount *= 2.0
        
        if "heavy_needle" in equipped_charms: amount *= 2.0
        
        base_crit = 0.60 if "tweeter" in equipped_charms else 0.10
        if "lucky_shot" in run_perks: base_crit += 0.20 * run_perks.count("lucky_shot")
        is_crit = random.random() < min(0.95, base_crit)
        if is_crit: amount *= 2.0
        
        e['hp'] -= amount
        
        damage_texts.append({
            'pos': [e['pos'][0] + random.randint(-10, 10), e['pos'][1] - 10], 
            'text': str(int(amount)), 
            'life': 60, 
            'crit': is_crit
        })
        
        if e['hp'] <= 0 and e in enemies:
            spawn_particle(e['pos'][0], e['pos'][1], e['color'][:3], 1.5, int(min(50, e['max_hp']*3)))
            enemies.remove(e)

            if e['type'] == "GHOST":
                unlock_random_charm()
                return True

            base_gold_earned = e['max_hp'] + combo
            if e['type'] == "BOSS": base_gold_earned *= 10
            if selected_skin == "diamond": base_gold_earned = int(base_gold_earned * 1.5)
            if "gold_plated" in equipped_charms: base_gold_earned = int(base_gold_earned * 1.5)
            if "gold_rush"  in run_perks: base_gold_earned = int(base_gold_earned * (1.4  ** run_perks.count("gold_rush")))
            if "gold_fever" in run_perks: base_gold_earned = int(base_gold_earned * (1.25 ** run_perks.count("gold_fever")))
            if "feedback_loop" in equipped_charms: gold += int(base_gold_earned * 0.1)
            base_gold_earned = int(base_gold_earned * (1.0 + (platinum_records * 0.5)))
            gold += base_gold_earned

            streak_count += 1
            if "beat_shield" in equipped_charms: beat_shield_kills += 1
            combo = min(combo + 1, 20)
            combo_timer = 0

            if streak_count > 0 and streak_count % 50 == 0:
                streak_popups.append({'text': f"{streak_count} STREAK!", 'y': float(HEIGHT//2 - 30), 'life': 150})

            shake_intensity = max(shake_intensity, 5 + int(min(20, e['max_hp'])))
            return True

        # Vampire perk: heal on damage dealt
        if "vampire" in run_perks:
            heal = amount * 0.15 * run_perks.count("vampire")
            player_hp = min(player_max_hp, player_hp + heal)

        return False

    # --- 4. MAIN LOOP ---
    running = True
    scroll_bg_x = 0.0
    scroll_bg_y = 0.0

    while running:            
        offset_x = random.randint(-shake_intensity, shake_intensity) if shake_intensity > 0 else 0
        offset_y = random.randint(-shake_intensity, shake_intensity) if shake_intensity > 0 else 0
        if shake_intensity > 0: shake_intensity -= 1

        safe_vol = smoothed_vol if not np.isnan(smoothed_vol) else 0.0
        
        # --- DARK SUBTLE CHECKERBOARD BACKGROUND ---
        scroll_speed = 0.2 + (safe_vol * 1.5) 
        scroll_bg_x = (scroll_bg_x + scroll_speed) % 40
        scroll_bg_y = (scroll_bg_y + scroll_speed) % 40
        
        bg_col_1 = (10, 10, 15) 
        bg_col_2 = (15, 15, 20) 
        if overdrive_active:
            bg_col_1 = (40, 10, 60)
            bg_col_2 = (30, 10, 50)

        main_surf.fill(bg_col_1)
        x_int = int(scroll_bg_x)
        y_int = int(scroll_bg_y)
        
        for y in range(-40, HEIGHT, 20):
            for x in range(-40, WIDTH, 20):
                if ((x // 20) + (y // 20)) % 2 == 0:
                    pygame.draw.rect(main_surf, bg_col_2, (x + x_int + offset_x, y + y_int + offset_y, 20, 20))

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.ACTIVEEVENT:
                if HWND and hasattr(event, 'gain') and event.gain == 0:
                    try:
                        import win32gui, win32con
                        win32gui.SetWindowPos(HWND, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                    except:
                        ctypes.windll.user32.SetWindowPos(HWND, -1, 0, 0, 0, 0, 0x0013)

            if event.type == pygame.QUIT:
                save_progress(); running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if app_state == "PLAYING":
                        if menu_open: menu_open = False; save_progress()
                        else: app_state = "PAUSED"
                    elif app_state == "PAUSED": app_state = "PLAYING"
                    elif app_state in ["CHAR_SELECT", "DIFF_SELECT", "OPTIONS"]: app_state = "MAIN_MENU"; save_progress()
                    elif app_state == "CHARMS": app_state = "CHAR_SELECT"
                elif event.key == pygame.K_SPACE and app_state == "PLAYING" and not menu_open:
                    if overdrive_meter >= 100.0:
                        overdrive_active = True
                        overdrive_timer = 600
                        overdrive_meter = 0.0
                        shake_intensity = 20
                        spawn_particle(WIDTH//2, HEIGHT//2, (255, 255, 255), 5.0, 100)
                        if "phase_shift" in equipped_charms:
                            phase_shift_active = True
                            phase_shift_timer = 120
                        if "equalizer" in equipped_charms:
                            equalizer_fired = True
                        
            elif event.type == pygame.MOUSEWHEEL:
                if app_state == "CHARMS":
                    max_scroll = max(0, math.ceil(len(ALL_CHARMS) / 2) - 5)
                    charm_scroll_offset = max(0, min(max_scroll, charm_scroll_offset - event.y))
                elif app_state == "RUN_LOG":
                    run_log_scroll = max(0, run_log_scroll - event.y)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                
                if app_state == "MAIN_MENU":
                    if btn_continue.collidepoint(event.pos): app_state = "PLAYING"
                    elif btn_new_game.collidepoint(event.pos): app_state = "DIFF_SELECT"
                    elif btn_options.collidepoint(event.pos): app_state = "OPTIONS"
                    elif btn_char_select.collidepoint(event.pos): app_state = "CHAR_SELECT"
                    elif btn_quit_main.collidepoint(event.pos): save_progress(); running = False

                elif app_state == "OPTIONS":
                    if btn_back_opt.collidepoint(event.pos): app_state = "MAIN_MENU"
                    elif btn_mon_prev.collidepoint(event.pos):
                        current_mon_idx = (current_mon_idx - 1) % max(1, len(monitors))
                        apply_snap()
                    elif btn_mon_next.collidepoint(event.pos):
                        current_mon_idx = (current_mon_idx + 1) % max(1, len(monitors))
                        apply_snap()
                        
                    for i, q_rect in enumerate(quad_rects):
                        if q_rect.collidepoint(event.pos):
                            snap_quad = i
                            apply_snap()

                elif app_state == "DIFF_SELECT":
                    if btn_back_diff.collidepoint(event.pos): app_state = "MAIN_MENU"
                    elif btn_diff_normal.collidepoint(event.pos):
                        start_new_run("NORMAL"); app_state = "PLAYING"
                    elif btn_diff_hard.collidepoint(event.pos):
                        start_new_run("HARD"); app_state = "PLAYING"
                    elif btn_diff_crazy.collidepoint(event.pos):
                        start_new_run("CRAZY"); app_state = "PLAYING"

                elif app_state == "CHAR_SELECT":
                    if btn_back_char.collidepoint(event.pos): save_progress(); app_state = "MAIN_MENU"
                    elif btn_prestige_garage.collidepoint(event.pos) and player_level >= 10:
                        execute_prestige()
                    elif btn_charms_menu.collidepoint(event.pos):
                        app_state = "CHARMS"
                    elif btn_skin_basic.collidepoint(event.pos): selected_skin = "basic"
                    elif btn_skin_silver.collidepoint(event.pos):
                        if skins["silver"]: selected_skin = "silver"
                        elif vinyls >= 10: vinyls -= 10; skins["silver"] = True; selected_skin = "silver"
                    elif btn_skin_gold.collidepoint(event.pos):
                        if skins["gold"]: selected_skin = "gold"
                        elif vinyls >= 50: vinyls -= 50; skins["gold"] = True; selected_skin = "gold"
                    elif btn_skin_neon.collidepoint(event.pos):
                        if skins["neon"]: selected_skin = "neon"
                        elif vinyls >= 20: vinyls -= 20; skins["neon"] = True; selected_skin = "neon"
                    elif btn_skin_diamond.collidepoint(event.pos):
                        if skins["diamond"]: selected_skin = "diamond"
                        elif vinyls >= 100: vinyls -= 100; skins["diamond"] = True; selected_skin = "diamond"
                    elif btn_skin_workshop.collidepoint(event.pos) and skins["workshop"]:
                        selected_skin = "workshop"
                        
                elif app_state == "CHARMS":
                    if btn_back_charms.collidepoint(event.pos): app_state = "CHAR_SELECT"; save_progress()
                    elif btn_charm_scroll_up.collidepoint(event.pos):
                        charm_scroll_offset = max(0, charm_scroll_offset - 1)
                    elif btn_charm_scroll_down.collidepoint(event.pos):
                        max_scroll = max(0, math.ceil(len(ALL_CHARMS) / 2) - 5)
                        charm_scroll_offset = min(max_scroll, charm_scroll_offset + 1)
                    else:
                        slots = get_max_charm_slots()
                        for charm_id, rect in charm_list_rects:
                            if rect.collidepoint(event.pos):
                                if charm_id in equipped_charms:
                                    equipped_charms.remove(charm_id)
                                elif len(equipped_charms) < slots and charm_id in unlocked_charms:
                                    equipped_charms.append(charm_id)
                        
                elif app_state == "WAVE_REWARD":
                    for i, wr_rect in enumerate(wave_reward_rects):
                        if i < len(wave_reward_options) and wr_rect.collidepoint(event.pos):
                            chosen = wave_reward_options[i]
                            run_perks.append(chosen)  # always append (stacking allowed)
                            run_history.append({'wave': current_wave, 'offered': list(wave_reward_options), 'picked': chosen})
                            # Immediate one-time effects on pick
                            if chosen == "iron_core":
                                player_max_hp += 150
                                player_hp = min(player_max_hp, player_hp + 150)
                            elif chosen == "shield_wall":
                                wave_shield_active = True
                            elif chosen == "blood_price":
                                reduction = 0.08 * run_perks.count("blood_price")
                                player_max_hp = max(10, player_max_hp * (1 - reduction))
                                player_hp = min(player_max_hp, player_hp)
                            elif chosen == "glass_cannon":
                                player_max_hp = max(10, player_max_hp * 0.5)
                                player_hp = min(player_max_hp, player_hp)
                            elif chosen == "overcharge":
                                pass  # handled per-frame via overdrive_timer_max
                            # Advance wave & award XP
                            current_wave += 1
                            wave_frames = 0
                            boss_spawned = False
                            player_xp += xp_just_earned
                            while player_xp >= get_xp_requirement(player_level):
                                player_xp -= get_xp_requirement(player_level)
                                player_level += 1
                                streak_popups.append({'text': f"LEVEL UP: {player_level}!", 'y': float(HEIGHT//2 + 40), 'life': 250})
                                shake_intensity = 15
                                spawn_particle(WIDTH//2, HEIGHT//2, (0, 255, 255), 4.0, 30)
                            app_state = "PLAYING"
                            break

                elif app_state == "PAUSED":
                    if btn_resume.collidepoint(event.pos): app_state = "PLAYING"
                    elif btn_run_log.collidepoint(event.pos): app_state = "RUN_LOG"; run_log_scroll = 0
                    elif btn_restart.collidepoint(event.pos):
                        start_new_run(difficulty); app_state = "PLAYING"
                    elif btn_quit_to_main.collidepoint(event.pos): save_progress(); app_state = "MAIN_MENU"

                elif app_state == "RUN_LOG":
                    if btn_back_run_log.collidepoint(event.pos): app_state = "PAUSED"

                elif app_state == "PLAYING":
                    if menu_open:
                        if btn_close_menu.collidepoint(event.pos): menu_open = False; save_progress()
                        for key, rect in upgrade_rects.items():
                            if rect.collidepoint(event.pos):
                                if key.startswith("mid_") and player_level < 5: continue
                                if key.startswith("hi_") and player_level < 10: continue
                                upg = upgrades[key]
                                if upg["level"] < upg["max"] and gold >= upg["cost"]:
                                    gold -= upg["cost"]; upg["level"] += 1; upg["cost"] = int(upg["cost"] * 2.0) 
                                    if key == "maxhp": player_max_hp += 25; player_hp += 25 
                                    save_progress()
                    else:
                        if btn_menu.collidepoint(event.pos): menu_open = True
                        elif btn_pause.collidepoint(event.pos): app_state = "PAUSED"

        # --- GAME LOGIC (DEATH STATE) ---
        if app_state == "GAME_OVER":
            death_timer -= 1
            if death_timer <= 0:
                handle_death()
                app_state = "PLAYING" 

            for p in particles[:]:
                p_dx = p['pos'][0] - WIDTH//2; p_dy = p['pos'][1] - HEIGHT//2
                p_dist = max(1, np.sqrt(p_dx**2 + p_dy**2))
                
                p['vel'][0] += (p_dx/p_dist) * safe_vol * 1.5; p['vel'][1] += (p_dy/p_dist) * safe_vol * 1.5
                p['vel'][0] *= 0.95; p['vel'][1] *= 0.95
                
                p['pos'][0] += p['vel'][0]; p['pos'][1] += p['vel'][1]; p['life'] -= 4 
                if p['life'] <= 0: particles.remove(p)
                else: 
                    p_sz = max(2, p['life']//40)
                    pygame.draw.rect(main_surf, p['color'][:3], (int(p['pos'][0])+offset_x - p_sz//2, int(p['pos'][1])+offset_y - p_sz//2, p_sz, p_sz))
            
            screen.blit(main_surf, (0, 0))
            
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((150, 0, 0, 80)) 
            screen.blit(overlay, (0, 0))
            
            death_text = big_font.render("CORE DESTROYED", False, (255, 50, 50))
            screen.blit(death_text, (WIDTH//2 - death_text.get_width()//2, HEIGHT//2 - 20))
            
            if difficulty == "HARD": sub_text = title_font.render("HARD RESTART...", False, (255, 200, 200))
            else: sub_text = title_font.render("RESTARTING...", False, (200, 255, 200))
            
            screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, HEIGHT//2 + 10))

        # --- GAME LOGIC (PLAYING STATE) ---
        elif app_state == "PLAYING" and not menu_open:
            
            # --- GOLDEN GHOST SPAWN LOGIC ---
            if player_level >= 5 and current_wave > 3 and intermission_timer == 0 and len(enemies) < 15:
                if random.randint(0, 15000) == 1:
                    if not any(e['type'] == 'GHOST' for e in enemies):
                        spawn_enemy(e_type="GHOST")
                        streak_popups.append({'text': "A RARE GHOST APPEARED!", 'y': float(HEIGHT//2 - 50), 'life': 200})

            if overdrive_active:
                overdrive_timer -= 1
                if overdrive_timer <= 0:
                    overdrive_active = False
            else:
                if difficulty == "CRAZY":
                    overdrive_meter = 100.0 # INSTANT RECHARGE FOR TIKTOK DROPS
                elif combo > 10 and intermission_timer == 0:
                    od_rate = 0.01 + (combo * 0.001)
                    if "cooling_fan" in equipped_charms: od_rate *= 2.0
                    overdrive_meter = min(100.0, overdrive_meter + od_rate)
            
            if intermission_timer > 0:
                intermission_timer -= 1
                if intermission_timer <= 0:
                    # Brief wave-clear display done — show roguelike perk pick
                    wave_reward_options = random.sample(list(PERK_POOL.keys()), min(3, len(PERK_POOL)))
                    app_state = "WAVE_REWARD"
            else:
                if wave_frames <= WAVE_DURATION:
                    wave_frames += 1

                non_ghost_enemies = [e for e in enemies if e['type'] != "GHOST"]
                if wave_frames > WAVE_DURATION and len(non_ghost_enemies) == 0:
                    intermission_timer = 90
                    vinyls_just_earned = current_wave * (2 if "vinyl_scratch" in equipped_charms else 1)
                    xp_just_earned = current_wave * 15
                    vinyls += vinyls_just_earned
                    wave_shield_active = "shield_wall" in run_perks  # refresh per-wave shield
                    spawn_particle(WIDTH//2, HEIGHT//2, (0, 255, 255), 3.0, 50)
                    shake_intensity = 15
                    enemies = [e for e in enemies if e['type'] != "GHOST"]
            
            regen_mod = 2.0 if selected_skin == "basic" else 1.0
            player_hp = min(player_max_hp, player_hp + (base_regen * upgrades["regen"]["level"] * regen_mod))

            safe_bass = current_bass if not np.isnan(current_bass) else 0.0
            safe_mid = current_mid if not np.isnan(current_mid) else 0.0
            safe_high = current_high if not np.isnan(current_high) else 0.0

            roll_bass = roll_bass * 0.98 + safe_bass * 0.02
            roll_mid = roll_mid * 0.98 + safe_mid * 0.02
            roll_high = roll_high * 0.98 + safe_high * 0.02
            
            core_angle += 1.0 + (safe_mid * 15.0) + (safe_high * 30.0)
            
            if intermission_timer == 0:
                combo_timer += 1
                if combo_timer > 180:
                    streak_count = 0 
                    if combo > 1 and combo_timer % 15 == 0: 
                        combo -= 1
            else:
                combo_timer = 0 

            if safe_vol > 0.6 and intermission_timer == 0: 
                elite_meter += 1
                if elite_meter > 180: spawn_enemy(is_elite=True); elite_meter = 0; shake_intensity = 10 
            else: elite_meter = max(0, elite_meter - 2)

            if cooldown_bass > 0: cooldown_bass -= 1
            if cooldown_mid > 0: cooldown_mid -= 1
            if cooldown_high > 0: cooldown_high -= 1

            beat_bass = safe_bass > (roll_bass * 1.6) and safe_bass > 0.01
            beat_mid = safe_mid > (roll_mid * 1.5) and safe_mid > 0.01  
            beat_high = safe_high > (roll_high * 1.6) and safe_high > 0.01 

            valid_targets = [e for e in enemies if 15 < e['pos'][0] < WIDTH - 15 and 15 < e['pos'][1] < HEIGHT - 15]
            if valid_targets: valid_targets.sort(key=lambda e: (WIDTH//2 - e['pos'][0])**2 + (HEIGHT//2 - e['pos'][1])**2)

            dmg_mod = 2.0 if selected_skin == "diamond" else 1.0
            cd_mod = 0.6 if selected_skin == "neon" else 1.0

            # Charm rate synergies
            if "heavy_needle" in equipped_charms: cd_mod *= 1.5
            if "neon_stylus" in equipped_charms: cd_mod *= 0.66
            if "distortion" in equipped_charms: dmg_mod *= 1.5

            # Run perk modifiers (all stack by count)
            n = run_perks.count
            if n("overclock"):      cd_mod  *= (0.75 ** n("overclock"))
            if n("chain_reaction"): dmg_mod *= (1.0 + 1.0 * n("chain_reaction"))
            if n("blood_price"):    dmg_mod *= (1.4 ** n("blood_price"))
            if n("glass_cannon"):   dmg_mod *= (2.0 ** n("glass_cannon"))
            if n("bass_amp"):       pass  # applied per missile below
            if n("berserker"):      dmg_mod *= (1.0 + 0.05 * len(run_perks))
            if n("adrenaline"):     dmg_mod *= (1.0 + 0.02 * combo * n("adrenaline"))
            if n("gold_fever"):
                pass  # applied in damage_enemy via run_perks check
            perk_combo_cap = 20 + 5 * n("combo_boost")
            if n("overcharge"):
                overdrive_timer_max = 600 + 180 * n("overcharge")  # track for display
            else:
                overdrive_timer_max = 600

            if overdrive_active: cd_mod *= 0.2

            # Phantom beat auto-fire (perk)
            if "phantom_beat" in run_perks:
                phantom_beat_timer += 1
                if phantom_beat_timer >= 300:
                    phantom_beat_timer = 0
                    if valid_targets and cooldown_bass == 0:
                        missiles.append({'pos': [float(WIDTH//2), float(HEIGHT//2)], 'target': valid_targets[0], 'trail': []})
                        spawn_particle(WIDTH//2, HEIGHT//2, (200, 100, 255), 0.5, 4)
                        cooldown_bass = int(10 * cd_mod)

            # Static field (charm) — zap enemies near core
            if "static_field" in equipped_charms and intermission_timer == 0:
                static_field_timer += 1
                if static_field_timer >= 20:
                    static_field_timer = 0
                    for _e in enemies[:]:
                        _dx = WIDTH//2 - _e['pos'][0]; _dy = HEIGHT//2 - _e['pos'][1]
                        if (_dx*_dx + _dy*_dy) < 80*80:
                            damage_enemy(_e, 0.3 * dmg_mod)
                    pygame.draw.circle(main_surf, (80, 255, 200, 40), (WIDTH//2 + offset_x, HEIGHT//2 + offset_y), 80, 1)

            # Beat shield kill counter
            if "beat_shield" in equipped_charms:
                if beat_shield_kills >= 10:
                    beat_shield_active = True
                    beat_shield_kills = 0
                    streak_popups.append({'text': "BEAT SHIELD READY!", 'y': float(HEIGHT//2 - 50), 'life': 100})

            if selected_skin == "gold" and intermission_timer == 0:
                if random.randint(0, 3000) < 15: 
                    super_novas.append({'radius': 15, 'alpha': 255, 'power': 5}) 
                    spawn_particle(WIDTH//2, HEIGHT//2, (255, 200, 50), 2.0, 15)
                    shake_intensity = 10

            def fire_missile(target_override=None):
                tgt = target_override
                if tgt is None and valid_targets:
                    if "resonance" in run_perks:
                        tgt = min(valid_targets, key=lambda e: e['hp'])
                    else:
                        tgt = valid_targets[0]
                if tgt:
                    missiles.append({'pos': [float(WIDTH//2), float(HEIGHT//2)], 'target': tgt, 'trail': []})
                    return True
                return False

            if beat_bass and cooldown_bass == 0 and intermission_timer == 0:
                spawn_particle(WIDTH//2, HEIGHT//2, (255, 100, 100), 0.5, 4)
                shockwaves.append({'radius': 25, 'alpha': 100, 'color': (255, 100, 100)})
                cooldown_bass = int(10 * cd_mod)
                if fire_missile(): shake_intensity = 3
                if n("beat_echo") and len(valid_targets) > 1:   fire_missile(valid_targets[1])
                if n("multishot") and len(valid_targets) > 1:   fire_missile(valid_targets[1])
                if n("multishot") > 1 and len(valid_targets) > 2: fire_missile(valid_targets[2])

            def fire_laser():
                if not valid_targets: return
                target = valid_targets[0]
                dx = target['pos'][0] - WIDTH//2; dy = target['pos'][1] - HEIGHT//2
                length = np.sqrt(dx**2 + dy**2)
                if length == 0: return
                dx, dy = dx/length, dy/length
                end_pos = (WIDTH//2 + dx*600, HEIGHT//2 + dy*600)
                lasers.append({'start': (WIDTH//2, HEIGHT//2), 'end': end_pos, 'life': 255})
                laser_width = upgrades["mid_wid"]["level"] * 15
                if n("shredder"):    laser_width *= 2 ** n("shredder")
                if n("laser_lens"):  laser_width *= (1.15 ** n("laser_lens"))
                for e in valid_targets[:]:
                    ex = e['pos'][0] - WIDTH//2; ey = e['pos'][1] - HEIGHT//2
                    proj = (ex * dx) + (ey * dy)
                    if proj > 0:
                        cx2 = WIDTH//2 + proj * dx; cy2 = HEIGHT//2 + proj * dy
                        if np.sqrt((e['pos'][0]-cx2)**2 + (e['pos'][1]-cy2)**2) < (laser_width + e['size']/2) or "diamond_tip" in equipped_charms:
                            damage_enemy(e, (0.5 + 0.5 * upgrades["mid_wid"]["level"]) * dmg_mod)

            if beat_mid and cooldown_mid == 0 and intermission_timer == 0 and player_level >= 5:
                spawn_particle(WIDTH//2, HEIGHT//2, (100, 255, 100), 0.5, 4)
                shockwaves.append({'radius': 25, 'alpha': 100, 'color': (100, 255, 100)})
                cooldown_mid = int(max(3, 10 - upgrades["mid_rate"]["level"]) * cd_mod)
                fire_laser()
                if n("beat_echo"):    fire_laser()
                if n("echo_volley"):
                    for _ in range(n("echo_volley")): fire_laser()
                shake_intensity = 2

            def fire_lightning():
                if not valid_targets: return
                points = [(WIDTH//2, HEIGHT//2)]
                curr = valid_targets[0]
                hit_ids = set()
                chain_jumps = upgrades["hi_arcs"]["level"]
                if "copper_wire" in equipped_charms: chain_jumps += 3
                if n("voltaic"):   chain_jumps += 2 * n("voltaic")
                if n("arc_surge"): chain_jumps += n("arc_surge")
                dmg = upgrades["hi_volt"]["level"] * dmg_mod * (1.3 ** n("volt_amp"))
                for _ in range(chain_jumps):
                    points.append(tuple(curr['pos']))
                    hit_ids.add(id(curr))
                    damage_enemy(curr, dmg)
                    next_t = [e for e in valid_targets if id(e) not in hit_ids]
                    if not next_t: break
                    next_t.sort(key=lambda e: (e['pos'][0]-curr['pos'][0])**2 + (e['pos'][1]-curr['pos'][1])**2)
                    curr = next_t[0]
                lightnings.append({'points': points, 'life': 255})

            if beat_high and cooldown_high == 0 and intermission_timer == 0 and player_level >= 10:
                spawn_particle(WIDTH//2, HEIGHT//2, (100, 100, 255), 0.5, 4)
                shockwaves.append({'radius': 25, 'alpha': 100, 'color': (100, 100, 255)})
                cooldown_high = int(8 * cd_mod)
                fire_lightning()
                if "beat_echo" in run_perks: fire_lightning()
                if "waveform" in equipped_charms: fire_laser()

            # Equalizer charm: fires all weapons simultaneously on overdrive activation
            if equalizer_fired:
                equalizer_fired = False
                fire_missile(); fire_laser(); fire_lightning()
                spawn_particle(WIDTH//2, HEIGHT//2, (255, 255, 100), 3.0, 30)

            if intermission_timer == 0 and wave_frames <= WAVE_DURATION:
                if current_wave % 10 == 0 and not boss_spawned:
                    spawn_enemy(e_type="BOSS")
                    boss_spawned = True
                elif not (current_wave % 10 == 0):
                    # CRAZY MODE SPAWN OVERRIDE
                    if difficulty == "CRAZY":
                        spawn_timer += 15.0 + (safe_vol * 30.0) # Absolute chaos
                    else:
                        spawn_timer += 0.8 + (safe_vol * 5.0) + (combo * 0.05) + (current_wave * 0.2)
                        
                    spawn_threshold = max(20, 60 - (current_wave * 2)) 
                    if spawn_timer > spawn_threshold: 
                        if safe_bass > (roll_bass * 2.0) and safe_bass > 0.1:
                            spawn_enemy(e_type="TANK")
                        elif safe_high > (roll_high * 2.0) and safe_high > 0.05:
                            spawn_enemy(e_type="SWARM")
                            spawn_enemy(e_type="SWARM")
                        else:
                            spawn_enemy()
                        spawn_timer = 0

            # --- 8-BIT SHAPES RENDERING ---
            for s in shockwaves[:]:
                s['radius'] += 12; s['alpha'] -= 8 
                if s['alpha'] <= 0: shockwaves.remove(s)
                else:
                    rad_int = int(s['radius'])
                    wave_surf = pygame.Surface((rad_int * 2, rad_int * 2), pygame.SRCALPHA)
                    pygame.draw.circle(wave_surf, (*s['color'], int(s['alpha'])), (rad_int, rad_int), rad_int, 2)
                    main_surf.blit(wave_surf, (int(WIDTH//2 + offset_x - rad_int), int(HEIGHT//2 + offset_y - rad_int)))

            for n in super_novas[:]:
                n['radius'] += 8; n['alpha'] -= 4
                if n['alpha'] <= 0: super_novas.remove(n)
                else:
                    rad_int = int(n['radius'])
                    wave_surf = pygame.Surface((rad_int * 2, rad_int * 2), pygame.SRCALPHA)
                    thickness = max(1, int(n['alpha']//30))
                    pygame.draw.circle(wave_surf, (255, 200, 50, int(n['alpha'])), (rad_int, rad_int), rad_int, thickness)
                    main_surf.blit(wave_surf, (int(WIDTH//2 + offset_x - rad_int), int(HEIGHT//2 + offset_y - rad_int)))
                    for e in enemies[:]:
                        edx = WIDTH//2 - e['pos'][0]; edy = HEIGHT//2 - e['pos'][1]
                        edist = np.sqrt(edx**2 + edy**2)
                        if abs(edist - n['radius']) < 20: 
                            if edist > 0: e['pos'][0] -= (edx/edist) * 2.5 * n['power']; e['pos'][1] -= (edy/edist) * 2.5 * n['power']
                            damage_enemy(e, 0.2 * n['power'] * dmg_mod) 

            for l in lasers[:]:
                l['life'] -= 20
                if l['life'] <= 0: lasers.remove(l)
                else: pygame.draw.line(main_surf, (100, 255, 100, l['life']), l['start'], l['end'], max(1, l['life']//40))

            for lt in lightnings[:]:
                lt['life'] -= 30
                if lt['life'] <= 0: lightnings.remove(lt)
                else:
                    if len(lt['points']) > 1:
                        for i in range(len(lt['points'])-1):
                            pygame.draw.line(main_surf, (200, 200, 255), lt['points'][i], lt['points'][i+1], max(1, lt['life']//80))

            missile_speed = (10 + (upgrades["bass_spd"]["level"] * 2)) * (1.3 ** n("velocity"))
            for m in missiles[:]:
                m['trail'].append(list(m['pos']))
                if len(m['trail']) > 5: m['trail'].pop(0) 
                
                dx = m['target']['pos'][0] - m['pos'][0]; dy = m['target']['pos'][1] - m['pos'][1]
                dist = np.sqrt(dx**2 + dy**2)
                if dist > 0: m['pos'][0] += (dx/dist) * missile_speed; m['pos'][1] += (dy/dist) * missile_speed
                
                for i, t_pos in enumerate(m['trail']):
                    t_size = max(2, i)
                    pygame.draw.rect(main_surf, (100, 255, 200), (int(t_pos[0])+offset_x - t_size//2, int(t_pos[1])+offset_y - t_size//2, t_size, t_size))
                
                pygame.draw.rect(main_surf, (255, 255, 255), (int(m['pos'][0])+offset_x - 3, int(m['pos'][1])+offset_y - 3, 6, 6))
                
                explosion_radius = 15 + (upgrades["bass_dmg"]["level"] * 5)
                if "subwoofer" in equipped_charms: explosion_radius *= 2.0
                if n("deep_bass"):   explosion_radius *= (1.5 ** n("deep_bass"))
                if n("mass_driver"): explosion_radius *= (1.25 ** n("mass_driver"))
                bass_dmg_mult = dmg_mod * (1.2 ** n("bass_amp"))
                hit_radius = (m['target']['size'] / 2) + missile_speed + 5
                
                # Echo chamber: trail deals damage
                if "echo_chamber" in equipped_charms:
                    for t_pos in m['trail']:
                        for e in valid_targets[:]:
                            if np.sqrt((e['pos'][0]-t_pos[0])**2 + (e['pos'][1]-t_pos[1])**2) < 8:
                                damage_enemy(e, 0.15 * dmg_mod)

                if dist < hit_radius:
                    spawn_particle(m['pos'][0], m['pos'][1], (255, 255, 255), 1.0, 3)
                    for e in valid_targets[:]:
                        e_dist = np.sqrt((e['pos'][0]-m['pos'][0])**2 + (e['pos'][1]-m['pos'][1])**2)
                        if e_dist < explosion_radius: damage_enemy(e, 1.5 * bass_dmg_mult)
                    # Bass drum: extra shockwave rings on explosion
                    if "bass_drum" in equipped_charms:
                        shockwaves.append({'radius': 10, 'alpha': 180, 'color': (255, 80, 80)})
                        shockwaves.append({'radius': 5,  'alpha': 120, 'color': (255, 160, 80)})
                    if m in missiles: missiles.remove(m)

            speed_mod = 0.7 if selected_skin == "silver" else 1.0
            if "rusty_gear" in equipped_charms: speed_mod *= 0.7
            if "distortion" in equipped_charms: speed_mod *= 1.25
            if "tempo_slow" in run_perks: speed_mod *= (0.8 ** run_perks.count("tempo_slow"))

            # Phase shift freeze countdown
            if phase_shift_active:
                phase_shift_timer -= 1
                if phase_shift_timer <= 0:
                    phase_shift_active = False
                speed_mod = 0.0  # frozen

            bass_ratio = safe_bass / max(roll_bass, 0.01)
            mid_ratio = safe_mid / max(roll_mid, 0.01)

            audio_push = max(0, (bass_ratio - 1.0) * 1.2 + (mid_ratio - 1.0) * 0.6)
            audio_push = min(audio_push, 2.5)

            for e in enemies[:]:
                edx = (WIDTH//2) - e['pos'][0]; edy = (HEIGHT//2) - e['pos'][1]
                edist = np.sqrt(edx**2 + edy**2)
                
                actual_speed = e['speed'] * (0.5 + audio_push) * speed_mod
                
                if edist > 0: e['pos'][0] += (edx/edist) * actual_speed; e['pos'][1] += (edy/edist) * actual_speed
                
                half_size = e['size'] / 2
                e_rect = pygame.Rect(e['pos'][0] - half_size + offset_x, e['pos'][1] - half_size + offset_y, e['size'], e['size'])
                
                if e['type'] == "GHOST":
                    ghost_surf = pygame.Surface((e['size'], e['size']), pygame.SRCALPHA)
                    pygame.draw.rect(ghost_surf, e['color'], (0, 0, e['size'], e['size']))
                    pygame.draw.rect(ghost_surf, (255, 255, 255, 200), (0, 0, e['size'], e['size']), 2)
                    main_surf.blit(ghost_surf, e_rect.topleft)
                else:
                    pygame.draw.rect(main_surf, (15, 15, 20), e_rect)
                    pygame.draw.rect(main_surf, e['color'][:3], e_rect, 3)
                
                if e['max_hp'] > 1 and e['type'] != "GHOST":
                    hp_pct = e['hp'] / e['max_hp']
                    pygame.draw.rect(main_surf, (0, 0, 0), (e_rect.x, e_rect.y - 8, e['size'], 4))
                    pygame.draw.rect(main_surf, (0, 255, 0), (e_rect.x, e_rect.y - 8, int(e['size'] * hp_pct), 4))
                
                if edist < (20 + half_size): 
                    if e['type'] == "GHOST":
                        spawn_particle(e['pos'][0], e['pos'][1], (200, 200, 200), 2.0, 30)
                        streak_popups.append({'text': "GHOST ESCAPED!", 'y': float(HEIGHT//2 - 30), 'life': 100})
                        if e in enemies: enemies.remove(e)
                    else:
                        shake_intensity = 15; combo = 1; streak_count = 0
                        if difficulty != "CRAZY":
                            if wave_shield_active:
                                wave_shield_active = False
                                streak_popups.append({'text': "SHIELD WALL BLOCKED!", 'y': float(HEIGHT//2 - 50), 'life': 120})
                                spawn_particle(e['pos'][0], e['pos'][1], (100, 220, 120), 3.0, 20)
                            elif beat_shield_active:
                                beat_shield_active = False
                                streak_popups.append({'text': "BEAT SHIELD!", 'y': float(HEIGHT//2 - 50), 'life': 120})
                                spawn_particle(e['pos'][0], e['pos'][1], (140, 200, 255), 3.0, 20)
                            else:
                                player_hp -= (15 * e['max_hp'])
                        spawn_particle(e['pos'][0], e['pos'][1], e['color'][:3], 3.0, 20)
                        if e in enemies: enemies.remove(e)
                    for m in missiles[:]:
                        if m['target'] == e: missiles.remove(m)

            if player_hp <= 0:
                shake_intensity = 30 
                spawn_particle(WIDTH//2, HEIGHT//2, (255, 50, 50), 8.0, 200) 
                enemies.clear() 
                app_state = "GAME_OVER"
                death_timer = 180 

            for p in particles[:]:
                p_dx = p['pos'][0] - WIDTH//2; p_dy = p['pos'][1] - HEIGHT//2
                p_dist = max(1, np.sqrt(p_dx**2 + p_dy**2))
                
                p['vel'][0] += (p_dx/p_dist) * safe_vol * 1.5; p['vel'][1] += (p_dy/p_dist) * safe_vol * 1.5
                p['vel'][0] *= 0.95; p['vel'][1] *= 0.95
                
                p['pos'][0] += p['vel'][0]; p['pos'][1] += p['vel'][1]; p['life'] -= 10 
                if p['life'] <= 0: particles.remove(p)
                else: 
                    p_sz = max(2, p['life']//40)
                    pygame.draw.rect(main_surf, p['color'][:3], (int(p['pos'][0])+offset_x - p_sz//2, int(p['pos'][1])+offset_y - p_sz//2, p_sz, p_sz))

            for dt in damage_texts[:]:
                dt['pos'][1] -= 1.0 
                dt['life'] -= 3
                if dt['life'] <= 0:
                    damage_texts.remove(dt)
                else:
                    font_to_use = crit_font if dt['crit'] else dmg_font
                    color = (255, 255, 0) if dt['crit'] else (255, 255, 255)
                    txt_surf = font_to_use.render(dt['text'], False, color) 
                    alpha_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
                    alpha_surf.fill((255, 255, 255, max(0, min(255, dt['life'] * 4))))
                    txt_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    main_surf.blit(txt_surf, (int(dt['pos'][0]) + offset_x, int(dt['pos'][1]) + offset_y))

        # --- DRAW CORE & UI (Applies to PLAYING and PAUSED states) ---
        if app_state in ["PLAYING", "PAUSED"]:
            p_size = 35 + int(safe_vol * 70); p_size = min(p_size, 80) 
            if overdrive_active: p_size = 80
            
            if images_loaded:
                if selected_skin == "gold": current_img = img_gold; skin_col = (255, 215, 0)
                elif selected_skin == "silver": current_img = img_silver; skin_col = (192, 192, 192)
                elif selected_skin == "neon": current_img = img_neon; skin_col = (255, 50, 255)
                elif selected_skin == "diamond": current_img = img_diamond; skin_col = (100, 255, 255)
                elif selected_skin == "workshop" and img_workshop: current_img = img_workshop; skin_col = (255, 255, 255)
                else: current_img = img_basic; skin_col = (100, 100, 100)
                
                pulsing_skin = pygame.transform.scale(current_img, (p_size, p_size))
                rotated_core = pygame.transform.rotate(pulsing_skin, core_angle)
                c_rect = rotated_core.get_rect(center=(WIDTH//2 + offset_x, HEIGHT//2 + offset_y))
                
                outline_color = (255, 255, 255) if overdrive_active else skin_col
                pygame.draw.circle(main_surf, outline_color, (WIDTH//2 + offset_x, HEIGHT//2 + offset_y), (p_size // 2) + 1, 1)
                
                main_surf.blit(rotated_core, c_rect.topleft)
            else:
                health_pct = max(0.0, player_hp / player_max_hp)
                core_r, core_g, core_b = int(255 * (1 - health_pct)), int(255 * health_pct), int(150 * health_pct)
                core_color = (core_r, core_g, core_b)
                if overdrive_active: core_color = (255, 255, 255)

                core_surf = pygame.Surface((p_size, p_size), pygame.SRCALPHA)
                pygame.draw.rect(core_surf, (max(0, core_r-50), max(0, core_g-50), max(0, core_b-50)), (0, 0, p_size, p_size))
                pygame.draw.rect(core_surf, core_color, (5, 5, p_size-10, p_size-10))
                pygame.draw.rect(core_surf, (255, 255, 255), (12, 12, p_size-24, p_size-24))
                
                rotated_core = pygame.transform.rotate(core_surf, core_angle)
                c_rect = rotated_core.get_rect(center=(WIDTH//2 + offset_x, HEIGHT//2 + offset_y))
                main_surf.blit(rotated_core, c_rect.topleft)

            screen.blit(main_surf, (0, 0))

            for sp in streak_popups[:]:
                sp['life'] -= 2
                sp['y'] -= 0.5 
                if sp['life'] <= 0: streak_popups.remove(sp)
                else:
                    txt_surf = big_font.render(sp['text'], False, (255, 215, 0))
                    alpha_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
                    alpha_surf.fill((255, 255, 255, max(0, min(255, sp['life'] * 2))))
                    txt_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    screen.blit(txt_surf, (WIDTH//2 - txt_surf.get_width()//2, int(sp['y'])))

            if intermission_timer > 0 and app_state == "PLAYING":
                t_clr = int(180 + 75 * math.sin(pygame.time.get_ticks() / 200.0))
                draw_text_shadow(screen, f"WAVE {current_wave} CLEARED!", big_font,
                                 (0, t_clr, 255),
                                 (WIDTH//2 - big_font.size(f"WAVE {current_wave} CLEARED!")[0]//2, HEIGHT//2 - 35),
                                 shadow_color=(0, 0, 60), offset=2)
                rw = title_font.render(f"+{vinyls_just_earned} VINYLS  +{xp_just_earned} XP", False, (255, 215, 0))
                screen.blit(rw, (WIDTH//2 - rw.get_width()//2, HEIGHT//2 + 8))
                hint_s = skin_desc_font.render("PERK PICK INCOMING...", False, (120, 120, 180))
                screen.blit(hint_s, (WIDTH//2 - hint_s.get_width()//2, HEIGHT//2 + 25))

            # HUD panel (top-left)
            hud_bg = pygame.Surface((120, 98), pygame.SRCALPHA)
            hud_bg.fill((0, 0, 0, 120))
            screen.blit(hud_bg, (8, 6))
            pygame.draw.rect(screen, (50, 50, 70), (8, 6, 120, 98), 1)

            draw_text_shadow(screen, f"CR: {gold}", title_font, (255, 215, 0), (14, 9))
            if platinum_records > 0:
                screen.blit(skin_desc_font.render(f"PLAT x{platinum_records}", False, (200, 180, 255)), (14, 22))

            combo_color = (255, 60, 60) if combo_timer > 180 else (0, 220, 255)
            combo_str = f"x{combo}{'!' if combo >= 20 else ''}"
            draw_text_shadow(screen, f"COMBO {combo_str}", title_font, combo_color, (14, 34))

            # HP bar
            health_pct = max(0.0, player_hp / player_max_hp)
            hp_col = (int(255*(1-health_pct)), int(220*health_pct), 0)
            screen.blit(skin_desc_font.render("HP", False, (200, 80, 80)), (14, 50))
            pygame.draw.rect(screen, (30, 8, 8), (30, 51, 94, 8))
            if beat_shield_active or wave_shield_active:
                pygame.draw.rect(screen, (80, 180, 255), (30, 51, 94, 8))
            else:
                pygame.draw.rect(screen, hp_col, (30, 51, int(94 * health_pct), 8))
            pygame.draw.rect(screen, (100, 40, 40), (30, 51, 94, 8), 1)

            # Overdrive bar
            od_label = "OD" if not overdrive_active else "ACTIVE"
            od_label_col = (255, 255, 255) if overdrive_active else (140, 60, 255)
            screen.blit(skin_desc_font.render(od_label, False, od_label_col), (14, 64))
            pygame.draw.rect(screen, (20, 10, 35), (30, 65, 94, 8))
            if overdrive_active:
                od_pct = overdrive_timer / 600.0
                pygame.draw.rect(screen, (220, 220, 255), (30, 65, int(94*od_pct), 8))
            else:
                od_pct = overdrive_meter / 100.0
                if od_pct > 0:
                    od_fill_col = (255, 240, 50) if overdrive_meter >= 100 else (140, 60, 255)
                    pygame.draw.rect(screen, od_fill_col, (30, 65, int(94*od_pct), 8))
            pygame.draw.rect(screen, (80, 40, 120), (30, 65, 94, 8), 1)
            if overdrive_meter >= 100.0 and not overdrive_active:
                t2 = pygame.time.get_ticks()
                if (t2 // 300) % 2 == 0:
                    screen.blit(skin_desc_font.render("SPACE!", False, (255, 240, 50)), (78, 64))

            # Wave / difficulty (bottom-left)
            diff_color = (255, 130, 255) if difficulty == "CRAZY" else ((80, 255, 120) if difficulty == "NORMAL" else (255, 80, 80))
            screen.blit(skin_desc_font.render(difficulty, False, diff_color), (14, 78))
            draw_text_shadow(screen, f"WAVE {current_wave}", title_font, (255, 255, 255), (14, 88))

            # Active run perks indicator (top-right, tiny)
            if run_perks:
                perk_str = skin_desc_font.render(f"PERKS:{len(run_perks)}", False, (160, 100, 255))
                screen.blit(perk_str, (WIDTH - perk_str.get_width() - 10, HEIGHT - 22))

            mouse_pos = pygame.mouse.get_pos()
            draw_glow_button(screen, btn_menu,  "UPGRADE", title_font, (25, 25, 45), (200, 200, 255), (80, 80, 200), hovered=btn_menu.collidepoint(mouse_pos))
            draw_glow_button(screen, btn_pause, "PAUSE",   title_font, (45, 20, 20), (255, 180, 180), (200, 60, 60),  hovered=btn_pause.collidepoint(mouse_pos))

            if menu_open:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 215))
                screen.blit(overlay, (0, 0))
                draw_panel(screen, pygame.Rect(8, 8, WIDTH-16, HEIGHT-16), bg=(14, 14, 24), border=(80, 80, 120), border_width=3)

                draw_text_shadow(screen, "UPGRADES", big_font, (255, 255, 255), (WIDTH//2 - big_font.size("UPGRADES")[0]//2, 14), offset=2)
                cr_s = title_font.render(f"CR: {gold}", False, (255, 215, 0))
                screen.blit(cr_s, (18, 18))
                draw_glow_button(screen, btn_close_menu, "X", big_font, (60, 15, 15), (255, 120, 120), (200, 40, 40), hovered=btn_close_menu.collidepoint(mouse_pos))

                for key, rect in upgrade_rects.items():
                    upg = upgrades[key]
                    is_locked = (key.startswith("mid_") and player_level < 5) or (key.startswith("hi_") and player_level < 10)
                    hov = rect.collidepoint(mouse_pos)

                    if is_locked:
                        draw_panel(screen, rect, bg=(12, 12, 16), border=(55, 55, 55))
                        screen.blit(desc_font.render(upg["name"], False, (80, 80, 80)), (rect.x + 5, rect.y + 5))
                        req = "LVL 5" if key.startswith("mid_") else "LVL 10"
                        rq = desc_font.render(f"REQ {req}", False, (200, 60, 60))
                        screen.blit(rq, (rect.right - rq.get_width() - 5, rect.y + 18))
                    else:
                        draw_panel(screen, rect, bg=(22, 22, 36) if hov else (14, 14, 26), border=upg["color"])
                        screen.blit(desc_font.render(upg["name"], False, (240, 240, 255)), (rect.x + 5, rect.y + 5))
                        screen.blit(skin_desc_font.render(upg["desc"], False, (150, 150, 180)), (rect.x + 5, rect.y + 17))
                        lvl_str = "".join(["=" if i < upg["level"] else "-" for i in range(upg["max"])])
                        screen.blit(skin_desc_font.render(lvl_str, False, upg["color"]), (rect.x + 5, rect.y + 28))
                        if upg["level"] >= upg["max"]:
                            mx = desc_font.render("MAX", False, (80, 255, 120))
                            screen.blit(mx, (rect.right - mx.get_width() - 5, rect.y + 15))
                        else:
                            cost_col = (255, 215, 0) if gold >= upg["cost"] else (180, 80, 80)
                            cs = desc_font.render(str(upg["cost"]), False, cost_col)
                            screen.blit(cs, (rect.right - cs.get_width() - 5, rect.y + 15))

            if app_state == "PAUSED":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 210))
                screen.blit(overlay, (0, 0))
                panel_rect = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 - 95, 180, 175)
                draw_panel(screen, panel_rect, bg=(14, 14, 24), border=(80, 80, 140), border_width=3)

                draw_text_shadow(screen, "PAUSED", big_font, (200, 200, 255),
                                 (WIDTH//2 - big_font.size("PAUSED")[0]//2, HEIGHT//2 - 90), offset=2)

                if run_perks:
                    rp_s = skin_desc_font.render(f"PERKS: {len(run_perks)} active", False, (140, 100, 220))
                    screen.blit(rp_s, (WIDTH//2 - rp_s.get_width()//2, HEIGHT//2 - 62))

                mp = pygame.mouse.get_pos()
                draw_glow_button(screen, btn_resume,      "RESUME",   title_font, (18, 38, 18), (180, 255, 180), (50, 200, 80),   hovered=btn_resume.collidepoint(mp))
                draw_glow_button(screen, btn_run_log,     "RUN LOG",  title_font, (18, 18, 40), (160, 160, 255), (60, 60, 200),   hovered=btn_run_log.collidepoint(mp))
                draw_glow_button(screen, btn_restart,     "RESTART",  title_font, (38, 18, 18), (255, 180, 180), (200, 50, 50),   hovered=btn_restart.collidepoint(mp))
                draw_glow_button(screen, btn_quit_to_main,"MENU",     title_font, (18, 18, 38), (180, 180, 255), (50, 50, 200),   hovered=btn_quit_to_main.collidepoint(mp))

        # --- DRAW RUN LOG ---
        elif app_state == "RUN_LOG":
            screen.blit(main_surf, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            screen.blit(overlay, (0, 0))
            draw_panel(screen, pygame.Rect(5, 5, WIDTH-10, HEIGHT-10))
            draw_text_shadow(screen, "RUN HISTORY", big_font, (200, 200, 255),
                             (WIDTH//2 - big_font.size("RUN HISTORY")[0]//2, 10), offset=2)
            draw_glow_button(screen, btn_back_run_log, "BACK", title_font,
                             (45, 15, 15), (255, 160, 160), (200, 40, 40),
                             hovered=btn_back_run_log.collidepoint(pygame.mouse.get_pos()))

            if not run_history:
                msg = title_font.render("No picks yet this run.", False, (100, 100, 140))
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 10))
            else:
                row_h = 52
                visible_area = pygame.Rect(10, 46, WIDTH-20, HEIGHT-56)
                old_clip = screen.get_clip()
                screen.set_clip(visible_area)
                max_scroll = max(0, len(run_history) * row_h - visible_area.height)
                run_log_scroll = min(run_log_scroll, max_scroll)

                for idx, entry in enumerate(run_history):
                    ry = visible_area.y + idx * row_h - run_log_scroll
                    if ry + row_h < visible_area.y or ry > visible_area.bottom:
                        continue
                    card = pygame.Rect(10, ry, WIDTH-20, row_h-4)
                    draw_panel(screen, card, bg=(16, 16, 28), border=(60, 60, 100))

                    # Wave label
                    wl = title_font.render(f"W{entry['wave']}", False, (0, 200, 255))
                    screen.blit(wl, (card.x + 4, card.y + 4))

                    # Offered options
                    ox = card.x + 35
                    for pid in entry['offered']:
                        if pid not in PERK_POOL: continue
                        p = PERK_POOL[pid]
                        picked = (pid == entry['picked'])
                        bg = (20, 35, 20) if picked else (22, 12, 22)
                        border = p["color"] if picked else (50, 50, 60)
                        pr = pygame.Rect(ox, card.y + 2, 100, row_h - 8)
                        draw_panel(screen, pr, bg=bg, border=border)

                        # Perk name fitted to card
                        use_f, fitted = fit_text(p["name"], skin_desc_font, skin_desc_font, pr.width - 6)
                        ns = use_f.render(fitted, False, (240, 240, 255) if picked else (130, 130, 150))
                        screen.blit(ns, (pr.x + 3, pr.y + 3))

                        rarity_s = skin_desc_font.render(p.get("rarity","")[0].upper(), False, RARITY_COLORS[p.get("rarity","common")])
                        screen.blit(rarity_s, (pr.x + 3, pr.y + 14))

                        if picked:
                            chk = skin_desc_font.render("PICKED", False, (80, 255, 120))
                            screen.blit(chk, (pr.x + pr.width - chk.get_width() - 3, pr.y + 3))
                        else:
                            sk = skin_desc_font.render("skipped", False, (80, 60, 80))
                            screen.blit(sk, (pr.x + pr.width - sk.get_width() - 3, pr.y + 3))

                        # Missed stat teaser
                        missed_desc = wrap_text(p["desc"], skin_desc_font, pr.width - 6)
                        if missed_desc and not picked:
                            ms = skin_desc_font.render(missed_desc[0], False, (80, 60, 80))
                            screen.blit(ms, (pr.x + 3, pr.y + 26))

                        ox += 104

                screen.set_clip(old_clip)

                # Scroll indicator
                if max_scroll > 0:
                    pct = run_log_scroll / max_scroll
                    bar_h = max(20, int(visible_area.height * visible_area.height / (len(run_history) * row_h)))
                    bar_y = visible_area.y + int((visible_area.height - bar_h) * pct)
                    pygame.draw.rect(screen, (60, 60, 100), (WIDTH-8, visible_area.y, 4, visible_area.height))
                    pygame.draw.rect(screen, (120, 120, 200), (WIDTH-8, bar_y, 4, bar_h))

            # Active perks summary at bottom
            if run_perks:
                summary_y = HEIGHT - 14
                perk_counts = {}
                for p in run_perks:
                    perk_counts[p] = perk_counts.get(p, 0) + 1
                parts = [f"{PERK_POOL[p]['name']}{'x'+str(c) if c>1 else ''}" for p,c in perk_counts.items() if p in PERK_POOL]
                summary = skin_desc_font.render("ACTIVE: " + ", ".join(parts[:6]), False, (100, 100, 160))
                screen.blit(summary, (8, summary_y))

        # --- DRAW OPTIONS MENU ---
        elif app_state == "OPTIONS":
            screen.blit(main_surf, (0, 0))
            
            title_text = big_font.render("OPTIONS", False, (255, 255, 255))
            screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 15))
            
            c_back = (100, 60, 60) if btn_back_opt.collidepoint(pygame.mouse.get_pos()) else (80, 40, 40)
            draw_button_centered(screen, btn_back_opt, "BACK", title_font, c_back, (255, 255, 255))
            
            mon_lbl = title_font.render("MONITOR SELECT", False, (200, 200, 200))
            screen.blit(mon_lbl, (WIDTH//2 - mon_lbl.get_width()//2, 65))
            
            c_prev = (80, 100, 80) if btn_mon_prev.collidepoint(pygame.mouse.get_pos()) else (60, 80, 60)
            draw_button_centered(screen, btn_mon_prev, "<", title_font, c_prev, (255, 255, 255))
            
            mon_txt = title_font.render(f"DISPLAY {current_mon_idx + 1}", False, (255, 255, 255))
            screen.blit(mon_txt, (WIDTH//2 - mon_txt.get_width()//2, 95))
            
            c_next = (80, 100, 80) if btn_mon_next.collidepoint(pygame.mouse.get_pos()) else (60, 80, 60)
            draw_button_centered(screen, btn_mon_next, ">", title_font, c_next, (255, 255, 255))

            snap_lbl = title_font.render("CORNER SNAP", False, (200, 200, 200))
            screen.blit(snap_lbl, (WIDTH//2 - snap_lbl.get_width()//2, 130))
            
            for i, q_rect in enumerate(quad_rects):
                color = (0, 200, 255) if snap_quad == i else (100, 100, 100)
                pygame.draw.rect(screen, (30, 30, 40), q_rect)
                pygame.draw.rect(screen, color, q_rect, 2)
                
                dx, dy = 0, 0
                if i == 0: dx, dy = 10, 10
                elif i == 1: dx, dy = qw - 10, 10
                elif i == 2: dx, dy = 10, qh - 10
                elif i == 3: dx, dy = qw - 10, qh - 10
                pygame.draw.rect(screen, color, (q_rect.x + dx - 3, q_rect.y + dy - 3, 6, 6))

        # --- DRAW DIFFICULTY SELECT ---
        elif app_state == "DIFF_SELECT":
            screen.blit(main_surf, (0, 0))
            mouse_pos = pygame.mouse.get_pos()
            draw_panel(screen, pygame.Rect(5, 5, WIDTH-10, HEIGHT-10))
            draw_text_shadow(screen, "SELECT MODE", big_font, (255, 255, 255), (WIDTH//2 - big_font.size("SELECT MODE")[0]//2, 15), offset=2)
            draw_glow_button(screen, btn_back_diff, "BACK", title_font, (45, 15, 15), (255, 160, 160), (200, 40, 40), hovered=btn_back_diff.collidepoint(mouse_pos))

            hov_n = btn_diff_normal.collidepoint(mouse_pos)
            draw_panel(screen, btn_diff_normal, bg=(20, 35, 20) if hov_n else (12, 25, 12), border=(80, 220, 80))
            draw_text_shadow(screen, "NORMAL", title_font, (100, 255, 100), (btn_diff_normal.x + 8, btn_diff_normal.y + 6))
            draw_text_in_rect(screen, "Keep upgrades on death. Lose 25% gold.", skin_desc_font, (160, 210, 160), btn_diff_normal, y_start=22)

            hov_h = btn_diff_hard.collidepoint(mouse_pos)
            draw_panel(screen, btn_diff_hard, bg=(35, 12, 12) if hov_h else (25, 8, 8), border=(220, 60, 60))
            draw_text_shadow(screen, "HARD", title_font, (255, 80, 80), (btn_diff_hard.x + 8, btn_diff_hard.y + 6))
            draw_text_in_rect(screen, "Lose ALL upgrades & credits on death.", skin_desc_font, (210, 140, 140), btn_diff_hard, y_start=22)

            hov_c = btn_diff_crazy.collidepoint(mouse_pos)
            draw_panel(screen, btn_diff_crazy, bg=(35, 12, 50) if hov_c else (22, 8, 35), border=(220, 80, 255))
            draw_text_shadow(screen, "VIDEO MODE", title_font, (255, 130, 255), (btn_diff_crazy.x + 8, btn_diff_crazy.y + 6))
            draw_text_in_rect(screen, "Max upgrades. Instant overdrive. No death.", skin_desc_font, (210, 170, 255), btn_diff_crazy, y_start=22)

        # --- DRAW WAVE REWARD (ROGUELIKE PERK PICK) ---
        elif app_state == "WAVE_REWARD":
            screen.blit(main_surf, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            t = pygame.time.get_ticks() / 1000.0
            pulse = int(200 + 55 * math.sin(t * 3))
            draw_text_shadow(screen, f"WAVE {current_wave} CLEARED!", big_font, (0, pulse, 255), (WIDTH//2 - 95, 15), offset=2)

            sub = title_font.render("CHOOSE A PERK", False, (255, 215, 0))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 52))

            vr_surf = desc_font.render(f"+ {vinyls_just_earned} VINYLS", False, (200, 200, 100))
            screen.blit(vr_surf, (WIDTH//2 - vr_surf.get_width()//2, 70))

            mouse_pos = pygame.mouse.get_pos()
            for i, wr_rect in enumerate(wave_reward_rects):
                if i >= len(wave_reward_options): break
                perk_id = wave_reward_options[i]
                perk = PERK_POOL[perk_id]
                hovered = wr_rect.collidepoint(mouse_pos)
                rarity = perk.get("rarity", "common")
                r_color = RARITY_COLORS[rarity]
                already_have = perk_id in run_perks

                draw_panel(screen, wr_rect, bg=(18, 14, 28) if not hovered else (28, 22, 42), border=perk["color"])
                if hovered:
                    glow_surf = pygame.Surface((wr_rect.width + 8, wr_rect.height + 8), pygame.SRCALPHA)
                    glow_surf.fill((*perk["color"], 40))
                    screen.blit(glow_surf, (wr_rect.x - 4, wr_rect.y - 4))

                # Rarity badge (skin_desc_font so it fits)
                r_label = skin_desc_font.render(rarity.upper(), False, r_color)
                screen.blit(r_label, (wr_rect.x + (wr_rect.width - r_label.get_width())//2, wr_rect.y + 5))

                # Perk name — wrap to card width using title_font; fall back to desc_font if still too wide
                inner_w = wr_rect.width - 8
                name_lines = wrap_text(perk["name"], title_font, inner_w)
                # If even a single word overflows title_font, use desc_font
                if any(title_font.size(ln)[0] > inner_w for ln in name_lines):
                    name_lines = wrap_text(perk["name"], desc_font, inner_w)
                    name_font = desc_font
                else:
                    name_font = title_font
                ny = wr_rect.y + 17
                for ln in name_lines[:2]:  # max 2 lines for name
                    ns = name_font.render(ln, False, (240, 240, 255))
                    screen.blit(ns, (wr_rect.x + (wr_rect.width - ns.get_width())//2, ny))
                    ny += name_font.size("A")[1] + 1

                # Perk icon color dot
                dot_y = wr_rect.y + 56
                pygame.draw.circle(screen, perk["color"], (wr_rect.x + wr_rect.width//2, dot_y), 9)
                pygame.draw.circle(screen, (255, 255, 255), (wr_rect.x + wr_rect.width//2, dot_y), 9, 1)

                # Description — always wrapped with skin_desc_font
                desc_lines = wrap_text(perk["desc"], skin_desc_font, inner_w)
                dy = dot_y + 13
                for ln in desc_lines[:3]:  # max 3 lines
                    ds = skin_desc_font.render(ln, False, (170, 170, 195))
                    screen.blit(ds, (wr_rect.x + (wr_rect.width - ds.get_width())//2, dy))
                    dy += skin_desc_font.size("A")[1] + 1

                if already_have:
                    dup = skin_desc_font.render("STACKS!", False, (255, 200, 50))
                    screen.blit(dup, (wr_rect.x + (wr_rect.width - dup.get_width())//2, wr_rect.y + wr_rect.height - 10))

            # Show active run perks at bottom
            if run_perks:
                perk_label = skin_desc_font.render("ACTIVE: " + ", ".join(PERK_POOL[p]["name"] for p in run_perks), False, (120, 120, 160))
                screen.blit(perk_label, (5, HEIGHT - 12))

        # --- DRAW CHARMS MENU ---
        elif app_state == "CHARMS":
            screen.blit(main_surf, (0, 0))
            mouse_pos = pygame.mouse.get_pos()

            draw_text_shadow(screen, "EQUIP CHARMS", big_font, (0, 220, 255), (WIDTH//2 - big_font.size("EQUIP CHARMS")[0]//2, 10), offset=2)
            draw_glow_button(screen, btn_back_charms, "BACK", title_font, (45, 15, 15), (255, 160, 160), (200, 40, 40), hovered=btn_back_charms.collidepoint(mouse_pos))

            slots = get_max_charm_slots()
            slot_text = title_font.render(f"SLOTS: {len(equipped_charms)}/{slots}", False, (255, 215, 0))
            screen.blit(slot_text, (WIDTH//2 - slot_text.get_width()//2, 40))
            hint = skin_desc_font.render("Kill GHOSTS to unlock charms", False, (80, 80, 120))
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 55))

            charm_list_rects.clear()
            charm_items = list(ALL_CHARMS.items())
            visible_rows = 5
            row_h = 40
            cy_start = 68
            col_w = 185

            # Clip rendering to charm area
            clip_rect = pygame.Rect(0, cy_start - 2, WIDTH - 35, visible_rows * row_h + 4)
            old_clip = screen.get_clip()
            screen.set_clip(clip_rect)

            for idx, (charm_id, data) in enumerate(charm_items):
                row = idx // 2
                col = idx % 2
                if row < charm_scroll_offset or row >= charm_scroll_offset + visible_rows:
                    charm_list_rects.append((charm_id, pygame.Rect(0, -100, 1, 1)))  # off-screen
                    continue
                cx = 8 + col * col_w
                cy = cy_start + (row - charm_scroll_offset) * row_h
                rect = pygame.Rect(cx, cy, 175, 36)
                charm_list_rects.append((charm_id, rect))
                is_unlocked = charm_id in unlocked_charms
                is_equipped = charm_id in equipped_charms

                if is_unlocked:
                    bg = (22, 40, 22) if is_equipped else (18, 18, 30)
                    draw_panel(screen, rect, bg=bg, border=data["color"])
                    if rect.collidepoint(mouse_pos):
                        glow_s = pygame.Surface((rect.width+4, rect.height+4), pygame.SRCALPHA)
                        glow_s.fill((*data["color"], 35))
                        screen.blit(glow_s, (rect.x-2, rect.y-2))
                    screen.blit(desc_font.render(data["name"], False, (240, 240, 255)), (rect.x + 5, rect.y + 4))
                    screen.blit(skin_desc_font.render(data["desc"], False, (150, 150, 180)), (rect.x + 5, rect.y + 18))
                    if is_equipped:
                        eq_s = skin_desc_font.render("ON", False, (80, 255, 120))
                        screen.blit(eq_s, (rect.right - eq_s.get_width() - 4, rect.y + 4))
                else:
                    draw_panel(screen, rect, bg=(12, 12, 18), border=(50, 50, 60))
                    lock_s = desc_font.render("LOCKED", False, (70, 70, 90))
                    screen.blit(lock_s, (rect.x + (rect.width - lock_s.get_width())//2, rect.y + 10))

            screen.set_clip(old_clip)

            # Scroll arrows
            max_scroll = max(0, math.ceil(len(ALL_CHARMS) / 2) - visible_rows)
            if charm_scroll_offset > 0:
                draw_glow_button(screen, btn_charm_scroll_up, "^", title_font, (20, 20, 35), (180, 180, 255), (80, 80, 200), hovered=btn_charm_scroll_up.collidepoint(mouse_pos))
            if charm_scroll_offset < max_scroll:
                draw_glow_button(screen, btn_charm_scroll_down, "v", title_font, (20, 20, 35), (180, 180, 255), (80, 80, 200), hovered=btn_charm_scroll_down.collidepoint(mouse_pos))

        # --- DRAW GARAGE (CHARACTER SELECT) & PRESTIGE ---
        elif app_state == "CHAR_SELECT":
            screen.blit(main_surf, (0, 0))
            
            sel_text = big_font.render("GARAGE", False, (255, 255, 255))
            screen.blit(sel_text, (WIDTH//2 - sel_text.get_width()//2, 20))
            
            vin_text = title_font.render(f"VINYLS: {vinyls}", False, (255, 215, 0))
            screen.blit(vin_text, (WIDTH//2 - vin_text.get_width()//2, 45))
            
            c_back = (100, 60, 60) if btn_back_char.collidepoint(pygame.mouse.get_pos()) else (80, 40, 40)
            draw_button_centered(screen, btn_back_char, "BACK", title_font, c_back, (255, 255, 255))
            
            c_charms = (80, 100, 150) if btn_charms_menu.collidepoint(pygame.mouse.get_pos()) else (60, 80, 120)
            draw_button_centered(screen, btn_charms_menu, "EQUIP CHARMS", title_font, c_charms, (255, 255, 255))
            
            if player_level >= 10:
                c_prest = (80, 150, 200) if btn_prestige_garage.collidepoint(pygame.mouse.get_pos()) else (60, 120, 180)
                draw_button_centered(screen, btn_prestige_garage, "PRESTIGE", title_font, c_prest, (255, 255, 255))
            else:
                draw_button_centered(screen, btn_prestige_garage, "LVL 10 REQ", title_font, (50, 50, 50), (100, 100, 100), (100, 100, 100))

            c_basic = (80, 100, 80) if selected_skin == "basic" else ((60, 60, 80) if btn_skin_basic.collidepoint(pygame.mouse.get_pos()) else (40, 40, 60))
            pygame.draw.rect(screen, c_basic, btn_skin_basic)
            pygame.draw.rect(screen, (200, 200, 200), btn_skin_basic, 4)
            draw_card_text_centered(screen, btn_skin_basic, "BASIC", desc_font, (255, 255, 255), 10)
            draw_card_text_centered(screen, btn_skin_basic, "2x HP Regen", skin_desc_font, (100, 255, 100), 35)
            draw_card_text_centered(screen, btn_skin_basic, "EQUIP" if selected_skin == "basic" else "OWNED", desc_font, (100, 255, 100), 60)

            c_silver = (80, 100, 80) if selected_skin == "silver" else ((60, 60, 80) if btn_skin_silver.collidepoint(pygame.mouse.get_pos()) else (40, 40, 60))
            pygame.draw.rect(screen, c_silver, btn_skin_silver)
            pygame.draw.rect(screen, (192, 192, 192), btn_skin_silver, 4)
            draw_card_text_centered(screen, btn_skin_silver, "SILVER", desc_font, (255, 255, 255), 10)
            draw_card_text_centered(screen, btn_skin_silver, "Slows Enemy", skin_desc_font, (100, 255, 255), 35)
            if skins["silver"]: draw_card_text_centered(screen, btn_skin_silver, "EQUIP" if selected_skin == "silver" else "OWNED", desc_font, (100, 255, 100), 60)
            else: draw_card_text_centered(screen, btn_skin_silver, "10 VNL", desc_font, (255, 215, 0) if vinyls >= 10 else (255, 100, 100), 60)

            c_gold = (80, 100, 80) if selected_skin == "gold" else ((60, 60, 80) if btn_skin_gold.collidepoint(pygame.mouse.get_pos()) else (40, 40, 60))
            pygame.draw.rect(screen, c_gold, btn_skin_gold)
            pygame.draw.rect(screen, (255, 215, 0), btn_skin_gold, 4)
            draw_card_text_centered(screen, btn_skin_gold, "GOLD", desc_font, (255, 255, 255), 10)
            draw_card_text_centered(screen, btn_skin_gold, "Sonic Nova", skin_desc_font, (255, 200, 50), 35)
            if skins["gold"]: draw_card_text_centered(screen, btn_skin_gold, "EQUIP" if selected_skin == "gold" else "OWNED", desc_font, (100, 255, 100), 60)
            else: draw_card_text_centered(screen, btn_skin_gold, "50 VNL", desc_font, (255, 215, 0) if vinyls >= 50 else (255, 100, 100), 60)

            c_neon = (80, 100, 80) if selected_skin == "neon" else ((60, 60, 80) if btn_skin_neon.collidepoint(pygame.mouse.get_pos()) else (40, 40, 60))
            pygame.draw.rect(screen, c_neon, btn_skin_neon)
            pygame.draw.rect(screen, (255, 50, 255), btn_skin_neon, 4)
            draw_card_text_centered(screen, btn_skin_neon, "NEON", desc_font, (255, 255, 255), 10)
            draw_card_text_centered(screen, btn_skin_neon, "Rapid Fire", skin_desc_font, (255, 100, 255), 35)
            if skins["neon"]: draw_card_text_centered(screen, btn_skin_neon, "EQUIP" if selected_skin == "neon" else "OWNED", desc_font, (100, 255, 100), 60)
            else: draw_card_text_centered(screen, btn_skin_neon, "20 VNL", desc_font, (255, 215, 0) if vinyls >= 20 else (255, 100, 100), 60)

            c_diamond = (80, 100, 80) if selected_skin == "diamond" else ((60, 60, 80) if btn_skin_diamond.collidepoint(pygame.mouse.get_pos()) else (40, 40, 60))
            pygame.draw.rect(screen, c_diamond, btn_skin_diamond)
            pygame.draw.rect(screen, (100, 255, 255), btn_skin_diamond, 4)
            draw_card_text_centered(screen, btn_skin_diamond, "DIAMOND", desc_font, (255, 255, 255), 10)
            draw_card_text_centered(screen, btn_skin_diamond, "2x Dmg,+Gold", skin_desc_font, (100, 255, 255), 35)
            if skins["diamond"]: draw_card_text_centered(screen, btn_skin_diamond, "EQUIP" if selected_skin == "diamond" else "OWNED", desc_font, (100, 255, 100), 60)
            else: draw_card_text_centered(screen, btn_skin_diamond, "100 VNL", desc_font, (255, 215, 0) if vinyls >= 100 else (255, 100, 100), 60)

            # --- NEW WORKSHOP BUTTON ---
            c_work = (80, 100, 80) if selected_skin == "workshop" else ((60, 60, 80) if btn_skin_workshop.collidepoint(pygame.mouse.get_pos()) else (40, 40, 60))
            pygame.draw.rect(screen, c_work, btn_skin_workshop)
            pygame.draw.rect(screen, (255, 255, 255), btn_skin_workshop, 4)
            draw_card_text_centered(screen, btn_skin_workshop, "WORKSHOP", desc_font, (255, 255, 255), 10)
            draw_card_text_centered(screen, btn_skin_workshop, "Custom PNG", skin_desc_font, (200, 200, 200), 35)
            if skins["workshop"]: draw_card_text_centered(screen, btn_skin_workshop, "EQUIP" if selected_skin == "workshop" else "OWNED", desc_font, (100, 255, 100), 60)
            else: draw_card_text_centered(screen, btn_skin_workshop, "EMPTY", desc_font, (150, 150, 150), 60)

        # --- DRAW MAIN MENU ---
        elif app_state == "MAIN_MENU":
            screen.blit(main_surf, (0, 0))
            mouse_pos = pygame.mouse.get_pos()
            t = pygame.time.get_ticks() / 1000.0

            # Animated title glow
            glow_val = int(180 + 75 * math.sin(t * 2.5))
            glow_surf = pygame.Surface((WIDTH, 28), pygame.SRCALPHA)
            glow_surf.fill((0, glow_val // 4, glow_val // 2, 30))
            screen.blit(glow_surf, (0, HEIGHT//2 - 118))

            draw_text_shadow(screen, "BEAT BARRAGE", big_font, (glow_val, glow_val, 255),
                             (WIDTH//2 - big_font.size("BEAT BARRAGE")[0]//2, HEIGHT//2 - 115),
                             shadow_color=(0, 0, 80), offset=2)

            tagline = skin_desc_font.render("MUSIC-REACTIVE IDLE DEFENDER", False, (100, 100, 160))
            screen.blit(tagline, (WIDTH//2 - tagline.get_width()//2, HEIGHT//2 - 96))

            if platinum_records > 0:
                plat_text = title_font.render(f"PLATINUM x{platinum_records}", False, (200, 180, 255))
                screen.blit(plat_text, (WIDTH//2 - plat_text.get_width()//2, HEIGHT//2 - 83))

            draw_glow_button(screen, btn_continue, "CONTINUE", title_font, (22, 45, 22), (200, 255, 200), (50, 200, 80), hovered=btn_continue.collidepoint(mouse_pos))
            draw_glow_button(screen, btn_new_game, "NEW GAME",  title_font, (40, 40, 20), (255, 255, 180), (200, 200, 50), hovered=btn_new_game.collidepoint(mouse_pos))
            draw_glow_button(screen, btn_options,  "OPTIONS",   title_font, (20, 20, 45), (180, 180, 255), (60, 60, 200),  hovered=btn_options.collidepoint(mouse_pos))
            draw_glow_button(screen, btn_char_select, "GARAGE", title_font, (40, 25, 10), (255, 210, 150), (180, 120, 40), hovered=btn_char_select.collidepoint(mouse_pos))
            draw_glow_button(screen, btn_quit_main, "QUIT",     title_font, (45, 15, 15), (255, 160, 160), (200, 40, 40),  hovered=btn_quit_main.collidepoint(mouse_pos))

            # XP bar
            xp_req = get_xp_requirement(player_level)
            xp_pct = player_xp / xp_req
            bar_w, bar_x, bar_y = 80, 15, 26
            draw_text_shadow(screen, f"LVL {player_level}", desc_font, (0, 220, 255), (bar_x, bar_y - 13))
            pygame.draw.rect(screen, (25, 25, 35), (bar_x, bar_y, bar_w, 7))
            pygame.draw.rect(screen, (60, 60, 90), (bar_x, bar_y, bar_w, 7), 1)
            if xp_pct > 0:
                pygame.draw.rect(screen, (0, 180, 255), (bar_x+1, bar_y+1, int((bar_w-2)*xp_pct), 5))

            # Vinyl display
            vinyl_display = title_font.render(f"VNL:{vinyls}", False, (255, 215, 0))
            vinyl_rect = vinyl_display.get_rect(topright=(WIDTH - 15, 15))
            screen.blit(vinyl_display, vinyl_rect)
            if vinyl_rect.collidepoint(mouse_pos):
                tip = desc_font.render("Earned per wave", False, (220, 220, 220))
                tt = tip.get_rect(topright=(WIDTH - 15, 30))
                draw_panel(screen, tt.inflate(8, 8))
                screen.blit(tip, tt)

        # --- GLOBAL WINDOW FRAME ---
        border_color = (80, 80, 100) 
        if overdrive_active: border_color = (255, 255, 255)
        pygame.draw.rect(screen, border_color, (0, 0, WIDTH, HEIGHT), 2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

except Exception as e:
    print("\n" + "="*60)
    print(" FATAL CRASH DETECTED ")
    print("="*60)
    traceback.print_exc()
    print("="*60)
    input("Press ENTER to close this window...")