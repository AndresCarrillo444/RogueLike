import pygame
import numpy as np
import math
import random
import json
import os
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from abc import ABC, abstractmethod

SCREEN_W, SCREEN_H = 1280, 720
FPS   = 60
TITLE = "COSMIC ROGUELIKE v3.0"

BLACK     = (0,   0,   0)
WHITE     = (255, 255, 255)
CYAN      = (0,   200, 235)
CYAN_DIM  = (0,   100, 140)
GREEN     = (0,   220, 100)
RED       = (230, 50,  50)
RED_DIM   = (120, 15,  15)
ORANGE    = (230, 120, 0)
PURPLE    = (160, 0,   230)
YELLOW    = (230, 200, 0)
DARK_BLUE = (3,   6,   18)
NEON_BLUE = (20,  60,  220)
GRAY      = (65,  65,  85)
DARK_GRAY = (22,  22,  35)
SILVER    = (160, 170, 180)
DEEP_RED  = (90,  0,   0)
TEAL      = (0,   180, 150)
LIME      = (140, 230, 0)

MAX_SPEED_PLAYER = 6.0
MAX_SPEED_ENEMY  = 3.0
BULLET_SPEED     = 15.0
BULLET_POOL_SIZE = 400
ENEMY_POOL_SIZE  = 120

WORLD_W, WORLD_H = 5120, 5120
SECTOR_SIZE      = 512
ASTEROID_DENSITY_BASE = 0.70

QT_MAX_OBJECTS = 8
QT_MAX_LEVELS  = 6

W_SEPARATION  = 1.8
W_ALIGNMENT   = 1.0
W_COHESION    = 0.9
W_SEEK_PLAYER = 0.5
NEIGHBOR_DIST = 120.0
SEP_DIST      = 45.0

DETECT_DIST = 350.0
ATTACK_DIST = 200.0
FLEE_HEALTH = 0.25

XP_PER_SCOUT    = 40
XP_PER_FIGHTER  = 80
XP_PER_HEAVY    = 130
XP_PER_SNIPER   = 100
XP_PER_KAMIKAZE = 60
XP_PER_CARRIER  = 200
XP_PER_BOSS     = 350
XP_BASE         = 120
XP_SCALE        = 1.35

GAMEMODE_CLASSIC    = "Clásico"
GAMEMODE_SURVIVAL   = "Supervivencia"
GAMEMODE_TIMEATTACK = "Contrarreloj"


class ResourceManager:
    _instance: Optional["ResourceManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._fonts: Dict[str, pygame.font.Font] = {}

    def get_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = f"{size}_{bold}"
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont("consolas", size, bold=bold)
        return self._fonts[key]


class SoundManager:
    _instance: Optional["SoundManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._music:  Dict[str, pygame.mixer.Sound] = {}
        self._muted        = False
        self._music_muted  = False
        self._vol_sfx      = 0.55
        self._vol_music    = 0.38
        self._current_track: Optional[str] = None
        self._music_channel: Optional[pygame.mixer.Channel] = None
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self._build_sounds()
            self._build_music()
            self._music_channel = pygame.mixer.Channel(15)
            self._ok = True
        except Exception:
            self._ok = False

    def _synth(self, samples: np.ndarray, vol: float = 0.5) -> pygame.mixer.Sound:
        samples = np.clip(samples, -1.0, 1.0)
        data    = (samples * 32767 * vol).astype(np.int16)
        stereo  = np.column_stack([data, data])
        return pygame.sndarray.make_sound(stereo)

    def _build_sounds(self):
        sr = 44100

        def env(length, attack=0.01, decay=0.1, sustain=0.6, release=0.2):
            n  = int(sr * length)
            a  = int(sr * attack * length)
            d  = int(sr * decay  * length)
            s  = int(sr * sustain* length)
            r  = n - a - d - s
            e  = np.zeros(n)
            if a: e[:a]           = np.linspace(0, 1, a)
            if d: e[a:a+d]        = np.linspace(1, 0.6, d)
            if s: e[a+d:a+d+s]    = 0.6
            if r > 0: e[a+d+s:]   = np.linspace(0.6, 0, max(r,1))
            return e

        t_shoot = np.linspace(0, 0.12, int(sr*0.12))
        freq_shoot = np.linspace(1200, 400, len(t_shoot))
        wave_shoot = np.sin(2*np.pi * np.cumsum(freq_shoot)/sr)
        noise_shoot = np.random.uniform(-0.3, 0.3, len(t_shoot))
        shoot_env = env(0.12, 0.005, 0.05, 0.3, 0.6)
        self._sounds["player_shoot"] = self._synth((wave_shoot*0.7 + noise_shoot*0.3) * shoot_env, 0.4)

        t_es = np.linspace(0, 0.18, int(sr*0.18))
        f_es = np.linspace(600, 180, len(t_es))
        wave_es = np.sin(2*np.pi * np.cumsum(f_es)/sr)
        noise_es = np.random.uniform(-0.4, 0.4, len(t_es))
        es_env = env(0.18, 0.01, 0.08, 0.4, 0.5)
        self._sounds["enemy_shoot"] = self._synth((wave_es*0.6 + noise_es*0.4) * es_env, 0.3)

        n_exp = int(sr * 0.55)
        noise_exp = np.random.uniform(-1, 1, n_exp)
        t_exp  = np.linspace(0, 1, n_exp)
        low    = np.sin(2*np.pi*60*t_exp) * np.exp(-t_exp*6)
        mid    = np.sin(2*np.pi*180*t_exp) * np.exp(-t_exp*10)
        exp_env= np.exp(-t_exp*5)
        self._sounds["explosion"] = self._synth((noise_exp*0.6 + low*0.25 + mid*0.15) * exp_env, 0.7)

        n_be = int(sr * 0.3)
        noise_be = np.random.uniform(-1, 1, n_be)
        t_be   = np.linspace(0, 1, n_be)
        low_be = np.sin(2*np.pi*40*t_be) * np.exp(-t_be*8)
        be_env = np.exp(-t_be*9)
        self._sounds["explosion_small"] = self._synth((noise_be*0.5 + low_be*0.5) * be_env, 0.45)

        n_bexp = int(sr * 0.9)
        noise_bexp = np.random.uniform(-1, 1, n_bexp)
        t_bexp = np.linspace(0, 1, n_bexp)
        sub    = np.sin(2*np.pi*30*t_bexp) * np.exp(-t_bexp*3)
        lo     = np.sin(2*np.pi*80*t_bexp) * np.exp(-t_bexp*5)
        bexp_env = np.exp(-t_bexp*3)
        self._sounds["explosion_boss"] = self._synth((noise_bexp*0.5 + sub*0.3 + lo*0.2) * bexp_env, 0.9)

        n_hit = int(sr * 0.08)
        t_hit = np.linspace(0, 1, n_hit)
        freq_hit = np.linspace(800, 300, n_hit)
        wave_hit = np.sin(2*np.pi * np.cumsum(freq_hit)/sr)
        hit_env  = np.exp(-t_hit*25)
        self._sounds["player_hit"] = self._synth(wave_hit * hit_env, 0.6)

        n_lup = int(sr * 0.7)
        t_lup = np.linspace(0, 1, n_lup)
        freqs = [523, 659, 784, 1047]
        wave_lup = np.zeros(n_lup)
        seg = n_lup // len(freqs)
        for i, f in enumerate(freqs):
            s2 = i*seg; e2 = s2+seg
            tt = np.linspace(0, seg/sr, seg)
            fade = np.linspace(0,1,seg//4)
            senv = np.ones(seg)
            senv[:seg//4] = fade
            wave_lup[s2:e2] = np.sin(2*np.pi*f*tt) * senv
        lup_env = np.exp(-t_lup*1.5)
        self._sounds["level_up"] = self._synth(wave_lup * lup_env, 0.5)

        n_upg = int(sr * 0.35)
        t_upg = np.linspace(0, 1, n_upg)
        f1 = np.sin(2*np.pi*440*t_upg)
        f2 = np.sin(2*np.pi*660*t_upg)
        upg_env = np.exp(-t_upg*5)
        self._sounds["skill_upgrade"] = self._synth((f1*0.5+f2*0.5)*upg_env, 0.4)

        n_thr = int(sr * 0.25)
        t_thr = np.linspace(0, 1, n_thr)
        noise_thr = np.random.uniform(-1, 1, n_thr)
        lo_thr = np.sin(2*np.pi*80*t_thr)
        thr_env = np.exp(-t_thr*8) * np.exp(-t_thr*1)
        self._sounds["thrust"] = self._synth((noise_thr*0.4+lo_thr*0.6)*thr_env, 0.15)

        n_ast = int(sr * 0.2)
        noise_ast = np.random.uniform(-1, 1, n_ast)
        t_ast = np.linspace(0, 1, n_ast)
        lo_ast = np.sin(2*np.pi*120*t_ast) * np.exp(-t_ast*12)
        ast_env = np.exp(-t_ast*12)
        self._sounds["asteroid_hit"] = self._synth((noise_ast*0.6+lo_ast*0.4)*ast_env, 0.35)

        n_warn = int(sr * 0.4)
        t_warn = np.linspace(0, 1, n_warn)
        beep1  = np.sin(2*np.pi*880*t_warn) * np.exp(-t_warn*8)
        beep2  = np.sin(2*np.pi*660*np.linspace(0,1,n_warn)) * np.exp(-t_warn*8)
        w_env  = np.zeros(n_warn)
        half   = n_warn//2
        w_env[:half] = np.exp(-np.linspace(0,1,half)*8)
        w_env[half:] = np.exp(-np.linspace(0,1,n_warn-half)*8)
        self._sounds["boss_warning"] = self._synth((beep1+beep2)*0.5*w_env, 0.55)

        n_km = int(sr * 0.15)
        t_km = np.linspace(0, 1, n_km)
        f_km = np.linspace(2000, 200, n_km)
        wave_km = np.sin(2*np.pi * np.cumsum(f_km)/sr)
        km_env = np.exp(-t_km*10)
        self._sounds["kamikaze_boom"] = self._synth(wave_km * km_env, 0.5)

        n_click = int(sr * 0.06)
        t_click = np.linspace(0, 1, n_click)
        f_click = np.linspace(1800, 900, n_click)
        wave_click = np.sin(2*np.pi * np.cumsum(f_click)/sr)
        click_env = np.exp(-t_click*30)
        self._sounds["ui_click"] = self._synth(wave_click * click_env, 0.3)

        n_whoosh = int(sr * 0.5)
        noise_w = np.random.uniform(-1, 1, n_whoosh)
        t_w  = np.linspace(0, 1, n_whoosh)
        f_lo = np.sin(2*np.pi*40*t_w)
        w_env = np.exp(-t_w*2) * np.linspace(0, 1, n_whoosh)**0.3
        self._sounds["titan_spawn"] = self._synth((noise_w*0.4+f_lo*0.6)*w_env, 0.8)

        # warp / hyperspace jump sound  (~3.2 s)
        warp_dur = 3.2
        nw  = int(sr * warp_dur)
        tw  = np.linspace(0, 1, nw)
        # rising frequency sweep  80 Hz → 3200 Hz
        f_sweep = np.exp(np.linspace(np.log(80), np.log(3200), nw))
        wave_sweep = np.sin(2*np.pi * np.cumsum(f_sweep) / sr)
        # layered harmonics that diverge
        h2 = np.sin(2*np.pi * np.cumsum(f_sweep * 1.5) / sr) * 0.4
        h3 = np.sin(2*np.pi * np.cumsum(f_sweep * 0.5) / sr) * 0.3
        # white-noise rush that builds and fades
        noise_warp = np.random.uniform(-1, 1, nw)
        noise_env  = np.concatenate([
            np.linspace(0, 1,  int(nw*0.55)),
            np.linspace(1, 0,  nw - int(nw*0.55))
        ])
        # sub-bass thump at start
        sub_thump  = np.sin(2*np.pi*45*tw) * np.exp(-tw*6)
        # master envelope: fast attack, sustain, quick fade at end
        warp_env = np.concatenate([
            np.linspace(0, 1, int(nw*0.08)),
            np.ones(int(nw*0.72)),
            np.linspace(1, 0, nw - int(nw*0.08) - int(nw*0.72))
        ])
        warp_mix = ((wave_sweep + h2 + h3)*0.45 +
                    noise_warp*noise_env*0.35 +
                    sub_thump*0.20) * warp_env
        self._sounds["warp"] = self._synth(warp_mix, 0.75)

    def _build_music(self):
        sr   = 44100
        bpm  = 72
        beat = 60.0 / bpm

        def make_sound(samples, vol=0.5):
            samples = np.clip(samples, -1.0, 1.0)
            data    = (samples * 32767 * vol).astype(np.int16)
            stereo  = np.column_stack([data, data])
            return pygame.sndarray.make_sound(stereo)

        def adsr(n, a_frac=0.05, d_frac=0.1, s_lev=0.7, r_frac=0.2):
            env = np.ones(n) * s_lev
            a = max(1, int(n * a_frac)); d = max(1, int(n * d_frac)); r = max(1, int(n * r_frac))
            env[:a]  = np.linspace(0, 1, a)
            env[a:a+d] = np.linspace(1, s_lev, d)
            env[max(0,n-r):] = np.linspace(s_lev, 0, min(r, n))
            return env

        def osc(freq, n, wave='sin', detune=0.0):
            t = np.arange(n) / sr
            if wave == 'sin':
                return np.sin(2*np.pi*freq*t) + detune*np.sin(2*np.pi*freq*1.005*t)
            elif wave == 'saw':
                return 2*(t*freq % 1) - 1
            elif wave == 'sq':
                return np.sign(np.sin(2*np.pi*freq*t))
            elif wave == 'tri':
                return 2*np.abs(2*(t*freq % 1) - 1) - 1
            return np.sin(2*np.pi*freq*t)

        def reverb(sig, delay_s=0.06, decay=0.35, n_taps=5):
            out = sig.copy().astype(np.float64)
            d   = int(delay_s * sr)
            for i in range(1, n_taps+1):
                shift = d * i
                if shift < len(sig):
                    out[shift:] += sig[:-shift] * (decay ** i)
            return np.clip(out, -1, 1)

        def low_pass(sig, cutoff=800, sr2=44100):
            alpha = cutoff / (cutoff + sr2 / (2*np.pi))
            out   = np.zeros_like(sig)
            out[0] = sig[0]
            for i in range(1, len(sig)):
                out[i] = out[i-1] + alpha * (sig[i] - out[i-1])
            return out

        # ── MENU MUSIC ── ethereal space ambient, 24s loop ──────────────────
        menu_dur = 24.0
        mn       = int(sr * menu_dur)
        t_m      = np.arange(mn) / sr

        base_pad  = (
            0.55 * np.sin(2*np.pi*55*t_m) * np.exp(-t_m*0.015) +
            0.35 * np.sin(2*np.pi*82.5*t_m + 0.3) +
            0.20 * np.sin(2*np.pi*110*t_m) * np.sin(2*np.pi*0.12*t_m) +
            0.12 * np.sin(2*np.pi*165*t_m + 0.8)
        )
        melody_freqs = [261.6, 293.7, 329.6, 392.0, 440.0, 392.0, 329.6, 261.6]
        mel_note_dur = int(sr * menu_dur / len(melody_freqs))
        melody = np.zeros(mn)
        for i, f in enumerate(melody_freqs):
            s2 = i * mel_note_dur
            e2 = min(mn, s2 + mel_note_dur)
            n2 = e2 - s2
            t2 = np.arange(n2) / sr
            note = (0.3*np.sin(2*np.pi*f*t2) +
                    0.15*np.sin(2*np.pi*f*2*t2) +
                    0.08*np.sin(2*np.pi*f*3*t2)) * adsr(n2, 0.08, 0.15, 0.5, 0.35)
            melody[s2:e2] += note

        shimmer_freqs = [880, 1047, 1174, 1397, 1568]
        shimmer = np.zeros(mn)
        for sf in shimmer_freqs:
            phase = random.uniform(0, math.pi*2)
            amp   = 0.04 * np.sin(2*np.pi*0.18*t_m + phase)
            shimmer += amp * np.sin(2*np.pi*sf*t_m)

        lfo_vol  = 0.75 + 0.25*np.sin(2*np.pi*0.08*t_m)
        menu_raw = (base_pad*0.45 + melody*0.4 + shimmer*0.15) * lfo_vol
        fade_in  = np.ones(mn)
        fade_in[:int(sr*2.5)] = np.linspace(0, 1, int(sr*2.5))
        fade_out = np.ones(mn)
        fade_out[int(sr*(menu_dur-3)):] = np.linspace(1, 0, mn - int(sr*(menu_dur-3)))
        menu_raw *= fade_in * fade_out
        menu_raw  = reverb(menu_raw, 0.08, 0.45, 6)
        self._music["menu"] = make_sound(menu_raw, 0.55)

        # ── CLASSIC GAME MUSIC ── space electronic, moderate drive, 20s loop ─
        clas_dur = 20.0
        cn       = int(sr * clas_dur)
        t_c      = np.arange(cn) / sr

        bass_notes = [55, 55, 65.4, 65.4, 73.4, 73.4, 55, 49]
        bass_beat  = int(sr * beat)
        bass_line  = np.zeros(cn)
        for i, bn in enumerate(bass_notes):
            s2 = i * bass_beat * 2
            if s2 >= cn: break
            nb = min(cn - s2, bass_beat * 2)
            tb = np.arange(nb) / sr
            note = (0.6*osc(bn, nb, 'saw') + 0.3*osc(bn*2, nb, 'sq')) * adsr(nb, 0.01, 0.1, 0.55, 0.3)
            note = low_pass(note, 400)
            bass_line[s2:s2+nb] += note

        arp_notes   = [220, 277.2, 329.6, 415.3, 329.6, 277.2, 220, 164.8]
        arp_note_dur = int(sr * beat * 0.9)
        arp_line    = np.zeros(cn)
        repeats      = cn // (len(arp_notes) * arp_note_dur) + 1
        for rep in range(repeats):
            for i, an in enumerate(arp_notes):
                s2 = (rep * len(arp_notes) + i) * arp_note_dur
                if s2 >= cn: break
                nb = min(cn - s2, arp_note_dur)
                tb = np.arange(nb) / sr
                note = 0.22*np.sin(2*np.pi*an*tb) * adsr(nb, 0.005, 0.06, 0.4, 0.5)
                arp_line[s2:s2+nb] += note

        kick_period = int(sr * beat)
        kick_line   = np.zeros(cn)
        for i in range(cn // kick_period):
            s2 = i * kick_period
            nk = min(cn - s2, int(sr*0.12))
            tk = np.arange(nk) / sr
            fk = np.linspace(120, 40, nk)
            kick = np.sin(2*np.pi*np.cumsum(fk)/sr) * np.exp(-tk*30)
            kick_line[s2:s2+nk] += kick * 0.5

        hat_period = int(sr * beat / 2)
        hat_line   = np.zeros(cn)
        for i in range(cn // hat_period):
            if i % 2 == 1:
                s2 = i * hat_period
                nh = min(cn - s2, int(sr*0.04))
                noise_h = np.random.uniform(-1, 1, nh) * np.exp(-np.linspace(0,1,nh)*40)
                hat_line[s2:s2+nh] += noise_h * 0.12

        pad_c  = (0.18*np.sin(2*np.pi*110*t_c) +
                  0.12*np.sin(2*np.pi*138.6*t_c) +
                  0.08*np.sin(2*np.pi*164.8*t_c)) * (0.7 + 0.3*np.sin(2*np.pi*0.15*t_c))

        clas_raw = bass_line*0.35 + arp_line*0.30 + kick_line*0.18 + hat_line*0.08 + pad_c*0.09
        fi2 = np.ones(cn); fi2[:int(sr*1.5)] = np.linspace(0, 1, int(sr*1.5))
        fo2 = np.ones(cn); fo2[int(sr*(clas_dur-2)):] = np.linspace(1, 0, cn-int(sr*(clas_dur-2)))
        clas_raw *= fi2 * fo2
        clas_raw  = reverb(clas_raw, 0.05, 0.25, 3)
        self._music["classic"] = make_sound(clas_raw, 0.62)

        # ── SURVIVAL MUSIC ── tense, aggressive, fast ostinato, 16s loop ─────
        surv_dur = 16.0
        sn       = int(sr * surv_dur)
        t_s      = np.arange(sn) / sr
        bpm_s    = 130
        beat_s   = 60.0 / bpm_s

        ostinato_freqs = [110, 110, 146.8, 110, 130.8, 110, 123.5, 110]
        ost_note_dur   = int(sr * beat_s * 0.48)
        ost_line       = np.zeros(sn)
        reps_ost       = sn // (len(ostinato_freqs) * ost_note_dur) + 1
        for rep in range(reps_ost):
            for i, on in enumerate(ostinato_freqs):
                s2 = (rep * len(ostinato_freqs) + i) * ost_note_dur
                if s2 >= sn: break
                nb = min(sn - s2, ost_note_dur)
                tb = np.arange(nb) / sr
                note = (0.5*osc(on, nb, 'saw') + 0.3*osc(on*2, nb, 'sq')) * adsr(nb, 0.005, 0.05, 0.55, 0.2)
                note = low_pass(note, 600)
                ost_line[s2:s2+nb] += note

        kick_s_period = int(sr * beat_s)
        kick_s_line   = np.zeros(sn)
        for i in range(sn // kick_s_period):
            s2 = i * kick_s_period
            nk = min(sn - s2, int(sr*0.09))
            tk = np.arange(nk) / sr
            fk = np.linspace(150, 35, nk)
            kick_s_line[s2:s2+nk] += np.sin(2*np.pi*np.cumsum(fk)/sr)*np.exp(-tk*40)*0.65

        snare_period = int(sr * beat_s * 2)
        snare_offset = int(sr * beat_s)
        snare_line   = np.zeros(sn)
        for i in range(sn // snare_period):
            s2 = i * snare_period + snare_offset
            if s2 >= sn: break
            ns = min(sn-s2, int(sr*0.07))
            noise_sn = np.random.uniform(-1,1,ns) * np.exp(-np.linspace(0,1,ns)*25)
            tone_sn  = np.sin(2*np.pi*200*np.arange(ns)/sr) * np.exp(-np.linspace(0,1,ns)*30)
            snare_line[s2:s2+ns] += (noise_sn*0.5 + tone_sn*0.3) * 0.45

        tension_lfo = 0.6 + 0.4*np.sin(2*np.pi*0.25*t_s)
        tension_pad = (0.15*np.sin(2*np.pi*82.4*t_s) +
                       0.10*np.sin(2*np.pi*103.8*t_s + 0.5) +
                       0.08*np.sin(2*np.pi*130.8*t_s + 1.0)) * tension_lfo

        surv_raw = ost_line*0.38 + kick_s_line*0.22 + snare_line*0.18 + tension_pad*0.12 + \
                   np.random.uniform(-0.008, 0.008, sn)
        fi3 = np.ones(sn); fi3[:int(sr*1.0)] = np.linspace(0, 1, int(sr*1.0))
        fo3 = np.ones(sn); fo3[int(sr*(surv_dur-1.5)):] = np.linspace(1,0,sn-int(sr*(surv_dur-1.5)))
        surv_raw *= fi3 * fo3
        surv_raw  = reverb(surv_raw, 0.03, 0.15, 2)
        self._music["survival"] = make_sound(surv_raw, 0.60)

        # ── TIME ATTACK MUSIC ── urgent pulse, rapid staccato, 12s loop ──────
        ta_dur = 12.0
        tn     = int(sr * ta_dur)
        t_ta   = np.arange(tn) / sr
        bpm_t  = 155
        beat_t = 60.0 / bpm_t

        pulse_notes = [220, 246.9, 220, 196.0, 220, 246.9, 261.6, 246.9]
        pulse_nd    = int(sr * beat_t * 0.45)
        pulse_line  = np.zeros(tn)
        reps_p      = tn // (len(pulse_notes) * pulse_nd) + 1
        for rep in range(reps_p):
            for i, pn in enumerate(pulse_notes):
                s2 = (rep * len(pulse_notes) + i) * pulse_nd
                if s2 >= tn: break
                nb = min(tn - s2, pulse_nd)
                tb = np.arange(nb) / sr
                note = (0.45*osc(pn, nb, 'sq') + 0.25*osc(pn*2, nb, 'sin')) * adsr(nb, 0.005, 0.04, 0.5, 0.15)
                pulse_line[s2:s2+nb] += note * 0.5

        bass_t_notes = [55, 55, 65.4, 55, 73.4, 65.4, 55, 49]
        bass_t_nd    = int(sr * beat_t * 2)
        bass_t_line  = np.zeros(tn)
        reps_bt      = tn // (len(bass_t_notes) * bass_t_nd) + 1
        for rep in range(reps_bt):
            for i, bn in enumerate(bass_t_notes):
                s2 = (rep * len(bass_t_notes) + i) * bass_t_nd
                if s2 >= tn: break
                nb = min(tn - s2, bass_t_nd)
                tb = np.arange(nb) / sr
                note = osc(bn, nb, 'saw') * adsr(nb, 0.01, 0.08, 0.6, 0.2)
                note = low_pass(note, 350)
                bass_t_line[s2:s2+nb] += note * 0.55

        kick_t_period = int(sr * beat_t)
        kick_t_line   = np.zeros(tn)
        for i in range(tn // kick_t_period):
            s2 = i * kick_t_period
            nk = min(tn-s2, int(sr*0.07))
            tk = np.arange(nk)/sr
            fk = np.linspace(160, 35, nk)
            kick_t_line[s2:s2+nk] += np.sin(2*np.pi*np.cumsum(fk)/sr)*np.exp(-tk*50)*0.7

        clap_period = int(sr * beat_t * 2)
        clap_offset = int(sr * beat_t)
        clap_line   = np.zeros(tn)
        for i in range(tn // clap_period):
            s2 = i * clap_period + clap_offset
            if s2 >= tn: break
            nc = min(tn-s2, int(sr*0.05))
            clap_line[s2:s2+nc] += np.random.uniform(-1,1,nc)*np.exp(-np.linspace(0,1,nc)*35)*0.4

        urgency = 0.75 + 0.25*np.sin(2*np.pi*0.4*t_ta)
        ta_raw  = (pulse_line*0.35 + bass_t_line*0.30 + kick_t_line*0.20 + clap_line*0.15) * urgency
        fi4 = np.ones(tn); fi4[:int(sr*0.8)] = np.linspace(0, 1, int(sr*0.8))
        fo4 = np.ones(tn); fo4[int(sr*(ta_dur-1.2)):] = np.linspace(1,0,tn-int(sr*(ta_dur-1.2)))
        ta_raw *= fi4 * fo4
        ta_raw  = reverb(ta_raw, 0.025, 0.12, 2)
        self._music["timeattack"] = make_sound(ta_raw, 0.65)

    def play_music(self, track: str, loops: int = -1):
        if not self._ok:
            return
        if track == self._current_track:
            return
        self._current_track = track
        snd = self._music.get(track)
        if snd and self._music_channel:
            self._music_channel.stop()
            if not self._music_muted:
                snd.set_volume(self._vol_music)
                self._music_channel.play(snd, loops=loops)

    def stop_music(self):
        if self._music_channel:
            self._music_channel.stop()
        self._current_track = None

    def toggle_music(self):
        self._music_muted = not self._music_muted
        if self._music_channel:
            if self._music_muted:
                self._music_channel.set_volume(0)
            else:
                self._music_channel.set_volume(self._vol_music)

    @property
    def music_muted(self): return self._music_muted

    def play(self, name: str, vol_override: float = None):
        if not self._ok or self._muted:
            return
        s = self._sounds.get(name)
        if s:
            vol = vol_override if vol_override is not None else self._vol_sfx
            s.set_volume(vol)
            s.play()

    def toggle_mute(self):
        self._muted = not self._muted

    @property
    def muted(self): return self._muted


Vec2 = pygame.math.Vector2

def vec_limit(v: Vec2, max_len: float) -> Vec2:
    length = v.length()
    if length > max_len and length > 0:
        return v * (max_len / length)
    return Vec2(v)


class PerlinNoise:
    def __init__(self, seed: int = 42):
        rng  = np.random.default_rng(seed)
        perm = np.arange(256, dtype=int)
        rng.shuffle(perm)
        self._p = np.concatenate([perm, perm])

    @staticmethod
    def _fade(t):  return t*t*t*(t*(t*6-15)+10)
    @staticmethod
    def _lerp(a,b,t): return a + t*(b-a)
    @staticmethod
    def _grad(h,x,y):
        h &= 3; vx,vy = (1,1,-1,-1)[h],(1,-1,1,-1)[h]
        return vx*x + vy*y

    def noise(self, x, y):
        xi,yi = int(math.floor(x))&255, int(math.floor(y))&255
        xf,yf = x-math.floor(x), y-math.floor(y)
        u,v   = self._fade(xf), self._fade(yf)
        p     = self._p
        aa,ab,ba,bb = p[p[xi]+yi],p[p[xi]+yi+1],p[p[xi+1]+yi],p[p[xi+1]+yi+1]
        x1 = self._lerp(self._grad(aa,xf,yf),  self._grad(ba,xf-1,yf),  u)
        x2 = self._lerp(self._grad(ab,xf,yf-1),self._grad(bb,xf-1,yf-1),u)
        return self._lerp(x1,x2,v)

    def octave_noise(self, x, y, octaves=4, persistence=0.5, lacunarity=2.0):
        val,amp,freq,mx = 0.0,1.0,1.0,0.0
        for _ in range(octaves):
            val += self.noise(x*freq,y*freq)*amp
            mx  += amp; amp *= persistence; freq *= lacunarity
        return val/mx


@dataclass
class QTBounds:
    x: float; y: float; w: float; h: float
    def contains(self,px,py): return self.x<=px<self.x+self.w and self.y<=py<self.y+self.h

class Quadtree:
    def __init__(self, bounds, level=0):
        self.bounds  = bounds; self.level = level
        self.objects: List[Any] = []
        self.nodes:  List[Optional["Quadtree"]] = [None]*4

    def clear(self):
        self.objects.clear()
        for i in range(4):
            if self.nodes[i]: self.nodes[i].clear(); self.nodes[i]=None

    def _split(self):
        hw,hh = self.bounds.w/2, self.bounds.h/2
        x,y   = self.bounds.x, self.bounds.y
        self.nodes[0]=Quadtree(QTBounds(x+hw,y,   hw,hh),self.level+1)
        self.nodes[1]=Quadtree(QTBounds(x,   y,   hw,hh),self.level+1)
        self.nodes[2]=Quadtree(QTBounds(x,   y+hh,hw,hh),self.level+1)
        self.nodes[3]=Quadtree(QTBounds(x+hw,y+hh,hw,hh),self.level+1)

    def _get_index(self, obj):
        mx,my = self.bounds.x+self.bounds.w/2, self.bounds.y+self.bounds.h/2
        top    = obj.rect.y < my and obj.rect.bottom < my
        bottom = obj.rect.y > my
        left   = obj.rect.x < mx and obj.rect.right < mx
        right  = obj.rect.x > mx
        if right and top:    return 0
        if left  and top:    return 1
        if left  and bottom: return 2
        if right and bottom: return 3
        return -1

    def insert(self, obj):
        if self.nodes[0]:
            idx = self._get_index(obj)
            if idx!=-1: self.nodes[idx].insert(obj); return
        self.objects.append(obj)
        if len(self.objects)>QT_MAX_OBJECTS and self.level<QT_MAX_LEVELS:
            if not self.nodes[0]: self._split()
            i=0
            while i<len(self.objects):
                idx=self._get_index(self.objects[i])
                if idx!=-1: self.nodes[idx].insert(self.objects.pop(i))
                else: i+=1

    def retrieve(self, obj):
        result = list(self.objects)
        if self.nodes[0]:
            idx=self._get_index(obj)
            if idx!=-1: result.extend(self.nodes[idx].retrieve(obj))
            else:
                for n in self.nodes:
                    if n: result.extend(n.retrieve(obj))
        return result


class Component(ABC):
    def __init__(self, owner): self.owner = owner
    @abstractmethod
    def update(self, dt): ...

class TransformComponent(Component):
    def __init__(self, owner, x=0.0, y=0.0):
        super().__init__(owner)
        self.pos   = Vec2(x, y)
        self.vel   = Vec2(0, 0)
        self.angle = 0.0

    def update(self, dt):
        self.pos += self.vel * dt * 60

class HealthComponent(Component):
    def __init__(self, owner, max_hp):
        super().__init__(owner)
        self.max_hp = max_hp; self.hp = max_hp
    def take_damage(self, amount):
        self.hp = max(0, self.hp-amount)
        return self.hp <= 0
    @property
    def ratio(self): return self.hp/self.max_hp
    def update(self, dt): pass

class PhysicsComponent(Component):
    def __init__(self, owner, max_speed, friction=0.92):
        super().__init__(owner)
        self.max_speed = max_speed; self.friction = friction
    def update(self, dt):
        t = self.owner.transform
        t.vel = vec_limit(t.vel, self.max_speed)
        t.vel *= self.friction

class InputComponent(Component):
    def update(self, dt):
        keys  = pygame.key.get_pressed()
        owner = self.owner
        acc   = Vec2(0,0)
        spd   = owner.physics.max_speed * 0.18
        if keys[pygame.K_w] or keys[pygame.K_UP]:    acc.y -= spd
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  acc.y += spd
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  acc.x -= spd
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: acc.x += spd
        owner.transform.vel += acc
        mx, my = pygame.mouse.get_pos()
        px = owner.transform.pos.x - owner.game.camera.x
        py = owner.transform.pos.y - owner.game.camera.y
        dx, dy = mx - px, my - py
        if dx != 0 or dy != 0:
            owner.transform.angle = math.degrees(math.atan2(dy, dx)) + 90


class ObjectPool:
    def __init__(self, factory, size):
        self._pool   = [factory() for _ in range(size)]
        self._active = []
    def get(self):
        if self._pool:
            obj = self._pool.pop()
            self._active.append(obj)
            return obj
        return None
    def release(self, obj):
        if obj in self._active:
            self._active.remove(obj)
            obj.reset()
            self._pool.append(obj)
    @property
    def active(self): return self._active


class Bullet:
    W, H = 4, 14

    def __init__(self):
        self.rect   = pygame.Rect(0,0,self.W,self.H)
        self.active = False
        self.vel    = Vec2(0,0)
        self.damage = 10
        self.owner  = "player"
        self.life   = 0.0
        self.color  = CYAN
        self.angle  = 0.0

    def reset(self):
        self.active = False; self.life = 0.0

    def activate(self, x, y, vel, damage=10, owner="player", color=CYAN, angle=0.0):
        self.rect.center = (int(x), int(y))
        self.vel    = Vec2(vel)
        self.damage = damage
        self.owner  = owner
        self.active = True
        self.life   = 0.0
        self.color  = color
        self.angle  = angle

    def update(self, dt):
        self.rect.x += int(self.vel.x * dt * 60)
        self.rect.y += int(self.vel.y * dt * 60)
        self.life += dt
        return (self.active and self.life < 2.2 and
                -200 < self.rect.x < WORLD_W+200 and
                -200 < self.rect.y < WORLD_H+200)

    def draw(self, surf, camera):
        sx = self.rect.centerx - camera.x
        sy = self.rect.centery - camera.y
        if not (-20 < sx < SCREEN_W+20 and -20 < sy < SCREEN_H+20):
            return
        rad  = math.radians(self.angle)
        hlen = self.H // 2
        dx   = math.sin(rad) * hlen
        dy   = -math.cos(rad) * hlen
        pygame.draw.line(surf, (20,20,20),
                         (int(sx-dx+3), int(sy-dy+3)),
                         (int(sx+dx+3), int(sy+dy+3)), self.W)
        pygame.draw.line(surf, self.color,
                         (int(sx-dx), int(sy-dy)),
                         (int(sx+dx), int(sy+dy)), self.W)
        bright = tuple(min(255, c+80) for c in self.color[:3])
        pygame.draw.line(surf, bright,
                         (int(sx-dx*0.3), int(sy-dy*0.3)),
                         (int(sx+dx*0.3), int(sy+dy*0.3)), 2)


class EnemyState(Enum):
    PATROL = auto(); CHASE = auto(); ATTACK = auto(); FLEE = auto()

class FSM:
    def __init__(self, initial):
        self.state = initial
        self._tr: Dict[EnemyState, List] = {}
    def add_transition(self, frm, cond, to, on_enter=None):
        self._tr.setdefault(frm,[]).append((cond,to,on_enter))
    def update(self, ctx):
        for cond,to,on_enter in self._tr.get(self.state,[]):
            if cond(ctx):
                self.state = to
                if on_enter: on_enter(ctx)
                break
        return self.state


class Enemy:
    RADIUS = 18
    COLORS = {
        EnemyState.PATROL: (90,180,240),
        EnemyState.CHASE:  ORANGE,
        EnemyState.ATTACK: RED,
        EnemyState.FLEE:   PURPLE,
    }

    def __init__(self, game):
        self.game      = game
        self.active    = False
        self.transform = TransformComponent(self,0,0)
        self.health    = HealthComponent(self,40)
        self.physics   = PhysicsComponent(self,MAX_SPEED_ENEMY,0.95)
        self.rect      = pygame.Rect(0,0,self.RADIUS*2,self.RADIUS*2)
        self.shoot_cd  = 0.0
        self.shoot_interval = 1.8
        self.etype     = "scout"
        self._build_fsm()

    def reset(self):
        self.active = False
        self.health.hp = self.health.max_hp
        self.transform.vel = Vec2(0,0)
        self.shoot_cd = 0.0

    def spawn(self, x, y):
        self.transform.pos = Vec2(x,y)
        self.active = True
        self.health.hp = self.health.max_hp
        self.fsm.state = EnemyState.PATROL

    def _build_fsm(self):
        self.fsm = FSM(EnemyState.PATROL)
        self.fsm.add_transition(EnemyState.PATROL,lambda c:c._dtp()<DETECT_DIST, EnemyState.CHASE)
        self.fsm.add_transition(EnemyState.CHASE, lambda c:c._dtp()<ATTACK_DIST, EnemyState.ATTACK)
        self.fsm.add_transition(EnemyState.CHASE, lambda c:c._dtp()>DETECT_DIST*1.4, EnemyState.PATROL)
        self.fsm.add_transition(EnemyState.ATTACK,lambda c:c.health.ratio<FLEE_HEALTH, EnemyState.FLEE)
        self.fsm.add_transition(EnemyState.ATTACK,lambda c:c._dtp()>ATTACK_DIST*1.5, EnemyState.CHASE)
        self.fsm.add_transition(EnemyState.FLEE,  lambda c:c._dtp()>DETECT_DIST*1.8, EnemyState.PATROL)

    def _dtp(self):
        return (self.transform.pos - self.game.player.transform.pos).length()

    def _boids_force(self, neighbors):
        sep=Vec2(0,0); ali=Vec2(0,0); coh=Vec2(0,0)
        ns=na=nc=0
        for o in neighbors:
            if o is self: continue
            d = (self.transform.pos - o.transform.pos).length()
            if 0<d<SEP_DIST:
                sep += (self.transform.pos-o.transform.pos).normalize()/d; ns+=1
            if 0<d<NEIGHBOR_DIST:
                ali += o.transform.vel; na+=1
                coh += o.transform.pos; nc+=1
        if ns: sep/=ns
        if na: ali=vec_limit(ali/na, MAX_SPEED_ENEMY)
        if nc: coh=vec_limit(coh/nc-self.transform.pos, MAX_SPEED_ENEMY)
        return sep*W_SEPARATION + ali*W_ALIGNMENT + coh*W_COHESION

    def update(self, dt, neighbors):
        if not self.active: return
        state      = self.fsm.update(self)
        player_pos = self.game.player.transform.pos
        boids      = self._boids_force(neighbors)
        force      = Vec2(0,0)

        if state == EnemyState.PATROL:
            t = time.time()*0.5
            force = Vec2(math.cos(t+id(self)*0.01), math.sin(t+id(self)*0.01))*0.3
        elif state == EnemyState.CHASE:
            to = player_pos - self.transform.pos
            if to.length()>0: force = to.normalize()*MAX_SPEED_ENEMY*W_SEEK_PLAYER
        elif state == EnemyState.ATTACK:
            to = player_pos - self.transform.pos
            if to.length()>80: force = to.normalize()*MAX_SPEED_ENEMY*0.4
            self._try_shoot(dt)
        elif state == EnemyState.FLEE:
            away = self.transform.pos - player_pos
            if away.length()>0: force = away.normalize()*MAX_SPEED_ENEMY*1.5

        self.transform.vel += (force+boids)*dt*60
        self.physics.update(dt)
        self.transform.update(dt)
        self.transform.pos.x = max(20, min(WORLD_W-20, self.transform.pos.x))
        self.transform.pos.y = max(20, min(WORLD_H-20, self.transform.pos.y))
        self.rect.center = (int(self.transform.pos.x), int(self.transform.pos.y))
        if self.shoot_cd>0: self.shoot_cd-=dt

    def _try_shoot(self, dt):
        if self.shoot_cd<=0:
            self.shoot_cd = self.shoot_interval
            to = self.game.player.transform.pos - self.transform.pos
            if to.length()>0:
                vel   = to.normalize()*(BULLET_SPEED*0.6)
                angle = math.degrees(math.atan2(to.y,to.x))+90
                b = self.game.bullet_pool.get()
                if b:
                    b.activate(self.transform.pos.x,self.transform.pos.y,
                                vel,8,"enemy",RED,angle)
                    self.game.sfx.play("enemy_shoot", 0.2)

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.transform.pos.x - camera.x)
        sy = int(self.transform.pos.y - camera.y)
        if not (-60<sx<SCREEN_W+60 and -60<sy<SCREEN_H+60): return

        color  = self.COLORS[self.fsm.state]
        dark_c = tuple(max(0,c-80) for c in color)
        angle  = math.atan2(self.transform.vel.y, self.transform.vel.x) + math.pi/2
        R      = self.RADIUS

        shadow_pts = self._ship_pts(sx+4, sy+5, angle, R)
        pygame.draw.polygon(surf, (8,8,18), shadow_pts)
        body_pts = self._ship_pts(sx, sy, angle, R)
        pygame.draw.polygon(surf, dark_c, body_pts)
        top_pts = self._ship_pts(sx-2, sy-2, angle, R*0.85)
        pygame.draw.polygon(surf, color, top_pts)
        pygame.draw.polygon(surf, WHITE, top_pts, 1)

        crad = max(3, R//4)
        pygame.draw.circle(surf,(8,8,18),(sx+2,sy+2), crad)
        pygame.draw.circle(surf, WHITE, (sx,sy), crad)
        pygame.draw.circle(surf, CYAN, (sx-1,sy-1), max(1,crad-2))

        bw,bh = 36,4
        pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2,sy-30,bw,bh))
        hcol = GREEN if self.health.ratio>0.5 else (ORANGE if self.health.ratio>0.25 else RED)
        pygame.draw.rect(surf, hcol, (sx-bw//2,sy-30,int(bw*self.health.ratio),bh))

    def _ship_pts(self, cx, cy, angle, R):
        pts = [
            (cx+R*math.cos(angle+math.pi),    cy+R*math.sin(angle+math.pi)),
            (cx+R*0.6*math.cos(angle+2.0),    cy+R*0.6*math.sin(angle+2.0)),
            (cx+R*0.6*math.cos(angle-2.0),    cy+R*0.6*math.sin(angle-2.0)),
        ]
        return [(int(x),int(y)) for x,y in pts]


class HeavyEnemy(Enemy):
    RADIUS = 26
    COLORS = {
        EnemyState.PATROL: (60,140,80),
        EnemyState.CHASE:  (100,200,60),
        EnemyState.ATTACK: (180,220,0),
        EnemyState.FLEE:   PURPLE,
    }
    def __init__(self, game):
        super().__init__(game)
        self.health = HealthComponent(self, 120)
        self.physics = PhysicsComponent(self, 2.0, 0.96)
        self.rect   = pygame.Rect(0,0,self.RADIUS*2,self.RADIUS*2)
        self.etype  = "heavy"

    def _try_shoot(self, dt):
        if self.shoot_cd<=0:
            self.shoot_cd = self.shoot_interval
            to = self.game.player.transform.pos - self.transform.pos
            if to.length()>0:
                for spread in (-12, 0, 12):
                    a2  = math.radians(math.degrees(math.atan2(to.y,to.x))+spread)
                    vel = Vec2(math.cos(a2)*BULLET_SPEED*0.55, math.sin(a2)*BULLET_SPEED*0.55)
                    ang = math.degrees(math.atan2(to.y,to.x))+90+spread
                    b = self.game.bullet_pool.get()
                    if b: b.activate(self.transform.pos.x,self.transform.pos.y,
                                      vel,10,"enemy",ORANGE,ang)
                self.game.sfx.play("enemy_shoot", 0.25)

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.transform.pos.x - camera.x)
        sy = int(self.transform.pos.y - camera.y)
        if not (-80<sx<SCREEN_W+80 and -80<sy<SCREEN_H+80): return
        color  = self.COLORS[self.fsm.state]
        dark_c = tuple(max(0,c-60) for c in color)
        angle  = math.atan2(self.transform.vel.y, self.transform.vel.x) + math.pi/2
        R      = self.RADIUS
        shadow_pts = self._heavy_pts(sx+5, sy+6, angle, R)
        pygame.draw.polygon(surf, (8,8,18), shadow_pts)
        pygame.draw.polygon(surf, dark_c, self._heavy_pts(sx,sy,angle,R))
        pygame.draw.polygon(surf, color, self._heavy_pts(sx-2,sy-2,angle,R*0.88))
        pygame.draw.polygon(surf, WHITE, self._heavy_pts(sx-2,sy-2,angle,R*0.88), 2)
        pygame.draw.circle(surf,(8,8,18),(sx+2,sy+2), 6)
        pygame.draw.circle(surf, WHITE, (sx,sy), 6)
        pygame.draw.circle(surf, LIME, (sx-1,sy-1), 4)
        bw,bh = 44,5
        pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2,sy-34,bw,bh))
        hcol = GREEN if self.health.ratio>0.5 else (ORANGE if self.health.ratio>0.25 else RED)
        pygame.draw.rect(surf, hcol, (sx-bw//2,sy-34,int(bw*self.health.ratio),bh))

    def _heavy_pts(self, cx, cy, angle, R):
        pts = []
        for i in range(6):
            a = angle + i * (math.pi*2/6)
            pts.append((cx + R*math.cos(a), cy + R*math.sin(a)))
        return [(int(x),int(y)) for x,y in pts]


class SniperEnemy(Enemy):
    RADIUS = 14
    COLORS = {
        EnemyState.PATROL: (180,60,220),
        EnemyState.CHASE:  (220,100,255),
        EnemyState.ATTACK: (255,150,255),
        EnemyState.FLEE:   GRAY,
    }
    def __init__(self, game):
        super().__init__(game)
        self.health = HealthComponent(self, 35)
        self.physics = PhysicsComponent(self, 3.8, 0.93)
        self.rect   = pygame.Rect(0,0,self.RADIUS*2,self.RADIUS*2)
        self.shoot_interval = 2.8
        self.etype  = "sniper"

    def _try_shoot(self, dt):
        if self.shoot_cd<=0:
            self.shoot_cd = self.shoot_interval
            to = self.game.player.transform.pos - self.transform.pos
            if to.length()>0:
                vel   = to.normalize()*(BULLET_SPEED*1.4)
                angle = math.degrees(math.atan2(to.y,to.x))+90
                b = self.game.bullet_pool.get()
                if b:
                    b.activate(self.transform.pos.x,self.transform.pos.y,
                                vel,18,"enemy",(255,0,200),angle)
                    self.game.sfx.play("player_shoot", 0.18)


class KamikazeEnemy(Enemy):
    RADIUS = 12
    COLORS = {
        EnemyState.PATROL: (200,80,0),
        EnemyState.CHASE:  (255,120,0),
        EnemyState.ATTACK: (255,200,0),
        EnemyState.FLEE:   GRAY,
    }
    def __init__(self, game):
        super().__init__(game)
        self.health = HealthComponent(self, 20)
        self.physics = PhysicsComponent(self, 5.5, 0.97)
        self.rect   = pygame.Rect(0,0,self.RADIUS*2,self.RADIUS*2)
        self.shoot_interval = 99
        self.etype  = "kamikaze"

    def update(self, dt, neighbors):
        if not self.active: return
        self.fsm.update(self)
        player_pos = self.game.player.transform.pos
        to = player_pos - self.transform.pos
        d  = to.length()
        if d > 0:
            force = to.normalize() * self.physics.max_speed * 0.5
            self.transform.vel += force * dt * 60
        self.physics.update(dt)
        self.transform.update(dt)
        self.transform.pos.x = max(20, min(WORLD_W-20, self.transform.pos.x))
        self.transform.pos.y = max(20, min(WORLD_H-20, self.transform.pos.y))
        self.rect.center = (int(self.transform.pos.x), int(self.transform.pos.y))
        if d < 28:
            self.game.player.take_damage(25)
            self.active = False
            self.game.enemy_pool.release(self)
            self.game._particles_spawn(self.transform.pos, ORANGE, 20)
            self.game.sfx.play("kamikaze_boom")


class CarrierEnemy(Enemy):
    RADIUS = 30
    COLORS = {
        EnemyState.PATROL: (0,100,140),
        EnemyState.CHASE:  (0,150,200),
        EnemyState.ATTACK: (0,200,220),
        EnemyState.FLEE:   GRAY,
    }
    def __init__(self, game):
        super().__init__(game)
        self.health = HealthComponent(self, 180)
        self.physics = PhysicsComponent(self, 1.8, 0.97)
        self.rect   = pygame.Rect(0,0,self.RADIUS*2,self.RADIUS*2)
        self.spawn_cd    = 0.0
        self.spawn_interval = 8.0
        self.etype  = "carrier"

    def update(self, dt, neighbors):
        super().update(dt, neighbors)
        if self.spawn_cd > 0: self.spawn_cd -= dt
        if self.spawn_cd <= 0 and self.active:
            self.spawn_cd = self.spawn_interval
            for _ in range(2):
                e = self.game.enemy_pool.get()
                if e and not isinstance(e, (HeavyEnemy, SniperEnemy, CarrierEnemy)):
                    EnemyFactory.configure(e, "scout")
                    offset = Vec2(random.uniform(-60,60), random.uniform(-60,60))
                    e.spawn(self.transform.pos.x+offset.x, self.transform.pos.y+offset.y)

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.transform.pos.x - camera.x)
        sy = int(self.transform.pos.y - camera.y)
        if not (-90<sx<SCREEN_W+90 and -90<sy<SCREEN_H+90): return
        color  = self.COLORS[self.fsm.state]
        dark_c = tuple(max(0,c-60) for c in color)
        R      = self.RADIUS
        pygame.draw.circle(surf, (5,5,15), (sx+5,sy+6), R)
        pygame.draw.circle(surf, dark_c,   (sx,sy),     R)
        pygame.draw.circle(surf, color,    (sx-2,sy-2), int(R*0.85))
        pygame.draw.circle(surf, WHITE,    (sx-2,sy-2), int(R*0.85), 2)
        pygame.draw.circle(surf,(8,8,18),(sx+2,sy+2), 7)
        pygame.draw.circle(surf, WHITE, (sx,sy), 7)
        pygame.draw.circle(surf, TEAL,  (sx-1,sy-1), 5)
        bw,bh = 52,5
        pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2,sy-38,bw,bh))
        hcol = GREEN if self.health.ratio>0.5 else (ORANGE if self.health.ratio>0.25 else RED)
        pygame.draw.rect(surf, hcol, (sx-bw//2,sy-38,int(bw*self.health.ratio),bh))


class TitanBoss(Enemy):
    RADIUS = 46
    COLORS = {
        EnemyState.PATROL: (120, 0,  180),
        EnemyState.CHASE:  (180, 0,  220),
        EnemyState.ATTACK: (255, 40, 255),
        EnemyState.FLEE:   (80,  0,  120),
    }

    def __init__(self, game):
        super().__init__(game)
        self.health          = HealthComponent(self, 1200)
        self.physics         = PhysicsComponent(self, 1.2, 0.97)
        self.rect            = pygame.Rect(0, 0, self.RADIUS*2, self.RADIUS*2)
        self.etype           = "titan"
        self.shoot_interval  = 0.4
        self.spawn_cd        = 0.0
        self.spawn_interval  = 6.0
        self.meteor_cd       = 0.0
        self.meteor_interval = 3.5
        self._rot            = 0.0
        self._phase          = 0
        self._phase_timer    = 0.0

    def reset(self):
        super().reset()
        self.spawn_cd  = 0.0
        self.meteor_cd = 0.0
        self._phase    = 0
        self._phase_timer = 0.0

    def update(self, dt, neighbors):
        if not self.active: return
        self._rot        += dt * 0.8
        self._phase_timer += dt

        if self._phase_timer > 12.0:
            self._phase       = (self._phase + 1) % 3
            self._phase_timer = 0.0

        super().update(dt, neighbors)

        if self.spawn_cd > 0: self.spawn_cd -= dt
        if self.spawn_cd <= 0 and self.active:
            self.spawn_cd = self.spawn_interval
            self._spawn_minions()

        if self.meteor_cd > 0: self.meteor_cd -= dt
        if self.meteor_cd <= 0 and self.active and self.fsm.state == EnemyState.ATTACK:
            self.meteor_cd = self.meteor_interval
            self._launch_meteors()

    def _try_shoot(self, dt):
        if self.shoot_cd <= 0:
            self.shoot_cd = self.shoot_interval
            to = self.game.player.transform.pos - self.transform.pos
            if to.length() == 0: return
            base_angle = math.degrees(math.atan2(to.y, to.x))

            if self._phase == 0:
                spreads = [-20, -10, 0, 10, 20]
            elif self._phase == 1:
                spreads = list(range(-30, 31, 12))
            else:
                spreads = list(range(0, 360, 45))

            for sp in spreads:
                a2  = math.radians(base_angle + sp)
                vel = Vec2(math.cos(a2)*BULLET_SPEED*0.7, math.sin(a2)*BULLET_SPEED*0.7)
                b   = self.game.bullet_pool.get()
                if b:
                    b.activate(self.transform.pos.x, self.transform.pos.y,
                               vel, 12, "enemy", (220, 0, 255), base_angle+sp+90)
            self.game.sfx.play("enemy_shoot", 0.3)

    def _spawn_minions(self):
        types = ["scout", "fighter", "kamikaze"]
        for i in range(3):
            e = self.game.enemy_pool.get()
            if e and not isinstance(e, TitanBoss):
                EnemyFactory.configure(e, random.choice(types))
                ang    = random.uniform(0, math.pi*2)
                offset = Vec2(math.cos(ang)*80, math.sin(ang)*80)
                e.spawn(self.transform.pos.x+offset.x, self.transform.pos.y+offset.y)
        self.game.sfx.play("boss_warning", 0.4)

    def _launch_meteors(self):
        pp = self.game.player.transform.pos
        for _ in range(4):
            ang  = random.uniform(0, math.pi*2)
            dist = random.uniform(100, 200)
            mx2  = pp.x + math.cos(ang)*dist
            my2  = pp.y + math.sin(ang)*dist
            meteor = EnemyMeteor(self.game, self.transform.pos.x, self.transform.pos.y, mx2, my2)
            self.game._active_meteors.append(meteor)
        self.game.sfx.play("explosion_small", 0.35)

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.transform.pos.x - camera.x)
        sy = int(self.transform.pos.y - camera.y)
        if not (-120<sx<SCREEN_W+120 and -120<sy<SCREEN_H+120): return

        t     = time.time()
        color = self.COLORS[self.fsm.state]
        dark_c = tuple(max(0,c-60) for c in color)
        R      = self.RADIUS

        for layer_r, layer_col, offset in [
            (R+6, (8,8,18), (6,7)),
            (R,   dark_c,   (0,0)),
            (int(R*0.88), color, (-2,-2)),
        ]:
            pts = []
            for i in range(8):
                angle = self._rot + i*(math.pi*2/8)
                pr    = layer_r * (1.0 + 0.08*math.sin(t*3 + i))
                pts.append((sx+offset[0]+pr*math.cos(angle),
                            sy+offset[1]+pr*math.sin(angle)))
            pygame.draw.polygon(surf, layer_col, [(int(x),int(y)) for x,y in pts])

        pygame.draw.polygon(surf, WHITE,
                            [(int(x),int(y)) for x,y in
                             [(sx-2+R*0.88*math.cos(self._rot+i*(math.pi*2/8)),
                               sy-2+R*0.88*math.sin(self._rot+i*(math.pi*2/8)))
                              for i in range(8)]], 2)

        for i in range(4):
            cannon_a = self._rot + i*(math.pi/2)
            cx2 = int(sx + R*0.7*math.cos(cannon_a))
            cy2 = int(sy + R*0.7*math.sin(cannon_a))
            pygame.draw.circle(surf, (8,8,18), (cx2+2,cy2+2), 6)
            pygame.draw.circle(surf, (200,0,200), (cx2,cy2), 6)
            pygame.draw.circle(surf, WHITE, (cx2,cy2), 6, 1)

        glow_r = int(10 + 5*math.sin(t*4))
        glow_s = pygame.Surface((glow_r*2,glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (200,0,255,80), (glow_r,glow_r), glow_r)
        surf.blit(glow_s, (sx-glow_r+2, sy-glow_r+2))
        pygame.draw.circle(surf, (8,8,18), (sx+2,sy+2), 10)
        pygame.draw.circle(surf, WHITE,    (sx,sy), 10)
        pygame.draw.circle(surf, (220,100,255), (sx-2,sy-2), 7)

        bw, bh = 90, 8
        pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2, sy-R-18, bw, bh), border_radius=4)
        pygame.draw.rect(surf, (200,0,200),
                         (sx-bw//2, sy-R-18, int(bw*self.health.ratio), bh), border_radius=4)
        pygame.draw.rect(surf, WHITE, (sx-bw//2, sy-R-18, bw, bh), 1, border_radius=4)
        label = ResourceManager().get_font(11,True).render("TITAN", True, (220,100,255))
        surf.blit(label, (sx-label.get_width()//2, sy-R-32))

        phase_names = ["DISPARO", "RÁFAGA", "OMNIDIRECCIONAL"]
        ph_t = ResourceManager().get_font(10).render(
            f"FASE: {phase_names[self._phase]}", True, (160,80,200))
        surf.blit(ph_t, (sx-ph_t.get_width()//2, sy-R-44))


class EnemyMeteor:
    def __init__(self, game, sx, sy, tx, ty):
        self.game   = game
        self.pos    = Vec2(sx, sy)
        self.radius = random.randint(14, 24)
        d           = Vec2(tx-sx, ty-sy)
        spd         = random.uniform(4.0, 7.0)
        if d.length() > 0:
            d = d.normalize() * spd
        self.vel    = d
        self.active = True
        self.life   = 3.5
        rng         = random.Random(random.randint(0,99999))
        self._pts   = [(rng.uniform(0.6,1.0), i*(360/8)) for i in range(8)]
        base        = rng.randint(70,110)
        self.color  = (base, int(base*0.85), int(base*0.7))
        self.dark   = tuple(max(0,c-35) for c in self.color)
        self.rot    = 0.0
        self.rot_spd= rng.uniform(-2.0, 2.0)
        self.rect   = pygame.Rect(0,0,self.radius*2,self.radius*2)

    def update(self, dt):
        self.pos  += self.vel * dt * 60
        self.life -= dt
        self.rot  += self.rot_spd * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.life <= 0:
            self.active = False
            return
        p = self.game.player
        if p.rect.colliderect(self.rect):
            p.take_damage(18)
            self.game._particles_spawn(self.pos, ORANGE, 12)
            self.game.sfx.play("asteroid_hit", 0.5)
            self.active = False

    def draw(self, surf, camera):
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        if not (-80<sx<SCREEN_W+80 and -80<sy<SCREEN_H+80): return

        glow_r = self.radius + 6
        gs = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (200, 100, 30, 80), (glow_r,glow_r), glow_r)
        surf.blit(gs, (sx-glow_r, sy-glow_r))

        sh_pts = []
        for fac, ba in self._pts:
            r2 = math.radians(ba + self.rot*57.3)
            r  = self.radius*fac
            sh_pts.append((sx+r*math.cos(r2)+4, sy+r*math.sin(r2)+5))
        pygame.draw.polygon(surf, (6,6,12), [(int(x),int(y)) for x,y in sh_pts])

        d_pts = []
        for fac, ba in self._pts:
            r2 = math.radians(ba + self.rot*57.3)
            r  = self.radius*fac
            d_pts.append((sx+r*math.cos(r2), sy+r*math.sin(r2)))
        pygame.draw.polygon(surf, self.dark, [(int(x),int(y)) for x,y in d_pts])

        l_pts = []
        for fac, ba in self._pts:
            r2 = math.radians(ba + self.rot*57.3)
            r  = self.radius*fac*0.80
            l_pts.append((sx-2+r*math.cos(r2), sy-2+r*math.sin(r2)))
        pygame.draw.polygon(surf, self.color, [(int(x),int(y)) for x,y in l_pts])
        pygame.draw.circle(surf, (220,140,60),
                           (sx-self.radius//3, sy-self.radius//3), max(2, self.radius//4))


class EnemyFactory:
    _types = {
        "scout":    {"hp":30,  "speed":3.5, "shoot":1.5,  "cls": Enemy},
        "fighter":  {"hp":60,  "speed":2.8, "shoot":1.1,  "cls": Enemy},
        "heavy":    {"hp":120, "speed":2.0, "shoot":0.9,  "cls": HeavyEnemy},
        "sniper":   {"hp":35,  "speed":3.8, "shoot":2.2,  "cls": SniperEnemy},
        "kamikaze": {"hp":20,  "speed":8.5, "shoot":99.0, "cls": KamikazeEnemy},
        "carrier":  {"hp":180, "speed":1.8, "shoot":2.8,  "cls": CarrierEnemy},
        "boss":     {"hp":280, "speed":1.8, "shoot":0.5,  "cls": Enemy},
        "titan":    {"hp":600, "speed":1.2, "shoot":0.4,  "cls": Enemy},
    }

    @staticmethod
    def configure(enemy, etype="scout"):
        cfg = EnemyFactory._types.get(etype, EnemyFactory._types["scout"])
        enemy.health.max_hp      = cfg["hp"]
        enemy.health.hp          = cfg["hp"]
        enemy.physics.max_speed  = cfg["speed"]
        enemy.shoot_interval     = cfg["shoot"]
        enemy.etype              = etype
        return enemy


class Asteroid:
    def __init__(self, x, y, radius, seed):
        self.pos    = Vec2(x,y)
        self.radius = radius
        self.rect   = pygame.Rect(int(x)-radius,int(y)-radius,radius*2,radius*2)
        self.hp     = radius*3; self.max_hp=self.hp
        self.vel    = Vec2(random.uniform(-0.3,0.3),random.uniform(-0.3,0.3))
        rng         = random.Random(seed)
        self._pts   = [(rng.uniform(0.65,1.0),i*(360/10)) for i in range(10)]
        base        = rng.randint(50,90)
        self.color  = (base, int(base*0.9), int(base*0.8))
        self.dark   = tuple(max(0,c-40) for c in self.color)
        self.rot    = 0.0
        self.rot_spd= rng.uniform(-0.5,0.5)

    def update(self, dt):
        self.pos += self.vel*dt*60
        self.pos.x = max(self.radius,min(WORLD_W-self.radius,self.pos.x))
        self.pos.y = max(self.radius,min(WORLD_H-self.radius,self.pos.y))
        self.rect.center = (int(self.pos.x),int(self.pos.y))
        self.rot += self.rot_spd*dt

    def draw(self, surf, camera):
        sx = int(self.pos.x-camera.x); sy = int(self.pos.y-camera.y)
        if not (-self.radius*2<sx<SCREEN_W+self.radius*2 and
                -self.radius*2<sy<SCREEN_H+self.radius*2): return

        sh_pts=[]
        for fac,ba in self._pts:
            r2=math.radians(ba+self.rot*57.3); r=self.radius*fac
            sh_pts.append((sx+r*math.cos(r2)+5, sy+r*math.sin(r2)+6))
        pygame.draw.polygon(surf,(6,6,12),[(int(x),int(y)) for x,y in sh_pts])

        d_pts=[]
        for fac,ba in self._pts:
            r2=math.radians(ba+self.rot*57.3); r=self.radius*fac
            d_pts.append((sx+r*math.cos(r2), sy+r*math.sin(r2)))
        pygame.draw.polygon(surf,self.dark,[(int(x),int(y)) for x,y in d_pts])

        l_pts=[]
        for fac,ba in self._pts:
            r2=math.radians(ba+self.rot*57.3); r=self.radius*fac*0.82
            l_pts.append((sx-2+r*math.cos(r2), sy-2+r*math.sin(r2)))
        pygame.draw.polygon(surf,self.color,[(int(x),int(y)) for x,y in l_pts])
        pygame.draw.polygon(surf,GRAY,[(int(x),int(y)) for x,y in l_pts],1)
        pygame.draw.circle(surf,(160,165,175),(sx-self.radius//3,sy-self.radius//3),
                           max(2,self.radius//5))


@dataclass
class Skill:
    name: str
    description: str
    max_level: int
    level: int = 0
    base_cost: int = 1
    cost_increment: int = 0

    @property
    def is_maxed(self): return self.level >= self.max_level

    @property
    def current_cost(self):
        return self.base_cost + self.level * self.cost_increment


class SkillTree:
    SAVE_FILE = "save_data.json"

    def __init__(self):
        self._reset_skills()

    def _reset_skills(self):
        self.points = 0
        self.skills: Dict[str, Skill] = {
            "fire_rate":  Skill("Cadencia",      "Dispara más rápido",          5, base_cost=1, cost_increment=0),
            "bullet_dmg": Skill("Daño",           "Más daño por bala",           5, base_cost=1, cost_increment=0),
            "speed":      Skill("Velocidad",      "Nave más veloz",              4, base_cost=1, cost_increment=0),
            "shield":     Skill("Escudo",         "Más HP máximo",               3, base_cost=2, cost_increment=0),
            "multi_shot": Skill("Multidisparo",   "Balas adicionales",           3, base_cost=3, cost_increment=2),
            "pierce":     Skill("Perforadora",    "Balas atraviesan enemigos",   2, base_cost=2, cost_increment=0),
        }

    def new_game(self):
        self._reset_skills()

    def upgrade(self, key):
        s = self.skills.get(key)
        if s and not s.is_maxed and self.points >= s.current_cost:
            self.points -= s.current_cost
            s.level     += 1
            self.save()
            try:
                from pygame import mixer as _m
                SoundManager().play("skill_upgrade")
            except Exception:
                pass
            return True
        return False

    def get_stat(self, key):
        s = self.skills.get(key)
        return 1.0 if not s else 1.0 + s.level * 0.25

    def save(self):
        with open(self.SAVE_FILE,"w") as f:
            json.dump({"points":self.points,
                       "skills":{k:v.level for k,v in self.skills.items()}},f,indent=2)

    def load(self):
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE) as f: data=json.load(f)
                self.points = data.get("points",0)
                for k,lvl in data.get("skills",{}).items():
                    if k in self.skills: self.skills[k].level = lvl
            except: pass


class LevelSystem:
    def __init__(self, player_ref):
        self.player           = player_ref
        self.level            = 1
        self.xp               = 0
        self.xp_next          = XP_BASE
        self.level_up_pending = False
        self.bonuses: List[str] = []
        self._banner_timer    = 0.0

    def add_xp(self, amount: int) -> bool:
        self.xp += amount
        if self.xp >= self.xp_next:
            self.xp      -= self.xp_next
            self.level   += 1
            self.xp_next  = int(XP_BASE * (XP_SCALE ** (self.level-1)))
            self.level_up_pending = True
            self._banner_timer    = 0.0
            self._apply_level_bonus()
            try:
                self.player.game.sfx.play("level_up")
            except Exception:
                pass
            return True
        return False

    def _apply_level_bonus(self):
        bonus_pool = [
            ("HP +20",
             lambda: (setattr(self.player.health,'max_hp',self.player.health.max_hp+20),
                      setattr(self.player.health,'hp',
                              min(self.player.health.hp+20,self.player.health.max_hp)))),
            ("Velocidad +5%",
             lambda: setattr(self.player.physics,'max_speed',
                             self.player.physics.max_speed*1.05)),
            ("Skill pts +2 extra",
             lambda: setattr(self.player.game.skill_tree,'points',
                             self.player.game.skill_tree.points+2)),
            ("HP restaurado",
             lambda: setattr(self.player.health,'hp',
                             min(self.player.health.hp+40,self.player.health.max_hp))),
        ]
        idx      = (self.level-2) % len(bonus_pool)
        name, fn = bonus_pool[idx]
        fn()
        self.player.game.skill_tree.points += 2
        self.bonuses.append(f"Nivel {self.level}: +2 Skill pts | {name}")

    @property
    def xp_ratio(self): return self.xp / max(1, self.xp_next)


class Player:
    RADIUS = 22

    def __init__(self, game):
        self.game      = game
        self.transform = TransformComponent(self, WORLD_W//2, WORLD_H//2)
        self.health    = HealthComponent(self, 100)
        self.physics   = PhysicsComponent(self, MAX_SPEED_PLAYER, 0.88)
        self.input     = InputComponent(self)
        self.rect      = pygame.Rect(0,0,self.RADIUS*2,self.RADIUS*2)
        self.shoot_cd  = 0.0
        self.score     = 0
        self.inv_cd    = 0.0
        self.level_sys = LevelSystem(self)
        self.kills: Dict[str, int] = {
            "scout":0,"fighter":0,"heavy":0,"sniper":0,
            "kamikaze":0,"carrier":0,"boss":0,"titan":0
        }
        self.total_kills = 0
        self.play_time   = 0.0

    @property
    def shoot_interval(self):
        return 0.22 / self.game.skill_tree.get_stat("fire_rate")

    @property
    def bullet_damage(self):
        return int(10 * self.game.skill_tree.get_stat("bullet_dmg"))

    def update(self, dt):
        self.play_time += dt
        self.input.update(dt)
        self.physics.update(dt)
        self.transform.update(dt)
        self.transform.pos.x = max(20, min(WORLD_W-20, self.transform.pos.x))
        self.transform.pos.y = max(20, min(WORLD_H-20, self.transform.pos.y))
        self.rect.center = (int(self.transform.pos.x), int(self.transform.pos.y))
        if self.shoot_cd > 0: self.shoot_cd -= dt
        if self.inv_cd   > 0: self.inv_cd   -= dt
        if pygame.mouse.get_pressed()[0] and self.shoot_cd <= 0:
            self._shoot()

    def _shoot(self):
        self.shoot_cd = self.shoot_interval
        self.game.sfx.play("player_shoot", 0.35)
        px = self.transform.pos.x - self.game.camera.x
        py = self.transform.pos.y - self.game.camera.y
        mx, my = pygame.mouse.get_pos()
        dx, dy = mx-px, my-py
        dist   = math.hypot(dx, dy)
        if dist == 0: return
        vx    = dx/dist * BULLET_SPEED
        vy    = dy/dist * BULLET_SPEED
        angle = math.degrees(math.atan2(dy, dx)) + 90

        def fire(vx2, vy2, a2):
            b = self.game.bullet_pool.get()
            if b: b.activate(self.transform.pos.x, self.transform.pos.y,
                              Vec2(vx2,vy2), self.bullet_damage, "player", CYAN, a2)

        fire(vx, vy, angle)
        lvl = self.game.skill_tree.skills["multi_shot"].level
        for i in range(lvl):
            spread = ((i//2)+1)*18 * (1 if i%2==0 else -1)
            a2     = math.radians(angle-90+spread)
            fire(math.cos(a2)*BULLET_SPEED, math.sin(a2)*BULLET_SPEED, angle+spread)

    def take_damage(self, amount):
        if self.inv_cd <= 0:
            self.health.take_damage(amount)
            self.inv_cd = 0.8
            self.game.sfx.play("player_hit")

    def add_xp(self, amount):
        return self.level_sys.add_xp(amount)

    def draw(self, surf, camera):
        sx = int(self.transform.pos.x - camera.x)
        sy = int(self.transform.pos.y - camera.y)
        if self.inv_cd > 0 and int(self.inv_cd*10) % 2: return

        angle_rad = math.radians(self.transform.angle)
        R = self.RADIUS

        def rot(dx, dy):
            rx = dx*math.cos(angle_rad) - dy*math.sin(angle_rad)
            ry = dx*math.sin(angle_rad) + dy*math.cos(angle_rad)
            return (int(sx+rx), int(sy+ry))

        tip    = rot(0,-R);          bl    = rot(-R*0.55, R*0.65)
        br     = rot(R*0.55, R*0.65); indent = rot(0, R*0.2)
        pygame.draw.polygon(surf,(8,8,18),
                            [(tip[0]+5,tip[1]+6),(bl[0]+5,bl[1]+6),
                             (indent[0]+5,indent[1]+6),(br[0]+5,br[1]+6)])
        pygame.draw.polygon(surf, CYAN_DIM, [tip,bl,indent,br])

        tip2    = (rot(0,-R*0.9)[0]-2,   rot(0,-R*0.9)[1]-2)
        bl2     = (rot(-R*0.45,R*0.55)[0]-2, rot(-R*0.45,R*0.55)[1]-2)
        br2     = (rot(R*0.45,R*0.55)[0]-2,  rot(R*0.45,R*0.55)[1]-2)
        indent2 = (rot(0,R*0.12)[0]-2,   rot(0,R*0.12)[1]-2)
        pygame.draw.polygon(surf, CYAN,  [tip2,bl2,indent2,br2])
        pygame.draw.polygon(surf, WHITE, [tip2,bl2,indent2,br2], 1)

        pygame.draw.circle(surf,(8,8,18),(sx+2,sy+2),5)
        pygame.draw.circle(surf,WHITE,(sx,sy),5)
        pygame.draw.circle(surf,CYAN,(sx-1,sy-1),3)

        if self.transform.vel.length() > 0.5:
            back = rot(0, R*0.7)
            for i in range(4):
                r = 4+i*3
                g = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
                pygame.draw.circle(g, (*NEON_BLUE, 130-i*30), (r,r), r)
                surf.blit(g, (back[0]-r, back[1]-r))

        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(surf, (0,70,110), (sx,sy), (mx,my), 1)


class WorldGenerator:
    def __init__(self, seed, player_level=1):
        self.seed         = seed
        self.player_level = player_level
        self.noise        = PerlinNoise(seed)
        self._cache: Dict[tuple,list]       = {}
        self._star_cache: Dict[tuple,list]  = {}

    def set_player_level(self, level):
        if level != self.player_level:
            self.player_level = level
            self._cache.clear()

    def get_sector(self, sx, sy):
        key = (sx, sy, self.player_level)
        if key in self._cache: return self._cache[key]
        wx, wy = sx*SECTOR_SIZE, sy*SECTOR_SIZE
        asts   = []
        rng    = random.Random(self.seed^(sx*31337)^(sy*73939))
        density_threshold = max(0.40, ASTEROID_DENSITY_BASE - self.player_level * 0.025)
        attempts = min(8 + self.player_level, 30)
        for _ in range(attempts):
            rx,ry = rng.uniform(0,SECTOR_SIZE), rng.uniform(0,SECTOR_SIZE)
            val   = self.noise.octave_noise((wx+rx)/800,(wy+ry)/800,octaves=4)
            if (val+1)/2 > density_threshold:
                asts.append(Asteroid(wx+rx,wy+ry,rng.randint(12,35),rng.randint(0,99999)))
        self._cache[key] = asts
        return asts

    def get_stars(self, sx, sy):
        key = (sx, sy)
        if key not in self._star_cache:
            rng = random.Random(self.seed^sx^(sy<<16))
            self._star_cache[key] = [
                (sx*SECTOR_SIZE+rng.uniform(0,SECTOR_SIZE),
                 sy*SECTOR_SIZE+rng.uniform(0,SECTOR_SIZE),
                 rng.randint(1,3), rng.randint(60,180))
                for _ in range(55)]
        return self._star_cache[key]

    def get_nebula_color(self, x, y):
        r = (self.noise.noise(x/2000+0.1,y/2000+0.2)+1)/2
        b = (self.noise.noise(x/2000+5.0,y/2000+3.0)+1)/2
        return (int(r*22), 0, int(b*30))


class WaveManager:
    ENEMY_POOL_BY_LEVEL = [
        ["scout"],
        ["scout", "scout", "fighter"],
        ["scout", "fighter", "kamikaze"],
        ["fighter", "kamikaze", "sniper"],
        ["fighter", "heavy", "sniper", "kamikaze"],
        ["heavy", "sniper", "carrier", "kamikaze"],
    ]

    def __init__(self, game):
        self.game          = game
        self.wave          = 0
        self.timer         = 0.0
        self.wave_interval = 22.0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.wave_interval:
            self.timer = 0.0
            self.wave += 1
            self._spawn_wave()

    def _spawn_wave(self):
        player_level = self.game.player.level_sys.level
        pool_idx     = min(player_level-1, len(self.ENEMY_POOL_BY_LEVEL)-1)
        pool         = self.ENEMY_POOL_BY_LEVEL[pool_idx]
        count        = 4 + self.wave*2 + player_level
        pp           = self.game.player.transform.pos

        is_boss_wave = (self.wave % 5 == 0)
        if is_boss_wave:
            self.game.sfx.play("boss_warning")

        for i in range(count):
            ang  = random.uniform(0, math.pi*2)
            dist = random.uniform(360, 640)
            ex   = max(50, min(WORLD_W-50, pp.x + math.cos(ang)*dist))
            ey   = max(50, min(WORLD_H-50, pp.y + math.sin(ang)*dist))

            e = self.game.enemy_pool.get()
            if not e: break

            if is_boss_wave and i == 0:
                etype = "boss"
            elif is_boss_wave and i == 1:
                etype = "carrier"
            else:
                etype = random.choice(pool)

            EnemyFactory.configure(e, etype)
            e.spawn(ex, ey)


class HUD:
    def __init__(self, game):
        self.game         = game
        self.rm           = ResourceManager()
        self._fps_samples = []

    def draw(self, surf, fps):
        p  = self.game.player
        wm = self.game.wave_manager
        ls = p.level_sys
        rm = self.rm

        self._bar(surf, 20, SCREEN_H-38, 210, 18, p.health.ratio,
                  GREEN if p.health.ratio>0.5 else (ORANGE if p.health.ratio>0.25 else RED),
                  f"HP {p.health.hp}/{p.health.max_hp}", bar_tag=f"❤ {p.health.hp}/{p.health.max_hp}")
        self._bar(surf, 20, SCREEN_H-14, 210, 12, ls.xp_ratio, PURPLE,
                  f"XP  Lv.{ls.level}", bar_tag=f"⭐ Lv.{ls.level}")

        f18 = rm.get_font(18, True)
        surf.blit(f18.render(f"Score: {p.score:,}", True, YELLOW),(20,20))
        surf.blit(f18.render(
            f"Wave: {wm.wave}  |  Próxima: {max(0,int(wm.wave_interval-wm.timer))}s",
            True, CYAN),(20,44))

        f16 = rm.get_font(16)
        surf.blit(f16.render(f"Nivel: {ls.level}  |  XP: {ls.xp}/{ls.xp_next}",
                             True, PURPLE),(20,68))
        surf.blit(f16.render(f"Skill pts: {self.game.skill_tree.points}  |  Modo: {self.game.game_mode}",
                             True, GREEN),(20,90))

        if self.game.game_mode == GAMEMODE_TIMEATTACK and hasattr(self.game,'_ta_time'):
            remaining = max(0, self.game._ta_limit - self.game._ta_time)
            col = RED if remaining < 30 else YELLOW
            surf.blit(rm.get_font(20,True).render(
                f"Tiempo: {int(remaining)}s", True, col),(SCREEN_W//2-70,20))

        self._fps_samples.append(fps)
        if len(self._fps_samples)>30: self._fps_samples.pop(0)
        avg = sum(self._fps_samples)/len(self._fps_samples)
        surf.blit(rm.get_font(13).render(f"FPS:{avg:.0f}", True,
                                         GREEN if avg>=55 else ORANGE),(SCREEN_W-72,10))

        self._minimap(surf)

        hint = rm.get_font(13).render(
            "WASD:Mover | Click:Disparar | [2]:Skills | ESC:Pausa | [M]:SFX | [N]:Música", True, GRAY)
        surf.blit(hint,(SCREEN_W//2-hint.get_width()//2, SCREEN_H-18))

        if self.game.sfx.muted:
            mute_t = rm.get_font(14,True).render("SFX OFF", True, RED)
            surf.blit(mute_t,(SCREEN_W-90, 28))
        if self.game.sfx.music_muted:
            mus_t = rm.get_font(14,True).render("MÚS OFF", True, ORANGE)
            surf.blit(mus_t,(SCREEN_W-90, 46))

        if ls.level_up_pending:
            self._draw_level_up_banner(surf, ls)

    def _bar(self, surf, x, y, w, h, ratio, color, label, bar_tag=""):
        pygame.draw.rect(surf, DARK_GRAY,(x,y,w,h),border_radius=4)
        fill_w = int(w*ratio)
        if fill_w > 0:
            pygame.draw.rect(surf, color,(x,y,fill_w,h),border_radius=4)
        pygame.draw.rect(surf, WHITE,(x,y,w,h),1,border_radius=4)
        # tag inside bar only (no external label above)
        if bar_tag and h >= 10:
            tag = self.rm.get_font(max(9,h-3),True).render(bar_tag, True, (255,255,255))
            tag_x = x + 5
            tag_y = y + h//2 - tag.get_height()//2
            surf.blit(tag, (tag_x, tag_y))

    def _minimap(self, surf):
        ms     = 110
        mx_pos = SCREEN_W-ms-12
        my_pos = SCREEN_H-ms-12
        mm     = pygame.Surface((ms,ms), pygame.SRCALPHA)
        mm.fill((6,6,18,190))
        scx,scy = ms/WORLD_W, ms/WORLD_H
        for e in self.game.enemy_pool.active:
            if e.active:
                pygame.draw.circle(mm, RED,
                                   (int(e.transform.pos.x*scx),
                                    int(e.transform.pos.y*scy)), 2)
        p = self.game.player
        pygame.draw.circle(mm, CYAN,
                           (int(p.transform.pos.x*scx),
                            int(p.transform.pos.y*scy)), 3)
        pygame.draw.rect(mm, WHITE, (0,0,ms,ms), 1)
        surf.blit(mm,(mx_pos,my_pos))

    def _draw_level_up_banner(self, surf, ls):
        banner_text = f"NIVEL {ls.level}!  {ls.bonuses[-1].split(':')[1].strip() if ls.bonuses else ''}"
        banner = self.rm.get_font(30,True).render(banner_text, True, YELLOW)
        bx = SCREEN_W//2 - banner.get_width()//2
        by = SCREEN_H//2 - 80
        bg = pygame.Surface((banner.get_width()+30, banner.get_height()+16), pygame.SRCALPHA)
        bg.fill((0,0,0,185))
        surf.blit(bg,(bx-15,by-8))
        surf.blit(banner,(bx,by))
        ls._banner_timer += 0.016
        if ls._banner_timer > 2.8:
            ls.level_up_pending = False
            ls._banner_timer    = 0.0


class SkillTreeScreen:
    def __init__(self, game):
        self.game     = game
        self.rm       = ResourceManager()
        self.selected = 0

    def handle_event(self, event):
        st   = self.game.skill_tree
        keys = list(st.skills.keys())
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected-1) % len(keys)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected+1) % len(keys)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                st.upgrade(keys[self.selected])
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            y0 = 155
            for i,k in enumerate(keys):
                by = y0 + i*76
                btn = pygame.Rect(SCREEN_W//2+178, by+8, 100, 40)
                if btn.collidepoint(event.pos):
                    st.upgrade(k)
                    break
            for i in range(len(keys)):
                row = pygame.Rect(SCREEN_W//2-295, y0+i*76, 590, 68)
                if row.collidepoint(event.pos):
                    self.selected = i
                    break

    def draw(self, surf):
        ov = pygame.Surface((SCREEN_W,SCREEN_H), pygame.SRCALPHA)
        ov.fill((0,0,0,215))
        surf.blit(ov,(0,0))

        st   = self.game.skill_tree
        rm   = self.rm
        keys = list(st.skills.keys())
        ls   = self.game.player.level_sys

        title = rm.get_font(34,True).render("ÁRBOL DE HABILIDADES", True, YELLOW)
        surf.blit(title,(SCREEN_W//2-title.get_width()//2, 30))

        info = rm.get_font(17).render(
            f"Puntos disponibles: {st.points}  |  Nivel jugador: {ls.level}", True, GREEN)
        surf.blit(info,(SCREEN_W//2-info.get_width()//2, 78))

        y0 = 155
        for i,key in enumerate(keys):
            skill = st.skills[key]
            sel   = (i == self.selected)
            bx    = SCREEN_W//2-295
            by    = y0 + i*76

            bg_c = (42,42,88) if sel else (16,16,36)
            pygame.draw.rect(surf, bg_c,    (bx,by,590,68), border_radius=8)
            pygame.draw.rect(surf, (YELLOW if sel else GRAY),(bx,by,590,68),2,border_radius=8)

            surf.blit(rm.get_font(16,True).render(
                f"{skill.name}  [Lv {skill.level}/{skill.max_level}]",
                True, YELLOW if sel else WHITE),(bx+14,by+6))

            surf.blit(rm.get_font(13).render(
                skill.description, True, GRAY),(bx+14,by+28))

            next_cost_text = "MAXED" if skill.is_maxed else f"Siguiente: {skill.current_cost} pts"
            cost_color = GRAY if skill.is_maxed else (GREEN if st.points>=skill.current_cost else RED)
            surf.blit(rm.get_font(12,True).render(next_cost_text, True, cost_color),(bx+14,by+48))

            if skill.cost_increment > 0 and not skill.is_maxed:
                scale_txt = rm.get_font(11).render(
                    f"(+{skill.cost_increment} por nivel)", True, (120,120,140))
                surf.blit(scale_txt,(bx+110,by+50))

            for lvl in range(skill.max_level):
                sx2 = bx+310+lvl*28
                sy2 = by+26
                pygame.draw.circle(surf, YELLOW if lvl<skill.level else DARK_GRAY,(sx2,sy2),9)
                pygame.draw.circle(surf, WHITE,(sx2,sy2),9,1)

            can   = not skill.is_maxed and st.points >= skill.current_cost
            btn_c = GREEN if can else DARK_GRAY
            btn_r = pygame.Rect(bx+482,by+12,100,38)
            pygame.draw.rect(surf, btn_c,  btn_r, border_radius=6)
            pygame.draw.rect(surf, WHITE,  btn_r, 1, border_radius=6)
            lbl   = "MEJORAR" if can else ("MAXED" if skill.is_maxed else "BLOQ.")
            surf.blit(rm.get_font(12,True).render(lbl,True,WHITE),(btn_r.x+18,btn_r.y+11))

        hint = rm.get_font(13).render("↑↓ Navegar | ENTER Mejorar | [2] Cerrar | ESC Pausa", True, GRAY)
        surf.blit(hint,(SCREEN_W//2-hint.get_width()//2, SCREEN_H-26))


class GameState(Enum):
    MENU     = auto()
    WARP     = auto()
    PLAYING  = auto()
    SKILL    = auto()
    PAUSED   = auto()
    GAME_OVER= auto()
    CONTROLS = auto()
    CREDITS  = auto()


class WarpTransition:
    """
    Interstellar warp animation (~3.2 s).

    Phases
    ------
    0  build-up  (0.0 – 0.6 s)  stars drift slowly, blue glow grows at centre
    1  stretch   (0.6 – 1.8 s)  stars elongate into radial streaks, tunnel forms
    2  rush       (1.8 – 2.8 s)  full hyperspace — bright white tunnel, star lines
                                  blur into solid beams
    3  fade-out   (2.8 – 3.2 s)  everything whites out, then black → game starts
    """

    DURATION = 3.2
    _PHASE_T = [0.0, 0.6, 1.8, 2.8, 3.2]

    def __init__(self, screen_w: int, screen_h: int):
        self.sw      = screen_w
        self.sh      = screen_h
        self.elapsed = 0.0
        self.done    = False
        self._cx     = screen_w // 2
        self._cy     = screen_h // 2

        rng = random.Random(99)
        self._stars: List[dict] = []
        for _ in range(520):
            angle = rng.uniform(0, math.pi * 2)
            dist  = rng.uniform(18, max(screen_w, screen_h) * 0.72)
            speed = rng.uniform(0.4, 1.0)
            size  = rng.uniform(0.5, 2.0)
            br    = rng.randint(160, 255)
            col   = rng.choice([
                (br, br, br),
                (int(br*0.75), int(br*0.85), br),
                (br, int(br*0.9), int(br*0.7)),
                (int(br*0.8), int(br*0.7), br),
            ])
            self._stars.append({
                "angle": angle,
                "dist":  dist,
                "speed": speed,
                "size":  size,
                "col":   col,
            })

    # ── helpers ─────────────────────────────────────────────────────────────

    def _phase(self) -> int:
        for i in range(len(self._PHASE_T) - 1):
            if self.elapsed < self._PHASE_T[i + 1]:
                return i
        return len(self._PHASE_T) - 2

    def _phase_t(self) -> float:
        """Normalised time [0,1] within the current phase."""
        ph = self._phase()
        t0 = self._PHASE_T[ph]
        t1 = self._PHASE_T[ph + 1]
        return (self.elapsed - t0) / max(1e-6, t1 - t0)

    @staticmethod
    def _ease_in_out(t: float) -> float:
        return t * t * (3 - 2 * t)

    @staticmethod
    def _ease_in(t: float) -> float:
        return t * t * t

    # ── update / draw ────────────────────────────────────────────────────────

    def update(self, dt: float):
        self.elapsed += dt
        if self.elapsed >= self.DURATION:
            self.done = True

    def draw(self, surf: pygame.Surface):
        ph   = self._phase()
        pt   = self._phase_t()
        t    = self.elapsed

        surf.fill((0, 0, 0))

        if ph == 0:           self._draw_buildup(surf, pt)
        elif ph == 1:         self._draw_stretch(surf, pt)
        elif ph == 2:         self._draw_rush(surf, pt)
        else:                 self._draw_fadeout(surf, pt)

    # ── phase renderers ──────────────────────────────────────────────────────

    def _draw_buildup(self, surf: pygame.Surface, pt: float):
        e = self._ease_in_out(pt)
        # slow gentle drift
        for st in self._stars:
            drift = 0.06 * e
            d2    = st["dist"] * (1 - drift * 0.25)
            x = int(self._cx + math.cos(st["angle"]) * d2)
            y = int(self._cy + math.sin(st["angle"]) * d2)
            sz  = max(1, int(st["size"] * (1 + e * 0.5)))
            al  = int(120 + 80 * e)
            col = tuple(min(255, int(c * (0.6 + 0.4 * e))) for c in st["col"])
            if 0 <= x < self.sw and 0 <= y < self.sh:
                pygame.draw.circle(surf, col, (x, y), sz)

        # central blue glow
        glow_r = int(30 + 120 * e)
        for r in range(glow_r, 0, -4):
            al = int(60 * (r / glow_r) * e)
            gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (40, 80, 255, al), (r, r), r)
            surf.blit(gs, (self._cx - r, self._cy - r))

        # "PREPARANDO SALTO" text
        rm  = ResourceManager()
        alpha_t = int(200 * e)
        txt = rm.get_font(22, True).render("PREPARANDO SALTO…", True, (alpha_t, alpha_t, 255))
        ts  = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
        ts.fill((0,0,0,0))
        ts.blit(txt, (0,0))
        ts.set_alpha(alpha_t)
        surf.blit(ts, (self._cx - txt.get_width()//2, self._cy + 140))

    def _draw_stretch(self, surf: pygame.Surface, pt: float):
        e = self._ease_in(pt)

        for st in self._stars:
            base_d  = st["dist"]
            stretch = 1 + e * 9.0       # stars rush outward
            d_front = base_d * stretch
            d_back  = base_d * (stretch - e * 2.0)
            d_back  = max(0, d_back)

            x1 = int(self._cx + math.cos(st["angle"]) * d_back)
            y1 = int(self._cy + math.sin(st["angle"]) * d_back)
            x2 = int(self._cx + math.cos(st["angle"]) * d_front)
            y2 = int(self._cy + math.sin(st["angle"]) * d_front)

            # clip to screen
            x1 = max(-2, min(self.sw+2, x1))
            y1 = max(-2, min(self.sh+2, y1))
            x2 = max(-2, min(self.sw+2, x2))
            y2 = max(-2, min(self.sh+2, y2))

            bright = min(255, int(160 + 95 * e))
            col    = tuple(min(255, int(c * 0.7 + bright * 0.3)) for c in st["col"])
            width  = max(1, int(st["size"] * (1 + e * 1.5)))
            pygame.draw.line(surf, col, (x1, y1), (x2, y2), width)

        # tunnel ring
        ring_r = int(40 + 200 * e)
        for r in range(ring_r, ring_r - 30, -3):
            if r <= 0: continue
            al = int(90 * (1 - (ring_r - r) / 30) * e)
            gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (80, 120, 255, al), (r, r), r, 3)
            surf.blit(gs, (self._cx - r, self._cy - r))

        # central white core
        core_r = int(8 + 40 * e)
        gs = pygame.Surface((core_r*2, core_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (200, 220, 255, int(180 * e)), (core_r, core_r), core_r)
        surf.blit(gs, (self._cx - core_r, self._cy - core_r))

    def _draw_rush(self, surf: pygame.Surface, pt: float):
        e = self._ease_in_out(pt)

        # deep tunnel gradient background
        for r in range(min(self.sw, self.sh)//2, 0, -8):
            frac = r / (min(self.sw, self.sh) // 2)
            al   = int(180 * (1 - frac) * 0.7)
            col  = (int(10 * frac), int(20 * frac), min(255, int(60 + 120 * (1-frac))))
            gs   = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*col, al), (r, r), r)
            surf.blit(gs, (self._cx - r, self._cy - r))

        # star streaks — full-speed beams
        for st in self._stars:
            speed_mult = 12 + e * 18
            d_front    = st["dist"] * speed_mult
            d_back     = st["dist"] * (speed_mult - 5 - e * 6)
            d_back     = max(0, d_back)

            x1 = int(self._cx + math.cos(st["angle"]) * d_back)
            y1 = int(self._cy + math.sin(st["angle"]) * d_back)
            x2 = int(self._cx + math.cos(st["angle"]) * d_front)
            y2 = int(self._cy + math.sin(st["angle"]) * d_front)

            bright = 255
            col    = tuple(min(255, int(c * 0.5 + bright * 0.5)) for c in st["col"])
            w      = max(1, int(st["size"] * (2 + e * 2)))
            pygame.draw.line(surf, col, (x1, y1), (x2, y2), w)

        # rings that rush toward the viewer
        for i in range(6):
            phase_off = (i / 6 + pt) % 1.0
            ring_r    = int(20 + phase_off * max(self.sw, self.sh) * 0.8)
            al        = int(160 * (1 - phase_off) * (0.4 + 0.6 * e))
            thick     = max(1, int(4 * (1 - phase_off)))
            gs        = pygame.Surface((ring_r*2, ring_r*2), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (120, 160, 255, al),
                                (0, ring_r//3, ring_r*2, ring_r), thick)
            surf.blit(gs, (self._cx - ring_r, self._cy - ring_r//2))

        # bright blinding core
        core_r = int(55 + 50 * e)
        gs = pygame.Surface((core_r*2, core_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (220, 235, 255, int(220 * (0.6 + 0.4 * e))),
                           (core_r, core_r), core_r)
        surf.blit(gs, (self._cx - core_r, self._cy - core_r))

        # speed lines vignette at edges
        vign = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        edge_al = int(140 * e)
        for edge_w in [40, 25, 12]:
            vign.fill((0, 0, 0, 0))
            pygame.draw.rect(vign, (0, 10, 40, edge_al),
                             (0, 0, edge_w, self.sh))
            pygame.draw.rect(vign, (0, 10, 40, edge_al),
                             (self.sw-edge_w, 0, edge_w, self.sh))
            pygame.draw.rect(vign, (0, 10, 40, edge_al),
                             (0, 0, self.sw, edge_w))
            pygame.draw.rect(vign, (0, 10, 40, edge_al),
                             (0, self.sh-edge_w, self.sw, edge_w))
            edge_al = edge_al * 3 // 4
        surf.blit(vign, (0, 0))

    def _draw_fadeout(self, surf: pygame.Surface, pt: float):
        # first half: white flash; second half: fade to black
        if pt < 0.5:
            e = pt * 2
            # keep drawing faint rush beneath
            self._draw_rush(surf, 1.0)
            flash = pygame.Surface((self.sw, self.sh))
            flash.fill((255, 255, 255))
            flash.set_alpha(int(240 * e))
            surf.blit(flash, (0, 0))
        else:
            e   = (pt - 0.5) * 2
            ovl = pygame.Surface((self.sw, self.sh))
            ovl.fill((0, 0, 0))
            ovl.set_alpha(int(255 * e))
            surf.blit(ovl, (0, 0))


class PauseMenu:
    OPTIONS = ["Continuar", "Árbol de Habilidades", "Controles", "Menú Principal", "Salir"]

    def __init__(self, game):
        self.game   = game
        self.rm     = ResourceManager()
        self.sel    = 0
        self._rects: List[pygame.Rect] = []

    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.sel = (self.sel-1) % len(self.OPTIONS)
            elif event.key == pygame.K_DOWN:
                self.sel = (self.sel+1) % len(self.OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.OPTIONS[self.sel]
            elif event.key == pygame.K_ESCAPE:
                return "Continuar"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i,r in enumerate(self._rects):
                if r.collidepoint(event.pos):
                    return self.OPTIONS[i]
        if event.type == pygame.MOUSEMOTION:
            for i,r in enumerate(self._rects):
                if r.collidepoint(event.pos):
                    self.sel = i
        return None

    def draw(self, surf):
        ov = pygame.Surface((SCREEN_W,SCREEN_H), pygame.SRCALPHA)
        ov.fill((0,0,0,180))
        surf.blit(ov,(0,0))

        rm       = self.rm
        box_w,box_h = 390,400
        bx       = SCREEN_W//2-box_w//2
        by       = SCREEN_H//2-box_h//2

        pygame.draw.rect(surf,(12,12,40),(bx+4,by+4,box_w,box_h),border_radius=14)
        pygame.draw.rect(surf,(18,18,50),(bx,by,box_w,box_h),border_radius=14)
        pygame.draw.rect(surf,CYAN,(bx,by,box_w,box_h),2,border_radius=14)

        title = rm.get_font(36,True).render("PAUSA", True, WHITE)
        surf.blit(title,(SCREEN_W//2-title.get_width()//2, by+22))

        self._rects = []
        oy = by+90
        for i,opt in enumerate(self.OPTIONS):
            sel = (i == self.sel)
            r   = pygame.Rect(SCREEN_W//2-145,oy,290,46)
            self._rects.append(r)
            if sel:
                pygame.draw.rect(surf, NEON_BLUE, r, border_radius=8)
            pygame.draw.rect(surf, CYAN if sel else GRAY, r, 1, border_radius=8)
            col = YELLOW if opt=="Menú Principal" else (CYAN if opt=="Controles" else (WHITE if sel else GRAY))
            t   = rm.get_font(18,sel).render(("▶ " if sel else "  ")+opt, True, col)
            surf.blit(t,(r.centerx-t.get_width()//2, r.centery-t.get_height()//2))
            oy += 58

        hint = rm.get_font(12).render("↑↓ Navegar | ENTER Seleccionar", True, GRAY)
        surf.blit(hint,(SCREEN_W//2-hint.get_width()//2, by+box_h-26))



class ControlsScreen:
    def __init__(self, game):
        self.game = game
        self.rm   = ResourceManager()
        self._back_rect = None
        self._from_state = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._go_back()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_rect and self._back_rect.collidepoint(event.pos):
                self._go_back()

    def _go_back(self):
        if self._from_state == GameState.MENU:
            self.game.state = GameState.MENU
        else:
            self.game.state = GameState.PAUSED

    def draw(self, surf):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 10, 230))
        surf.blit(ov, (0, 0))
        rm = self.rm
        title = rm.get_font(36, True).render("CONTROLES E INSTRUCCIONES", True, CYAN)
        surf.blit(title, (SCREEN_W//2 - title.get_width()//2, 30))
        box_w = 900
        bx = SCREEN_W//2 - box_w//2
        controls = [
            ("MOVIMIENTO", [
                ("W / Arriba", "Mover nave arriba"),
                ("S / Abajo",  "Mover nave abajo"),
                ("A / Izquierda", "Mover nave a la izquierda"),
                ("D / Derecha",   "Mover nave a la derecha"),
                ("Raton",      "Apuntar la nave"),
            ]),
            ("COMBATE", [
                ("Click Izquierdo", "Disparar"),
                ("Mantener Click",  "Disparo continuo"),
            ]),
            ("INTERFAZ", [
                ("ESC",  "Abrir/cerrar menu de pausa"),
                ("2",    "Abrir arbol de habilidades"),
                ("M",    "Activar/desactivar sonido"),
                ("N",    "Activar/desactivar musica"),
            ]),
            ("MODOS DE JUEGO", [
                ("Clasico",       "Oleadas infinitas, supera tu record"),
                ("Supervivencia", "Enemigos sin parar, aguanta todo lo que puedas"),
                ("Contrarreloj",  "3 minutos, maxima puntuacion posible"),
            ]),
            ("ENEMIGOS", [
                ("Explorador",     "Rapido pero debil, ataca en grupo"),
                ("Cazador",        "Equilibrado, ataca con determinacion"),
                ("Kamikaze",       "Se lanza directo, dano explosivo"),
                ("Francotirador",  "Dispara desde lejos, esquiva sus balas"),
                ("Pesado",         "Muy resistente, dispara en rafaga"),
                ("Transportador",  "Libera naves menores, eliminalo primero"),
                ("Jefe/TITAN",     "Cada 5 oleadas, usa todo tu arsenal"),
            ]),
        ]
        y = 90
        col_w = box_w // 2
        for side, sections in enumerate([controls[:3], controls[3:]]):
            cx = bx + side * col_w + 10
            sy = y
            for section_title, items in sections:
                sec_t = rm.get_font(15, True).render(section_title, True, YELLOW)
                surf.blit(sec_t, (cx, sy)); sy += 26
                pygame.draw.line(surf, (60,60,100), (cx, sy), (cx + col_w - 20, sy), 1); sy += 8
                for key, desc in items:
                    key_t = rm.get_font(13, True).render(key, True, CYAN)
                    surf.blit(key_t, (cx + 10, sy))
                    desc_t = rm.get_font(13).render(desc, True, (170, 170, 190))
                    surf.blit(desc_t, (cx + 180, sy))
                    sy += 22
                sy += 10
        back_btn = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H - 52, 200, 38)
        self._back_rect = back_btn
        pygame.draw.rect(surf, (20, 20, 60), back_btn, border_radius=8)
        pygame.draw.rect(surf, CYAN, back_btn, 2, border_radius=8)
        bt = rm.get_font(16, True).render("ESC  Volver", True, WHITE)
        surf.blit(bt, (back_btn.centerx - bt.get_width()//2, back_btn.centery - bt.get_height()//2))


class CreditsScreen:
    def __init__(self, game):
        self.game = game
        self.rm   = ResourceManager()
        self._back_rect = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.state = GameState.MENU
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_rect and self._back_rect.collidepoint(event.pos):
                self.game.state = GameState.MENU

    def draw(self, surf):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 10, 240))
        surf.blit(ov, (0, 0))
        rm = self.rm
        title = rm.get_font(42, True).render("CREDITOS", True, YELLOW)
        surf.blit(title, (SCREEN_W//2 - title.get_width()//2, 40))
        pygame.draw.line(surf, (80, 80, 30), (SCREEN_W//2 - 200, 100), (SCREEN_W//2 + 200, 100), 1)
        credits_data = [
            ("DESARROLLO Y PROGRAMACION", CYAN, [
                "Equipo de Desarrollo",
                "Arquitectura del juego, sistemas de combate,",
                "generacion procedural y arbol de habilidades.",
            ]),
            ("DISENO DE AUDIO", (160, 100, 255), [
                "Sintesis de sonido procedural con NumPy.",
                "Musica ambiental generada algoritmicamente.",
                "Efectos: disparo, explosion, nivel y warp.",
            ]),
            ("INTELIGENCIA ARTIFICIAL", (100, 220, 100), [
                "Sistema Boids para comportamiento de enjambre.",
                "Maquina de estados para cada tipo de enemigo.",
                "QuadTree para deteccion de colisiones.",
            ]),
            ("TECNOLOGIAS USADAS", ORANGE, [
                "Python 3  .  Pygame  .  NumPy",
                "Generacion procedural con Perlin Noise.",
                "Patrones: Object Pool, ECS, Singleton.",
            ]),
            ("AGRADECIMIENTOS", (200, 180, 255), [
                "A todos los jugadores que disfrutan el cosmos.",
                "Gracias por jugar COSMIC ROGUELIKE!  Star",
            ]),
        ]
        y = 130
        for section_title, col, lines in credits_data:
            st = rm.get_font(17, True).render(section_title, True, col)
            surf.blit(st, (SCREEN_W//2 - st.get_width()//2, y)); y += 28
            for line in lines:
                lt = rm.get_font(14).render(line, True, (190, 190, 210))
                surf.blit(lt, (SCREEN_W//2 - lt.get_width()//2, y)); y += 22
            y += 14
        ver_t = rm.get_font(12).render("COSMIC ROGUELIKE v3.0", True, (50, 55, 70))
        surf.blit(ver_t, (SCREEN_W//2 - ver_t.get_width()//2, SCREEN_H - 72))
        back_btn = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H - 52, 200, 38)
        self._back_rect = back_btn
        pygame.draw.rect(surf, (20, 20, 60), back_btn, border_radius=8)
        pygame.draw.rect(surf, YELLOW, back_btn, 2, border_radius=8)
        bt = rm.get_font(16, True).render("ESC  Volver", True, WHITE)
        surf.blit(bt, (back_btn.centerx - bt.get_width()//2, back_btn.centery - bt.get_height()//2))


class MenuBackground:
    def __init__(self):
        self._stars = []
        rng = random.Random(77)
        for _ in range(320):
            self._stars.append({
                "x": rng.uniform(0, SCREEN_W),
                "y": rng.uniform(0, SCREEN_H),
                "spd": rng.uniform(0.05, 0.4),
                "sz":  rng.randint(1, 3),
                "br":  rng.randint(40, 200),
                "twinkle": rng.uniform(0, math.pi*2),
            })
        self._ships = []
        for i in range(6):
            rng2 = random.Random(i*999)
            self._ships.append({
                "x":   rng2.uniform(0, SCREEN_W),
                "y":   rng2.uniform(60, SCREEN_H-60),
                "spd": rng2.uniform(0.6, 1.8),
                "size":rng2.randint(6, 14),
                "col": random.choice([CYAN, (100,180,255), (180,100,255), TEAL]),
                "trail": [],
            })
        self._nebula_surf = self._make_nebula()
        self._particles   = []
        self._part_cd     = 0.0
        self._scroll      = 0.0

    def _make_nebula(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        rng = random.Random(12)
        for _ in range(8):
            cx  = rng.randint(0, SCREEN_W)
            cy  = rng.randint(0, SCREEN_H)
            rad = rng.randint(60, 200)
            col = random.choice([
                (0, 20, 60, 18), (30, 0, 60, 15), (0, 40, 50, 14), (20, 0, 40, 12)
            ])
            for r in range(rad, 0, -10):
                alpha = int(col[3] * (r/rad))
                pygame.draw.circle(s, (*col[:3], alpha), (cx,cy), r)
        return s

    def update(self, dt):
        t = time.time()
        self._scroll += dt * 12

        for st in self._stars:
            st["x"] -= st["spd"] * dt * 60
            if st["x"] < -4:
                st["x"] = SCREEN_W + 4
                rng = random.Random(int(time.time()*1000) % 99999)
                st["y"] = rng.uniform(0, SCREEN_H)

        for sh in self._ships:
            sh["x"] -= sh["spd"] * dt * 60
            sh["trail"].append((sh["x"], sh["y"]))
            if len(sh["trail"]) > 18:
                sh["trail"].pop(0)
            if sh["x"] < -30:
                sh["x"] = SCREEN_W + 30
                sh["y"] = random.uniform(60, SCREEN_H-60)
                sh["trail"].clear()

        self._part_cd -= dt
        if self._part_cd <= 0:
            self._part_cd = random.uniform(0.04, 0.12)
            self._particles.append({
                "x": random.uniform(0, SCREEN_W),
                "y": random.uniform(0, SCREEN_H),
                "vx": random.uniform(-0.3, 0.3),
                "vy": random.uniform(-0.3, 0.3),
                "life": random.uniform(1.5, 3.5),
                "max_life": 3.5,
                "col": random.choice([(0,180,255),(100,80,255),(0,220,200),(180,60,255)]),
                "sz":  random.randint(1, 3),
            })
        alive = []
        for p in self._particles:
            p["life"] -= dt
            p["x"]    += p["vx"] * dt * 60
            p["y"]    += p["vy"] * dt * 60
            if p["life"] > 0:
                alive.append(p)
        self._particles = alive

    def draw(self, surf):
        surf.fill((2, 4, 12))
        surf.blit(self._nebula_surf, (0,0))

        t = time.time()
        for st in self._stars:
            tw  = 0.5 + 0.5*math.sin(t*1.5 + st["twinkle"])
            br  = int(st["br"] * tw)
            pygame.draw.circle(surf, (br,br,br),
                               (int(st["x"]), int(st["y"])), st["sz"])

        for p in self._particles:
            alpha = int(200 * p["life"] / p["max_life"])
            gs = pygame.Surface((p["sz"]*2, p["sz"]*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*p["col"], alpha), (p["sz"],p["sz"]), p["sz"])
            surf.blit(gs, (int(p["x"])-p["sz"], int(p["y"])-p["sz"]))

        for sh in self._ships:
            for i, (tx, ty) in enumerate(sh["trail"]):
                alpha = int(120 * i / max(1, len(sh["trail"])))
                w     = max(1, sh["size"]//4 - (len(sh["trail"])-i)//4)
                ts    = pygame.Surface((w*2+2, w*2+2), pygame.SRCALPHA)
                pygame.draw.circle(ts, (*sh["col"], alpha), (w+1,w+1), w)
                surf.blit(ts, (int(tx)-w-1, int(ty)-w-1))

            sx2 = int(sh["x"]); sy2 = int(sh["y"]); R = sh["size"]
            angle = math.pi
            tip   = (sx2, sy2-R)
            bl    = (sx2-int(R*0.55), sy2+int(R*0.65))
            br    = (sx2+int(R*0.55), sy2+int(R*0.65))
            ind   = (sx2, sy2+int(R*0.2))
            dark  = tuple(max(0,c-80) for c in sh["col"])
            pygame.draw.polygon(surf, dark,     [tip,bl,ind,br])
            tip2  = (sx2,   sy2-int(R*0.9))
            bl2   = (sx2-int(R*0.45), sy2+int(R*0.55))
            br2   = (sx2+int(R*0.45), sy2+int(R*0.55))
            ind2  = (sx2,   sy2+int(R*0.12))
            pygame.draw.polygon(surf, sh["col"], [tip2,bl2,ind2,br2])
            pygame.draw.circle(surf, WHITE, (sx2,sy2), max(2,R//4))
            pygame.draw.circle(surf, sh["col"], (sx2-1,sy2-1), max(1,R//4-1))


class MainMenu:
    MODES = [GAMEMODE_CLASSIC, GAMEMODE_SURVIVAL, GAMEMODE_TIMEATTACK]
    MODE_DESC = {
        GAMEMODE_CLASSIC:    "Oleadas infinitas. Construye tu nave y supera tu récord.",
        GAMEMODE_SURVIVAL:   "Enemigos aparecen sin parar. ¿Cuánto tiempo aguantas?",
        GAMEMODE_TIMEATTACK: "3 minutos. Máxima puntuación posible.",
    }

    def __init__(self, game):
        self.game       = game
        self.rm         = ResourceManager()
        self.mode_sel   = 0
        self._rects: List[pygame.Rect] = []
        self._btn_rects: List[pygame.Rect] = []
        self._bg        = MenuBackground()
        self._prev_sel  = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.sfx.play("ui_click")
                self.game.game_mode = self.MODES[self.mode_sel]
                self.game._begin_warp()
            elif event.key == pygame.K_LEFT:
                self.mode_sel = (self.mode_sel-1) % len(self.MODES)
                self.game.sfx.play("ui_click", 0.2)
            elif event.key == pygame.K_RIGHT:
                self.mode_sel = (self.mode_sel+1) % len(self.MODES)
                self.game.sfx.play("ui_click", 0.2)
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rects:
                play_btn = self._btn_rects[0]
                if play_btn.collidepoint(event.pos):
                    self.game.sfx.play("ui_click")
                    self.game.game_mode = self.MODES[self.mode_sel]
                    self.game._begin_warp()
                    return
                if len(self._btn_rects) > 1 and self._btn_rects[1].collidepoint(event.pos):
                    self.game.sfx.play("ui_click", 0.2)
                    self.game.running = False
                    return
                if len(self._btn_rects) > 2 and self._btn_rects[2].collidepoint(event.pos):
                    self.game.sfx.play("ui_click", 0.2)
                    self.game.controls_screen._from_state = GameState.MENU
                    self.game.state = GameState.CONTROLS
                    return
                if len(self._btn_rects) > 3 and self._btn_rects[3].collidepoint(event.pos):
                    self.game.sfx.play("ui_click", 0.2)
                    self.game.state = GameState.CREDITS
                    return
            for i,r in enumerate(self._rects):
                if r.collidepoint(event.pos):
                    if self.mode_sel != i:
                        self.game.sfx.play("ui_click", 0.2)
                    self.mode_sel = i

        if event.type == pygame.MOUSEMOTION:
            for i,r in enumerate(self._rects):
                if r.collidepoint(event.pos):
                    if self.mode_sel != i:
                        self.game.sfx.play("ui_click", 0.15)
                    self.mode_sel = i

    def draw(self, surf, dt=0.016):
        self._bg.update(dt)
        self._bg.draw(surf)

        t   = time.time()
        gv  = int((math.sin(t*1.6)+1)/2*50+180)
        rm  = self.rm

        title_str = "COSMIC ROGUELIKE"
        sh = rm.get_font(54,True).render(title_str, True,(0,30,65))
        surf.blit(sh,(SCREEN_W//2-sh.get_width()//2+4,94))
        title = rm.get_font(54,True).render(title_str, True,(0,gv,220))
        surf.blit(title,(SCREEN_W//2-title.get_width()//2,90))

        sub = rm.get_font(16).render(
            "3D Space Shooter · Procedural Gen · Boids AI · 7 Tipos de Enemigos",
            True,(0,120,160))
        surf.blit(sub,(SCREEN_W//2-sub.get_width()//2, 158))

        mode_title = rm.get_font(18,True).render("MODO DE JUEGO", True,(100,100,130))
        surf.blit(mode_title,(SCREEN_W//2-mode_title.get_width()//2, 210))

        self._rects = []
        box_w = 240
        total_w = len(self.MODES)*(box_w+16) - 16
        start_x = SCREEN_W//2 - total_w//2

        for i,mode in enumerate(self.MODES):
            sel = (i == self.mode_sel)
            bx  = start_x + i*(box_w+16)
            by  = 238
            bh  = 110

            bg_col = (18,28,60) if sel else (8,10,22)
            border_col = CYAN if sel else (40,40,60)
            pygame.draw.rect(surf, bg_col,    (bx,by,box_w,bh), border_radius=10)
            pygame.draw.rect(surf, border_col,(bx,by,box_w,bh), 2, border_radius=10)

            r = pygame.Rect(bx,by,box_w,bh)
            self._rects.append(r)

            name_col = YELLOW if sel else (150,150,170)
            nm = rm.get_font(17,True).render(mode, True, name_col)
            surf.blit(nm,(bx+box_w//2-nm.get_width()//2, by+16))

            desc = self.MODE_DESC[mode]
            words = desc.split()
            lines = []
            cur   = ""
            for w in words:
                test = cur+" "+w if cur else w
                if rm.get_font(12).size(test)[0] < box_w-16:
                    cur = test
                else:
                    lines.append(cur); cur=w
            if cur: lines.append(cur)
            for li,line in enumerate(lines):
                lt = rm.get_font(12).render(line, True,(100,110,130) if not sel else (160,170,190))
                surf.blit(lt,(bx+8, by+42+li*16))

            if sel:
                pygame.draw.polygon(surf,CYAN,[
                    (bx+box_w//2-8,by+bh-12),
                    (bx+box_w//2+8,by+bh-12),
                    (bx+box_w//2,  by+bh-2)])

        py_btn = pygame.Rect(SCREEN_W//2-110,370,220,50)
        pygame.draw.rect(surf,(0,80,160),py_btn,border_radius=10)
        pygame.draw.rect(surf,CYAN,py_btn,2,border_radius=10)
        play_t = rm.get_font(20,True).render("JUGAR", True, WHITE)
        surf.blit(play_t,(py_btn.centerx-play_t.get_width()//2,
                          py_btn.centery-play_t.get_height()//2))

        ex_btn = pygame.Rect(SCREEN_W//2-80,434,160,38)
        pygame.draw.rect(surf,(40,10,10),ex_btn,border_radius=8)
        pygame.draw.rect(surf,(80,20,20),ex_btn,1,border_radius=8)
        ex_t = rm.get_font(16).render("Salir", True,(160,80,80))
        surf.blit(ex_t,(ex_btn.centerx-ex_t.get_width()//2,
                        ex_btn.centery-ex_t.get_height()//2))

        ctrl_btn = pygame.Rect(SCREEN_W//2-240,434,150,38)
        pygame.draw.rect(surf,(10,30,60),ctrl_btn,border_radius=8)
        pygame.draw.rect(surf,CYAN,ctrl_btn,1,border_radius=8)
        ctrl_t = rm.get_font(15).render("Controles", True, CYAN)
        surf.blit(ctrl_t,(ctrl_btn.centerx-ctrl_t.get_width()//2,
                          ctrl_btn.centery-ctrl_t.get_height()//2))

        cred_btn = pygame.Rect(SCREEN_W//2+90,434,150,38)
        pygame.draw.rect(surf,(30,20,10),cred_btn,border_radius=8)
        pygame.draw.rect(surf,YELLOW,cred_btn,1,border_radius=8)
        cred_t = rm.get_font(15).render("Créditos", True, YELLOW)
        surf.blit(cred_t,(cred_btn.centerx-cred_t.get_width()//2,
                          cred_btn.centery-cred_t.get_height()//2))

        self._btn_rects = [py_btn, ex_btn, ctrl_btn, cred_btn]

        nav = rm.get_font(13).render("◄ ► Cambiar modo de juego  |  [N] Música", True,(50,55,70))
        surf.blit(nav,(SCREEN_W//2-nav.get_width()//2, 488))

        if self.game.sfx.music_muted:
            mt = rm.get_font(13,True).render("MÚSICA DESACTIVADA", True,(120,50,50))
            surf.blit(mt,(SCREEN_W//2-mt.get_width()//2, 510))

        seed_t = rm.get_font(12).render(f"Seed: {self.game.seed}", True,(40,44,58))
        surf.blit(seed_t,(SCREEN_W//2-seed_t.get_width()//2, SCREEN_H-26))


class Game:
    def __init__(self):
        pygame.init()
        self.screen    = pygame.display.set_mode((SCREEN_W,SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock     = pygame.time.Clock()
        self.rm        = ResourceManager()
        self.sfx       = SoundManager()
        self.running   = True
        self.state     = GameState.MENU
        self.game_mode = GAMEMODE_CLASSIC

        self.seed       = random.randint(0,999999)
        self.world_gen  = WorldGenerator(self.seed)
        self.skill_tree = SkillTree()

        self.bullet_pool = ObjectPool(lambda: Bullet(),      BULLET_POOL_SIZE)
        self.enemy_pool  = self._make_enemy_pool()

        self.player       = Player(self)
        self.wave_manager = WaveManager(self)
        self.hud          = HUD(self)
        self.skill_screen = SkillTreeScreen(self)
        self.pause_menu   = PauseMenu(self)
        self.main_menu    = MainMenu(self)
        self.controls_screen = ControlsScreen(self)
        self.credits_screen  = CreditsScreen(self)

        self.quadtree   = Quadtree(QTBounds(0,0,WORLD_W,WORLD_H))
        self.camera     = Vec2(0,0)
        self._particles: List[dict] = []
        self._nebula_surf = self._build_nebula()

        self._ta_time  = 0.0
        self._ta_limit = 180.0
        self._surv_spawn_cd = 0.0
        self._active_meteors: List["EnemyMeteor"] = []
        self._last_titan_level = 0
        self._warp: Optional[WarpTransition] = None
        self._final_stats: dict = {}
        self._stats_scroll = 0
        self.sfx.play_music("menu")

    def _make_enemy_pool(self) -> "ObjectPool":
        counts = {
            Enemy:        50,
            HeavyEnemy:   20,
            SniperEnemy:  20,
            KamikazeEnemy:20,
            CarrierEnemy: 10,
            TitanBoss:     3,
        }
        pool_list = []
        for cls, n in counts.items():
            for _ in range(n):
                pool_list.append(cls(self))
        random.shuffle(pool_list)
        p = ObjectPool.__new__(ObjectPool)
        p._pool   = pool_list
        p._active = []
        return p

    def _begin_warp(self):
        """Start the warp animation; game initialises silently in the background."""
        self._warp = WarpTransition(SCREEN_W, SCREEN_H)
        self._start_game()                          # prepare world now (silent)
        self.state = GameState.WARP                 # but show warp first
        self.sfx.stop_music()                       # silence menu music
        self.sfx.play("warp")                       # play warp sfx

    def _build_nebula(self):
        scale = 8
        w,h   = SCREEN_W//scale, SCREEN_H//scale
        surf  = pygame.Surface((w,h))
        for px in range(w):
            for py in range(h):
                surf.set_at((px,py), self.world_gen.get_nebula_color(
                    self.player.transform.pos.x+(px-w//2)*scale,
                    self.player.transform.pos.y+(py-h//2)*scale))
        return pygame.transform.scale(surf,(SCREEN_W,SCREEN_H))

    def run(self):
        self._last_dt = 0.016
        while self.running:
            dt  = min(self.clock.tick(FPS)/1000.0, 0.05)
            self._last_dt = dt
            fps = self.clock.get_fps()
            self._events()
            self._update(dt)
            self._draw(fps)
        self.skill_tree.save()
        pygame.quit()

    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False

            elif self.state == GameState.MENU:
                self.main_menu.handle_event(ev)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_n:
                    self.sfx.toggle_music()

            elif self.state == GameState.WARP:
                pass  # eat all input during warp

            elif self.state == GameState.PLAYING:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    elif ev.key == pygame.K_2:
                        self._skill_from_pause = False
                        self.state = GameState.SKILL
                    elif ev.key == pygame.K_m:
                        self.sfx.toggle_mute()
                    elif ev.key == pygame.K_n:
                        self.sfx.toggle_music()

            elif self.state == GameState.SKILL:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_2:
                    self.state = GameState.PLAYING
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    # Return to pause menu if we came from there, else playing
                    if hasattr(self, '_skill_from_pause') and self._skill_from_pause:
                        self.state = GameState.PAUSED
                    else:
                        self.state = GameState.PLAYING
                else:
                    self.skill_screen.handle_event(ev)

            elif self.state == GameState.PAUSED:
                action = self.pause_menu.handle_event(ev)
                if action == "Continuar":
                    self.state = GameState.PLAYING
                elif action == "Árbol de Habilidades":
                    self._skill_from_pause = True
                    self.state = GameState.SKILL
                elif action == "Controles":
                    self.controls_screen._from_state = GameState.PAUSED
                    self.state = GameState.CONTROLS
                elif action == "Menú Principal":
                    self.skill_tree.save()
                    self.sfx.play_music("menu")
                    self.state = GameState.MENU
                elif action == "Salir":
                    self.running = False

            elif self.state == GameState.GAME_OVER:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RETURN:
                        self._begin_warp()
                    elif ev.key == pygame.K_ESCAPE:
                        self.sfx.play_music("menu")
                        self.state = GameState.MENU
                    elif ev.key == pygame.K_UP:
                        self._stats_scroll = max(0, self._stats_scroll - 30)
                    elif ev.key == pygame.K_DOWN:
                        self._stats_scroll += 30
                if ev.type == pygame.MOUSEWHEEL:
                    self._stats_scroll = max(0, self._stats_scroll - ev.y * 25)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    rects = getattr(self, '_gameover_btn_rects', [])
                    if len(rects) > 0 and rects[0].collidepoint(ev.pos):
                        self._begin_warp()
                    elif len(rects) > 1 and rects[1].collidepoint(ev.pos):
                        self.sfx.play_music("menu")
                        self.state = GameState.MENU

            elif self.state == GameState.CONTROLS:
                self.controls_screen.handle_event(ev)

            elif self.state == GameState.CREDITS:
                self.credits_screen.handle_event(ev)

    def _update(self, dt):
        # ── warp transition ──────────────────────────────────────────────────
        if self.state == GameState.WARP:
            if self._warp:
                self._warp.update(dt)
                if self._warp.done:
                    self._warp = None
                    self.state = GameState.PLAYING
                    track_map  = {
                        GAMEMODE_CLASSIC:    "classic",
                        GAMEMODE_SURVIVAL:   "survival",
                        GAMEMODE_TIMEATTACK: "timeattack",
                    }
                    self.sfx.play_music(track_map.get(self.game_mode, "classic"))
            return

        if self.state != GameState.PLAYING:
            return

        p = self.player
        self.camera += (p.transform.pos - Vec2(SCREEN_W,SCREEN_H)/2 - self.camera) * min(dt*8,1.0)

        if self.game_mode == GAMEMODE_TIMEATTACK:
            self._ta_time += dt
            if self._ta_time >= self._ta_limit:
                self._snapshot_stats()
                self.state = GameState.GAME_OVER
                return

        if self.game_mode == GAMEMODE_SURVIVAL:
            self._surv_spawn_cd -= dt
            if self._surv_spawn_cd <= 0:
                self._surv_spawn_cd = max(0.4, 2.2 - self.player.level_sys.level * 0.12)
                self._spawn_survival_enemy()

        p.update(dt)
        self.wave_manager.update(dt)

        player_level = p.level_sys.level
        self.world_gen.set_player_level(player_level)

        if player_level >= 8 and player_level % 8 == 0 and player_level != self._last_titan_level:
            self._last_titan_level = player_level
            self._spawn_titan()

        active_en = [e for e in self.enemy_pool.active if e.active]
        for e in active_en:
            e.update(dt, active_en)

        # ── auto-advance wave when battlefield is clear ──────────────────────
        if (self.game_mode == GAMEMODE_CLASSIC and
                self.wave_manager.wave > 0 and
                len(active_en) == 0 and
                self.wave_manager.timer < self.wave_manager.wave_interval - 2.0):
            self.wave_manager.timer = self.wave_manager.wave_interval  # trigger now

        if self.game_mode == GAMEMODE_TIMEATTACK:
            # in time-attack, wave also triggers when cleared
            if (self.wave_manager.wave > 0 and
                    len(active_en) == 0 and
                    self.wave_manager.timer < self.wave_manager.wave_interval - 2.0):
                self.wave_manager.timer = self.wave_manager.wave_interval

        dead_b = [b for b in list(self.bullet_pool.active) if not b.update(dt)]
        for b in dead_b:
            self.bullet_pool.release(b)

        asteroids = []
        cx_s = int(p.transform.pos.x // SECTOR_SIZE)
        cy_s = int(p.transform.pos.y // SECTOR_SIZE)
        for ddx in range(-2,3):
            for ddy in range(-2,3):
                sx2,sy2 = cx_s+ddx, cy_s+ddy
                if 0<=sx2<WORLD_W//SECTOR_SIZE and 0<=sy2<WORLD_H//SECTOR_SIZE:
                    asteroids.extend(self.world_gen.get_sector(sx2,sy2))
        for a in asteroids:
            a.update(dt)

        self.quadtree.clear()
        for a in asteroids:
            self.quadtree.insert(a)
        for e in active_en:
            self.quadtree.insert(e)
        self.quadtree.insert(p)

        self._collisions(asteroids, active_en)
        self._active_meteors = [m for m in self._active_meteors if m.active]
        for m in self._active_meteors:
            m.update(dt)
        self._update_particles(dt)

        if p.health.hp <= 0:
            self._snapshot_stats()
            self.state = GameState.GAME_OVER

    def _spawn_titan(self):
        pp  = self.player.transform.pos
        ang = random.uniform(0, math.pi*2)
        ex  = max(100, min(WORLD_W-100, pp.x + math.cos(ang)*700))
        ey  = max(100, min(WORLD_H-100, pp.y + math.sin(ang)*700))
        for obj in self.enemy_pool._pool:
            if isinstance(obj, TitanBoss):
                self.enemy_pool._pool.remove(obj)
                self.enemy_pool._active.append(obj)
                EnemyFactory.configure(obj, "titan")
                obj.spawn(ex, ey)
                self.sfx.play("titan_spawn")
                self.sfx.play("boss_warning")
                return
        for obj in self.enemy_pool.active:
            if isinstance(obj, TitanBoss) and not obj.active:
                EnemyFactory.configure(obj, "titan")
                obj.spawn(ex, ey)
                self.sfx.play("titan_spawn")
                self.sfx.play("boss_warning")
                return

    def _snapshot_stats(self):
        p  = self.player
        ls = p.level_sys
        st = self.skill_tree
        self._final_stats = {
            "score":       p.score,
            "level":       ls.level,
            "wave":        self.wave_manager.wave,
            "kills":       dict(p.kills),
            "total_kills": p.total_kills,
            "play_time":   p.play_time,
            "skill_pts":   st.points,
            "skills":      {k: v.level for k,v in st.skills.items()},
            "mode":        self.game_mode,
        }

    def _active_enemy_count(self) -> int:
        return sum(1 for e in self.enemy_pool.active if e.active)

    def _spawn_survival_enemy(self):
        pp   = self.player.transform.pos
        lvl  = self.player.level_sys.level
        pool = ["scout","fighter","kamikaze","sniper","heavy"]
        w    = [5, 3, max(1,lvl), max(1,lvl-1), max(1,lvl-2)]
        count = random.randint(2, 3 + lvl // 2)
        for _ in range(count):
            ang  = random.uniform(0, math.pi*2)
            dist = random.uniform(350, 650)
            ex   = max(50, min(WORLD_W-50, pp.x+math.cos(ang)*dist))
            ey   = max(50, min(WORLD_H-50, pp.y+math.sin(ang)*dist))
            e    = self.enemy_pool.get()
            if e:
                etype = random.choices(pool, weights=w)[0]
                EnemyFactory.configure(e, etype)
                e.spawn(ex, ey)

    def _collisions(self, asteroids, enemies):
        p          = self.player
        to_release = []

        for bullet in list(self.bullet_pool.active):
            candidates = self.quadtree.retrieve(bullet)
            hit        = False
            for obj in candidates:
                if hit: break
                if isinstance(obj, Enemy) and obj.active and bullet.owner=="player":
                    if bullet.rect.colliderect(obj.rect):
                        dead = obj.health.take_damage(bullet.damage)
                        self._particles_spawn(obj.transform.pos, ORANGE, 6)
                        if dead:
                            xp_map = {
                                "scout":40,"fighter":80,"heavy":130,
                                "sniper":100,"kamikaze":60,"carrier":200,"boss":350,"titan":1200
                            }
                            sc_map = {
                                "scout":100,"fighter":200,"heavy":280,
                                "sniper":180,"kamikaze":120,"carrier":400,"boss":700,"titan":3000
                            }
                            xp  = xp_map.get(obj.etype, 40)
                            pts = sc_map.get(obj.etype, 100)
                            p.score += pts
                            obj.active = False
                            self.enemy_pool.release(obj)
                            p.add_xp(xp)
                            p.kills[obj.etype] = p.kills.get(obj.etype, 0) + 1
                            p.total_kills += 1
                            self.skill_tree.save()
                            self._particles_spawn(obj.transform.pos, RED, 15)
                            if obj.etype == "titan":
                                self.sfx.play("explosion_boss")
                                for _ in range(3):
                                    self._particles_spawn(obj.transform.pos, PURPLE, 20)
                            elif obj.etype == "boss":
                                self.sfx.play("explosion_boss")
                            elif obj.etype in ("heavy", "carrier"):
                                self.sfx.play("explosion")
                            else:
                                self.sfx.play("explosion_small")
                        if self.skill_tree.skills["pierce"].level == 0:
                            to_release.append(bullet)
                            hit = True
                elif isinstance(obj, Asteroid) and bullet.owner=="player":
                    if bullet.rect.colliderect(obj.rect):
                        obj.hp -= bullet.damage
                        self._particles_spawn(obj.pos, GRAY, 4)
                        self.sfx.play("asteroid_hit", 0.25)
                        if obj.hp <= 0:
                            p.score += 20
                            p.add_xp(10)
                        to_release.append(bullet)
                        hit = True

        for bullet in list(self.bullet_pool.active):
            if bullet.owner=="enemy" and bullet.rect.colliderect(p.rect):
                p.take_damage(bullet.damage)
                self._particles_spawn(p.transform.pos, RED, 4)
                to_release.append(bullet)

        for b in set(to_release):
            if b in self.bullet_pool.active:
                self.bullet_pool.release(b)

        for a in asteroids:
            if p.rect.colliderect(a.rect):
                d = p.transform.pos - a.pos
                if d.length() > 0:
                    p.transform.vel += d.normalize() * 3
                p.take_damage(4)

    def _particles_spawn(self, pos, color, count):
        for _ in range(count):
            a   = random.uniform(0, math.pi*2)
            spd = random.uniform(1.5, 4.5)
            self._particles.append({
                "pos":     Vec2(pos),
                "vel":     Vec2(math.cos(a)*spd, math.sin(a)*spd),
                "life":    random.uniform(0.3, 0.9),
                "max_life":0.9,
                "color":   color,
                "size":    random.randint(2,5)
            })

    def _update_particles(self, dt):
        alive = []
        for p in self._particles:
            p["life"] -= dt
            p["pos"]  += p["vel"] * dt * 60
            p["vel"]  *= 0.91
            if p["life"] > 0:
                alive.append(p)
        self._particles = alive

    def _draw(self, fps):
        s = self.screen
        if   self.state == GameState.MENU:
            self.main_menu.draw(s, self._last_dt)
        elif self.state == GameState.WARP:
            if self._warp:
                self._warp.draw(s)
        elif self.state == GameState.PLAYING:
            self._draw_world(s)
            self.hud.draw(s, fps)
        elif self.state == GameState.SKILL:
            self._draw_world(s)
            self.hud.draw(s, fps)
            self.skill_screen.draw(s)
        elif self.state == GameState.PAUSED:
            self._draw_world(s)
            self.hud.draw(s, fps)
            self.pause_menu.draw(s)
        elif self.state == GameState.GAME_OVER:
            self._draw_world(s)
            self._draw_game_over(s)
        elif self.state == GameState.CONTROLS:
            # Draw background (menu or game world depending on origin)
            if self.controls_screen._from_state == GameState.MENU:
                self.main_menu.draw(s, self._last_dt)
            else:
                self._draw_world(s)
                self.hud.draw(s, fps)
            self.controls_screen.draw(s)
        elif self.state == GameState.CREDITS:
            self.main_menu.draw(s, self._last_dt)
            self.credits_screen.draw(s)
        pygame.display.flip()

    def _draw_world(self, surf):
        surf.fill(DARK_BLUE)
        surf.blit(self._nebula_surf,(0,0))

        cx_s = int(self.player.transform.pos.x // SECTOR_SIZE)
        cy_s = int(self.player.transform.pos.y // SECTOR_SIZE)
        for ddx in range(-3,4):
            for ddy in range(-3,4):
                for wx,wy,sz,br in self.world_gen.get_stars(cx_s+ddx,cy_s+ddy):
                    sx2 = int(wx - self.camera.x*0.28) % SCREEN_W
                    sy2 = int(wy - self.camera.y*0.28) % SCREEN_H
                    pygame.draw.circle(surf,(br,br,br),(sx2,sy2),sz)

        cx2 = int(self.player.transform.pos.x // SECTOR_SIZE)
        cy2 = int(self.player.transform.pos.y // SECTOR_SIZE)
        for ddx in range(-2,3):
            for ddy in range(-2,3):
                sx3,sy3 = cx2+ddx, cy2+ddy
                if 0<=sx3<WORLD_W//SECTOR_SIZE and 0<=sy3<WORLD_H//SECTOR_SIZE:
                    for a in self.world_gen.get_sector(sx3,sy3):
                        a.draw(surf, self.camera)

        for e in self.enemy_pool.active:
            if e.active:
                e.draw(surf, self.camera)

        for b in self.bullet_pool.active:
            b.draw(surf, self.camera)

        for m in self._active_meteors:
            m.draw(surf, self.camera)

        self.player.draw(surf, self.camera)

        for p in self._particles:
            sx4 = int(p["pos"].x - self.camera.x)
            sy4 = int(p["pos"].y - self.camera.y)
            al  = int(255 * p["life"] / p["max_life"])
            gs  = pygame.Surface((p["size"]*2, p["size"]*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*p["color"][:3],al),(p["size"],p["size"]),p["size"])
            surf.blit(gs,(sx4-p["size"],sy4-p["size"]))

        bx = int(-self.camera.x)
        by = int(-self.camera.y)
        pygame.draw.rect(surf,(80,0,0),(bx,by,WORLD_W,WORLD_H),3)

    def _draw_game_over(self, surf):
        rm = self.rm
        st = self._final_stats
        if not st:
            return

        # ── motivational space messages by score tier ────────────────────────
        score = st.get("score", 0)
        kills = st.get("total_kills", 0)
        messages = [
            (20000, "¡LEYENDA GALÁCTICA! Las estrellas guardarán tu nombre por eones."),
            (10000, "¡Digno de los Guardianes del Cosmos! El universo te reconoce."),
            (5000,  "¡Explorador de élite! Cada supernova es un escalón hacia la gloria."),
            (2000,  "Las nebulosas recuerdan a quienes se atreven a atravesarlas. ¡Sigue!"),
            (500,   "Cada estrella comenzó como polvo cósmico. Tú también brillarás."),
            (0,     "El vacío del espacio no es el fin — es el comienzo de tu odisea."),
        ]
        # Gather all messages for this score tier and above
        candidate_msgs = [msg for threshold, msg in messages if score >= threshold]
        if not candidate_msgs:
            candidate_msgs = [messages[-1][1]]
        # Rotate through candidates without repeating, using a session index
        if not hasattr(self, '_motivation_used'):
            self._motivation_used = []
        # Filter out used ones; reset if all used
        unused = [m for m in candidate_msgs if m not in self._motivation_used]
        if not unused:
            self._motivation_used = []
            unused = candidate_msgs
        motivation = unused[0]
        if motivation not in self._motivation_used:
            self._motivation_used.append(motivation)

        skill_names = {
            "fire_rate":"Cadencia","bullet_dmg":"Daño","speed":"Velocidad",
            "shield":"Escudo","multi_shot":"Multidisparo","pierce":"Perforadora"
        }

        # ── layout constants ─────────────────────────────────────────────────
        PAD     = 28
        CARD_W  = 860
        CARD_X  = SCREEN_W//2 - CARD_W//2
        SCROLL  = self._stats_scroll
        ROW_H   = 30

        # dim background
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 10, 210))
        surf.blit(ov, (0, 0))

        # scrollable canvas
        content_h = 820
        canvas    = pygame.Surface((CARD_W, content_h), pygame.SRCALPHA)

        y = 0

        # ── GAME OVER header ─────────────────────────────────────────────────
        def sh(txt, size, color, cy, bold=True, canvas=canvas):
            s  = rm.get_font(size, bold).render(txt, True, (10,10,30))
            s2 = rm.get_font(size, bold).render(txt, True, color)
            cx2 = CARD_W//2 - s2.get_width()//2
            canvas.blit(s,  (cx2+2, cy+2))
            canvas.blit(s2, (cx2,   cy))

        def left(txt, size, color, cy, x=PAD, bold=False, canvas=canvas):
            s = rm.get_font(size, bold).render(txt, True, color)
            canvas.blit(s, (x, cy))

        def right(txt, size, color, cy, canvas=canvas):
            s = rm.get_font(size, True).render(txt, True, color)
            canvas.blit(s, (CARD_W - PAD - s.get_width(), cy))

        def divider(cy, col=(40,40,80), canvas=canvas):
            pygame.draw.line(canvas, col, (PAD, cy), (CARD_W-PAD, cy), 1)

        # Title
        sh("GAME OVER", 46, RED, y); y += 56
        mode_col = {
            GAMEMODE_CLASSIC: CYAN, GAMEMODE_SURVIVAL: ORANGE, GAMEMODE_TIMEATTACK: YELLOW
        }.get(st.get("mode",""), WHITE)
        sh(f"Modo: {st.get('mode','')}", 18, mode_col, y); y += 32
        divider(y); y += 14

        # ── CORE STATS ───────────────────────────────────────────────────────
        sh("ESTADÍSTICAS DE MISIÓN", 20, YELLOW, y, bold=True); y += 30
        divider(y, (60,60,100)); y += 10

        mins = int(st.get("play_time",0)//60)
        secs = int(st.get("play_time",0)%60)
        rows = [
            ("🏆  Puntuación final",  f"{st.get('score',0):,}",   YELLOW),
            ("⏱  Tiempo de misión",   f"{mins}m {secs:02d}s",     CYAN),
            ("⭐  Nivel alcanzado",    str(st.get("level",1)),     GREEN),
            ("🌊  Oleada máxima",      str(st.get("wave",0)),      (100,180,255)),
            ("💀  Enemigos eliminados",str(st.get("total_kills",0)),(230,80,80)),
            ("🔮  Skill pts restantes",str(st.get("skill_pts",0)), PURPLE),
        ]
        for label, value, col in rows:
            left(label,  16, (180,180,200), y)
            right(value, 17, col, y)
            y += ROW_H
        y += 6; divider(y); y += 14

        # ── ENEMIES KILLED BREAKDOWN ─────────────────────────────────────────
        sh("BAJAS POR TIPO", 18, (200,120,255), y, bold=True); y += 28
        divider(y, (60,60,100)); y += 10

        kill_map = st.get("kills", {})
        kill_order = ["scout","fighter","kamikaze","sniper","heavy","carrier","boss","titan"]
        kill_cols  = {
            "scout":   (120,200,255), "fighter": (200,200,100),
            "kamikaze":(255,140,60),  "sniper":  (200,80,255),
            "heavy":   (80,220,80),   "carrier": (0,200,200),
            "boss":    (255,80,80),   "titan":   (220,80,255),
        }
        kill_names = {
            "scout":"Explorador","fighter":"Cazador","kamikaze":"Kamikaze",
            "sniper":"Francotirador","heavy":"Pesado","carrier":"Transportador",
            "boss":"Jefe","titan":"TITAN"
        }
        shown = [(k, kill_map.get(k,0)) for k in kill_order if kill_map.get(k,0)>0]
        if not shown:
            left("  — Sin bajas registradas —", 15, GRAY, y); y += ROW_H
        else:
            for k, count in shown:
                col = kill_cols.get(k, WHITE)
                left(f"  {kill_names.get(k,k)}", 15, col, y)
                right(str(count), 16, col, y)
                # small bar
                bar_w = min(200, count * 8)
                pygame.draw.rect(canvas, (30,30,50),  (CARD_W//2-80, y+4, 200, 12), border_radius=4)
                pygame.draw.rect(canvas, (*col, 180), (CARD_W//2-80, y+4, bar_w, 12), border_radius=4)
                y += ROW_H - 4
        y += 10; divider(y); y += 14

        # ── SKILL LEVELS ─────────────────────────────────────────────────────
        sh("MEJORAS CONSEGUIDAS", 18, YELLOW, y, bold=True); y += 28
        divider(y, (60,60,100)); y += 10

        skills = st.get("skills", {})
        skill_max = {"fire_rate":5,"bullet_dmg":5,"speed":4,"shield":3,"multi_shot":3,"pierce":2}
        for sk, lv in skills.items():
            max_lv = skill_max.get(sk, 5)
            name   = skill_names.get(sk, sk)
            col    = GREEN if lv >= max_lv else (CYAN if lv > 0 else GRAY)
            left(f"  {name}", 15, col, y)
            # pips
            for pip in range(max_lv):
                px2 = CARD_W - PAD - (max_lv-pip)*22
                pc  = YELLOW if pip < lv else (40,40,60)
                pygame.draw.circle(canvas, pc, (px2, y+8), 7)
                pygame.draw.circle(canvas, WHITE, (px2, y+8), 7, 1)
            lv_txt = rm.get_font(13, True).render(f"Lv {lv}/{max_lv}", True, col)
            canvas.blit(lv_txt, (CARD_W - PAD - max_lv*22 - lv_txt.get_width() - 10, y+1))
            y += ROW_H - 2
        y += 12; divider(y); y += 18

        # ── MOTIVATIONAL MESSAGE ─────────────────────────────────────────────
        box_h_mot = 70
        pygame.draw.rect(canvas, (8,8,28), (PAD-8, y-4, CARD_W-PAD*2+16, box_h_mot), border_radius=8)
        pygame.draw.rect(canvas, (60,40,120), (PAD-8, y-4, CARD_W-PAD*2+16, box_h_mot), 1, border_radius=8)
        # word-wrap the message centered
        words = motivation.split()
        lines2, cur2 = [], ""
        max_w = CARD_W - PAD*3
        for w in words:
            test = (cur2 + " " + w).strip()
            if rm.get_font(14).size(test)[0] < max_w:
                cur2 = test
            else:
                lines2.append(cur2); cur2 = w
        if cur2: lines2.append(cur2)
        total_text_h = len(lines2) * 20
        text_start_y = y + (box_h_mot - total_text_h) // 2
        for li, line in enumerate(lines2):
            lt = rm.get_font(14, li==0).render(line, True, (200,180,255))
            canvas.blit(lt, (CARD_W//2 - lt.get_width()//2, text_start_y + li*20))
        y += box_h_mot + 10

        # ── blit canvas with scroll clipping ────────────────────────────────
        visible_h   = SCREEN_H - 100
        card_y_top  = 50
        max_scroll  = max(0, y - visible_h)
        self._stats_scroll = min(self._stats_scroll, max_scroll)
        SCROLL = self._stats_scroll

        card_bg = pygame.Surface((CARD_W + 4, visible_h + 4), pygame.SRCALPHA)
        pygame.draw.rect(card_bg, (6,6,22,240), (0,0,CARD_W+4,visible_h+4), border_radius=10)
        pygame.draw.rect(card_bg, (40,40,80,200), (0,0,CARD_W+4,visible_h+4), 1, border_radius=10)
        surf.blit(card_bg, (CARD_X-2, card_y_top-2))

        clip_surf = pygame.Surface((CARD_W, visible_h), pygame.SRCALPHA)
        clip_surf.fill((0,0,0,0))
        clip_surf.blit(canvas, (0, -SCROLL))
        surf.blit(clip_surf, (CARD_X, card_y_top))

        # scroll hint
        if max_scroll > 0:
            sh_t = rm.get_font(12).render("↑↓ Desplazar", True, (80,80,100))
            surf.blit(sh_t, (CARD_X + CARD_W - sh_t.get_width() - 10, card_y_top + visible_h + 4))

        # ── action buttons ────────────────────────────────────────────────────
        btn_y = SCREEN_H - 44
        self._gameover_btn_rects = []
        def draw_btn(text, cx, col_bg, col_border, col_txt):
            bw, bh = 200, 36
            bx2 = cx - bw//2
            r = pygame.Rect(bx2, btn_y, bw, bh)
            pygame.draw.rect(surf, col_bg,     r, border_radius=8)
            pygame.draw.rect(surf, col_border, r, 2, border_radius=8)
            t2 = rm.get_font(16, True).render(text, True, col_txt)
            surf.blit(t2, (cx - t2.get_width()//2, btn_y + bh//2 - t2.get_height()//2))
            self._gameover_btn_rects.append(r)

        draw_btn("Reintentar", SCREEN_W//2 - 120, (0,50,120),(0,150,220), WHITE)
        draw_btn("Menú Principal", SCREEN_W//2 + 120, (60,10,10),(180,40,40), (220,120,120))

    def _start_game(self):
        self.skill_tree.new_game()
        self.seed         = random.randint(0,999999)
        self.world_gen    = WorldGenerator(self.seed)
        self.player       = Player(self)
        self.wave_manager = WaveManager(self)
        self.bullet_pool  = ObjectPool(lambda: Bullet(),     BULLET_POOL_SIZE)
        self.enemy_pool   = self._make_enemy_pool()
        self.quadtree     = Quadtree(QTBounds(0,0,WORLD_W,WORLD_H))
        self._particles   = []
        self.camera       = Vec2(0,0)
        self._nebula_surf = self._build_nebula()
        self.pause_menu   = PauseMenu(self)
        self.skill_screen = SkillTreeScreen(self)
        self.hud          = HUD(self)
        self._ta_time     = 0.0
        self._surv_spawn_cd = 2.0
        self._active_meteors = []
        self._last_titan_level = 0
        self._stats_scroll = 0
        self.wave_manager.timer = self.wave_manager.wave_interval - 4.0

        if self.state != GameState.WARP:
            self.state = GameState.PLAYING
            track_map = {
                GAMEMODE_CLASSIC:    "classic",
                GAMEMODE_SURVIVAL:   "survival",
                GAMEMODE_TIMEATTACK: "timeattack",
            }
            self.sfx.play_music(track_map.get(self.game_mode, "classic"))


if __name__ == "__main__":
    game = Game()
    game.run()