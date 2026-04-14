# Standard library and third-party imports required by the engine.
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

# Window dimensions, target frame-rate and window title.
SCREEN_W, SCREEN_H = 1280, 720
FPS   = 60
TITLE = "COSMIC ROGUELIKE"

# Named colour palette used throughout the rendering code.
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
HACK_GREEN = (0, 255, 120)
MAGENTA   = (255, 0, 200)
GOLD      = (255, 200, 50)

# Movement and projectile speed caps (world units per second at 60 FPS).
MAX_SPEED_PLAYER = 6.0
MAX_SPEED_ENEMY  = 3.0
BULLET_SPEED     = 15.0
BULLET_POOL_SIZE = 400
ENEMY_POOL_SIZE  = 120

# World and sector dimensions. The world is subdivided into SECTOR_SIZE tiles
# for efficient procedural generation and spatial queries.
WORLD_W, WORLD_H = 5120, 5120
SECTOR_SIZE      = 512
ASTEROID_DENSITY_BASE = 0.70

# Quadtree capacity limits: max objects per node before subdivision,
# and the maximum recursion depth.
QT_MAX_OBJECTS = 8
QT_MAX_LEVELS  = 6

# Boids flocking weights: separation keeps ships from overlapping,
# alignment matches heading, cohesion groups them, seek pulls toward the player.
W_SEPARATION  = 1.8
W_ALIGNMENT   = 1.0
W_COHESION    = 0.9
W_SEEK_PLAYER = 0.5
NEIGHBOR_DIST = 120.0
SEP_DIST      = 45.0

# Enemy AI distances: detection range, attack range, and HP ratio at which
# enemies switch to flee behaviour.
DETECT_DIST = 350.0
ATTACK_DIST = 200.0
FLEE_HEALTH = 0.25

# XP rewards per enemy type and level-scaling parameters.
XP_PER_SCOUT    = 40
XP_PER_FIGHTER  = 80
XP_PER_HEAVY    = 130
XP_PER_SNIPER   = 100
XP_PER_KAMIKAZE = 60
XP_PER_CARRIER  = 200
XP_PER_BOSS     = 350
XP_BASE         = 120
XP_SCALE        = 1.35



# Gravitational physics constants and miscellaneous gameplay thresholds.
PLANET_GRAVITY       = 380.0
PLANET_SLINGSHOT_CAP = 14.0
GHOST_SAVE_FILE      = "ghost_run.json"
WARP_GRID_COLS       = 18
WARP_GRID_ROWS       = 10
NEBULA_RADAR_THRESH  = 0.68
NEBULA_PLASMA_THRESH = 0.72
SHAKE_DECAY          = 8.0
NANO_BOT_ORBIT_R     = 55
NANO_BOT_ORBIT_T     = 3.0
ALERT_WAVE_SPEED     = 220.0

GRAVITY_ZONE_RADIUS  = 280
GRAVITY_STRENGTH     = 420.0
NEBULA_SLOW_FACTOR   = 0.55
CREATURE_SPEED       = 1.4
CREATURE_HP          = 60
MODULE_DROP_CHANCE   = 0.28
AI_LOG_MAX           = 6

# Game mode identifier strings used for state switching and music selection.
GAMEMODE_CLASSIC    = "Clásico"
GAMEMODE_SURVIVAL   = "Supervivencia"
GAMEMODE_TIMEATTACK = "Contrarreloj"
GAMEMODE_PRACTICE   = "Practica"

# Hack ability timings and visual configuration.
HACK_DURATION        = 2.8
HACK_COOLDOWN        = 12.0
HACK_COLOR           = (0, 255, 120)
HACK_RADIUS          = 420
FACTION_SWARM        = "swarm"
FACTION_DRONE        = "drone"
FACTION_DMG_BONUS    = 1.6
MOTION_BLUR_FRAMES   = 8
ZOOM_MIN             = 0.65
ZOOM_MAX             = 1.20
ZOOM_SPEED           = 2.0
BOSS_BULLET_HELL_CD  = 0.08
DATA_FRAG_DROP_CHANCE = 0.35
NEXUS_SAVE_FILE       = "nexus_data.json"
SCOREBOARD_SAVE_FILE  = "scoreboard.json"   # Persistent high-score table.

# Bullet-time (slow-motion) system parameters.
BULLET_TIME_HP_THRESH  = 0.10
BULLET_TIME_SCALE      = 0.28
BULLET_TIME_FADE_SPEED = 3.0
# Ambient darkness level for the deferred lighting pass (0 = no darkness,
# 255 = fully black). Lowered from 200 to 120 for a brighter ambient environment.
LIGHT_SURF_ALPHA       = 120
# Number of independent star layers used by the parallax background system.
PARALLAX_LAYERS        = 3
# Lifespan and burst size of hull-damage sparks.
SPARK_LIFE             = 0.45
SPARK_COUNT_HIT        = 8
# Camera shake triggered by proximity to Titan-class enemies.
SHAKE_TITAN_DIST       = 600
SHAKE_TITAN_STRENGTH   = 0.25




class AILog:
    """The sarcastic ship AI that comments on everything."""
    QUIPS_DANGER = [
        "Recomiendo HUIR. Ahora mismo.", "Shields al 0%. Interesante decisión.",
        "Matemáticamente, estás muerto.", "¿Seguro que esto es una táctica?",
    ]
    QUIPS_KILL_STREAK = [
        "Impresionante. Casi como un piloto de verdad.", "Racha de bajas. Inusual.",
        "Quizás sobrevivas después de todo.", "Estadísticas actualizadas: menos malo.",
        "Elimina 10 más y lo anoto en mi log positivo.",
    ]
    QUIPS_IDLE = [
        "Detectando amenazas... o café. Difícil de decir.",
        "Sistema de propulsión: operativo. Piloto: cuestionable.",
        "Escaneo de sector completado. Nada interesante. Como siempre.",
        "Energía reactora al 94%. El 6% restante es suspenso.",
        "Recuerda: los asteroides no son decorativos.",
        "IA v7.3 en línea. Esperando órdenes coherentes.",
        "He calculado 1.4M de formas de morir aquí. Buena suerte.",
    ]
    QUIPS_ECO = [
        "Los enemigos aprenden de tus tácticas. Variedad, piloto.",
        "Mutación detectada en hostiles. Tu culpa.",
        "Siguiente oleada: más rápida, más resistente. ¿Contento?",
    ]
    QUIPS_MODULE = [
        "Módulo recogido. Arquitectura naval... creativa.",
        "Componente enemigo instalado. Espero que no explote.",
        "Tu nave ya no es tuya. Es una colección.",
    ]
    QUIPS_ZONE = [
        "Zona gravitacional detectada. Consejo: no acercarse.",
        "Agujero negro a la vista. Procede con... precaución.",
        "Nebulosa densa. Propulsores al 55%. Encantador.",
    ]
    QUIPS_SYNERGY = {
        "laser_shield":  "Has aprendido a usar las paredes. Eficiente, supongo.",
        "nano_storm":    "Los nano-bots ahora generan campo eléctrico. Mi creación favorita.",
        "gravity_burst": "El EMP también empuja. Usas la física como arma. Bien.",
        "overdrive":     "Tu estela de movimiento es ahora letal. Poético.",
        "echo_shot":     "Disparo eco activo. Cada décimo balazo busca solo. Elegante.",
    }
    QUIPS_FACTION_SWARM = [
        "TRADUCCIÓN ENJAMBRE: '¡Consumir! ¡Crecer! ¡Devorar todo!'",
        "ENJAMBRE: señal química detectada — 'Intrusos en nuestro sector de caza.'",
        "ENJAMBRE: '¿Qué es esa cosa pequeña? ¿Comestible?'",
    ]
    QUIPS_FACTION_DRONE = [
        "TRADUCCIÓN DRONES: 'OBJETIVO: extracción. OBSTÁCULO: orgánicos. SOLUCIÓN: eliminar.'",
        "DRONES: protocolo 7-KRIBEL activado — purga de sector iniciada.",
        "DRONES: 'La eficiencia requiere la eliminación de variables no controladas.'",
    ]
    QUIPS_BULLET_TIME = [
        "MODO CRÍTICO — Dilatación temporal activada. Sobrevive.",
        "Integridad estructural: CRÍTICA. Tiempo: relativo. Ahora esquiva.",
        "Último 10%. La física te da una oportunidad. No la desperdicies.",
    ]

    def __init__(self):
        self._lines: List[Tuple[str,float]] = []
        self._cd    = 0.0
        self._streak_kill = 0
        self._last_hp  = 100

    def update(self, dt, player, eco: "EcoEvolution"):
        self._cd -= dt
        self._lines = [(t, ttl-dt) for t,ttl in self._lines if ttl-dt > 0]

        if self._cd > 0:
            return
        self._cd = random.uniform(5.0, 11.0)

        hp_ratio = player.health.ratio
        kills    = player.total_kills

        if hp_ratio < 0.25:
            self._push(random.choice(self.QUIPS_DANGER), 5.0)
        elif kills != self._streak_kill and kills > 0 and kills % 10 == 0:
            self._streak_kill = kills
            self._push(random.choice(self.QUIPS_KILL_STREAK), 5.5)
        elif eco.evolved_color_mix > 0.2 and random.random() < 0.35:
            self._push(random.choice(self.QUIPS_ECO), 4.5)
        else:
            self._push(random.choice(self.QUIPS_IDLE), 4.0)

    def push_module(self):
        self._push(random.choice(self.QUIPS_MODULE), 4.5)

    def push_zone(self):
        self._push(random.choice(self.QUIPS_ZONE), 4.5)

    def push_synergy(self, synergy_id: str):
        """Called when player unlocks a synergy in the Nexus."""
        msg = self.QUIPS_SYNERGY.get(synergy_id)
        if msg:
            self._push(msg, 6.0)

    def push_faction_war(self, faction: str):
        """Called when a faction conflict erupts — AI 'translates' enemy chatter."""
        if faction == FACTION_SWARM:
            self._push(random.choice(self.QUIPS_FACTION_SWARM), 5.5)
        elif faction == FACTION_DRONE:
            self._push(random.choice(self.QUIPS_FACTION_DRONE), 5.5)

    def push_bullet_time(self):
        self._push(random.choice(self.QUIPS_BULLET_TIME), 5.0)

    def _push(self, text: str, ttl: float):
        self._lines.append((text, ttl))
        if len(self._lines) > AI_LOG_MAX:
            self._lines.pop(0)

    def draw(self, surf, rm):
        if not self._lines:
            return
        x, y0 = 20, SCREEN_H - 150
        for text, ttl in reversed(self._lines[-3:]):
            alpha = min(255, int(ttl * 140))
            col   = (0, int(180 * ttl / 5.5), int(200 * ttl / 5.5))
            t_surf = rm.get_font(12).render(text, True, (80, 200, 180))
            ts2    = pygame.Surface(t_surf.get_size(), pygame.SRCALPHA)
            ts2.fill((0,0,0,0))
            ts2.blit(t_surf, (0,0))
            ts2.set_alpha(alpha)
            surf.blit(ts2, (x, y0))
            y0 -= 18



class DataNexus:
    """
    Persistent meta-progression. Data Fragments survive death.
    Unlocks lore entries and permanent Synergies between weapon upgrades.
    """
    SYNERGIES = [
        {
            "id": "laser_shield",
            "name": "Rebote de Escudo",
            "desc": "Tus disparos rebotan en los bordes de pantalla una vez.",
            "cost": 25,
            "unlocked": False,
        },
        {
            "id": "nano_storm",
            "name": "Tormenta de Nano-Bots",
            "desc": "Los Nano-Bots generan un campo eléctrico que ralentiza enemigos cercanos.",
            "cost": 30,
            "unlocked": False,
        },
        {
            "id": "gravity_burst",
            "name": "Pulso Gravitacional",
            "desc": "Al activar el Hack, los fragmentos también empujan a los enemigos.",
            "cost": 20,
            "unlocked": False,
        },
        {
            "id": "overdrive",
            "name": "Modo Sobredrive",
            "desc": "Turbo: la estela de movimiento inflige daño a enemigos que toca.",
            "cost": 35,
            "unlocked": False,
        },
        {
            "id": "echo_shot",
            "name": "Disparo Eco",
            "desc": "Cada décimo disparo crea un duplicado que apunta al enemigo más cercano.",
            "cost": 40,
            "unlocked": False,
        },
    ]
    LORE = [
        ("Sector Alpha-7", "Los primeros colonos nunca regresaron. Sus señales aún rebotan en la nebulosa.", 5),
        ("Enjambre Orgánico", "Son restos de una bioforma extinta. Atacan por instinto, no por orden.", 10),
        ("Drones Mineros", "Originalmente construidos para extraer Kribellita. Algo los reprogramó.", 15),
        ("El Nexo", "Una red de datos cuánticos que conecta todos los sectores. Nadie sabe quién la construyó.", 20),
        ("La Señal", "Hay una frecuencia repetida en todos los sectores: 77.3 Hz. Nadie sabe su origen.", 30),
    ]

    def __init__(self):
        self.fragments  = 0
        self.synergies  = {s["id"]: False for s in self.SYNERGIES}
        self.lore_found: List[str] = []
        self._menu_sel  = 0
        self._load()

    def add_fragments(self, n: int):
        self.fragments += n
        self._save()

    def has_synergy(self, sid: str) -> bool:
        return self.synergies.get(sid, False)

    def buy_synergy(self, sid: str, ai_log=None) -> bool:
        for s in self.SYNERGIES:
            if s["id"] == sid and not self.synergies[sid]:
                if self.fragments >= s["cost"]:
                    self.fragments -= s["cost"]
                    self.synergies[sid] = True
                    self._save()
                    if ai_log is not None:
                        ai_log.push_synergy(sid)
                    return True
        return False

    def check_lore(self):
        for title, text, needed in self.LORE:
            if self.fragments >= needed and title not in self.lore_found:
                self.lore_found.append(title)

    def _save(self):
        try:
            data = {
                "fragments": self.fragments,
                "synergies": self.synergies,
                "lore":      self.lore_found,
            }
            with open(NEXUS_SAVE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load(self):
        try:
            if os.path.exists(NEXUS_SAVE_FILE):
                with open(NEXUS_SAVE_FILE) as f:
                    data = json.load(f)
                self.fragments = data.get("fragments", 0)
                self.synergies.update(data.get("synergies", {}))
                self.lore_found = data.get("lore", [])
        except Exception:
            pass

    def draw_menu_overlay(self, surf, rm, dt):
        """Full-screen nexus menu drawn over the main menu."""
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 20, 230))
        surf.blit(ov, (0, 0))

        t_title = rm.get_font(36, True).render("NEXO DE DATOS", True, (0, 220, 255))
        surf.blit(t_title, (SCREEN_W//2 - t_title.get_width()//2, 30))

        frag_t = rm.get_font(18).render(f"Fragmentos: {self.fragments}", True, GOLD)
        surf.blit(frag_t, (SCREEN_W//2 - frag_t.get_width()//2, 80))

        y = 130
        surf.blit(rm.get_font(20, True).render("SINERGIAS", True, CYAN), (80, y)); y += 34
        for i, s in enumerate(self.SYNERGIES):
            unlocked = self.synergies[s["id"]]
            sel = (i == self._menu_sel)
            col = GREEN if unlocked else (YELLOW if sel else GRAY)
            bg_col = (20, 40, 20) if unlocked else ((30, 30, 60) if sel else (10, 10, 30))
            pygame.draw.rect(surf, bg_col, (72, y-2, 560, 48), border_radius=8)
            pygame.draw.rect(surf, col, (72, y-2, 560, 48), 1, border_radius=8)
            nm = rm.get_font(16, True).render(s["name"], True, col)
            surf.blit(nm, (84, y))
            ds = rm.get_font(12).render(s["desc"], True, (140, 140, 160))
            surf.blit(ds, (84, y + 20))
            status = "DESBLOQUEADO" if unlocked else f"{s['cost']} frags"
            st_col = GREEN if unlocked else (YELLOW if self.fragments >= s["cost"] else RED)
            st_t = rm.get_font(13, True).render(status, True, st_col)
            surf.blit(st_t, (560, y + 12))
            y += 56

        y += 10
        surf.blit(rm.get_font(18, True).render("ARCHIVOS DESBLOQUEADOS", True, (180, 100, 255)), (80, y)); y += 28
        for title, text, needed in self.LORE:
            if title in self.lore_found:
                nm2 = rm.get_font(13, True).render(f"  {title}", True, (200, 160, 255))
                surf.blit(nm2, (84, y)); y += 18
            else:
                nxt = rm.get_font(12).render(f"??? — Necesitas {needed} frags", True, (60, 60, 80))
                surf.blit(nxt, (84, y)); y += 18

        hint = rm.get_font(13).render("↑↓ Navegar  |  ENTER: Comprar Sinergia  |  ESC: Volver", True, (60, 80, 100))
        surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 30))

    def handle_event(self, event, ai_log=None) -> bool:
        """Returns True if ESC was pressed (close menu)."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._menu_sel = (self._menu_sel - 1) % len(self.SYNERGIES)
            elif event.key == pygame.K_DOWN:
                self._menu_sel = (self._menu_sel + 1) % len(self.SYNERGIES)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                sid = self.SYNERGIES[self._menu_sel]["id"]
                self.buy_synergy(sid, ai_log=ai_log)
            elif event.key == pygame.K_ESCAPE:
                return True
        return False


class HackSystem:
    """
    Active ability (key E): creates an EMP pulse that freezes all
    enemy bullets on screen, turns them green, and when the effect ends
    fires them all toward the nearest enemy.
    """
    def __init__(self):
        self.active   = False
        self.timer    = 0.0
        self.cooldown = 0.0
        self._hacked_bullets: list = []
        self._pulse_r = 0.0

    @property
    def ready(self) -> bool:
        return self.cooldown <= 0

    @property
    def cd_ratio(self) -> float:
        return max(0.0, self.cooldown / HACK_COOLDOWN)

    def activate(self, game):
        if not self.ready or self.active:
            return
        self.active   = True
        self.timer    = HACK_DURATION
        self.cooldown = HACK_COOLDOWN
        self._pulse_r = 0.0
        pp = game.player.transform.pos
        self._hacked_bullets = []
        for b in list(game.bullet_pool.active):
            if b.owner == "enemy" and b.active:
                bpos = Vec2(b.rect.centerx, b.rect.centery)
                if (bpos - pp).length() <= HACK_RADIUS:
                    b._hacked = True
                    b._orig_vel = Vec2(b.vel)
                    b.vel = Vec2(0, 0)
                    b.color = HACK_GREEN
                    self._hacked_bullets.append(b)
        game.sfx.play("skill_upgrade")
        game.ai_log._push("HACK activado — Proyectiles capturados.", 4.0)

    def update(self, dt, game):
        if self.cooldown > 0:
            self.cooldown -= dt

        if not self.active:
            return

        self._pulse_r = min(HACK_RADIUS, self._pulse_r + HACK_RADIUS * dt * 2)
        self.timer -= dt

        for b in self._hacked_bullets:
            if b.active:
                b.vel = Vec2(0, 0)

        if self.timer <= 0:
            self._release(game)

    def _release(self, game):
        self.active = False
        enemies = [e for e in game.enemy_pool.active if e.active]
        pp = game.player.transform.pos

        for b in self._hacked_bullets:
            if not b.active:
                continue
            b._hacked = False
            b.owner   = "player"
            b.color   = HACK_GREEN
            b.damage  = max(b.damage, 15)

            bpos = Vec2(b.rect.centerx, b.rect.centery)
            target = None
            best_d = 9999999
            for e in enemies:
                d = (e.transform.pos - bpos).length()
                if d < best_d:
                    best_d = d
                    target = e

            if target:
                to_t = target.transform.pos - bpos
                if to_t.length() > 0:
                    b.vel = to_t.normalize() * BULLET_SPEED * 1.1
                    b.angle = math.degrees(math.atan2(to_t.y, to_t.x)) + 90
            else:
                a = random.uniform(0, math.pi*2)
                b.vel = Vec2(math.cos(a)*BULLET_SPEED, math.sin(a)*BULLET_SPEED)

        n = len([b for b in self._hacked_bullets if b.active])
        if n > 0:
            game.ai_log._push(f"{n} proyectiles redirigidos. ¡Fuego amigo convertido!", 4.5)
            if hasattr(game, "nexus") and game.nexus.has_synergy("gravity_burst"):
                for e in enemies:
                    ep = e.transform.pos - pp
                    if ep.length() < HACK_RADIUS and ep.length() > 0:
                        e.transform.vel += ep.normalize() * 8

        self._hacked_bullets.clear()
        self._pulse_r = 0.0

    def draw_overlay(self, surf, camera, player_pos):
        """Draw the visual EMP pulse ring."""
        if not self.active or self._pulse_r <= 0:
            return
        sx = int(player_pos.x - camera.x)
        sy = int(player_pos.y - camera.y)
        r  = int(self._pulse_r)
        prog = 1.0 - (self.timer / HACK_DURATION)
        alpha = int(80 * (1 - prog))
        gs = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*HACK_GREEN, alpha), (r+2, r+2), r, 3)
        surf.blit(gs, (sx-r-2, sy-r-2))
        bw = 120
        ratio = self.timer / HACK_DURATION
        pygame.draw.rect(surf, (20,20,20), (sx-bw//2, sy-50, bw, 8), border_radius=4)
        pygame.draw.rect(surf, HACK_GREEN, (sx-bw//2, sy-50, int(bw*ratio), 8), border_radius=4)
        rm2 = ResourceManager()
        lbl = rm2.get_font(11, True).render("HACK ACTIVO", True, HACK_GREEN)
        surf.blit(lbl, (sx - lbl.get_width()//2, sy - 64))

    def draw_hud(self, surf, rm, x, y):
        """Draw cooldown indicator."""
        if self.ready:
            col = HACK_GREEN
            txt = "[E] HACK "
        else:
            ratio = 1.0 - self.cd_ratio
            col = (int(HACK_GREEN[0]*ratio), int(HACK_GREEN[1]*ratio), int(HACK_GREEN[2]*ratio))
            secs = int(self.cooldown) + 1
            txt = f"[E] HACK  {secs}s"
        t = rm.get_font(13, True).render(txt, True, col)
        surf.blit(t, (x, y))
        bw = 110
        pygame.draw.rect(surf, (20,20,20), (x, y+16, bw, 5), border_radius=2)
        fill = int(bw * (1 - self.cd_ratio))
        if fill > 0:
            pygame.draw.rect(surf, col, (x, y+16, fill, 5), border_radius=2)


class FactionTag:
    """Mixin to give enemies a faction."""
    def init_faction(self, faction: str):
        self._faction = faction
        self._faction_cd = 0.0

    def faction_color_tint(self, base_color):
        if getattr(self, "_faction", None) == FACTION_SWARM:
            return (min(255, base_color[0]+40), base_color[1], max(0, base_color[2]-40))
        elif getattr(self, "_faction", None) == FACTION_DRONE:
            return (max(0, base_color[0]-40), base_color[1], min(255, base_color[2]+60))
        return base_color


class FactionWarManager:
    """
    Manages inter-faction combat.
    Sometimes spawns enemies that fight each other before (or instead of) the player.
    """
    FACTION_WAVE_INTERVAL = 45.0

    def __init__(self, game):
        self.game        = game
        self._timer      = self.FACTION_WAVE_INTERVAL * 0.5
        self._active_war = False
        self._war_timer  = 0.0
        self._swarm_ids: List[int] = []
        self._drone_ids: List[int] = []
        self._buff_active = False
        self._buff_timer  = 0.0

    def update(self, dt):
        self._timer -= dt
        if self._buff_active:
            self._buff_timer -= dt
            if self._buff_timer <= 0:
                self._buff_active = False
                self.game.ai_log._push("  Buff de facción expirado.", 3.5)

        active_en = [e for e in self.game.enemy_pool.active if e.active]
        for e in active_en:
            faction = getattr(e, "_faction", None)
            if faction is None:
                continue
            e._faction_cd = getattr(e, "_faction_cd", 0.0) - dt
            if e._faction_cd > 0:
                continue
            enemy_faction = FACTION_DRONE if faction == FACTION_SWARM else FACTION_SWARM
            best_target = None
            best_d = 300.0
            for o in active_en:
                if getattr(o, "_faction", None) == enemy_faction:
                    d = (e.transform.pos - o.transform.pos).length()
                    if d < best_d:
                        best_d = d
                        best_target = o
            if best_target:
                e._faction_cd = 1.8
                to_t = best_target.transform.pos - e.transform.pos
                if to_t.length() > 0:
                    vel  = to_t.normalize() * BULLET_SPEED * 0.7
                    ang  = math.degrees(math.atan2(to_t.y, to_t.x)) + 90
                    col  = (255,100,50) if faction == FACTION_SWARM else (50, 150, 255)
                    b    = self.game.bullet_pool.get()
                    if b:
                        b.activate(e.transform.pos.x, e.transform.pos.y, vel, 12,
                                   "faction_war", col, ang)

        for b in list(self.game.bullet_pool.active):
            if b.owner != "faction_war":
                continue
            bcol = b.color
            for e in active_en:
                faction = getattr(e, "_faction", None)
                if faction is None:
                    continue
                if b.rect.colliderect(e.rect):
                    is_swarm_bullet = (bcol[0] > 200)
                    is_swarm_enemy  = (faction == FACTION_SWARM)
                    if is_swarm_bullet and is_swarm_enemy:
                        continue
                    if not is_swarm_bullet and not is_swarm_enemy:
                        continue
                    dead = e.health.take_damage(b.damage)
                    self.game._particles_spawn(e.transform.pos, bcol, 4)
                    if dead:
                        e.active = False
                        self.game.enemy_pool.release(e)
                        self.game._particles_spawn(e.transform.pos, RED, 8)
                        self.game.player.add_xp(25)
                        self.game.player.score += 80
                        if hasattr(self.game, "nexus") and random.random() < DATA_FRAG_DROP_CHANCE:
                            self.game.nexus.add_fragments(1)
                    if b in self.game.bullet_pool.active:
                        self.game.bullet_pool.release(b)
                    break

        if self._timer <= 0:
            self._timer = self.FACTION_WAVE_INTERVAL
            self._spawn_faction_conflict()

    def _spawn_faction_conflict(self):
        p  = self.game.player
        pp = p.transform.pos
        count_each = 3 + p.level_sys.level // 2
        self.game.ai_log._push(
            f"CONFLICTO DE FACCIONES — Enjambre vs Drones en tu sector.", 6.0)
        self.game.sfx.play("boss_warning")
        self.game.ai_log.push_faction_war(FACTION_SWARM)
        self.game.ai_log.push_faction_war(FACTION_DRONE)

        for _ in range(count_each):
            ang  = random.uniform(0, math.pi*2)
            dist = random.uniform(350, 600)
            ex   = max(50, min(WORLD_W-50, pp.x + math.cos(ang)*dist))
            ey   = max(50, min(WORLD_H-50, pp.y + math.sin(ang)*dist))
            e    = self.game.enemy_pool.get()
            if e:
                etype = random.choice(["scout", "fighter", "kamikaze"])
                EnemyFactory.configure(e, etype)
                e.init_faction(FACTION_SWARM)
                e.spawn(ex, ey)

        for _ in range(count_each):
            ang  = random.uniform(0, math.pi*2)
            dist = random.uniform(350, 600)
            ex   = max(50, min(WORLD_W-50, pp.x + math.cos(ang)*dist))
            ey   = max(50, min(WORLD_H-50, pp.y + math.sin(ang)*dist))
            e    = self.game.enemy_pool.get()
            if e:
                etype = random.choice(["heavy", "sniper"])
                EnemyFactory.configure(e, etype)
                e.init_faction(FACTION_DRONE)
                e.spawn(ex, ey)

        self._active_war = True
        self._war_timer  = 20.0

    def player_sided_with(self, faction: str):
        """Call when player kills an enemy of the OPPOSITE faction, implicitly siding."""
        if not self._active_war:
            return
        self._buff_active = True
        self._buff_timer  = 15.0
        self._active_war  = False
        self.game.ai_log._push(
            f"Alianza temporal con {'Enjambre' if faction == FACTION_SWARM else 'Drones'}. "
            f"Velocidad +20% por 15s.", 5.5)

    @property
    def buff_active(self) -> bool:
        return self._buff_active

    @property
    def speed_buff(self) -> float:
        return 1.20 if self._buff_active else 1.0


FACTION_ALLY = "ally"

class AlliedDrone:
    """
    A single allied drone that flocks using Boids (separation, alignment, cohesion)
    and attacks enemies automatically. Spawned by AlliedFleet.
    """
    RADIUS = 10

    def __init__(self, game, idx: int):
        self.game    = game
        self.idx     = idx
        self.pos     = Vec2(0, 0)
        self.vel     = Vec2(0, 0)
        self.active  = False
        self.hp      = 40
        self.max_hp  = 40
        self.rect    = pygame.Rect(0, 0, self.RADIUS*2, self.RADIUS*2)
        self.shoot_cd = 0.0
        self._angle  = 0.0

    def spawn(self, x, y):
        self.pos    = Vec2(x, y)
        self.vel    = Vec2(random.uniform(-1,1), random.uniform(-1,1))
        self.hp     = self.max_hp
        self.active = True

    def reset(self):
        self.active = False
        self.vel    = Vec2(0, 0)

    def _boids(self, siblings):
        sep = Vec2(0,0); ali = Vec2(0,0); coh = Vec2(0,0)
        ns = na = nc = 0
        for o in siblings:
            if o is self or not o.active: continue
            d = (self.pos - o.pos).length()
            if 0 < d < SEP_DIST * 0.6:
                sep += (self.pos - o.pos).normalize() / max(d,0.1); ns += 1
            if 0 < d < NEIGHBOR_DIST * 0.7:
                ali += o.vel; na += 1
                coh += o.pos; nc += 1
        if ns: sep /= ns
        if na: ali = vec_limit(ali / na, MAX_SPEED_ENEMY)
        if nc: coh = vec_limit(coh/nc - self.pos, MAX_SPEED_ENEMY)
        return sep*W_SEPARATION + ali*W_ALIGNMENT + coh*W_COHESION

    def update(self, dt, siblings):
        if not self.active: return
        p   = self.game.player
        pp  = p.transform.pos

        # Cohesion toward player
        to_player = pp - self.pos
        if to_player.length() > 120:
            seek = to_player.normalize() * MAX_SPEED_ENEMY * 0.9
        else:
            seek = Vec2(0, 0)

        boids = self._boids(siblings)
        force = seek * W_SEEK_PLAYER + boids
        self.vel += force * dt * 60
        self.vel  = vec_limit(self.vel, MAX_SPEED_ENEMY * 1.4)
        self.vel *= 0.93
        self.pos += self.vel * dt * 60
        self.pos.x = max(20, min(WORLD_W-20, self.pos.x))
        self.pos.y = max(20, min(WORLD_H-20, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        if self.vel.length() > 0.1:
            self._angle = math.degrees(math.atan2(self.vel.y, self.vel.x)) + 90

        # Attack nearest non-allied enemy
        self.shoot_cd -= dt
        if self.shoot_cd <= 0:
            best_e = None; best_d = 280.0
            for e in self.game.enemy_pool.active:
                if not e.active: continue
                if getattr(e, "_faction", None) == FACTION_ALLY: continue
                d = (e.transform.pos - self.pos).length()
                if d < best_d:
                    best_d = d; best_e = e
            if best_e:
                self.shoot_cd = 1.2
                to_e = best_e.transform.pos - self.pos
                if to_e.length() > 0:
                    vel2 = to_e.normalize() * BULLET_SPEED * 0.75
                    ang2 = math.degrees(math.atan2(to_e.y, to_e.x)) + 90
                    b    = self.game.bullet_pool.get()
                    if b:
                        b.activate(self.pos.x, self.pos.y, vel2, 8, "player", (80, 255, 140), ang2)

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        if not (-30 < sx < SCREEN_W+30 and -30 < sy < SCREEN_H+30): return
        t   = time.time()
        R   = self.RADIUS
        rad = math.radians(self._angle)
        def rot(dx, dy):
            rx = dx*math.cos(rad) - dy*math.sin(rad)
            ry = dx*math.sin(rad) + dy*math.cos(rad)
            return (int(sx+rx), int(sy+ry))
        col = (80, 255, 140)
        pygame.draw.polygon(surf, (10,40,20), [rot(0,-R), rot(-R*0.5,R*0.6), rot(0,R*0.15), rot(R*0.5,R*0.6)])
        pygame.draw.polygon(surf, col, [rot(0,-R*0.9), rot(-R*0.45,R*0.55), rot(0,R*0.1), rot(R*0.45,R*0.55)])
        pygame.draw.polygon(surf, WHITE, [rot(0,-R*0.9), rot(-R*0.45,R*0.55), rot(0,R*0.1), rot(R*0.45,R*0.55)], 1)
        # Glow
        pulse = int(6 + 3*math.sin(t*4 + self.idx))
        gs = pygame.Surface((pulse*2, pulse*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (80,255,140,60), (pulse,pulse), pulse)
        surf.blit(gs, (sx-pulse, sy-pulse))
        # HP bar
        bw = 20
        pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2, sy+R+2, bw, 3))
        pygame.draw.rect(surf, GREEN, (sx-bw//2, sy+R+2, int(bw*self.hp/self.max_hp), 3))


class AlliedFleet:
    """
    Manages the player's allied drone squadron.
    Activated with [F] key (cooldown 45s). Spawns 4 drones that use Boids AI
    and auto-attack enemies. They are recognized as allies by the faction system.
    """
    MAX_DRONES  = 4
    SUMMON_CD   = 45.0
    DRONE_LIFE  = 30.0   # seconds before drones expire

    def __init__(self, game):
        self.game    = game
        self._drones: List[AlliedDrone] = [AlliedDrone(game, i) for i in range(self.MAX_DRONES)]
        self._cooldown = 0.0
        self._life_timer = 0.0
        self._active = False

    @property
    def ready(self): return self._cooldown <= 0

    @property
    def cd_ratio(self): return max(0.0, self._cooldown / self.SUMMON_CD)

    def summon(self):
        if not self.ready: return
        self._cooldown   = self.SUMMON_CD
        self._life_timer = self.DRONE_LIFE
        self._active     = True
        pp = self.game.player.transform.pos
        for i, d in enumerate(self._drones):
            ang  = i * (math.pi * 2 / self.MAX_DRONES)
            d.spawn(pp.x + math.cos(ang)*80, pp.y + math.sin(ang)*80)
        self.game.ai_log._push(f"FLOTA DE APOYO invocada — {self.MAX_DRONES} drones aliados.", 5.5)
        self.game.sfx.play("skill_upgrade")

    def update(self, dt):
        if self._cooldown > 0:
            self._cooldown -= dt
        if not self._active:
            return
        self._life_timer -= dt
        if self._life_timer <= 0:
            for d in self._drones:
                d.reset()
            self._active = False
            self.game.ai_log._push("Drones aliados han expirado.", 3.5)
            return
        active_siblings = [d for d in self._drones if d.active]
        for d in self._drones:
            d.update(dt, active_siblings)

    def draw(self, surf, camera):
        for d in self._drones:
            d.draw(surf, camera)

    def draw_hud(self, surf, rm, x, y):
        if self.ready:
            col = (80, 255, 140)
            txt = "[F] FLOTA "
        else:
            ratio = 1.0 - self.cd_ratio
            col   = (int(80*ratio), int(255*ratio), int(140*ratio))
            secs  = int(self._cooldown) + 1
            txt   = f"[F] FLOTA  {secs}s"
        t2 = rm.get_font(13, True).render(txt, True, col)
        surf.blit(t2, (x, y))
        bw = 110
        pygame.draw.rect(surf, (20,20,20), (x, y+16, bw, 5), border_radius=2)
        fill = int(bw * (1 - self.cd_ratio))
        if fill > 0:
            pygame.draw.rect(surf, col, (x, y+16, fill, 5), border_radius=2)


class DynamicCamera:
    """
    Tracks player speed and boss proximity to zoom in/out smoothly.
    Returns a zoom factor and a rendered scaled surface.
    """
    def __init__(self):
        self._zoom        = 1.0
        self._target_zoom = 1.0

    def update(self, dt, player, game):
        spd = player.transform.vel.length()
        if spd > MAX_SPEED_PLAYER * 0.7:
            speed_ratio = min(1.0, (spd - MAX_SPEED_PLAYER*0.7) / (MAX_SPEED_PLAYER*1.3))
            z_spd = ZOOM_MAX - (ZOOM_MAX - ZOOM_MIN) * speed_ratio * 0.6
        else:
            z_spd = ZOOM_MAX

        z_boss = 1.0
        active_en = [e for e in game.enemy_pool.active if e.active]
        for e in active_en:
            if e.etype in ("boss", "titan"):
                d = (e.transform.pos - player.transform.pos).length()
                if d < 600:
                    z_boss = ZOOM_MIN + (1.0 - ZOOM_MIN) * d / 600.0
                    break
        if hasattr(game, "_worm_boss") and game._worm_boss and game._worm_boss.active:
            d = (game._worm_boss.head.pos - player.transform.pos).length()
            z_boss = min(z_boss, ZOOM_MIN + (1.0 - ZOOM_MIN) * min(1.0, d / 500.0))

        self._target_zoom = max(ZOOM_MIN, min(ZOOM_MAX, min(z_spd, z_boss if z_boss < 1.0 else z_spd)))
        self._zoom += (self._target_zoom - self._zoom) * min(dt * ZOOM_SPEED, 1.0)

    @property
    def zoom(self) -> float:
        return self._zoom

    def apply(self, surf: pygame.Surface) -> pygame.Surface:
        """Scale surface around center for zoom effect."""
        if abs(self._zoom - 1.0) < 0.01:
            return surf
        new_w = int(SCREEN_W / self._zoom)
        new_h = int(SCREEN_H / self._zoom)
        cx    = SCREEN_W // 2
        cy    = SCREEN_H // 2
        src_rect = pygame.Rect(cx - new_w//2, cy - new_h//2, new_w, new_h)
        src_rect.clamp_ip(pygame.Rect(0, 0, SCREEN_W, SCREEN_H))
        sub = surf.subsurface(src_rect)
        return pygame.transform.scale(sub, (SCREEN_W, SCREEN_H))


class MotionTrail:
    """
    Sistema de Ecos: records player position/angle history and draws fading ghost
    silhouettes with decreasing opacity. Each ghost uses set_alpha per-frame.
    Activates during turbo (high speed) or near boss.
    """
    GHOST_FRAMES = 10
    SAMPLE_CD    = 0.035

    def __init__(self):
        self._history: List[Tuple[float, float, float]] = []
        self._cd = 0.0

    def update(self, dt, player):
        self._cd -= dt
        spd = player.transform.vel.length()
        if spd > MAX_SPEED_PLAYER * 0.45 and self._cd <= 0:
            self._cd = self.SAMPLE_CD
            self._history.append((
                player.transform.pos.x,
                player.transform.pos.y,
                player.transform.angle
            ))
            if len(self._history) > self.GHOST_FRAMES:
                self._history.pop(0)
        elif spd <= MAX_SPEED_PLAYER * 0.25:
            if self._history:
                self._history.pop(0)

    def draw(self, surf, camera):
        n = len(self._history)
        if n < 2:
            return
        R = Player.RADIUS
        for i, (px, py, ang) in enumerate(self._history):
            sx = int(px - camera.x)
            sy = int(py - camera.y)
            if not (-80 < sx < SCREEN_W+80 and -80 < sy < SCREEN_H+80):
                continue
            ratio  = (i + 1) / n          # 0=oldest fade, 1=newest bright
            alpha  = int(55 * ratio)
            scale  = 0.5 + 0.5 * ratio
            rad    = math.radians(ang)
            r      = max(1, int(R * scale))
            ghost_col = (
                int(80 + 175 * (1 - ratio)),
                int(180 + 75 * ratio),
                255
            )
            cos_r, sin_r = math.cos(rad), math.sin(rad)

            def _r(dx, dy, sx=sx, sy=sy, scale=scale, cr=cos_r, sr=sin_r):
                return (int(sx + (dx*cr - dy*sr)*scale),
                        int(sy + (dx*sr + dy*cr)*scale))

            pts = [_r(0,-r), _r(-r*0.55, r*0.65), _r(0, r*0.2), _r(r*0.55, r*0.65)]
            ghost_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.polygon(ghost_s, (*ghost_col, alpha), pts)
            pygame.draw.polygon(ghost_s, (*ghost_col, min(255, alpha*2)), pts, 1)
            surf.blit(ghost_s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


class BulletHellBoss:
    """
    A special boss that fires mathematical bullet-hell patterns:
    - Archimedes spiral
    - Rose petals (sin/cos)
    - Rotating rings with gaps
    """
    RADIUS = 36
    HP     = 450

    def __init__(self, game):
        self.game      = game
        self.pos       = Vec2(0, 0)
        self.vel       = Vec2(0, 0)
        self.hp        = self.HP
        self.max_hp    = self.HP
        self.active    = False
        self.rect      = pygame.Rect(0, 0, self.RADIUS*2, self.RADIUS*2)
        self._rot      = 0.0
        self._phase    = 0
        self._phase_timer = 0.0
        self._phase_duration = 8.0
        self._shoot_cd = 0.0
        self._shoot_t  = 0.0
        self._flash    = 0.0
        self._warning_shown = False
        self._intro_t  = 3.0
        self._spiral_angle = 0.0

    def spawn(self, x, y):
        self.pos       = Vec2(x, y)
        self.hp        = self.HP
        self.max_hp    = self.HP
        self.active    = True
        self._rot      = 0.0
        self._phase    = 0
        self._phase_timer = 0.0
        self._shoot_cd = 0.0
        self._shoot_t  = 0.0
        self._flash    = 0.0
        self._intro_t  = 3.0
        self._spiral_angle = 0.0
        self.rect.center = (int(x), int(y))
        self.game.sfx.play("boss_warning")
        self.game.sfx.play("titan_spawn")
        self.game.ai_log._push("JEFE GEOMÉTRICO detectado — Patrones Bullet Hell activos.", 6.0)

    def update(self, dt):
        if not self.active:
            return

        self._rot += dt * 1.2
        self._shoot_t += dt
        self._flash = max(0.0, self._flash - dt)

        player = self.game.player
        to_p = player.transform.pos - self.pos
        dist = to_p.length()

        if dist > 320:
            if to_p.length() > 0:
                self.vel += to_p.normalize() * 2.5 * dt * 60
        elif dist < 220:
            if to_p.length() > 0:
                self.vel -= to_p.normalize() * 2.0 * dt * 60
        spd = self.vel.length()
        if spd > 2.0: self.vel *= 2.0/spd
        self.vel *= 0.94
        self.pos += self.vel * dt * 60
        self.pos.x = max(60, min(WORLD_W-60, self.pos.x))
        self.pos.y = max(60, min(WORLD_H-60, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        if self._intro_t > 0:
            self._intro_t -= dt
            return

        self._phase_timer += dt
        if self._phase_timer >= self._phase_duration:
            self._phase_timer = 0.0
            self._phase = (self._phase + 1) % 3

        self._shoot_cd -= dt
        if self._shoot_cd > 0:
            return

        self._shoot_cd = BOSS_BULLET_HELL_CD

        if   self._phase == 0: self._fire_spiral()
        elif self._phase == 1: self._fire_rose()
        else:                  self._fire_ring_gap()

    def _fire_spiral(self):
        """Archimedes spiral: angle advances per shot."""
        self._spiral_angle += 0.22
        a    = self._spiral_angle
        vel  = Vec2(math.cos(a) * BULLET_SPEED * 0.55,
                    math.sin(a) * BULLET_SPEED * 0.55)
        ang  = math.degrees(a) + 90
        b    = self.game.bullet_pool.get()
        if b: b.activate(self.pos.x, self.pos.y, vel, 8, "enemy", (255, 120, 0), ang)
        a2   = a + math.pi
        vel2 = Vec2(math.cos(a2)*BULLET_SPEED*0.55, math.sin(a2)*BULLET_SPEED*0.55)
        b2   = self.game.bullet_pool.get()
        if b2: b2.activate(self.pos.x, self.pos.y, vel2, 8, "enemy", (255, 80, 0), math.degrees(a2)+90)

    def _fire_rose(self):
        """Rose petal pattern: r = cos(k*theta) with k=4."""
        t  = self._shoot_t * 2.0
        k  = 4
        r_val = math.cos(k * t)
        a  = t
        px = math.cos(a) * r_val
        py = math.sin(a) * r_val
        if abs(px) + abs(py) < 0.1:
            return
        length = math.hypot(px, py)
        if length > 0:
            vel = Vec2(px/length * BULLET_SPEED * 0.5, py/length * BULLET_SPEED * 0.5)
            ang = math.degrees(math.atan2(py, px)) + 90
            b   = self.game.bullet_pool.get()
            if b: b.activate(self.pos.x, self.pos.y, vel, 7, "enemy", (200, 0, 255), ang)

    def _fire_ring_gap(self):
        """Ring of bullets with rotating gap. Player must find the gap."""
        n_bullets = 16
        gap_angle = self._shoot_t * 1.5
        gap_range = math.pi / 4
        for i in range(n_bullets):
            a = i * (2*math.pi / n_bullets)
            diff = ((a - gap_angle) % (2*math.pi))
            if diff < gap_range or diff > 2*math.pi - gap_range:
                continue
            vel = Vec2(math.cos(a)*BULLET_SPEED*0.45, math.sin(a)*BULLET_SPEED*0.45)
            ang = math.degrees(a) + 90
            b   = self.game.bullet_pool.get()
            if b: b.activate(self.pos.x, self.pos.y, vel, 9, "enemy", (100, 200, 255), ang)

    def take_damage(self, dmg) -> bool:
        self.hp = max(0, self.hp - dmg)
        self._flash = 0.1
        return self.hp <= 0

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        R  = self.RADIUS
        if not (-R-10 < sx < SCREEN_W+R+10 and -R-10 < sy < SCREEN_H+R+10): return

        t   = time.time()
        col = WHITE if self._flash > 0 else (
            (180, 80, 255) if self._phase == 0 else
            (255, 100, 50) if self._phase == 1 else
            (100, 200, 255)
        )

        glow_r = int(R + 14 + 6*math.sin(t*3))
        gs     = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*col, 40), (glow_r, glow_r), glow_r)
        surf.blit(gs, (sx-glow_r, sy-glow_r))

        pts = []
        for i in range(8):
            a = self._rot + i*(math.pi*2/8)
            pts.append((int(sx+R*math.cos(a)), int(sy+R*math.sin(a))))
        pygame.draw.polygon(surf, (20,5,30), [(p[0]+3,p[1]+3) for p in pts])
        pygame.draw.polygon(surf, tuple(max(0,c-60) for c in col), pts)
        pygame.draw.polygon(surf, col, pts, 2)

        for i in range(4):
            ca = self._rot*2 + i*(math.pi/2)
            cx2 = int(sx + (R*0.55)*math.cos(ca))
            cy2 = int(sy + (R*0.55)*math.sin(ca))
            pygame.draw.circle(surf, col, (cx2, cy2), 6)
            pygame.draw.circle(surf, WHITE, (cx2, cy2), 6, 1)
        pygame.draw.circle(surf, (8,8,18), (sx+2,sy+2), 10)
        pygame.draw.circle(surf, WHITE,    (sx,sy), 10)
        pygame.draw.circle(surf, col, (sx-1,sy-1), 7)

        bw = 80
        pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2, sy-R-18, bw, 8), border_radius=4)
        pygame.draw.rect(surf, col,       (sx-bw//2, sy-R-18, int(bw*self.hp/self.max_hp), 8), border_radius=4)
        pygame.draw.rect(surf, WHITE,     (sx-bw//2, sy-R-18, bw, 8), 1, border_radius=4)

        phase_names = ["ESPIRAL", "PÉTALOS", "ANILLO"]
        rm2 = ResourceManager()
        lbl = rm2.get_font(11, True).render(f"JEFE GEOMÉTRICO  [{phase_names[self._phase]}]",
                                            True, col)
        surf.blit(lbl, (sx-lbl.get_width()//2, sy-R-32))

        if self._intro_t > 0:
            cd_lbl = rm2.get_font(22, True).render(
                f"ACTIVANDO EN {math.ceil(self._intro_t)}...", True, RED)
            surf.blit(cd_lbl, (sx - cd_lbl.get_width()//2, sy + R + 10))


class DeferredLighting:
    """
    Creates a darkness layer and additively blends coloured light sources:
    - Player engine  → warm blue glow
    - Every bullet   → small colour-matched glow
    - Black holes    → purple ambient light
    - Explosions     → brief orange flash registered via add_flash()

    Uses pygame.BLEND_RGBA_ADD on a per-frame surface for zero-cost
    accumulation of many small lights.
    """
    def __init__(self):
        self._dark    = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._light   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._flashes: List[Dict] = []      # {"pos":(sx,sy), "r":int, "col":rgb, "life":float}
        self._glow_cache: Dict[Tuple, pygame.Surface] = {}

    def _get_glow(self, r: int, color: tuple, alpha_center: int = 180) -> pygame.Surface:
        key = (r, color, alpha_center)
        if key not in self._glow_cache:
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            for step in range(r, 0, -2):
                a = int(alpha_center * (step / r) ** 1.8)
                pygame.draw.circle(s, (*color[:3], a), (r, r), step)
            self._glow_cache[key] = s
        return self._glow_cache[key]

    def add_flash(self, screen_x: int, screen_y: int, radius: int,
                  color: tuple, life: float = 0.25):
        self._flashes.append({
            "pos": (screen_x, screen_y), "r": radius,
            "col": color[:3], "life": life, "max_life": life
        })

    def update(self, dt):
        alive_f = []
        for f in self._flashes:
            f["life"] -= dt
            if f["life"] > 0:
                alive_f.append(f)
        self._flashes = alive_f

    def render(self, surf, game):
        """Call AFTER all world objects are drawn."""
        self._light.fill((0, 0, 0, 0))
        cam = game.camera

        p   = game.player
        spd = p.transform.vel.length()
        if spd > 0.3:
            angle_rad = math.radians(p.transform.angle)
            R         = p.RADIUS
            bx = int(p.transform.pos.x - cam.x + R * 0.7 * math.sin(angle_rad))
            by = int(p.transform.pos.y - cam.y + R * 0.7 * -math.cos(angle_rad))
            intensity = min(1.0, spd / MAX_SPEED_PLAYER)
            glow_r    = int(22 + 12 * intensity)
            gs = self._get_glow(glow_r, (20, 80, 255), int(140 * intensity))
            self._light.blit(gs, (bx - glow_r, by - glow_r),
                             special_flags=pygame.BLEND_RGBA_ADD)

        for b in game.bullet_pool.active:
            if not b.active:
                continue
            bsx = b.rect.centerx - int(cam.x)
            bsy = b.rect.centery - int(cam.y)
            if not (-40 < bsx < SCREEN_W+40 and -40 < bsy < SCREEN_H+40):
                continue
            col = b.color[:3]
            glow_r = 14 if b.owner == "faction_war" else 8
            alpha  = 120 if b.owner == "faction_war" else 70
            gs = self._get_glow(glow_r, col, alpha)
            self._light.blit(gs, (bsx - glow_r, bsy - glow_r),
                             special_flags=pygame.BLEND_RGBA_ADD)

        for gz in getattr(game, "_gravity_zones", []):
            if gz.type == gz.TYPE_BLACKHOLE:
                sx = int(gz.pos.x - cam.x)
                sy = int(gz.pos.y - cam.y)
                if -gz.radius < sx < SCREEN_W+gz.radius and -gz.radius < sy < SCREEN_H+gz.radius:
                    gr = int(gz.radius * 0.55)
                    gs = self._get_glow(gr, (120, 0, 200), 55)
                    self._light.blit(gs, (sx - gr, sy - gr),
                                     special_flags=pygame.BLEND_RGBA_ADD)

        for e in game.enemy_pool.active:
            if not e.active:
                continue
            esx = int(e.transform.pos.x - cam.x)
            esy = int(e.transform.pos.y - cam.y)
            if not (-50 < esx < SCREEN_W+50 and -50 < esy < SCREEN_H+50):
                continue
            faction = getattr(e, "_faction", None)
            if faction == FACTION_SWARM:
                ecol, ealpha = (255, 80, 30), 55
            elif faction == FACTION_DRONE:
                ecol, ealpha = (50, 140, 255), 55
            else:
                ecol, ealpha = (200, 80, 0), 35
            spd_e = e.transform.vel.length()
            if spd_e > 0.5:
                er = int(8 + 6 * min(1.0, spd_e / MAX_SPEED_ENEMY))
                gs = self._get_glow(er, ecol, ealpha)
                self._light.blit(gs, (esx - er, esy - er),
                                 special_flags=pygame.BLEND_RGBA_ADD)

        for f in self._flashes:
            ratio = f["life"] / f["max_life"]
            fr    = int(f["r"] * (0.5 + 0.5 * ratio))
            falph = int(200 * ratio)
            gs = self._get_glow(max(4, fr), f["col"], falph)
            fx, fy = f["pos"]
            self._light.blit(gs, (fx - fr, fy - fr),
                             special_flags=pygame.BLEND_RGBA_ADD)

        self._dark.fill((0, 0, 0, LIGHT_SURF_ALPHA))
        self._dark.blit(self._light, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        surf.blit(self._dark, (0, 0))


class BulletTimeSystem:
    """
    Watches player HP. When it drops below BULLET_TIME_HP_THRESH,
    gradually scales the game dt toward BULLET_TIME_SCALE.
    Returns a modified dt multiplier.  Recovery: HP goes back above threshold.
    """
    def __init__(self):
        self._scale       = 1.0
        self._active      = False
        self._announced   = False
        self._vignette    = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._build_vignette()

    def _build_vignette(self):
        """Pre-bake a blood-red edge vignette for critical HP."""
        self._vignette.fill((0, 0, 0, 0))
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        max_r  = int(math.hypot(cx, cy))
        for r in range(max_r, max_r - 80, -4):
            a = int(90 * (1 - (r - (max_r-80)) / 80))
            pygame.draw.ellipse(self._vignette, (180, 0, 0, a),
                                (cx - r, cy - int(r * 0.7),
                                 r * 2, int(r * 1.4)), 6)

    def update(self, dt: float, player, ai_log=None) -> float:
        """Returns scaled dt to use for this frame."""
        hp_ratio = player.health.ratio
        if hp_ratio <= BULLET_TIME_HP_THRESH:
            if not self._active:
                self._active    = True
                self._announced = False
            if not self._announced and ai_log:
                ai_log.push_bullet_time()
                self._announced = True
            target = BULLET_TIME_SCALE
        else:
            self._active    = False
            self._announced = False
            target = 1.0

        self._scale += (target - self._scale) * min(dt * BULLET_TIME_FADE_SPEED, 1.0)
        return dt * self._scale

    @property
    def active(self) -> bool:
        return self._active

    @property
    def scale(self) -> float:
        return self._scale

    def draw_vignette(self, surf):
        """Draw blood-red vignette when bullet time is close to active."""
        intensity = max(0.0, 1.0 - self._scale)
        if intensity < 0.05:
            return
        vs = self._vignette.copy()
        vs.set_alpha(int(255 * intensity))
        surf.blit(vs, (0, 0))
        tint = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        tint.fill((180, 10, 10, int(30 * intensity)))
        surf.blit(tint, (0, 0))


class ParallaxBackground:
    """
    Multiple independent star layers scrolling at different speeds.
    Layer 0 = closest (fastest), layer N = farthest (slowest, bigger glow).
    Also includes a large slow-moving nebula cloud layer.
    """
    SPEEDS      = [0.08, 0.18, 0.32]
    STAR_COUNTS = [80,   140,  200]
    STAR_SIZES  = [(1,2), (1,2), (1,3)]
    NEBULA_COLS = [
        (0, 10, 40, 14), (20, 0, 45, 12), (0, 25, 35, 10), (30, 5, 50, 9),
        (10, 0, 60, 11), (0, 40, 30, 8),
    ]

    def __init__(self, seed: int = 42):
        rng = random.Random(seed)
        self._layers: List[List[dict]] = []
        for li in range(PARALLAX_LAYERS):
            layer = []
            min_sz, max_sz = self.STAR_SIZES[li]
            for _ in range(self.STAR_COUNTS[li]):
                layer.append({
                    "x":    rng.uniform(0, SCREEN_W),
                    "y":    rng.uniform(0, SCREEN_H),
                    "sz":   rng.randint(min_sz, max_sz),
                    "br":   rng.randint(40 + li*30, 100 + li*50),
                    "twinkle": rng.uniform(0, math.pi*2),
                })
            self._layers.append(layer)

        self._nebulae: List[dict] = []
        for _ in range(8):
            self._nebulae.append({
                "x":   rng.uniform(0, SCREEN_W),
                "y":   rng.uniform(0, SCREEN_H),
                "r":   rng.randint(80, 240),
                "col": rng.choice(self.NEBULA_COLS),
                "twinkle": rng.uniform(0, math.pi*2),
            })

        self._prev_cam = Vec2(0, 0)

    def draw(self, surf, camera: "Vec2"):
        t = time.time()
        cam_dx = camera.x - self._prev_cam.x
        cam_dy = camera.y - self._prev_cam.y
        self._prev_cam = Vec2(camera)

        for nb in self._nebulae:
            nb["x"] = (nb["x"] - cam_dx * 0.03) % SCREEN_W
            nb["y"] = (nb["y"] - cam_dy * 0.03) % SCREEN_H
            pulse   = 0.88 + 0.12 * math.sin(t * 0.3 + nb["twinkle"])
            r       = int(nb["r"] * pulse)
            col     = nb["col"]
            for ox in [-SCREEN_W, 0, SCREEN_W]:
                for oy in [-SCREEN_H, 0, SCREEN_H]:
                    nx, ny = int(nb["x"]) + ox, int(nb["y"]) + oy
                    if -r < nx < SCREEN_W+r and -r < ny < SCREEN_H+r:
                        gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                        for rr in range(r, 0, -15):
                            a = int(col[3] * (rr/r) * pulse)
                            pygame.draw.circle(gs, (*col[:3], a), (r,r), rr)
                        surf.blit(gs, (nx-r, ny-r))
                        break
                else:
                    continue
                break

        for li, layer in enumerate(self._layers):
            spd = self.SPEEDS[li]
            for st in layer:
                st["x"] = (st["x"] - cam_dx * spd) % SCREEN_W
                st["y"] = (st["y"] - cam_dy * spd) % SCREEN_H
                tw  = 0.55 + 0.45 * math.sin(t * (1.2 + li*0.4) + st["twinkle"])
                br  = int(st["br"] * tw)
                pygame.draw.circle(surf, (br, br, min(255, br+40)),
                                   (int(st["x"]), int(st["y"])), st["sz"])


class ShipVisualUpgrade:
    """
    Draws additional visible parts on the player ship depending on
    which skills/modules are active:
    - Multidisparo lv1+ → side cannon nubs
    - Multidisparo lv2+ → extra cannon barrels
    - Nano-bots unlocked → glowing antenna on nose
    - Speed skill lv3+  → thruster fins
    - Modules (core)    → glowing core gem
    """
    @staticmethod
    def draw_extras(surf, player, sx: int, sy: int, angle_rad: float):
        R   = player.RADIUS
        st  = player.game.skill_tree

        def rot(dx, dy):
            rx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
            ry = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
            return (int(sx + rx), int(sy + ry))

        ms_lv = st.skills.get("multi_shot", None)
        ms    = ms_lv.level if ms_lv else 0
        if ms >= 1:
            for sign in (-1, 1):
                c1  = rot(sign * R * 0.6, R * 0.2)
                c2  = rot(sign * R * 0.6, -R * 0.5)
                pygame.draw.line(surf, (0, 160, 200), c1, c2, 2)
                pygame.draw.circle(surf, (0, 220, 255), c2, 3)
        if ms >= 2:
            for sign in (-1, 1):
                c1  = rot(sign * R * 0.8, R * 0.3)
                c2  = rot(sign * R * 0.8, -R * 0.6)
                pygame.draw.line(surf, (0, 120, 180), c1, c2, 2)
                pygame.draw.circle(surf, CYAN, c2, 2)
        if ms >= 3:
            for sign in (-1, 1):
                c1  = rot(sign * R * 1.0, R * 0.4)
                c2  = rot(sign * R * 1.0, -R * 0.35)
                pygame.draw.line(surf, (0, 80, 160), c1, c2, 1)
                pygame.draw.circle(surf, (100, 180, 255), c2, 2)

        nb_lv = st.skills.get("nano_bots", None)
        if nb_lv and nb_lv.level > 0:
            tip   = rot(0, -R)
            ant1  = rot(-4, -R - 10)
            ant2  = rot( 4, -R - 10)
            pygame.draw.line(surf, CYAN, tip, ant1, 1)
            pygame.draw.line(surf, CYAN, tip, ant2, 1)
            t = time.time()
            pulse = int(150 + 100 * math.sin(t * 5))
            pygame.draw.circle(surf, (0, pulse, 255), ant1, 2)
            pygame.draw.circle(surf, (0, pulse, 255), ant2, 2)

        sp_lv = st.skills.get("speed", None)
        if sp_lv and sp_lv.level >= 3:
            for sign in (-1, 1):
                f1  = rot(sign * R * 0.55, R * 0.65)
                f2  = rot(sign * R * 1.1,  R * 0.9)
                f3  = rot(sign * R * 0.55, R * 0.3)
                pygame.draw.polygon(surf, (0, 60, 140), [f1, f2, f3])
                pygame.draw.polygon(surf, (0, 140, 220), [f1, f2, f3], 1)

        core_slots = player.modules._slots.get("core", 0)
        if core_slots > 0:
            t   = time.time()
            gr  = int(4 + 2 * math.sin(t * 4))
            gcol = (200, 80, 255)
            gs  = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*gcol, 160), (gr, gr), gr)
            surf.blit(gs, (sx - gr, sy - gr))
            pygame.draw.circle(surf, gcol, (sx, sy), 3)


class LocalizedSparks:
    """
    Spawns persistent spark/plasma-leak particles from a ship's damaged sectors.
    Updated and drawn separately from the main particle system so they stay
    attached to the ship even while it moves.
    """
    SECTOR_OFFSETS = {
        "Front": (0, -1.0),
        "Back":  (0,  1.0),
        "Left":  (-1.0, 0),
        "Right": ( 1.0, 0),
    }

    def __init__(self):
        self._sparks: List[dict] = []
        self._emit_cd: dict = {s: 0.0 for s in LocalizedDamage.SECTORS}

    def update(self, dt, player):
        """Emit new sparks from damaged sectors; update existing ones."""
        loc = player.loc_damage
        angle_rad = math.radians(player.transform.angle)
        px, py    = player.transform.pos.x, player.transform.pos.y
        R         = player.RADIUS

        for sector in LocalizedDamage.SECTORS:
            dmg = loc.damage[sector]
            if dmg < 20:
                continue
            self._emit_cd[sector] -= dt
            if self._emit_cd[sector] > 0:
                continue
            self._emit_cd[sector] = max(0.04, 0.25 - dmg * 0.002)

            ox, oy   = self.SECTOR_OFFSETS[sector]
            rx = ox * math.cos(angle_rad) - oy * math.sin(angle_rad)
            ry = ox * math.sin(angle_rad) + oy * math.cos(angle_rad)
            ex = px + rx * R * 0.8 + random.uniform(-4, 4)
            ey = py + ry * R * 0.8 + random.uniform(-4, 4)

            heat  = min(1.0, dmg / 100.0)
            col   = (255, int(50 + 150*heat), int(20*(1-heat)))
            spd   = random.uniform(1.5, 4.5)
            ang   = random.uniform(0, math.pi*2)
            self._sparks.append({
                "x": ex, "y": ey,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": random.uniform(0.15, SPARK_LIFE),
                "max_life": SPARK_LIFE,
                "col": col,
                "sz":  random.randint(1, 3),
            })

        alive = []
        for sp in self._sparks:
            sp["life"] -= dt
            sp["x"]    += sp["vx"] * dt * 60
            sp["y"]    += sp["vy"] * dt * 60
            sp["vx"]   *= 0.88
            sp["vy"]   *= 0.88
            if sp["life"] > 0:
                alive.append(sp)
        self._sparks = alive

    def draw(self, surf, camera):
        for sp in self._sparks:
            sx = int(sp["x"] - camera.x)
            sy = int(sp["y"] - camera.y)
            if not (-10 < sx < SCREEN_W+10 and -10 < sy < SCREEN_H+10):
                continue
            alpha = int(220 * sp["life"] / sp["max_life"])
            r     = sp["sz"]
            gs    = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*sp["col"], alpha), (r, r), r)
            surf.blit(gs, (sx - r, sy - r))


class CameraShake:
    """Directional screen shake with exponential decay."""
    def __init__(self):
        self._offset = Vec2(0, 0)
        self._vel    = Vec2(0, 0)
        self._trauma = 0.0

    def add(self, direction: "Vec2", strength: float):
        """direction should be a unit vector pointing TOWARD the impact."""
        self._trauma = min(1.0, self._trauma + strength)
        if direction.length() > 0:
            self._vel += (-direction.normalize()) * strength * 18

    def update(self, dt: float):
        self._trauma = max(0.0, self._trauma - dt * SHAKE_DECAY * 0.5)
        noise_x = math.sin(time.time() * 47.3) * self._trauma ** 2 * 12
        noise_y = math.cos(time.time() * 31.7) * self._trauma ** 2 * 12
        self._vel += Vec2(noise_x, noise_y) * dt * 60
        self._vel  *= (1 - SHAKE_DECAY * dt)
        self._offset = self._vel

    @property
    def offset(self) -> "Vec2":
        return self._offset


class EcoEvolution:
    """Tracks player tactics and evolves enemy traits accordingly."""
    def __init__(self):
        self.shots_fired   = 0
        self.multi_used    = 0
        self.kills_by_type: Dict[str,int] = {}
        self.shield_proj   = 0.0
        self.dodge_boost   = 0.0
        self.evolved_color_mix = 0.0
        self._ticks = 0

    def register_shot(self, multi=False):
        self.shots_fired += 1
        if multi: self.multi_used += 1

    def register_kill(self, etype: str):
        self.kills_by_type[etype] = self.kills_by_type.get(etype, 0) + 1
        self._recalculate()

    def _recalculate(self):
        total = max(1, sum(self.kills_by_type.values()))
        multi_ratio = self.multi_used / max(1, self.shots_fired)
        self.shield_proj = min(0.55, multi_ratio * 1.2)
        self.dodge_boost = min(0.7, total / 180.0)
        self.evolved_color_mix = min(1.0, (self.shield_proj + self.dodge_boost) / 1.2)

    def apply_to_enemy(self, enemy):
        """Called right after EnemyFactory.configure()."""
        if self.shield_proj > 0.05:
            enemy._eco_shield = self.shield_proj
        else:
            enemy._eco_shield = 0.0
        if self.dodge_boost > 0.05:
            enemy.physics.max_speed = min(
                enemy.physics.max_speed * (1 + self.dodge_boost * 0.5),
                MAX_SPEED_ENEMY * 2.2
            )
        enemy._eco_mix = self.evolved_color_mix

    def hud_summary(self) -> str:
        if self.evolved_color_mix < 0.05:
            return ""
        parts = []
        if self.shield_proj > 0.1:
            parts.append(f"Escudo:{int(self.shield_proj*100)}%")
        if self.dodge_boost > 0.1:
            parts.append(f"Veloc.+{int(self.dodge_boost*50)}%")
        return "ECO: " + " | ".join(parts) if parts else ""


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

        warp_dur = 3.2
        nw  = int(sr * warp_dur)
        tw  = np.linspace(0, 1, nw)
        f_sweep = np.exp(np.linspace(np.log(80), np.log(3200), nw))
        wave_sweep = np.sin(2*np.pi * np.cumsum(f_sweep) / sr)
        h2 = np.sin(2*np.pi * np.cumsum(f_sweep * 1.5) / sr) * 0.4
        h3 = np.sin(2*np.pi * np.cumsum(f_sweep * 0.5) / sr) * 0.3
        noise_warp = np.random.uniform(-1, 1, nw)
        noise_env  = np.concatenate([
            np.linspace(0, 1,  int(nw*0.55)),
            np.linspace(1, 0,  nw - int(nw*0.55))
        ])
        sub_thump  = np.sin(2*np.pi*45*tw) * np.exp(-tw*6)
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

    def set_music_lowpass(self, active: bool, strength: float = 0.35):
        """
        Simulate a low-pass / muffled audio filter by reducing music volume.
        Called when player enters nebula or shield breaks.
        strength=0.0 → full volume, strength=1.0 → near-silent.
        """
        if not self._ok or not self._music_channel or self._music_muted:
            return
        target_vol = self._vol_music * (1.0 - strength * 0.72)
        self._music_channel.set_volume(max(0.0, target_vol))

    def restore_music_volume(self):
        """Restore music to full volume after muffling."""
        if not self._ok or not self._music_channel or self._music_muted:
            return
        self._music_channel.set_volume(self._vol_music)

    @property
    def muted(self): return self._muted


# Alias for pygame's 2D vector type used throughout the codebase.
Vec2 = pygame.math.Vector2

def vec_limit(v: Vec2, max_len: float) -> Vec2:
    """Return v scaled down to max_len if its length exceeds that value."""
    length = v.length()
    if length > max_len and length > 0:
        return v * (max_len / length)
    return Vec2(v)


class PerlinNoise:
    """
    Deterministic Perlin noise generator used for procedural terrain,
    asteroid density, and nebula colour variation.
    """
    def __init__(self, seed: int = 42):
        rng  = np.random.default_rng(seed)
        perm = np.arange(256, dtype=int)
        rng.shuffle(perm)
        self._p = np.concatenate([perm, perm])

    # Ken Perlin's smoothstep, linear interpolation, and gradient helpers.
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


# Axis-aligned bounding rectangle for a quadtree node.
@dataclass
class QTBounds:
    x: float; y: float; w: float; h: float
    def contains(self,px,py): return self.x<=px<self.x+self.w and self.y<=py<self.y+self.h

class Quadtree:
    """
    Recursive spatial partitioning structure used to accelerate
    bullet-enemy and bullet-asteroid collision queries.
    """
    def __init__(self, bounds, level=0):
        self.bounds  = bounds; self.level = level
        self.objects: List[Any] = []
        self.nodes:  List[Optional["Quadtree"]] = [None]*4

    def clear(self):
        """Remove all objects and collapse all child nodes."""
        self.objects.clear()
        for i in range(4):
            if self.nodes[i]: self.nodes[i].clear(); self.nodes[i]=None

    def _split(self):
        """Subdivide this node into four equal quadrants."""
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
        """Insert obj into the deepest fitting node, splitting if over capacity."""
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
        """Return all objects that could collide with obj."""
        result = list(self.objects)
        if self.nodes[0]:
            idx=self._get_index(obj)
            if idx!=-1: result.extend(self.nodes[idx].retrieve(obj))
            else:
                for n in self.nodes:
                    if n: result.extend(n.retrieve(obj))
        return result


class Component(ABC):
    """Base class for all entity components. owner is the entity that holds it."""
    def __init__(self, owner): self.owner = owner
    @abstractmethod
    def update(self, dt): ...

class TransformComponent(Component):
    """Stores world position, velocity and rotation angle. Updated every frame."""
    def __init__(self, owner, x=0.0, y=0.0):
        super().__init__(owner)
        self.pos   = Vec2(x, y)
        self.vel   = Vec2(0, 0)
        self.angle = 0.0

    def update(self, dt):
        self.pos += self.vel * dt * 60

class HealthComponent(Component):
    """Tracks HP, exposes a take_damage() method and a normalised ratio property."""
    def __init__(self, owner, max_hp):
        super().__init__(owner)
        self.max_hp = max_hp; self.hp = max_hp
    def take_damage(self, amount):
        """Reduce HP by amount. Returns True if the entity died (HP reached 0)."""
        self.hp = max(0, self.hp-amount)
        return self.hp <= 0
    @property
    def ratio(self): return self.hp/self.max_hp
    def update(self, dt): pass

class PhysicsComponent(Component):
    """Clamps velocity to max_speed and applies per-frame friction."""
    def __init__(self, owner, max_speed, friction=0.92):
        super().__init__(owner)
        self.max_speed = max_speed; self.friction = friction
    def update(self, dt):
        t = self.owner.transform
        t.vel = vec_limit(t.vel, self.max_speed)
        t.vel *= self.friction

class InputComponent(Component):
    """Reads keyboard/mouse state and applies acceleration and rotation to the player."""
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
    """
    Pre-allocates a fixed set of reusable objects to avoid GC pressure.
    Used for bullets and enemies. Inactive objects sit in _pool; active
    ones are tracked in _active.
    """
    def __init__(self, factory, size):
        self._pool   = [factory() for _ in range(size)]
        self._active = []
    def get(self):
        """Retrieve an object from the pool. Returns None if the pool is exhausted."""
        if self._pool:
            obj = self._pool.pop()
            self._active.append(obj)
            return obj
        return None
    def release(self, obj):
        """Return obj to the pool, calling reset() to clear its state."""
        if obj in self._active:
            self._active.remove(obj)
            obj.reset()
            self._pool.append(obj)
    @property
    def active(self): return self._active


class Bullet:
    """
    Pooled projectile. Supports player, enemy and faction-war ownership.
    Visual appearance uses a short line with a bright highlight at the centre.
    """
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
        self._bounced = False
        self._hacked  = False

    def reset(self):
        """Clear state so this object can be reused from the pool."""
        self.active = False; self.life = 0.0
        self._bounced = False
        self._hacked  = False

    def activate(self, x, y, vel, damage=10, owner="player", color=CYAN, angle=0.0):
        """Initialise the bullet at world position (x,y) with the given velocity."""
        self.rect.center = (int(x), int(y))
        self.vel    = Vec2(vel)
        self.damage = damage
        self.owner  = owner
        self.active = True
        self.life   = 0.0
        self.color  = color
        self.angle  = angle

    def update(self, dt, game=None):
        """Move the bullet and return False when it should be recycled."""
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


# Finite-state machine states for enemy AI.
class EnemyState(Enum):
    PATROL = auto(); CHASE = auto(); ATTACK = auto(); FLEE = auto()

class FSM:
    """
    Lightweight finite-state machine. Transitions are evaluated in
    insertion order; the first matching condition wins.
    """
    def __init__(self, initial):
        self.state = initial
        self._tr: Dict[EnemyState, List] = {}
    def add_transition(self, frm, cond, to, on_enter=None):
        """Register a conditional transition from state frm to state to."""
        self._tr.setdefault(frm,[]).append((cond,to,on_enter))
    def update(self, ctx):
        """Evaluate all transitions for the current state and switch if a condition fires."""
        for cond,to,on_enter in self._tr.get(self.state,[]):
            if cond(ctx):
                self.state = to
                if on_enter: on_enter(ctx)
                break
        return self.state


class Enemy:
    """
    Base enemy entity. Uses a component architecture (Transform, Health, Physics)
    and a Boids-based flocking force combined with FSM states (PATROL / CHASE /
    ATTACK / FLEE). Subclasses override _try_shoot() and draw() for specialised
    attack patterns and visuals.
    """
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
        self._eco_shield = 0.0
        self._eco_mix    = 0.0
        self._alerted    = False
        self._faction    = None
        self._faction_cd = 0.0
        self._build_fsm()

    def reset(self):
        self.active = False
        self.health.hp = self.health.max_hp
        self.transform.vel = Vec2(0,0)
        self.shoot_cd = 0.0
        self._faction = None
        self._faction_cd = 0.0

    def spawn(self, x, y):
        self.transform.pos = Vec2(x,y)
        self.active = True
        self.health.hp = self.health.max_hp
        self.fsm.state = EnemyState.PATROL
        self._faction = None

    def init_faction(self, faction: str):
        """Assign this enemy to a faction for inter-faction warfare."""
        self._faction = faction

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
        """Compute combined Boids steering force from nearby enemies."""
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
            self._alerted = False
        elif state == EnemyState.CHASE:
            if not self._alerted:
                self._alerted = True
                if hasattr(self.game, "_alert_waves"):
                    self.game._alert_waves.append(AlertWave(self.transform.pos.x, self.transform.pos.y))
                for ne in neighbors:
                    if ne is not self and ne.fsm.state == EnemyState.PATROL:
                        d2 = (ne.transform.pos - self.transform.pos).length()
                        if d2 < 200:
                            ne.fsm.state = EnemyState.CHASE
            to = player_pos - self.transform.pos
            if to.length()>0: force = to.normalize()*MAX_SPEED_ENEMY*W_SEEK_PLAYER
        elif state == EnemyState.ATTACK:
            to = player_pos - self.transform.pos
            if to.length()>80: force = to.normalize()*MAX_SPEED_ENEMY*0.4
            self._try_shoot(dt)
        elif state == EnemyState.FLEE:
            ally_center = Vec2(0, 0)
            ally_count  = 0
            for ne in neighbors:
                if ne is not self and ne.fsm.state != EnemyState.FLEE:
                    d2 = (ne.transform.pos - self.transform.pos).length()
                    if d2 < 250:
                        ally_center += ne.transform.pos
                        ally_count  += 1
            if ally_count > 0:
                ally_center /= ally_count
                to_ally = ally_center - self.transform.pos
                if to_ally.length() > 0:
                    force = to_ally.normalize() * MAX_SPEED_ENEMY * 1.2
            else:
                away = self.transform.pos - player_pos
                if away.length() > 0: force = away.normalize() * MAX_SPEED_ENEMY * 1.5

        self.transform.vel += (force+boids)*dt*60
        self.physics.update(dt)
        self.transform.update(dt)
        self.transform.pos.x = max(20, min(WORLD_W-20, self.transform.pos.x))
        self.transform.pos.y = max(20, min(WORLD_H-20, self.transform.pos.y))
        self.rect.center = (int(self.transform.pos.x), int(self.transform.pos.y))
        if self.shoot_cd>0: self.shoot_cd-=dt

    def _try_shoot(self, dt):
        """Fire a single bullet toward the player when the cooldown expires."""
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

        base_color = self.COLORS[self.fsm.state]
        mix = getattr(self, "_eco_mix", 0.0)
        eco_tint = (220, 80, 20)
        color = tuple(int(base_color[i]*(1-mix) + eco_tint[i]*mix) for i in range(3))
        faction = getattr(self, "_faction", None)
        if faction == FACTION_SWARM:
            color = (min(255, color[0]+50), color[1], max(0, color[2]-40))
        elif faction == FACTION_DRONE:
            color = (max(0, color[0]-40), color[1], min(255, color[2]+60))
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
    """
    Slow, high-HP enemy that fires three-bullet spread shots.
    Drawn as a hexagon to visually distinguish it from the triangular scouts.
    """
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
    """
    Lightweight enemy that fires a single fast-moving bullet with high damage.
    Prefers to maintain distance and flees when damaged.
    """
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
    """
    Rushes directly at the player and explodes on contact.
    Ignores the standard FSM and uses simplified direct-pursuit logic.
    """
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
    """
    Large enemy that periodically deploys scout drones from its pool slot.
    Destroying it stops the drone production for that instance.
    """
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
    """
    End-game boss with three attack phases: spread shot, burst, and omnidirectional.
    Periodically spawns minions and launches meteor projectiles at the player.
    Phase cycles every 12 seconds based on an internal timer.
    """
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
    """
    Slow-moving chunk of debris launched by TitanBoss toward the player's position.
    Damages the player on contact and is removed after a fixed lifetime.
    """
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
    """
    Stateless factory that configures a pooled Enemy instance for a given type.
    Centralises all stat definitions so balance changes are made in one place.
    """
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
        """Apply stat overrides from _types to the given enemy instance."""
        cfg = EnemyFactory._types.get(etype, EnemyFactory._types["scout"])
        enemy.health.max_hp      = cfg["hp"]
        enemy.health.hp          = cfg["hp"]
        enemy.physics.max_speed  = cfg["speed"]
        enemy.shoot_interval     = cfg["shoot"]
        enemy.etype              = etype
        return enemy


class Asteroid:
    """
    Procedurally shaped obstacle.  HP scales with radius; destroyed asteroids
    award a small XP and score bonus. Shape is pre-baked from a seeded RNG
    so it remains stable between frames.
    """
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


# Data container for a single upgradeable skill node.
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
    """
    Manages nine upgradeable skills. Skill points are earned on level-up
    and persisted to disk between sessions. get_stat() translates a skill
    level into a numeric multiplier used by the player entity.
    """
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
            "grav_pull":  Skill("Gravedad Cuántica", "Balas atraen enemigos, proyectiles curvan", 3, base_cost=3, cost_increment=1),
            "nano_bots":  Skill("Nano-Bots",       "Balas impacto orbitan buscando nuevo objetivo", 1, base_cost=4, cost_increment=0),
            "slingshot":  Skill("Asistencia Grav.", "Gana vel. extra cerca de planetas",             2, base_cost=2, cost_increment=1),
        }

    def new_game(self):
        self._reset_skills()

    def upgrade(self, key):
        """Spend points to advance a skill by one level if affordable."""
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
        """Return the numeric multiplier for a skill (1.0 = no bonus)."""
        s = self.skills.get(key)
        if not s: return 1.0
        if key == "grav_pull": return float(s.level)
        return 1.0 + s.level * 0.25

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
    """
    Tracks accumulated XP and handles level-up events.  On each level-up,
    the player receives +2 skill points and a rotating passive bonus
    (HP, speed, or extra skill points).
    """
    def __init__(self, player_ref):
        self.player           = player_ref
        self.level            = 1
        self.xp               = 0
        self.xp_next          = XP_BASE
        self.level_up_pending = False
        self.bonuses: List[str] = []
        self._banner_timer    = 0.0

    def add_xp(self, amount: int) -> bool:
        """Add XP and trigger a level-up if the threshold is reached. Returns True on level-up."""
        self.xp += amount
        if self.xp >= self.xp_next:
            self.xp      -= self.xp_next
            self.level   += 1
            self.xp_next  = int(XP_BASE * (XP_SCALE ** (self.level-1)))
            self.level_up_pending = True
            self._banner_timer    = 0.0
            self._apply_level_bonus()
            try:
                self.player.game._mission_log.log_event(f"levelup:{self.level}")
            except Exception:
                pass
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


class DirectionalShield:
    """
    Arc shield covering 90 degrees that the player rotates manually.
    Blocks projectiles coming from the shielded arc direction.
    Rotate with Q/R keys. Each block consumes shield energy; recharges over time.
    """
    ARC_DEGREES = 90.0
    MAX_ENERGY  = 100.0
    RECHARGE_RATE = 12.0   # energy/s
    DRAIN_PER_BLOCK = 25.0

    def __init__(self):
        self.angle    = 0.0      # center angle of shield arc in degrees (world-space)
        self.energy   = self.MAX_ENERGY
        self.active   = False    # True while [Q] held
        self._block_flash = 0.0

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.active = keys[pygame.K_q] and self.energy > 0
        if keys[pygame.K_r]:
            mx, my = pygame.mouse.get_pos()
            # Align shield toward mouse (set externally by player update)
            pass
        if not self.active:
            self.energy = min(self.MAX_ENERGY, self.energy + self.RECHARGE_RATE * dt)
        self._block_flash = max(0.0, self._block_flash - dt)

    def rotate_to_mouse(self, player_screen_x, player_screen_y):
        """Called from player update to keep arc aimed at mouse."""
        mx, my = pygame.mouse.get_pos()
        dx = mx - player_screen_x
        dy = my - player_screen_y
        if dx != 0 or dy != 0:
            self.angle = math.degrees(math.atan2(dy, dx))

    def blocks(self, impact_angle_deg: float) -> bool:
        """Return True if the shield absorbs a hit from impact_angle_deg."""
        if not self.active or self.energy <= 0:
            return False
        diff = (impact_angle_deg - self.angle + 180) % 360 - 180
        if abs(diff) <= self.ARC_DEGREES / 2:
            self.energy = max(0, self.energy - self.DRAIN_PER_BLOCK)
            self._block_flash = 0.15
            return True
        return False

    def draw(self, surf, sx, sy, player_angle_rad):
        """Draw the arc segment around the player ship."""
        if not self.active and self.energy >= self.MAX_ENERGY:
            return
        R = 36
        arc_rad = math.radians(self.ARC_DEGREES)
        start   = math.radians(self.angle) - arc_rad / 2
        end     = math.radians(self.angle) + arc_rad / 2

        energy_ratio = self.energy / self.MAX_ENERGY
        if self._block_flash > 0:
            col = (255, 255, 100)
        elif self.active:
            col = (int(80 * (1 - energy_ratio) + 0 * energy_ratio),
                   int(200 * energy_ratio),
                   int(255 * energy_ratio))
        else:
            col = (60, 60, 80)

        arc_surf = pygame.Surface((R*2+8, R*2+8), pygame.SRCALPHA)
        alpha = 200 if self.active else 80
        pygame.draw.arc(arc_surf, (*col, alpha),
                        (4, 4, R*2, R*2), -end, -start, 5)
        surf.blit(arc_surf, (sx - R - 4, sy - R - 4))

        # Energy bar under ship
        bw = 40
        pygame.draw.rect(surf, (20,20,20), (sx-bw//2, sy+R+4, bw, 5), border_radius=2)
        fill = int(bw * energy_ratio)
        if fill > 0:
            ecol = (0, 200, 255) if energy_ratio > 0.3 else (255, 80, 80)
            pygame.draw.rect(surf, ecol, (sx-bw//2, sy+R+4, fill, 5), border_radius=2)

    @property
    def ratio(self):
        return self.energy / self.MAX_ENERGY


class Player:
    """
    The player-controlled ship.  Composes Transform, Health, Physics and Input
    components. Shooting logic, nano-bot management, damage effects and
    module-stat integration all live here.
    """
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
        self.modules     = ModuleInventory()
        self.loc_damage  = LocalizedDamage()
        self._nano_bots: List[NanoBotCloud] = []
        self.dir_shield  = DirectionalShield()

    @property
    def shoot_interval(self):
        return 0.22 / self.game.skill_tree.get_stat("fire_rate")

    @property
    def bullet_damage(self):
        base = int(10 * self.game.skill_tree.get_stat("bullet_dmg"))
        return int(base * self.modules.stat_dmg_bonus())

    def update(self, dt):
        self.play_time += dt
        if not self._nano_bots:
            self._nano_bots = [NanoBotCloud(self.game, i) for i in range(6)]
        for nb in self._nano_bots:
            nb.update(dt)
        self.loc_damage.repair_over_time(dt)
        base_speed = MAX_SPEED_PLAYER * self.game.skill_tree.get_stat("speed")
        self.physics.max_speed = base_speed * self.modules.stat_speed_bonus()
        self.input.update(dt)
        self.physics.update(dt)
        self.transform.vel = self.loc_damage.apply_drift(self.transform.vel)
        self.transform.update(dt)
        self.transform.pos.x = max(20, min(WORLD_W-20, self.transform.pos.x))
        self.transform.pos.y = max(20, min(WORLD_H-20, self.transform.pos.y))
        self.rect.center = (int(self.transform.pos.x), int(self.transform.pos.y))
        if self.shoot_cd > 0: self.shoot_cd -= dt
        if self.inv_cd   > 0: self.inv_cd   -= dt
        self.dir_shield.update(dt)
        sx_p = int(self.transform.pos.x - self.game.camera.x)
        sy_p = int(self.transform.pos.y - self.game.camera.y)
        self.dir_shield.rotate_to_mouse(sx_p, sy_p)
        if pygame.mouse.get_pressed()[0] and self.shoot_cd <= 0:
            self._shoot()

    def _shoot(self):
        """Fire bullets toward the mouse cursor, respecting multi-shot level and synergies."""
        self.shoot_cd = self.shoot_interval
        self.game.sfx.play("player_shoot", 0.35)
        self.game.eco.register_shot(multi=self.game.skill_tree.skills["multi_shot"].level > 0)
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

        nexus = getattr(self.game, "nexus", None)
        if nexus and nexus.has_synergy("echo_shot"):
            self._echo_counter = getattr(self, "_echo_counter", 0) + 1
            if self._echo_counter >= 10:
                self._echo_counter = 0
                best_e = None
                best_d = 9999
                for e in self.game.enemy_pool.active:
                    if e.active:
                        d = (e.transform.pos - self.transform.pos).length()
                        if d < best_d:
                            best_d = d; best_e = e
                if best_e:
                    to_e = best_e.transform.pos - self.transform.pos
                    if to_e.length() > 0:
                        ev2 = to_e.normalize() * BULLET_SPEED
                        ea  = math.degrees(math.atan2(to_e.y, to_e.x)) + 90
                        b_e = self.game.bullet_pool.get()
                        if b_e:
                            b_e.activate(self.transform.pos.x, self.transform.pos.y,
                                         ev2, self.bullet_damage * 2, "player", GOLD, ea)


    def take_damage(self, amount, bullet_pos=None):
        """Apply damage, start invincibility frames, trigger audio muffling and camera shake."""
        if self.inv_cd <= 0:
            # Check directional shield
            if bullet_pos:
                impact_dir = bullet_pos - self.transform.pos
                impact_angle = math.degrees(math.atan2(impact_dir.y, impact_dir.x))
                if self.dir_shield.blocks(impact_angle):
                    # Shield absorbed the hit — spark effect only
                    self.game._particles_spawn(bullet_pos, (80, 220, 255), 6)
                    return
            prev_hp = self.health.hp
            self.health.take_damage(amount)
            self.inv_cd = 0.8
            self.game.sfx.play("player_hit")
            if prev_hp > self.health.hp and amount >= 15:
                self.game.sfx.set_music_lowpass(True, strength=0.55)
                self.game._audio_muffle_cd = 1.2
            if bullet_pos:
                self.loc_damage.register_hit(bullet_pos, self.transform.pos, self.transform.angle)
                d = bullet_pos - self.transform.pos
                if d.length() > 0:
                    self.game._cam_shake.add(d.normalize(), 0.45)
            else:
                self.game._cam_shake.add(Vec2(random.uniform(-1,1), random.uniform(-1,1)), 0.3)
            self.game._chroma_cd = 0.35

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

        for nb in self._nano_bots:
            nb.draw(surf, camera)

        #Tesla Link: draw lightning between active nano-bots within range 
        active_nbs = [nb for nb in self._nano_bots if nb.active]
        TESLA_DIST = 140
        for i in range(len(active_nbs)):
            for j in range(i+1, len(active_nbs)):
                nb_a = active_nbs[i]
                nb_b = active_nbs[j]
                pp2  = self.transform.pos
                pa   = Vec2(pp2.x + math.cos(nb_a.angle)*NANO_BOT_ORBIT_R,
                            pp2.y + math.sin(nb_a.angle)*NANO_BOT_ORBIT_R)
                pb2  = Vec2(pp2.x + math.cos(nb_b.angle)*NANO_BOT_ORBIT_R,
                            pp2.y + math.sin(nb_b.angle)*NANO_BOT_ORBIT_R)
                dist_ab = (pa - pb2).length()
                if dist_ab < TESLA_DIST:
                    sax = int(pa.x - camera.x); say = int(pa.y - camera.y)
                    sbx = int(pb2.x - camera.x); sby = int(pb2.y - camera.y)
                    # Jagged lightning: 4 midpoint segments
                    pts = [(sax, say)]
                    steps = 4
                    for k in range(1, steps):
                        t2 = k / steps
                        mx2 = int(sax + (sbx-sax)*t2 + random.randint(-6,6))
                        my2 = int(say + (sby-say)*t2 + random.randint(-6,6))
                        pts.append((mx2, my2))
                    pts.append((sbx, sby))
                    alpha = int(180 * (1 - dist_ab/TESLA_DIST))
                    bolt_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    pygame.draw.lines(bolt_s, (100, 220, 255, alpha), False, pts, 1)
                    pygame.draw.lines(bolt_s, (200, 240, 255, alpha//3), False, pts, 2)
                    surf.blit(bolt_s, (0, 0))

        # Directional Shield visual 
        angle_rad2 = math.radians(self.transform.angle)
        self.dir_shield.draw(surf, sx, sy, angle_rad2)

        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(surf, (0,70,110), (sx,sy), (mx,my), 1)





class GhostRun:
    """Saves last-run data and lets the player fight their own ghost."""
    @staticmethod
    def save(player, wave: int, sector: tuple):
        data = {
            "pos_x":   player.transform.pos.x,
            "pos_y":   player.transform.pos.y,
            "score":   player.score,
            "wave":    wave,
            "kills":   player.total_kills,
            "sector":  list(sector),
            "hp":      player.health.max_hp,
            "modules": {k: v for k, v in player.modules._slots.items()},
        }
        try:
            with open(GHOST_SAVE_FILE, "w") as f:
                import json
                json.dump(data, f)
        except Exception:
            pass

    @staticmethod
    def load() -> dict:
        try:
            if os.path.exists(GHOST_SAVE_FILE):
                with open(GHOST_SAVE_FILE) as f:
                    import json
                    return json.load(f)
        except Exception:
            pass
        return {}


class ShadowShip:
    """
    The ghost of the player's previous run.
    Appears as a wreck near death coordinates; when the player gets close,
    it activates as a boss-like shadow that mimics aggressive fighter AI.
    """
    RADIUS = 22
    HP     = 180

    def __init__(self, game):
        self.game    = game
        self.active  = False
        self.spawned = False
        self.pos     = Vec2(0, 0)
        self.vel     = Vec2(0, 0)
        self.hp      = self.HP
        self.max_hp  = self.HP
        self.rect    = pygame.Rect(0, 0, self.RADIUS*2, self.RADIUS*2)
        self.shoot_cd= 0.0
        self._angle  = 0.0
        self._wreck  = True
        self._data: dict = {}
        self._flash_t = 0.0
        self._alert_spawned = False

    def init_from_ghost(self, data: dict):
        self._data   = data
        self.pos     = Vec2(data.get("pos_x", WORLD_W//2),
                            data.get("pos_y", WORLD_H//2))
        self.hp      = int(self.HP * (1 + data.get("kills", 0) / 60))
        self.max_hp  = self.hp
        self.active  = True
        self._wreck  = True
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt):
        if not self.active: return
        player = self.game.player
        dist   = (player.transform.pos - self.pos).length()

        if self._wreck:
            if dist < 300:
                self._wreck = False
                self.game.ai_log._push("PECIO ACTIVADO — IA Sombra en línea.", 6.0)
                self.game.sfx.play("boss_warning")
            return

        to_player = player.transform.pos - self.pos
        if to_player.length() > 0:
            self._angle = math.degrees(math.atan2(to_player.y, to_player.x)) + 90
            if dist > 160:
                force = to_player.normalize() * 3.5
            else:
                force = Vec2(0, 0)
            self.vel += force * dt * 60
        spd = self.vel.length()
        if spd > 4.5: self.vel *= 4.5 / spd
        self.vel *= 0.92
        self.pos += self.vel * dt * 60
        self.pos.x = max(40, min(WORLD_W-40, self.pos.x))
        self.pos.y = max(40, min(WORLD_H-40, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        self.shoot_cd -= dt
        if self.shoot_cd <= 0 and dist < 320:
            self.shoot_cd = 0.9
            if to_player.length() > 0:
                vel = to_player.normalize() * (BULLET_SPEED * 0.7)
                ang = math.degrees(math.atan2(to_player.y, to_player.x)) + 90
                b   = self.game.bullet_pool.get()
                if b:
                    b.activate(self.pos.x, self.pos.y, vel, 12, "enemy",
                               (180, 80, 255), ang)

        self._flash_t = max(0.0, self._flash_t - dt)

    def take_damage(self, dmg) -> bool:
        self.hp = max(0, self.hp - dmg)
        self._flash_t = 0.08
        return self.hp <= 0

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        R  = self.RADIUS
        if not (-R-10 < sx < SCREEN_W+R+10 and -R-10 < sy < SCREEN_H+R+10): return

        if self._wreck:
            t = time.time()
            for i in range(5):
                a2  = math.radians(i * 72 + t * 20)
                r2  = int(R * 0.6)
                px2 = sx + int(math.cos(a2) * r2)
                py2 = sy + int(math.sin(a2) * r2)
                pygame.draw.circle(surf, (60, 30, 80), (px2, py2), 4)
            pygame.draw.circle(surf, (100, 50, 130), (sx, sy), R//2, 2)
            rm2 = ResourceManager()
            lbl = rm2.get_font(11, True).render("PECIO — acércate", True, (160, 80, 200))
            surf.blit(lbl, (sx - lbl.get_width()//2, sy - R - 16))
        else:
            col = WHITE if self._flash_t > 0 else (180, 80, 255)
            ang = math.radians(self._angle)

            def rot(dx, dy):
                rx = dx*math.cos(ang) - dy*math.sin(ang)
                ry = dx*math.sin(ang) + dy*math.cos(ang)
                return (int(sx+rx), int(sy+ry))

            pygame.draw.polygon(surf, (40,0,60),
                [rot(0,-R), rot(-R*0.55,R*0.65), rot(0,R*0.2), rot(R*0.55,R*0.65)])
            pygame.draw.polygon(surf, col,
                [rot(0,-R*0.9), rot(-R*0.45,R*0.55), rot(0,R*0.12), rot(R*0.45,R*0.55)])
            pygame.draw.polygon(surf, WHITE,
                [rot(0,-R*0.9), rot(-R*0.45,R*0.55), rot(0,R*0.12), rot(R*0.45,R*0.55)], 1)

            bw = 44
            pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2, sy-R-10, bw, 5))
            hcol = (180,80,255) if self.hp/self.max_hp > 0.4 else RED
            pygame.draw.rect(surf, hcol, (sx-bw//2, sy-R-10, int(bw*self.hp/self.max_hp), 5))
            rm2 = ResourceManager()
            lbl = rm2.get_font(11, True).render("IA SOMBRA", True, (180, 80, 255))
            surf.blit(lbl, (sx - lbl.get_width()//2, sy - R - 22))



class NebulaTerrainSystem:
    """
    Queries PerlinNoise at player position to apply terrain effects:
      • Interference nebula (high noise): radar glitch, HUD flicker
      • Plasma nebula (very high noise): shield drain, speed overcharge
    These are purely positional – no separate objects needed.
    """
    def __init__(self, noise: "PerlinNoise"):
        self._noise = noise
        self.in_interference = False
        self.in_plasma       = False
        self._plasma_boost   = 0.0

    def update(self, player_pos: "Vec2", player, dt: float):
        x, y  = player_pos.x / 900, player_pos.y / 900
        val   = (self._noise.octave_noise(x, y, octaves=3) + 1) / 2

        self.in_interference = val > NEBULA_RADAR_THRESH
        self.in_plasma       = val > NEBULA_PLASMA_THRESH

        if self.in_plasma:
            player.physics.max_speed = min(
                player.physics.max_speed * (1 + 0.8 * dt),
                MAX_SPEED_PLAYER * 2.8
            )
            if player.inv_cd <= 0:
                player.health.hp = max(1, player.health.hp - int(6 * dt + 0.5))
            self._plasma_boost = 1.0
        else:
            self._plasma_boost = max(0.0, self._plasma_boost - dt * 2)

    def hud_label(self) -> str:
        if self.in_plasma:       return "  PLASMA — Vel MAX | Escudo drain"
        if self.in_interference: return "  Interferencia — Radar OFF"
        return ""

    def radar_active(self) -> bool:
        return not self.in_interference



class AlertWave:
    """Visual radio-wave ripple emitted when an enemy spots the player."""
    def __init__(self, x, y):
        self.pos    = Vec2(x, y)
        self.radius = 20.0
        self.max_r  = 260.0
        self.active = True

    def update(self, dt):
        self.radius += ALERT_WAVE_SPEED * dt
        if self.radius >= self.max_r:
            self.active = False

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        r  = int(self.radius)
        al = int(160 * (1 - self.radius / self.max_r))
        gs = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (255, 180, 0, al), (r+2, r+2), r, 2)
        surf.blit(gs, (sx-r-2, sy-r-2))


class OrbitalBody:
    """Planet or neutron star with real gravitational field and warp-grid visual."""
    TYPE_PLANET  = "planet"
    TYPE_NEUTRON = "neutron"

    PLANET_COLORS = [(60,120,200),(80,160,80),(160,80,60),(120,60,180),(200,140,40)]

    def __init__(self, x, y, mass, btype, seed=0):
        self.pos    = Vec2(x, y)
        self.mass   = mass
        self.radius = int(20 + mass * 0.06)
        self.type   = btype
        self._color = self.PLANET_COLORS[seed % len(self.PLANET_COLORS)]
        self._pulse = 0.0
        self._ring_angle = 0.0
        self.rect   = pygame.Rect(0, 0, self.radius*2, self.radius*2)
        self.rect.center = (int(x), int(y))

    def update(self, dt):
        self._pulse      += dt
        self._ring_angle += dt * 0.4

    def gravity_force(self, pos: "Vec2", dt: float) -> "Vec2":
        d    = self.pos - pos
        dist = max(self.radius + 5, d.length())
        strength = PLANET_GRAVITY * self.mass / (dist * dist) * dt
        return d.normalize() * strength

    def draw(self, surf, camera):
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        R  = self.radius
        if not (-R-10 < sx < SCREEN_W+R+10 and -R-10 < sy < SCREEN_H+R+10):
            return

        self._draw_warp_grid(surf, sx, sy, camera)

        if self.type == self.TYPE_NEUTRON:
            for r in range(R+20, 0, -4):
                al = int(50 * (1 - r/(R+20)))
                gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (140, 180, 255, al), (r, r), r)
                surf.blit(gs, (sx-r, sy-r))
            pulse_r = R + int(4 * math.sin(self._pulse * 6))
            pygame.draw.circle(surf, (200, 220, 255), (sx, sy), pulse_r)
            pygame.draw.circle(surf, WHITE, (sx, sy), max(4, R//3))
            rm2 = ResourceManager()
            lbl = rm2.get_font(10, True).render(" ESTRELLA DE NEUTRONES", True, (180, 210, 255))
            surf.blit(lbl, (sx - lbl.get_width()//2, sy + R + 4))
        else:
            atm_r = R + 8
            atm_s = pygame.Surface((atm_r*2, atm_r*2), pygame.SRCALPHA)
            pygame.draw.circle(atm_s, (*self._color, 35), (atm_r, atm_r), atm_r)
            surf.blit(atm_s, (sx-atm_r, sy-atm_r))
            pygame.draw.circle(surf, tuple(max(0,c-50) for c in self._color), (sx, sy), R)
            pygame.draw.circle(surf, self._color, (sx-2, sy-2), R)
            for i in range(3):
                stripe_y = sy - R//2 + i*(R//2)
                w2 = int(math.sqrt(max(0, R**2 - (stripe_y-sy)**2)))
                pygame.draw.line(surf, tuple(min(255,c+30) for c in self._color),
                                 (sx-w2, stripe_y), (sx+w2, stripe_y), 1)
            pygame.draw.circle(surf, WHITE, (sx, sy), R, 1)
            rx = int(R * 1.8)
            ry = int(R * 0.3)
            ring_surf = pygame.Surface((rx*2+4, ry*2+4), pygame.SRCALPHA)
            pygame.draw.ellipse(ring_surf, (*self._color, 80), (0, 0, rx*2, ry*2), 2)
            angle_deg = math.degrees(self._ring_angle)
            ring_rot  = pygame.transform.rotate(ring_surf, angle_deg)
            surf.blit(ring_rot, (sx - ring_rot.get_width()//2,
                                  sy - ring_rot.get_height()//2))
            rm2 = ResourceManager()
            lbl = rm2.get_font(10).render("PLANETA", True, self._color)
            surf.blit(lbl, (sx - lbl.get_width()//2, sy + R + 4))

    def _draw_warp_grid(self, surf, sx, sy, camera):
        """Draw a distorted grid around the body showing gravitational lensing."""
        influence = self.radius * 5
        step = 40
        col  = (30, 50, 100) if self.type == self.TYPE_PLANET else (60, 0, 120)

        for gy in range(-influence, influence+1, step):
            pts = []
            for gx in range(-influence, influence+1, step//2):
                wx = self.pos.x + gx
                wy = self.pos.y + gy
                d  = math.hypot(gx, gy)
                if d < 1: d = 1
                factor = min(0.85, self.mass * 18000 / (d * d))
                dx2 = gx / d * factor * -1
                dy2 = gy / d * factor * -1
                px2 = int(wx + dx2*step - camera.x)
                py2 = int(wy + dy2*step - camera.y)
                pts.append((px2, py2))
            if len(pts) > 1:
                pygame.draw.lines(surf, col, False, pts, 1)

        for gx in range(-influence, influence+1, step):
            pts = []
            for gy in range(-influence, influence+1, step//2):
                wx = self.pos.x + gx
                wy = self.pos.y + gy
                d  = math.hypot(gx, gy)
                if d < 1: d = 1
                factor = min(0.85, self.mass * 18000 / (d * d))
                dx2 = gx / d * factor * -1
                dy2 = gy / d * factor * -1
                px2 = int(wx + dx2*step - camera.x)
                py2 = int(wy + dy2*step - camera.y)
                pts.append((px2, py2))
            if len(pts) > 1:
                pygame.draw.lines(surf, col, False, pts, 1)



class BossSegment:
    """One ring of the segmented worm boss."""
    def __init__(self, idx: int):
        self.idx     = idx
        self.pos     = Vec2(0, 0)
        self.hp      = 80 - idx * 4
        self.max_hp  = self.hp
        self.radius  = max(10, 26 - idx * 2)
        self.active  = True
        self.rect    = pygame.Rect(0, 0, self.radius*2, self.radius*2)
        self._flash  = 0.0

    def take_damage(self, dmg) -> bool:
        self.hp = max(0, self.hp - dmg)
        self._flash = 0.08
        return self.hp <= 0

    def draw(self, surf, camera, angle: float):
        if not self.active: return
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        R  = self.radius
        if not (-R-5 < sx < SCREEN_W+R+5 and -R-5 < sy < SCREEN_H+R+5): return
        ratio = self.hp / self.max_hp
        col   = WHITE if self._flash > 0 else (
            int(220*(1-ratio)+40*ratio), int(80*ratio), int(40+80*ratio))
        pygame.draw.circle(surf, (20, 5, 5), (sx+2, sy+2), R)
        pygame.draw.circle(surf, col, (sx, sy), R)
        pygame.draw.circle(surf, WHITE, (sx, sy), R, 1)
        self._flash = max(0.0, self._flash - 0.016)
        bw = R*2
        pygame.draw.rect(surf, DARK_GRAY, (sx-R, sy-R-6, bw, 3))
        pygame.draw.rect(surf, col, (sx-R, sy-R-6, int(bw*ratio), 3))
        self.rect.center = (sx + int(camera.x), sy + int(camera.y))


class SegmentedWormBoss:
    """
    Multi-segment space worm.  Each segment is independent; destroying all
    segments kills the boss.  The head does shooting; body/tail are pure HP sinks.
    """
    NUM_SEGMENTS = 8
    SEG_SPACING  = 30

    def __init__(self, game):
        self.game     = game
        self.active   = False
        self.segments: List[BossSegment] = [BossSegment(i) for i in range(self.NUM_SEGMENTS)]
        self._trail: List[Vec2] = []
        self._speed  = 2.8
        self._angle  = 0.0
        self._shoot_cd = 0.0
        self._debris: List[dict] = []

    @property
    def head(self) -> BossSegment:
        return self.segments[0]

    def spawn(self, x, y):
        for i, seg in enumerate(self.segments):
            seg.pos    = Vec2(x - i * self.SEG_SPACING, y)
            seg.hp     = seg.max_hp
            seg.active = True
        self._trail = [Vec2(s.pos) for s in self.segments]
        self.active = True
        self.game.ai_log._push("GUSANO ESPACIAL detectado. Prioridad MÁXIMA.", 7.0)
        self.game.sfx.play("boss_warning")
        self.game.sfx.play("titan_spawn")

    def update(self, dt):
        if not self.active: return
        player = self.game.player
        head   = self.head

        to_p  = player.transform.pos - head.pos
        if to_p.length() > 0:
            target_ang = math.atan2(to_p.y, to_p.x)
            diff = (target_ang - math.radians(self._angle) + math.pi) % (2*math.pi) - math.pi
            self._angle += math.degrees(diff) * min(dt * 2.5, 1.0)
        head.pos.x += math.cos(math.radians(self._angle)) * self._speed * dt * 60
        head.pos.y += math.sin(math.radians(self._angle)) * self._speed * dt * 60
        head.pos.x  = max(40, min(WORLD_W-40, head.pos.x))
        head.pos.y  = max(40, min(WORLD_H-40, head.pos.y))
        head.rect.center = (int(head.pos.x), int(head.pos.y))

        self._trail.insert(0, Vec2(head.pos))
        max_trail = self.NUM_SEGMENTS * self.SEG_SPACING * 2
        if len(self._trail) > max_trail:
            self._trail = self._trail[:max_trail]

        for i in range(1, self.NUM_SEGMENTS):
            seg = self.segments[i]
            if not seg.active: continue
            target_dist = i * self.SEG_SPACING
            for t_pos in self._trail:
                if (head.pos - t_pos).length() >= target_dist:
                    seg.pos = Vec2(t_pos)
                    seg.rect.center = (int(seg.pos.x), int(seg.pos.y))
                    break

        self._shoot_cd -= dt
        if head.active and self._shoot_cd <= 0 and to_p.length() < 500:
            self._shoot_cd = 1.4
            vel = to_p.normalize() * (BULLET_SPEED * 0.65) if to_p.length() > 0 else Vec2(0,0)
            ang = math.degrees(math.atan2(vel.y, vel.x)) + 90
            b   = self.game.bullet_pool.get()
            if b:
                b.activate(head.pos.x, head.pos.y, vel, 14, "enemy", (255, 80, 40), ang)

        for d in self._debris:
            d["pos"] += d["vel"] * dt * 60
            d["vel"] *= 0.97
            d["life"] -= dt
        self._debris = [d for d in self._debris if d["life"] > 0]

        if not any(s.active for s in self.segments):
            self.active = False
            self.game.player.score += 2500
            self.game.player.add_xp(800)
            self.game._nebula_flash_cd = 0.35

    def hit_segment(self, seg_idx: int, dmg: int):
        seg = self.segments[seg_idx]
        if seg.take_damage(dmg):
            for _ in range(6):
                a = random.uniform(0, math.pi*2)
                spd = random.uniform(1.0, 3.5)
                self._debris.append({
                    "pos": Vec2(seg.pos),
                    "vel": Vec2(math.cos(a)*spd, math.sin(a)*spd),
                    "life": random.uniform(2.0, 5.0),
                    "col": (120, 40, 20),
                    "r": random.randint(3, 7)
                })
            seg.active = False
            self.game._particles_spawn(seg.pos, RED, 12)
            self.game.sfx.play("explosion")

    def draw(self, surf, camera):
        if not self.active: return
        prev = None
        for seg in self.segments:
            if not seg.active:
                prev = None
                continue
            sx = int(seg.pos.x - camera.x)
            sy = int(seg.pos.y - camera.y)
            if prev:
                pygame.draw.line(surf, (80, 20, 10), prev, (sx, sy), 3)
            prev = (sx, sy)
        ang = self._angle
        for seg in reversed(self.segments):
            seg.draw(surf, camera, ang)
        for d in self._debris:
            dx = int(d["pos"].x - camera.x)
            dy = int(d["pos"].y - camera.y)
            al = int(200 * d["life"] / 5.0)
            pygame.draw.circle(surf, (*d["col"], al) if len(d["col"])==3 else d["col"],
                               (dx, dy), d["r"])



class NanoBotCloud:
    """
    Spawned when nano_bots skill is active.  Bullets that hit an enemy instead
    orbit the player for NANO_BOT_ORBIT_T seconds seeking new targets.
    """
    def __init__(self, game, idx: int):
        self.game   = game
        self.active = False
        self.angle  = idx * (math.pi * 2 / 6)
        self.life   = NANO_BOT_ORBIT_T
        self.damage = 8

    def spawn(self, damage: int):
        self.active = True
        self.life   = NANO_BOT_ORBIT_T
        self.damage = damage

    def update(self, dt):
        if not self.active: return
        self.life -= dt
        if self.life <= 0:
            self.active = False
            return
        self.angle += dt * 2.8
        pp  = self.game.player.transform.pos
        my_pos = Vec2(
            pp.x + math.cos(self.angle) * NANO_BOT_ORBIT_R,
            pp.y + math.sin(self.angle) * NANO_BOT_ORBIT_R
        )
        best_e, best_d = None, 180.0
        for e in self.game.enemy_pool.active:
            if not e.active: continue
            d = (e.transform.pos - my_pos).length()
            if d < best_d:
                best_d, best_e = d, e
        if best_e and best_d < 100:
            to_e = best_e.transform.pos - my_pos
            if to_e.length() > 0:
                move = to_e.normalize() * 5.0
                new_pos = my_pos + move
                if new_pos.distance_to(best_e.transform.pos) < best_e.RADIUS + 4:
                    shield = getattr(best_e, "_eco_shield", 0.0)
                    dead   = best_e.health.take_damage(max(1, int(self.damage * (1 - shield))))
                    self.game._particles_spawn(best_e.transform.pos, CYAN, 5)
                    if dead:
                        best_e.active = False
                        self.game.enemy_pool.release(best_e)
                        self.game.player.score += 80
                        self.game.player.add_xp(30)
                        self.game.sfx.play("explosion_small")
                    self.active = False

    def draw(self, surf, camera):
        if not self.active: return
        pp  = self.game.player.transform.pos
        sx  = int(pp.x + math.cos(self.angle) * NANO_BOT_ORBIT_R - camera.x)
        sy  = int(pp.y + math.sin(self.angle) * NANO_BOT_ORBIT_R - camera.y)
        alpha = int(200 * self.life / NANO_BOT_ORBIT_T)
        gs = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(gs, (0, 220, 255, alpha), (5, 5), 4)
        surf.blit(gs, (sx-5, sy-5))



class LocalizedDamage:
    """
    Divides the ship into 4 sectors (Front/Back/Left/Right).
    Heavy damage to a sector causes drift toward that side.
    """
    SECTORS = ["Front", "Back", "Left", "Right"]

    def __init__(self):
        self.damage  = {s: 0 for s in self.SECTORS}
        self._drift  = Vec2(0, 0)
        self._drift_labels = {"Front": Vec2(0,-1), "Back": Vec2(0,1),
                              "Left":  Vec2(-1,0),  "Right": Vec2(1,0)}

    def register_hit(self, bullet_pos: "Vec2", player_pos: "Vec2", player_angle: float):
        """Determine which sector was hit based on angle."""
        d = bullet_pos - player_pos
        if d.length() == 0: return
        ship_rad = math.radians(player_angle)
        local_x  =  d.x * math.cos(-ship_rad) - d.y * math.sin(-ship_rad)
        local_y  =  d.x * math.sin(-ship_rad) + d.y * math.cos(-ship_rad)
        if abs(local_x) > abs(local_y):
            sector = "Right" if local_x > 0 else "Left"
        else:
            sector = "Back" if local_y > 0 else "Front"
        self.damage[sector] = min(100, self.damage[sector] + 10)
        self._recalc_drift()

    def _recalc_drift(self):
        drift = Vec2(0, 0)
        for s, dmg in self.damage.items():
            if dmg > 30:
                drift += self._drift_labels[s] * (dmg / 100.0) * 0.12
        self._drift = drift

    def apply_drift(self, vel: "Vec2") -> "Vec2":
        return vel + self._drift

    def repair_over_time(self, dt: float):
        for s in self.SECTORS:
            self.damage[s] = max(0, self.damage[s] - dt * 2)
        self._recalc_drift()

    def worst_sector(self):
        return max(self.damage, key=self.damage.get)

    def draw_hud(self, surf, rm, cx, cy):
        """Draw a tiny 4-quadrant ship damage indicator."""
        size = 28
        colors = {s: self._dmg_color(self.damage[s]) for s in self.SECTORS}
        offsets = {"Front":(0,-size//2), "Back":(0,size//2),
                   "Left":(-size//2,0),  "Right":(size//2,0)}
        for s, (ox, oy) in offsets.items():
            pygame.draw.rect(surf, colors[s],
                             (cx+ox-8, cy+oy-8, 16, 16), border_radius=3)
            pygame.draw.rect(surf, WHITE,
                             (cx+ox-8, cy+oy-8, 16, 16), 1, border_radius=3)
        pygame.draw.line(surf, WHITE, (cx-size//2, cy), (cx+size//2, cy), 1)
        pygame.draw.line(surf, WHITE, (cx, cy-size//2), (cx, cy+size//2), 1)
        worst = self.worst_sector()
        if self.damage[worst] > 25:
            lbl = rm.get_font(10, True).render(f" {worst[:2]}", True, RED)
            surf.blit(lbl, (cx - lbl.get_width()//2, cy + size//2 + 4))

    @staticmethod
    def _dmg_color(dmg):
        r = min(255, int(dmg * 2.55))
        g = max(0,   int(255 - dmg * 2.55))
        return (r, g, 0)



class MissionLog:
    """
    Records player trajectory and key events.
    On death, generates a procedural chronicle and a mini heat-map.
    """
    SAMPLE_INTERVAL = 0.8

    def __init__(self):
        self._positions: List[Tuple[float,float]] = []
        self._events:    List[str] = []
        self._cd = 0.0

    def update(self, dt, player):
        self._cd -= dt
        if self._cd <= 0:
            self._cd = self.SAMPLE_INTERVAL
            self._positions.append((player.transform.pos.x, player.transform.pos.y))
            if len(self._positions) > 600:
                self._positions = self._positions[-600:]

    def log_event(self, text: str):
        self._events.append(text)
        if len(self._events) > 40:
            self._events = self._events[-40:]

    def generate_chronicle(self, stats: dict) -> List[str]:
        kills   = stats.get("total_kills", 0)
        wave    = stats.get("wave", 0)
        score   = stats.get("score", 0)
        mode    = stats.get("mode", "")
        ks      = stats.get("kills", {})
        time_s  = int(stats.get("play_time", 0))
        mins    = time_s // 60
        secs    = time_s % 60

        last_pos = self._positions[-1] if self._positions else (WORLD_W//2, WORLD_H//2)
        sector_x = int(last_pos[0] // SECTOR_SIZE)
        sector_y = int(last_pos[1] // SECTOR_SIZE)

        fav_enemy = max(ks, key=ks.get) if ks else "ninguno"
        fav_names = {
            "scout":"Exploradores","fighter":"Cazadores","kamikaze":"Kamikazes",
            "sniper":"Francotiradores","heavy":"Pesados","carrier":"Transportadores",
            "boss":"Jefes","titan":"TITANES"
        }

        lines = [
            f" CRÓNICA DE MISIÓN ",
            f"Modo: {mode} | Duración: {mins}m {secs:02d}s",
            f"El piloto operó en el Sector ({sector_x},{sector_y}).",
        ]
        if kills > 0:
            lines.append(f"Eliminó {kills} hostiles siendo el terror de los {fav_names.get(fav_enemy,'enemigos')}.")
        if wave > 0:
            lines.append(f"Resistió {wave} oleada{'s' if wave!=1 else ''} antes de caer.")
        if score > 5000:
            lines.append("Su puntuación resonó en los registros del sector.")
        elif score > 1000:
            lines.append("Dejó una marca modesta en los archivos de combate.")
        else:
            lines.append("El espacio apenas registró su paso.")
        flavours = [
            "Los asteroides aún llevan las marcas de su paso.",
            "Las criaturas espaciales se alejaron de su trayectoria.",
            "La IA de la nave reportó: 'Actuación... aceptable.'",
            "Los enemigos supervivientes no hablarán de esta batalla.",
            "El eco de sus disparos se perdió en la nebulosa.",
        ]
        lines.append(random.choice(flavours))
        return lines

    def draw_heatmap(self, surf, offset_x, offset_y, w, h):
        """Draw a mini trajectory heatmap scaled to (w x h) at (offset_x, offset_y)."""
        if len(self._positions) < 2: return
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((4, 4, 16, 200))
        surf.blit(bg, (offset_x, offset_y))
        pygame.draw.rect(surf, (40, 40, 80), (offset_x, offset_y, w, h), 1)

        sx2 = w / WORLD_W
        sy2 = h / WORLD_H
        pts = [(offset_x + int(x*sx2), offset_y + int(y*sy2))
               for x, y in self._positions]
        n = len(pts)
        for i in range(1, n):
            ratio = i / n
            col   = (int(255*ratio), int(80*(1-ratio)), int(180*(1-ratio)))
            pygame.draw.line(surf, col, pts[i-1], pts[i], 1)
        if pts:
            pygame.draw.circle(surf, RED, pts[-1], 3)

        rm2 = ResourceManager()
        lbl = rm2.get_font(10).render("Trayectoria", True, (80,80,120))
        surf.blit(lbl, (offset_x + 2, offset_y + h - 14))

    def reset(self):
        self._positions.clear()
        self._events.clear()
        self._cd = 0.0


class SpaceCreature:
    """Neutral wandering creature – can be hunted for XP and module drops."""
    RADIUS = 14
    def __init__(self):
        self.pos    = Vec2(0, 0)
        self.vel    = Vec2(0, 0)
        self.hp     = CREATURE_HP
        self.max_hp = CREATURE_HP
        self.active = False
        self.angle  = 0.0
        self.rect   = pygame.Rect(0, 0, self.RADIUS*2, self.RADIUS*2)
        self._wander_t = 0.0

    def spawn(self, x, y):
        self.pos  = Vec2(x, y)
        ang = random.uniform(0, math.pi*2)
        self.vel  = Vec2(math.cos(ang)*CREATURE_SPEED, math.sin(ang)*CREATURE_SPEED)
        self.hp   = self.max_hp
        self.active = True

    def update(self, dt):
        if not self.active: return
        self._wander_t += dt
        turn = math.sin(self._wander_t * 0.7 + id(self)*0.001) * 0.04
        cs, sn = math.cos(turn), math.sin(turn)
        vx, vy = self.vel.x*cs - self.vel.y*sn, self.vel.x*sn + self.vel.y*cs
        self.vel = Vec2(vx, vy)
        spd = self.vel.length()
        if spd > CREATURE_SPEED: self.vel *= CREATURE_SPEED / spd
        self.pos += self.vel * dt * 60
        self.pos.x = max(40, min(WORLD_W-40, self.pos.x))
        self.pos.y = max(40, min(WORLD_H-40, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.angle = math.degrees(math.atan2(self.vel.y, self.vel.x))

    def take_damage(self, dmg) -> bool:
        self.hp = max(0, self.hp - dmg)
        return self.hp <= 0

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        if not (-40 < sx < SCREEN_W+40 and -40 < sy < SCREEN_H+40): return
        t = time.time()
        pulse = int(6 + 4*math.sin(t*3 + id(self)*0.1))
        for r in range(pulse, 0, -2):
            a = int(80 * r / pulse)
            gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (0, 200, 140, a), (r,r), r)
            surf.blit(gs, (sx-r, sy-r))
        pygame.draw.circle(surf, (0, 255, 180), (sx, sy), 5)
        for i in range(5):
            a2 = math.radians(self.angle + i*72 + t*60)
            tx2 = sx + int(math.cos(a2)*12)
            ty2 = sy + int(math.sin(a2)*12)
            pygame.draw.line(surf, (0, 180, 120), (sx, sy), (tx2, ty2), 1)
        bw = 28
        pygame.draw.rect(surf, DARK_GRAY, (sx-bw//2, sy-22, bw, 3))
        pygame.draw.rect(surf, (0,220,140), (sx-bw//2, sy-22, int(bw*self.hp/self.max_hp), 3))


class GravityZone:
    """Black hole, slow nebula, or white hole zone generated procedurally in sectors."""
    TYPE_BLACKHOLE = "blackhole"
    TYPE_NEBULA    = "nebula"
    TYPE_WHITEHOLE = "whitehole"

    def __init__(self, x, y, radius, zone_type):
        self.pos      = Vec2(x, y)
        self.radius   = radius
        self.type     = zone_type
        self._warned  = False
        self._pulse_t = 0.0

    def update(self, dt):
        self._pulse_t += dt

    def apply(self, entity_pos: "Vec2", entity_vel: "Vec2", dt: float) -> "Vec2":
        """Returns velocity delta to apply."""
        d = entity_pos - self.pos
        dist = d.length()
        if dist > self.radius or dist < 1: return Vec2(0,0)
        strength = 1.0 - dist/self.radius
        if self.type == self.TYPE_BLACKHOLE:
            pull = -d.normalize() * GRAVITY_STRENGTH * strength * dt
            return pull
        if self.type == self.TYPE_WHITEHOLE:
            push = d.normalize() * GRAVITY_STRENGTH * 0.65 * strength * dt
            return push
        return Vec2(0, 0)

    def in_zone(self, pos: "Vec2") -> bool:
        return (pos - self.pos).length() < self.radius

    def draw(self, surf, camera):
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        r  = self.radius
        if not (-r < sx < SCREEN_W+r and -r < sy < SCREEN_H+r): return
        t = self._pulse_t
        if self.type == self.TYPE_BLACKHOLE:
            for ring_r in range(int(r), 0, -20):
                al = int(40 * (1 - ring_r/r) + 10*math.sin(t*2 + ring_r*0.05))
                al = max(0, min(90, al))
                gs = pygame.Surface((ring_r*2, ring_r*2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (60, 0, 120, al), (ring_r, ring_r), ring_r)
                surf.blit(gs, (sx-ring_r, sy-ring_r))
            core = int(18 + 6*math.sin(t*4))
            pygame.draw.circle(surf, (0,0,0), (sx, sy), core)
            pygame.draw.circle(surf, (140,0,220), (sx, sy), core, 2)
            rm2 = ResourceManager()
            lbl = rm2.get_font(11, True).render("AGUJERO NEGRO", True, (140,0,220))
            surf.blit(lbl, (sx - lbl.get_width()//2, sy + core + 4))
        else:
            for ring_r in range(int(r), 0, -25):
                al = int(18 * (1 - ring_r/r))
                gs = pygame.Surface((ring_r*2, ring_r*2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (0, 60, 160, al), (ring_r, ring_r), ring_r)
                surf.blit(gs, (sx-ring_r, sy-ring_r))
            rm2 = ResourceManager()
            lbl = rm2.get_font(11).render("NEBULOSA DENSA", True, (60, 120, 200))
            surf.blit(lbl, (sx - lbl.get_width()//2, sy - 14))

        if self.type == self.TYPE_WHITEHOLE:
            for ring_r in range(int(r), 0, -20):
                al = int(35 * (ring_r/r) + 5*math.sin(t*3 + ring_r*0.05))
                al = max(0, min(90, al))
                gs = pygame.Surface((ring_r*2, ring_r*2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (255, 255, 180, al), (ring_r, ring_r), ring_r)
                surf.blit(gs, (sx-ring_r, sy-ring_r))
            core = int(18 + 6*math.sin(t*4))
            pygame.draw.circle(surf, (255, 255, 255), (sx, sy), core)
            pygame.draw.circle(surf, (255, 220, 80), (sx, sy), core, 2)
            rm2 = ResourceManager()
            lbl = rm2.get_font(11, True).render("AGUJERO BLANCO", True, (255, 230, 80))
            surf.blit(lbl, (sx - lbl.get_width()//2, sy + core + 4))

class ShipModule:
    """Dropped by destroyed enemies; player collects them for stat boosts."""
    TYPES = {
        "wing":   {"label":"ALA",    "color":(100,200,255), "desc":"Giro +15%",    "stat":"turn"},
        "engine": {"label":"MOTOR",  "color":(255,160,40),  "desc":"Vel +10%",     "stat":"speed"},
        "armor":  {"label":"ARMADURA","color":(80,220,80),  "desc":"HP +25",       "stat":"hp"},
        "core":   {"label":"NÚCLEO", "color":(200,80,255),  "desc":"Daño +12%",    "stat":"dmg"},
        "lens":   {"label":"LENTE",  "color":(255,220,0),   "desc":"Gravedad",    "stat":"grav"},
    }
    RADIUS = 10

    def __init__(self, x, y, mtype):
        self.pos    = Vec2(x, y)
        self.mtype  = mtype
        self.active = True
        self.rect   = pygame.Rect(0, 0, self.RADIUS*2, self.RADIUS*2)
        self.rect.center = (int(x), int(y))
        self._life  = 12.0
        self._pulse = 0.0

    def update(self, dt):
        self._life  -= dt
        self._pulse += dt
        if self._life <= 0: self.active = False

    def draw(self, surf, camera):
        if not self.active: return
        sx = int(self.pos.x - camera.x)
        sy = int(self.pos.y - camera.y)
        if not (-20 < sx < SCREEN_W+20 and -20 < sy < SCREEN_H+20): return
        info = self.TYPES[self.mtype]
        col  = info["color"]
        pulse = math.sin(self._pulse * 4) * 0.4 + 0.6
        r = int(self.RADIUS * pulse)
        gs = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*col, 120), (r+2, r+2), r+2)
        pygame.draw.circle(gs, (*col, 220), (r+2, r+2), max(1,r-2))
        surf.blit(gs, (sx-r-2, sy-r-2))
        rm2 = ResourceManager()
        lbl = rm2.get_font(10, True).render(info["label"], True, col)
        surf.blit(lbl, (sx - lbl.get_width()//2, sy + r + 2))
        ttl_w = int(24 * self._life / 12.0)
        pygame.draw.rect(surf, DARK_GRAY, (sx-12, sy-r-8, 24, 3))
        pygame.draw.rect(surf, col, (sx-12, sy-r-8, ttl_w, 3))


class ModuleInventory:
    """Tracks collected modules and applies their stats."""
    MAX_PER_TYPE = 3

    def __init__(self):
        self._slots: Dict[str, int] = {k: 0 for k in ShipModule.TYPES}

    def collect(self, mtype: str) -> bool:
        if self._slots[mtype] < self.MAX_PER_TYPE:
            self._slots[mtype] += 1
            return True
        return False

    def stat_speed_bonus(self) -> float:
        return 1.0 + self._slots.get("engine", 0) * 0.10

    def stat_dmg_bonus(self) -> float:
        return 1.0 + self._slots.get("core", 0) * 0.12

    def stat_hp_bonus(self) -> int:
        return self._slots.get("armor", 0) * 25

    def has_gravity_lens(self) -> bool:
        return self._slots.get("lens", 0) > 0

    def draw_hud(self, surf, rm, x, y):
        for i, (mtype, count) in enumerate(self._slots.items()):
            if count == 0: continue
            info = ShipModule.TYPES[mtype]
            col  = info["color"]
            lbl  = rm.get_font(11, True).render(f"{info['label']} x{count}", True, col)
            surf.blit(lbl, (x, y + i*16))


class WorldGenerator:
    """
    Procedural content generator.  Sectors are generated on demand and cached
    so they remain stable as the player revisits areas.  Noise-based density
    controls asteroid distribution; heavier sectors appear closer to the origin.
    """
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
        """Return the list of Asteroid objects for sector (sx, sy), generating if needed."""
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
        """Return the background star data for sector (sx, sy)."""
        key = (sx, sy)
        if key not in self._star_cache:
            rng = random.Random(self.seed^sx^(sy<<16))
            self._star_cache[key] = [
                (sx*SECTOR_SIZE+rng.uniform(0,SECTOR_SIZE),
                 sy*SECTOR_SIZE+rng.uniform(0,SECTOR_SIZE),
                 rng.randint(1,3), rng.randint(60,180))
                for _ in range(55)]
        return self._star_cache[key]


    def get_orbital_bodies(self, sx: int, sy: int) -> list:
        """Return any OrbitalBody instances present in sector (sx, sy)."""
        key = ("ob", sx, sy)
        if key in self._cache: return self._cache[key]
        rng    = random.Random(self.seed ^ (sx*77711) ^ (sy*55337))
        bodies = []
        if rng.random() < 0.12:
            wx   = sx*SECTOR_SIZE + rng.uniform(100, SECTOR_SIZE-100)
            wy   = sy*SECTOR_SIZE + rng.uniform(100, SECTOR_SIZE-100)
            mass = rng.uniform(1200, 4000)
            btype = OrbitalBody.TYPE_NEUTRON if rng.random() < 0.25 else OrbitalBody.TYPE_PLANET
            bodies.append(OrbitalBody(wx, wy, mass, btype, seed=rng.randint(0,99)))
        self._cache[key] = bodies
        return bodies

    def get_gravity_zones(self, sx: int, sy: int) -> list:
        """Return any GravityZone instances present in sector (sx, sy)."""
        key = ("gz", sx, sy)
        if key in self._cache: return self._cache[key]
        rng   = random.Random(self.seed ^ (sx*11117) ^ (sy*33331))
        zones = []
        if rng.random() < 0.18:
            wx = sx*SECTOR_SIZE + rng.uniform(80, SECTOR_SIZE-80)
            wy = sy*SECTOR_SIZE + rng.uniform(80, SECTOR_SIZE-80)
            r  = rng.uniform(110, 220)
            roll = rng.random()
            if roll < 0.35:
                zt = GravityZone.TYPE_BLACKHOLE
            elif roll < 0.55:
                zt = GravityZone.TYPE_WHITEHOLE
            else:
                zt = GravityZone.TYPE_NEBULA
            zones.append(GravityZone(wx, wy, r, zt))
        self._cache[key] = zones
        return zones

    def get_nebula_color(self, x, y):
        r = (self.noise.noise(x/2000+0.1,y/2000+0.2)+1)/2
        b = (self.noise.noise(x/2000+5.0,y/2000+3.0)+1)/2
        return (int(r*22), 0, int(b*30))


class WaveManager:
    """
    Spawns enemy waves on a fixed interval. Wave composition escalates with
    player level; every fifth wave is a boss wave that includes a heavy
    Carrier and a boss-class enemy.
    """
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
        # Practice Mode overrides (set by Game._start_game when mode == PRACTICE)
        self._practice_types: List[str] = []
        self._practice_interval: float  = 10.0
        self._practice_count: int       = 6

    def update(self, dt):
        is_practice = (self.game.game_mode == GAMEMODE_PRACTICE)
        interval    = self._practice_interval if is_practice else self.wave_interval
        self.timer += dt
        if self.timer >= interval:
            self.timer = 0.0
            self.wave += 1
            self._spawn_wave()

    def _spawn_wave(self):
        """Spawn a new set of enemies at random positions around the player."""
        is_practice  = (self.game.game_mode == GAMEMODE_PRACTICE)
        player_level = self.game.player.level_sys.level
        pp           = self.game.player.transform.pos

        if is_practice:
            # Use the player-configured type list and count
            enabled_types = self._practice_types or ["scout"]
            count         = self._practice_count
            for i in range(count):
                ang  = random.uniform(0, math.pi * 2)
                dist = random.uniform(360, 640)
                ex   = max(50, min(WORLD_W - 50, pp.x + math.cos(ang) * dist))
                ey   = max(50, min(WORLD_H - 50, pp.y + math.sin(ang) * dist))
                e = self.game.enemy_pool.get()
                if not e: break
                EnemyFactory.configure(e, random.choice(enabled_types))
                if hasattr(self.game, "eco"): self.game.eco.apply_to_enemy(e)
                e.spawn(ex, ey)
            return

        pool_idx = min(player_level - 1, len(self.ENEMY_POOL_BY_LEVEL) - 1)
        pool     = self.ENEMY_POOL_BY_LEVEL[pool_idx]
        count    = 4 + self.wave * 2 + player_level

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
            if hasattr(self.game, "eco"): self.game.eco.apply_to_enemy(e)
            e.spawn(ex, ey)


class HUD:
    """
    Renders all in-game overlay elements: HP/XP bars, score, wave counter,
    minimap, AI log, skill points, module inventory and control hints.
    """
    def __init__(self, game):
        self.game         = game
        self.rm           = ResourceManager()
        self._fps_samples = []

    def draw(self, surf, fps):
        p  = self.game.player
        wm = self.game.wave_manager
        ls = p.level_sys
        rm = self.rm

        self._bar(surf, 20, SCREEN_H-44, 210, 14, p.health.ratio,
                  GREEN if p.health.ratio>0.5 else (ORANGE if p.health.ratio>0.25 else RED),
                  f"HP {p.health.hp}/{p.health.max_hp}", bar_tag="HP")
        self._bar(surf, 20, SCREEN_H-22, 210, 8, ls.xp_ratio, PURPLE,
                  f"XP  Lv.{ls.level}", bar_tag="XP")

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
            "WASD:Mover | Click:Disparar | [E]:Hack | [F]:Flota | [Q]:Escudo | [2]:Skills | ESC:Pausa | [M]:SFX | [N]:Música | [X]:Nexo", True, GRAY)
        surf.blit(hint,(SCREEN_W//2-hint.get_width()//2, SCREEN_H-18))

        hs2 = getattr(self.game, "hack_sys", None)
        if hs2:
            hs2.draw_hud(surf, rm, 20, 132)

        af3 = getattr(self.game, "allied_fleet", None)
        if af3:
            af3.draw_hud(surf, rm, 20, 155)

        nx = getattr(self.game, "nexus", None)
        if nx:
            nxt = rm.get_font(12).render(f"Frags: {nx.fragments}", True, GOLD)
            surf.blit(nxt, (20, 178))

        # Directional shield energy bar
        ds = getattr(self.game.player, "dir_shield", None)
        if ds:
            shield_ratio = ds.ratio
            shield_col   = (0, 200, 255) if shield_ratio > 0.3 else RED
            active_txt   = "[Q] ESCUDO" if ds.active else f"[Q] ESCUDO {int(shield_ratio*100)}%"
            sh_t = rm.get_font(12, True).render(active_txt, True, shield_col)
            surf.blit(sh_t, (20, 196))

        fw = getattr(self.game, "faction_war", None)
        if fw and fw.buff_active:
            fw_t = rm.get_font(12, True).render("ALIANZA ACTIVA +20% vel", True, (100,220,255))
            surf.blit(fw_t, (20, 214))

        if self.game.sfx.muted:
            mute_t = rm.get_font(14,True).render("SFX OFF", True, RED)
            surf.blit(mute_t,(SCREEN_W-90, 28))
        if self.game.sfx.music_muted:
            mus_t = rm.get_font(14,True).render("MÚS OFF", True, ORANGE)
            surf.blit(mus_t,(SCREEN_W-90, 46))

        if ls.level_up_pending:
            self._draw_level_up_banner(surf, ls)

        if hasattr(self.game, "ai_log"):
            self.game.ai_log.draw(surf, rm)

        eco = getattr(self.game, "eco", None)
        if eco:
            summary = eco.hud_summary()
            if summary:
                eco_t = rm.get_font(11, True).render(summary, True, (220, 120, 40))
                surf.blit(eco_t, (20, 114))

        p2 = self.game.player
        if hasattr(p2, "modules"):
            p2.modules.draw_hud(surf, rm, SCREEN_W - 130, 64)

        grav_sk = self.game.skill_tree.skills.get("grav_pull")
        if grav_sk and grav_sk.level > 0:
            gl = rm.get_font(11, True).render(f" GRAV Lv{grav_sk.level}", True, (200,80,255))
            surf.blit(gl, (SCREEN_W - 130, 48))

        p2 = self.game.player
        p2.loc_damage.draw_hud(surf, rm, SCREEN_W - 40, SCREEN_H - 90)

        nb_t = getattr(self.game, "_nebula_terrain", None)
        if nb_t:
            lbl_nb = nb_t.hud_label()
            if lbl_nb:
                nbl = rm.get_font(12, True).render(lbl_nb, True,
                    (255, 120, 0) if "PLASMA" in lbl_nb else (60, 140, 255))
                surf.blit(nbl, (SCREEN_W//2 - nbl.get_width()//2, 44))
            if not nb_t.radar_active():
                glitch = rm.get_font(11, True).render("RADAR OFFLINE", True, RED)
                surf.blit(glitch, (SCREEN_W - 155, SCREEN_H - 135))

        wb2 = getattr(self.game, "_worm_boss", None)
        if wb2 and wb2.active:
            alive_segs = [s for s in wb2.segments if s.active]
            total_hp   = sum(s.hp for s in alive_segs)
            max_hp     = sum(s.max_hp for s in wb2.segments)
            ratio      = total_hp / max(1, max_hp)
            bw2 = 300
            bx2 = SCREEN_W//2 - bw2//2
            by2 = 12
            pygame.draw.rect(surf, DARK_GRAY, (bx2, by2, bw2, 14), border_radius=4)
            pygame.draw.rect(surf, (220,60,30), (bx2, by2, int(bw2*ratio), 14), border_radius=4)
            pygame.draw.rect(surf, WHITE, (bx2, by2, bw2, 14), 1, border_radius=4)
            wlbl = rm.get_font(11, True).render(f"GUSANO ESPACIAL  {len(alive_segs)}/{wb2.NUM_SEGMENTS} segmentos", True, WHITE)
            surf.blit(wlbl, (SCREEN_W//2 - wlbl.get_width()//2, by2+16))

    def _bar(self, surf, x, y, w, h, ratio, color, label, bar_tag=""):
        """Draw a labelled fill-bar at (x,y) with the given dimensions and fill ratio."""
        pygame.draw.rect(surf, DARK_GRAY,(x,y,w,h),border_radius=4)
        fill_w = int(w*ratio)
        if fill_w > 0:
            pygame.draw.rect(surf, color,(x,y,fill_w,h),border_radius=4)
        pygame.draw.rect(surf, WHITE,(x,y,w,h),1,border_radius=4)
        surf.blit(self.rm.get_font(12).render(label,True,WHITE),(x,y-16))
        if bar_tag and h >= 10:
            tag = self.rm.get_font(max(9,h-3),True).render(bar_tag, True, (255,255,255))
            tag_x = x + 5
            tag_y = y + h//2 - tag.get_height()//2
            surf.blit(tag, (tag_x, tag_y))

    def _minimap(self, surf):
        """Render a small top-down overview map in the bottom-right corner."""
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
    HEADER_H  = 110
    FOOTER_H  = 36
    ROW_H     = 82

    def __init__(self, game):
        self.game     = game
        self.rm       = ResourceManager()
        self.selected = 0
        self._scroll  = 0
        self._drag    = False
        self._drag_y  = 0
        self._drag_scroll_start = 0

    def _visible_area(self):
        return SCREEN_H - self.HEADER_H - self.FOOTER_H

    def _max_scroll(self, n_skills):
        total = n_skills * self.ROW_H
        vis   = self._visible_area()
        return max(0, total - vis)

    def handle_event(self, event):
        st   = self.game.skill_tree
        keys = list(st.skills.keys())

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(self._scroll - event.y * 28,
                                      self._max_scroll(len(keys))))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            self._drag = True
            self._drag_y = event.pos[1]
            self._drag_scroll_start = self._scroll

        if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            self._drag = False

        if event.type == pygame.MOUSEMOTION and self._drag:
            dy = self._drag_y - event.pos[1]
            self._scroll = max(0, min(self._drag_scroll_start + dy,
                                      self._max_scroll(len(keys))))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(keys)
                self._ensure_visible(self.selected, len(keys))
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(keys)
                self._ensure_visible(self.selected, len(keys))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                st.upgrade(keys[self.selected])

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            scroll_y0 = self.HEADER_H
            content_y  = my - scroll_y0 + self._scroll
            row_i = content_y // self.ROW_H
            if 0 <= row_i < len(keys):
                bx  = SCREEN_W // 2 - 295
                btn = pygame.Rect(bx + 482, scroll_y0 + row_i * self.ROW_H - self._scroll + 12, 100, 38)
                if btn.collidepoint(mx, my):
                    st.upgrade(keys[row_i])
                else:
                    self.selected = row_i

    def _ensure_visible(self, idx, n):
        top    = idx * self.ROW_H
        bottom = top + self.ROW_H
        vis    = self._visible_area()
        if top < self._scroll:
            self._scroll = top
        elif bottom > self._scroll + vis:
            self._scroll = bottom - vis
        self._scroll = max(0, min(self._scroll, self._max_scroll(n)))

    def draw(self, surf):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 215))
        surf.blit(ov, (0, 0))

        st   = self.game.skill_tree
        rm   = self.rm
        keys = list(st.skills.keys())
        ls   = self.game.player.level_sys
        n    = len(keys)

        title = rm.get_font(32, True).render("ÁRBOL DE HABILIDADES", True, YELLOW)
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 12))

        info = rm.get_font(16).render(
            f"Puntos disponibles: {st.points}  |  Nivel jugador: {ls.level}", True, GREEN)
        surf.blit(info, (SCREEN_W // 2 - info.get_width() // 2, 54))

        scroll_hint = rm.get_font(12).render("Rueda del ratón o ↑↓ para desplazar", True, (70, 90, 110))
        surf.blit(scroll_hint, (SCREEN_W // 2 - scroll_hint.get_width() // 2, 82))

        scroll_y0 = self.HEADER_H
        vis_h     = self._visible_area()

        clip_surf = pygame.Surface((SCREEN_W, vis_h), pygame.SRCALPHA)
        clip_surf.fill((0, 0, 0, 0))

        bx = SCREEN_W // 2 - 295
        for i, key in enumerate(keys):
            skill = st.skills[key]
            sel   = (i == self.selected)
            by_c  = i * self.ROW_H - self._scroll

            if by_c + self.ROW_H < 0 or by_c > vis_h:
                continue

            mx_p, my_p = pygame.mouse.get_pos()
            row_rect = pygame.Rect(bx, scroll_y0 + by_c, 590, 68)
            hovered  = row_rect.collidepoint(mx_p, my_p)

            bg_c = (52, 52, 100) if hovered or sel else (16, 16, 36)
            border_c = YELLOW if sel else ((80, 180, 255) if hovered else GRAY)

            pygame.draw.rect(clip_surf, bg_c,     (bx, by_c, 590, 68), border_radius=8)
            pygame.draw.rect(clip_surf, border_c, (bx, by_c, 590, 68), 2, border_radius=8)

            clip_surf.blit(rm.get_font(16, True).render(
                f"{skill.name}  [Lv {skill.level}/{skill.max_level}]",
                True, YELLOW if sel else WHITE), (bx + 14, by_c + 6))

            clip_surf.blit(rm.get_font(13).render(
                skill.description, True, GRAY), (bx + 14, by_c + 28))

            next_cost_text = "MAXED" if skill.is_maxed else f"Siguiente: {skill.current_cost} pts"
            cost_color = GRAY if skill.is_maxed else (GREEN if st.points >= skill.current_cost else RED)
            clip_surf.blit(rm.get_font(12, True).render(next_cost_text, True, cost_color),
                           (bx + 14, by_c + 48))

            if skill.cost_increment > 0 and not skill.is_maxed:
                clip_surf.blit(rm.get_font(11).render(
                    f"(+{skill.cost_increment} por nivel)", True, (120, 120, 140)),
                    (bx + 110, by_c + 50))

            for lvl in range(skill.max_level):
                sx2 = bx + 310 + lvl * 28
                sy2 = by_c + 26
                pygame.draw.circle(clip_surf, YELLOW if lvl < skill.level else DARK_GRAY, (sx2, sy2), 9)
                pygame.draw.circle(clip_surf, WHITE, (sx2, sy2), 9, 1)

            can   = not skill.is_maxed and st.points >= skill.current_cost
            btn_c = GREEN if can else DARK_GRAY
            btn_r = pygame.Rect(bx + 482, by_c + 12, 100, 38)
            btn_hover = pygame.Rect(bx + 482, scroll_y0 + by_c + 12, 100, 38).collidepoint(mx_p, my_p)
            if btn_hover and can:
                btn_c = (0, 180, 80)
            pygame.draw.rect(clip_surf, btn_c, btn_r, border_radius=6)
            pygame.draw.rect(clip_surf, WHITE, btn_r, 1, border_radius=6)
            lbl = "MEJORAR" if can else ("MAXED" if skill.is_maxed else "BLOQ.")
            clip_surf.blit(rm.get_font(12, True).render(lbl, True, WHITE),
                           (btn_r.x + 18, btn_r.y + 11))

        surf.blit(clip_surf, (0, scroll_y0))

        max_sc = self._max_scroll(n)
        if max_sc > 0:
            bar_x  = SCREEN_W // 2 + 300
            bar_y  = scroll_y0
            bar_h  = vis_h
            thumb_h = max(24, int(bar_h * vis_h / (n * self.ROW_H)))
            thumb_y = int(bar_y + (bar_h - thumb_h) * self._scroll / max_sc)
            pygame.draw.rect(surf, (30, 30, 50), (bar_x, bar_y, 6, bar_h), border_radius=3)
            pygame.draw.rect(surf, CYAN, (bar_x, thumb_y, 6, thumb_h), border_radius=3)

        hint = rm.get_font(13).render("↑↓ Navegar  |  ENTER / Clic Mejorar  |  [2] Cerrar", True, GRAY)
        surf.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 26))


# Top-level states that drive the main game loop.
class GameState(Enum):
    MENU           = auto()
    WARP           = auto()
    PLAYING        = auto()
    SKILL          = auto()
    PAUSED         = auto()
    GAME_OVER      = auto()
    PRACTICE_SETUP = auto()   # Pantalla de configuracion del Modo Practica


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


    def _draw_buildup(self, surf: pygame.Surface, pt: float):
        e = self._ease_in_out(pt)
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

        glow_r = int(30 + 120 * e)
        for r in range(glow_r, 0, -4):
            al = int(60 * (r / glow_r) * e)
            gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (40, 80, 255, al), (r, r), r)
            surf.blit(gs, (self._cx - r, self._cy - r))

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
            stretch = 1 + e * 9.0
            d_front = base_d * stretch
            d_back  = base_d * (stretch - e * 2.0)
            d_back  = max(0, d_back)

            x1 = int(self._cx + math.cos(st["angle"]) * d_back)
            y1 = int(self._cy + math.sin(st["angle"]) * d_back)
            x2 = int(self._cx + math.cos(st["angle"]) * d_front)
            y2 = int(self._cy + math.sin(st["angle"]) * d_front)

            x1 = max(-2, min(self.sw+2, x1))
            y1 = max(-2, min(self.sh+2, y1))
            x2 = max(-2, min(self.sw+2, x2))
            y2 = max(-2, min(self.sh+2, y2))

            bright = min(255, int(160 + 95 * e))
            col    = tuple(min(255, int(c * 0.7 + bright * 0.3)) for c in st["col"])
            width  = max(1, int(st["size"] * (1 + e * 1.5)))
            pygame.draw.line(surf, col, (x1, y1), (x2, y2), width)

        ring_r = int(40 + 200 * e)
        for r in range(ring_r, ring_r - 30, -3):
            if r <= 0: continue
            al = int(90 * (1 - (ring_r - r) / 30) * e)
            gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (80, 120, 255, al), (r, r), r, 3)
            surf.blit(gs, (self._cx - r, self._cy - r))

        core_r = int(8 + 40 * e)
        gs = pygame.Surface((core_r*2, core_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (200, 220, 255, int(180 * e)), (core_r, core_r), core_r)
        surf.blit(gs, (self._cx - core_r, self._cy - core_r))

    def _draw_rush(self, surf: pygame.Surface, pt: float):
        e = self._ease_in_out(pt)

        for r in range(min(self.sw, self.sh)//2, 0, -8):
            frac = r / (min(self.sw, self.sh) // 2)
            al   = int(180 * (1 - frac) * 0.7)
            col  = (int(10 * frac), int(20 * frac), min(255, int(60 + 120 * (1-frac))))
            gs   = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*col, al), (r, r), r)
            surf.blit(gs, (self._cx - r, self._cy - r))

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

        for i in range(6):
            phase_off = (i / 6 + pt) % 1.0
            ring_r    = int(20 + phase_off * max(self.sw, self.sh) * 0.8)
            al        = int(160 * (1 - phase_off) * (0.4 + 0.6 * e))
            thick     = max(1, int(4 * (1 - phase_off)))
            gs        = pygame.Surface((ring_r*2, ring_r*2), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (120, 160, 255, al),
                                (0, ring_r//3, ring_r*2, ring_r), thick)
            surf.blit(gs, (self._cx - ring_r, self._cy - ring_r//2))

        core_r = int(55 + 50 * e)
        gs = pygame.Surface((core_r*2, core_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (220, 235, 255, int(220 * (0.6 + 0.4 * e))),
                           (core_r, core_r), core_r)
        surf.blit(gs, (self._cx - core_r, self._cy - core_r))

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
        if pt < 0.5:
            e = pt * 2
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
    OPTIONS = ["Continuar", "Árbol de Habilidades", "Menú Principal", "Salir"]

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
        box_w,box_h = 390,330
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
            col = YELLOW if opt=="Menú Principal" else (WHITE if sel else GRAY)
            t   = rm.get_font(18,sel).render(("" if sel else "  ")+opt, True, col)
            surf.blit(t,(r.centerx-t.get_width()//2, r.centery-t.get_height()//2))
            oy += 58

        hint = rm.get_font(12).render("↑↓ Navegar | ENTER Seleccionar", True, GRAY)
        surf.blit(hint,(SCREEN_W//2-hint.get_width()//2, by+box_h-26))


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


class ControlsGuide:
    """Full-screen controls/help overlay explaining the game."""

    SECTIONS = [
        ("CONTROLES", [
            ("Movimiento",         "W A S D  o  flechas del teclado"),
            ("Disparar",           "Clic izquierdo del rat\u00f3n (apunta con el cursor)"),
            ("Hack EMP",           "[E]  \u2014 congela las balas enemigas cercanas"),
            ("\u00c1rbol de habilidades","[2]  \u2014 abre/cierra el \u00e1rbol de mejoras"),
            ("Pausa",              "[ESC]"),
            ("Silenciar efectos",  "[M]"),
            ("Silenciar m\u00fasica",   "[N]"),
        ]),
        ("ENEMIGOS", [
            ("Explorador",       "R\u00e1pido y ligero. Patrulla y embiste. Poco HP."),
            ("Cazador",          "IA de enjambre (Boids). Se agrupa con otros."),
            ("Kamikaze",         "Carga directa contra ti. Explota al impacto."),
            ("Francotirador",    "Dispara balas muy r\u00e1pidas desde lejos. Huye si lo alcanzas."),
            ("Pesado",           "Dispara r\u00e1fagas de 3 balas. Mucho HP, lento."),
            ("Transportador",    "Lanza mini-drones. Al destruirlo caen m\u00f3dulos."),
            ("Jefe",             "HP elevado, ataques m\u00faltiples. Aparece cada varias oleadas."),
            ("TITAN",            "Enorme, lento y devastador. Aparece en niveles 8, 16, 24\u2026"),
            ("Jefe Geom\u00e9trico",  "Patrones Bullet Hell: espiral, p\u00e9talos de rosa, anillo con hueco."),
            ("Nave Sombra",      "El fantasma de tu partida anterior. Aparece como pecio y se activa."),
            ("Gusano Espacial",  "Jefe segmentado. Destruye cada segmento por separado."),
        ]),
        ("PODERES Y MEC\u00c1NICAS", [
            ("Hack EMP  [E]",       "Congela balas enemigas en radio 420 px por 2.8 s. Recarga: 12 s."),
            ("Nano-Bots",           "Los bots orbitan tu nave y persiguen enemigos cercanos."),
            ("Gravedad Cu\u00e1ntica",   "Atrae balas enemigas hacia un punto de colapso."),
            ("Asistencia Grav.",    "Usa cuerpos orbitales para acelerar tu nave (efecto honda)."),
            ("Bullet Time",         "Al bajar al 10\u202f% de HP el tiempo se ralentiza autom\u00e1ticamente."),
            ("Modo Sobredrive",     "Sinergia Nexo: tu estela de movimiento da\u00f1a a los enemigos."),
            ("Disparo Eco",         "Sinergia Nexo: cada 10.\u00ba disparo apunta solo al enemigo m\u00e1s cercano."),
            ("Rebote de Escudo",    "Sinergia Nexo: tus balas rebotan en los bordes de pantalla."),
            ("Tormenta Nano-Bot",   "Sinergia Nexo: los bots generan campo el\u00e9ctrico que ralentiza."),
            ("Pulso Gravitacional", "Sinergia Nexo: el Hack tambi\u00e9n empuja a los enemigos."),
        ]),
        ("ZONAS Y ENTORNO", [
            ("Nebulosa densa",      "Reduce tu velocidad m\u00e1xima al 55\u202f%."),
            ("Agujero negro",       "Te atrae. \u00dasalo para girar y acelerar \u2014 o muere."),
            ("Cuerpos orbitales",   "Planetas con gravedad. Pasa cerca para recibir impulso."),
            ("Asteroides",          "Bloquean el paso. Dispara para destruirlos (+XP)."),
            ("Criaturas espaciales","Neutrales. Puedes cazarlas por XP y m\u00f3dulos extra."),
            ("Guerra de Facciones", "Enjambre vs Drones luchan entre s\u00ed. Ayuda a uno y recibe buff de velocidad."),
        ]),
        ("M\u00d3DULOS Y PROGRESI\u00d3N", [
            ("M\u00f3dulos de nave",     "Caen al destruir enemigos. Rec\u00f3gelos para mejoras pasivas."),
            ("  ALA",              "Giro +15\u202f%"),
            ("  MOTOR",            "Velocidad +10\u202f%"),
            ("  ARMADURA",         "HP +25 (permanente en la partida)"),
            ("  N\u00daCLEO",           "Da\u00f1o +12\u202f%"),
            ("  LENTE",            "Potencia la habilidad de Gravedad Cu\u00e1ntica"),
            ("Fragmentos de Datos","Se acumulan entre partidas. \u00dasalos en el Nexo de Datos [X]."),
            ("Nexo de Datos",      "Meta-progresi\u00f3n: compra Sinergias permanentes con tus Fragmentos."),
            ("\u00c1rbol de Habilidades","[2] durante la partida. 9 habilidades, cada una con varios niveles."),
            ("Niveles de jugador", "Cada nivel otorga +2 Skill pts y un bonus aleatorio (HP, vel, etc.)"),
        ]),
        ("MODOS DE JUEGO", [
            ("Cl\u00e1sico",            "Oleadas cronometradas. La siguiente llega al limpiar el mapa."),
            ("Supervivencia",      "Spawn constante de enemigos. Sin respiro. \u00bfCu\u00e1nto aguantas?"),
            ("Contrarreloj",       "3 minutos para maximizar puntuaci\u00f3n. Enfoque en kills r\u00e1pidos."),
        ]),
    ]

    def __init__(self):
        self.rm      = ResourceManager()
        self._scroll = 0
        self._open   = False

    def toggle(self):
        self._open  = not self._open
        self._scroll = 0

    @property
    def open(self):
        return self._open

    def handle_event(self, event):
        if not self._open:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_h):
            self._open = False
            return True
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 22)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            close_r = pygame.Rect(SCREEN_W - 54, 14, 40, 40)
            if close_r.collidepoint(event.pos):
                self._open = False
            return True
        return self._open

    def draw(self, surf):
        if not self._open:
            return
        rm = self.rm
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((2, 4, 18, 245))
        surf.blit(ov, (0, 0))

        PANEL_X = 60
        PANEL_W = SCREEN_W - 120
        VIS_Y0  = 70
        VIS_H   = SCREEN_H - 90

        title_s = rm.get_font(28, True).render("GU\u00cdA DE CONTROLES", True, (0, 200, 255))
        surf.blit(title_s, (SCREEN_W // 2 - title_s.get_width() // 2, 18))

        close_r = pygame.Rect(SCREEN_W - 54, 14, 40, 40)
        pygame.draw.rect(surf, (60, 10, 10), close_r, border_radius=6)
        pygame.draw.rect(surf, (180, 40, 40), close_r, 1, border_radius=6)
        cl = rm.get_font(20, True).render("x", True, (220, 100, 100))
        surf.blit(cl, (close_r.centerx - cl.get_width() // 2,
                       close_r.centery - cl.get_height() // 2))

        canvas_h = 3000
        canvas   = pygame.Surface((PANEL_W, canvas_h), pygame.SRCALPHA)
        y = 0
        COL_A = 8
        COL_B = int(PANEL_W * 0.38)

        for sec_title, rows in self.SECTIONS:
            sec_bg = pygame.Surface((PANEL_W, 30), pygame.SRCALPHA)
            sec_bg.fill((10, 20, 50, 200))
            canvas.blit(sec_bg, (0, y))
            pygame.draw.line(canvas, (0, 100, 180), (0, y + 29), (PANEL_W, y + 29), 1)
            st = rm.get_font(16, True).render(sec_title, True, (0, 200, 255))
            canvas.blit(st, (8, y + 6))
            y += 36

            for label, desc in rows:
                lbl_s  = rm.get_font(13, True).render(label, True, (200, 220, 255))
                desc_s = rm.get_font(13).render(desc,  True, (140, 160, 190))
                canvas.blit(lbl_s,  (COL_A, y))
                canvas.blit(desc_s, (COL_B, y))
                y += 22

            y += 10

        max_scroll = max(0, y - VIS_H)
        self._scroll = min(self._scroll, max_scroll)

        clip = pygame.Surface((PANEL_W, VIS_H), pygame.SRCALPHA)
        clip.fill((0, 0, 0, 0))
        clip.blit(canvas, (0, -self._scroll))
        surf.blit(clip, (PANEL_X, VIS_Y0))

        if max_scroll > 0:
            bar_x  = SCREEN_W - 18
            bar_y  = VIS_Y0
            bar_h  = VIS_H
            thumb_h = max(24, int(bar_h * VIS_H / max(1, y)))
            thumb_y = int(bar_y + (bar_h - thumb_h) * self._scroll / max_scroll)
            pygame.draw.rect(surf, (30, 30, 50), (bar_x, bar_y, 6, bar_h), border_radius=3)
            pygame.draw.rect(surf, (0, 160, 220), (bar_x, thumb_y, 6, thumb_h), border_radius=3)

        hint = rm.get_font(12).render(
            "Rueda del rat\u00f3n para desplazar  |  [ESC] o X para cerrar",
            True, (50, 60, 80))
        surf.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 22))



class Scoreboard:
    """
    Persistent high-score table stored in SCOREBOARD_SAVE_FILE.

    Each entry records score, level, wave, total kills, play time, game mode,
    top-2 skills, and heat-map trajectory positions.

    The draw() method renders a full-screen list; clicking a row opens a
    detail panel showing the heat-map, top skills and enemy-kill breakdown.
    """

    MAX_ENTRIES = 10

    def __init__(self):
        self._entries: list = []
        self._scroll        = 0
        self._selected      = -1   # index of detail-view row (-1 = none)
        self._load()

    def add_entry(self, stats: dict):
        """
        Append a new run result from a _final_stats dict.
        Keeps only the top MAX_ENTRIES scores and persists immediately.
        """
        # Compute top-2 skills by level
        skills_dict = stats.get("skills", {})
        skill_names_map = {
            "fire_rate": "Cadencia", "bullet_dmg": "Dano",
            "speed": "Velocidad",   "shield": "Escudo",
            "multi_shot": "Multidisparo", "pierce": "Perforadora",
            "grav_pull": "Gravedad", "nano_bots": "Nano-Bots",
            "slingshot": "Asist.Grav.",
        }
        top2 = sorted(
            [(skill_names_map.get(k, k), v) for k, v in skills_dict.items() if v > 0],
            key=lambda x: x[1], reverse=True
        )[:2]

        entry = {
            "score":        stats.get("score", 0),
            "level":        stats.get("level", 1),
            "wave":         stats.get("wave", 0),
            "total_kills":  stats.get("total_kills", 0),
            "play_time":    stats.get("play_time", 0.0),
            "mode":         stats.get("mode", ""),
            "kills":        stats.get("kills", {}),
            "top2_skills":  top2,
            "heatmap_pos":  stats.get("heatmap_pos", []),
        }
        self._entries.append(entry)
        self._entries.sort(key=lambda e: e["score"], reverse=True)
        self._entries = self._entries[:self.MAX_ENTRIES]
        self._save()

    def handle_event(self, event) -> bool:
        """
        Process scroll/click input inside the scoreboard overlay.
        Returns True if the overlay should be closed (ESC or X button).
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._selected >= 0:
                    self._selected = -1   # close detail panel first
                    return False
                return True
            if event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 30)
            if event.key == pygame.K_DOWN:
                self._scroll += 30
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 28)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            close_r = pygame.Rect(SCREEN_W - 54, 14, 40, 40)
            if close_r.collidepoint(event.pos):
                if self._selected >= 0:
                    self._selected = -1
                    return False
                return True
            # Click on a row to toggle detail panel
            VIS_Y0 = 86
            ROW_H  = 56
            PAD    = 40
            mx, my = event.pos
            row_i  = (my - VIS_Y0 + self._scroll) // ROW_H
            if 0 <= row_i < len(self._entries):
                self._selected = -1 if self._selected == row_i else row_i
        return False

    def _draw_heatmap_inline(self, surf, positions, ox, oy, w, h):
        """Draw a mini heat-map from a list of (x,y) world positions."""
        if len(positions) < 2:
            bg = pygame.Surface((w, h), pygame.SRCALPHA)
            bg.fill((4, 4, 16, 200))
            surf.blit(bg, (ox, oy))
            pygame.draw.rect(surf, (40, 40, 80), (ox, oy, w, h), 1)
            rm = ResourceManager()
            lbl = rm.get_font(10).render("Sin datos", True, GRAY)
            surf.blit(lbl, (ox + w//2 - lbl.get_width()//2, oy + h//2 - 6))
            return
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((4, 4, 16, 200))
        surf.blit(bg, (ox, oy))
        pygame.draw.rect(surf, (40, 40, 80), (ox, oy, w, h), 1)
        sx = w / WORLD_W
        sy = h / WORLD_H
        pts = [(ox + int(x * sx), oy + int(y * sy)) for x, y in positions]
        n = len(pts)
        for i in range(1, n):
            ratio = i / n
            col   = (int(255 * ratio), int(80 * (1 - ratio)), int(180 * (1 - ratio)))
            pygame.draw.line(surf, col, pts[i-1], pts[i], 1)
        if pts:
            pygame.draw.circle(surf, RED,  pts[-1], 3)
            pygame.draw.circle(surf, GREEN, pts[0],  2)
        rm = ResourceManager()
        lbl = rm.get_font(9).render("Trayectoria", True, (60, 80, 120))
        surf.blit(lbl, (ox + 2, oy + h - 12))

    def _draw_detail_panel(self, surf, entry, px, py, pw, ph):
        """Draw a detail card for the selected entry."""
        rm = ResourceManager()
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((6, 8, 28, 240))
        surf.blit(bg, (px, py))
        pygame.draw.rect(surf, GOLD, (px, py, pw, ph), 1, border_radius=8)

        y = py + 10
        title_t = rm.get_font(14, True).render("DETALLES DE PARTIDA", True, GOLD)
        surf.blit(title_t, (px + pw//2 - title_t.get_width()//2, y)); y += 22


        hm_w, hm_h = pw - 20, 110
        self._draw_heatmap_inline(surf, entry.get("heatmap_pos", []),
                                  px + 10, y, hm_w, hm_h)
        y += hm_h + 8


        pygame.draw.line(surf, (40,40,80), (px+8, y), (px+pw-8, y), 1); y += 6
        t2_hdr = rm.get_font(12, True).render("MEJORES HABILIDADES", True, (180, 220, 255))
        surf.blit(t2_hdr, (px + 10, y)); y += 18
        top2 = entry.get("top2_skills", [])
        if top2:
            for sk_name, sk_lv in top2:
                bar_w = min(pw - 24, sk_lv * 22)
                pygame.draw.rect(surf, (20, 60, 80), (px+10, y, pw-20, 14), border_radius=4)
                pygame.draw.rect(surf, CYAN, (px+10, y, bar_w, 14), border_radius=4)
                sk_t = rm.get_font(11, True).render(f"{sk_name}  Lv{sk_lv}", True, WHITE)
                surf.blit(sk_t, (px+14, y+1)); y += 18
        else:
            na_t = rm.get_font(11).render("Sin habilidades", True, GRAY)
            surf.blit(na_t, (px+10, y)); y += 18
        y += 4

        pygame.draw.line(surf, (40,40,80), (px+8, y), (px+pw-8, y), 1); y += 6
        kills_hdr = rm.get_font(12, True).render("ENEMIGOS ELIMINADOS", True, (230, 80, 80))
        surf.blit(kills_hdr, (px + 10, y)); y += 18
        kills = entry.get("kills", {})
        kill_names_map = {
            "scout":"Explorador","fighter":"Cazador","kamikaze":"Kamikaze",
            "sniper":"Francotirador","heavy":"Pesado","carrier":"Transportador",
            "boss":"Jefe","titan":"TITAN",
        }
        kill_cols_map = {
            "scout":(120,200,255),"fighter":(200,200,100),"kamikaze":(255,140,60),
            "sniper":(200,80,255),"heavy":(80,220,80),"carrier":(0,200,200),
            "boss":(255,80,80),"titan":(220,80,255),
        }
        total_k = max(1, sum(kills.values()))
        for k, count in sorted(kills.items(), key=lambda x: x[1], reverse=True):
            if count == 0: continue
            kcol  = kill_cols_map.get(k, WHITE)
            kname = kill_names_map.get(k, WHITE)
            bar_w = max(2, int((pw - 24) * count / total_k))
            pygame.draw.rect(surf, (20,20,20), (px+10, y, pw-20, 12), border_radius=3)
            pygame.draw.rect(surf, kcol,       (px+10, y, bar_w, 12), border_radius=3)
            kt = rm.get_font(11).render(f"{kname}: {count}", True, WHITE)
            surf.blit(kt, (px+14, y)); y += 15
            if y > py + ph - 16: break

    def draw(self, surf):
        """Render the scoreboard as a full-screen overlay."""
        rm = ResourceManager()

        # Dim background.
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((2, 4, 18, 245))
        surf.blit(ov, (0, 0))

        # Title.
        title = rm.get_font(30, True).render("MEJORES PUNTUACIONES", True, GOLD)
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 16))

        # Close button.
        close_r = pygame.Rect(SCREEN_W - 54, 14, 40, 40)
        pygame.draw.rect(surf, (60, 10, 10), close_r, border_radius=6)
        pygame.draw.rect(surf, (180, 40, 40), close_r, 1, border_radius=6)
        cl = rm.get_font(20, True).render("x", True, (220, 100, 100))
        surf.blit(cl, (close_r.centerx - cl.get_width() // 2,
                       close_r.centery - cl.get_height() // 2))

        VIS_Y0 = 86
        ROW_H  = 56
        PAD    = 40

        # Determine layout: if detail open, shrink list width
        detail_open = (self._selected >= 0 and
                       self._selected < len(self._entries))
        LIST_W = SCREEN_W - PAD * 2 if not detail_open else SCREEN_W // 2 - PAD
        VIS_H  = SCREEN_H - VIS_Y0 - 30

        # Column headers.
        headers = ["#", "Puntuación", "Modo", "Nivel", "Oleada", "Bajas", "Tiempo"]
        col_x   = [PAD, PAD+50, PAD+180, PAD+290, PAD+360, PAD+430, PAD+510]
        for hdr, cx in zip(headers, col_x):
            if cx > PAD + LIST_W: break
            ht = rm.get_font(12, True).render(hdr, True, (100, 160, 200))
            surf.blit(ht, (cx, VIS_Y0))
        pygame.draw.line(surf, (40, 60, 100),
                         (PAD, VIS_Y0 + 18), (PAD + LIST_W, VIS_Y0 + 18), 1)

        click_hint = rm.get_font(11).render("Clic en una fila para ver detalles", True, (50,70,100))
        surf.blit(click_hint, (PAD, VIS_Y0 - 14))

        if not self._entries:
            empty = rm.get_font(16).render("Sin partidas registradas todavía.", True, GRAY)
            surf.blit(empty, (SCREEN_W // 2 - empty.get_width() // 2,
                              VIS_Y0 + VIS_H // 2))
        else:
            content_h  = len(self._entries) * ROW_H + 8
            max_scroll = max(0, content_h - VIS_H + 24)
            self._scroll = min(self._scroll, max_scroll)

            canvas = pygame.Surface((LIST_W + PAD*2, content_h), pygame.SRCALPHA)
            canvas.fill((0, 0, 0, 0))

            medal_cols = [GOLD, SILVER, (180, 100, 60)]

            for i, entry in enumerate(self._entries):
                ry = i * ROW_H
                selected = (i == self._selected)

                row_col = (20, 35, 70) if selected else ((10, 16, 36) if i % 2 == 0 else (6, 10, 26))
                pygame.draw.rect(canvas, row_col,
                                 (PAD - 8, ry + 2, LIST_W + 16, ROW_H - 4),
                                 border_radius=6)
                if selected:
                    pygame.draw.rect(canvas, GOLD,
                                     (PAD - 8, ry + 2, LIST_W + 16, ROW_H - 4),
                                     1, border_radius=6)

                rank_col = medal_cols[i] if i < 3 else (160, 170, 190)
                mins = int(entry["play_time"] // 60)
                secs = int(entry["play_time"] % 60)
                mode_short = {
                    GAMEMODE_CLASSIC:    "Clásico",
                    GAMEMODE_SURVIVAL:   "Superv.",
                    GAMEMODE_TIMEATTACK: "Contra.",
                }.get(entry["mode"], entry["mode"][:7])
                mode_col = {
                    GAMEMODE_CLASSIC:    CYAN,
                    GAMEMODE_SURVIVAL:   ORANGE,
                    GAMEMODE_TIMEATTACK: YELLOW,
                }.get(entry["mode"], WHITE)

                # Top-2 skills snippet on row
                top2 = entry.get("top2_skills", [])
                top2_txt = "  ".join(f"{n} L{l}" for n, l in top2) if top2 else "-"

                cells = [
                    (f"#{i+1}",              rank_col,     True),
                    (f"{entry['score']:,}",   YELLOW,       True),
                    (mode_short,              mode_col,     False),
                    (str(entry["level"]),     GREEN,        False),
                    (str(entry["wave"]),      (100,180,255),False),
                    (str(entry["total_kills"]),(230, 80, 80),False),
                    (f"{mins}m {secs:02d}s", (160,200,255),False),
                ]
                for (text, col, bold), cx in zip(cells, col_x):
                    if cx > PAD + LIST_W: break
                    ct = rm.get_font(13, bold).render(text, True, col)
                    canvas.blit(ct, (cx, ry + ROW_H // 2 - ct.get_height() // 2))

                # Top-2 skills in small text under the row
                if top2_txt != "-":
                    sk_t = rm.get_font(10).render(f"{top2_txt}", True, (80, 160, 220))
                    canvas.blit(sk_t, (PAD, ry + ROW_H - 14))

            # Clip to visible region.
            clip = pygame.Surface((LIST_W + PAD*2, VIS_H), pygame.SRCALPHA)
            clip.fill((0, 0, 0, 0))
            clip.blit(canvas, (0, -self._scroll))
            surf.blit(clip, (0, VIS_Y0 + 22))

            # Scroll bar.
            if max_scroll > 0:
                bar_x   = PAD + LIST_W + 8
                bar_y   = VIS_Y0 + 22
                bar_h   = VIS_H
                thumb_h = max(24, int(bar_h * VIS_H / max(1, content_h)))
                thumb_y = int(bar_y + (bar_h - thumb_h) * self._scroll / max_scroll)
                pygame.draw.rect(surf, (30, 30, 50), (bar_x, bar_y, 6, bar_h), border_radius=3)
                pygame.draw.rect(surf, GOLD,          (bar_x, thumb_y, 6, thumb_h), border_radius=3)

            # Detail panel
            if detail_open:
                panel_x = SCREEN_W // 2 + 10
                panel_w = SCREEN_W // 2 - PAD - 10
                panel_h = VIS_H + 22
                self._draw_detail_panel(surf, self._entries[self._selected],
                                        panel_x, VIS_Y0, panel_w, panel_h)

        hint = rm.get_font(12).render("↑↓ Desplazar  |  Clic: detalles  |  ESC o X para cerrar",
                                      True, (50, 60, 80))
        surf.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 22))

    # ── Persistence ────────────────────────────────────────────────────────

    def _save(self):
        try:
            with open(SCOREBOARD_SAVE_FILE, "w") as f:
                json.dump(self._entries, f, indent=2)
        except Exception:
            pass

    def _load(self):
        try:
            if os.path.exists(SCOREBOARD_SAVE_FILE):
                with open(SCOREBOARD_SAVE_FILE) as f:
                    self._entries = json.load(f)
        except Exception:
            self._entries = []


# ─────────────────────────────────────────────────────────────────────────────
# PRACTICE MODE CONFIG + MENU
# ─────────────────────────────────────────────────────────────────────────────

class PracticeModeConfig:
    """
    Configuracion persistente del Modo Practica para una sesion.
    Guarda que tipos de enemigos estan habilitados y con que frecuencia aparecen.
    """
    ALL_TYPES = [
        ("scout",    "Explorador",     (90,  180, 240)),
        ("fighter",  "Cazador",        (230, 120, 0)),
        ("kamikaze", "Kamikaze",       (255, 160, 30)),
        ("sniper",   "Francotirador",  (200, 80,  255)),
        ("heavy",    "Pesado",         (80,  220, 80)),
        ("carrier",  "Transportador",  (0,   200, 220)),
        ("boss",     "Jefe",           (255, 80,  80)),
        ("titan",    "TITAN",          (220, 80,  255)),
    ]

    def __init__(self):
        self.enabled: Dict[str, bool] = {t[0]: True for t in self.ALL_TYPES}
        self.spawn_interval: float    = 10.0   # segundos entre oleadas
        self.spawn_count: int         = 6      # enemigos por oleada

    def get_enabled_types(self) -> List[str]:
        return [t[0] for t in self.ALL_TYPES if self.enabled.get(t[0], False)]

    def toggle(self, etype: str):
        self.enabled[etype] = not self.enabled.get(etype, True)


class PracticeModeMenu:
    """
    Pantalla de configuracion del Modo Practica.
    Permite seleccionar tipos de enemigos (checkboxes coloreados) y ajustar el
    intervalo de spawn (slider). Diseno premium con glassmorphism y particulas.
    """
    SLIDER_MIN = 3.0
    SLIDER_MAX = 25.0

    def __init__(self, game):
        self.game    = game
        self.rm      = ResourceManager()
        self.cfg     = game._practice_cfg
        self._sel    = 0   # 0..7=enemigos, 8=slider, 9=spawn_count, 10=start, 11=back
        self._anim_t = 0.0
        self._particles: List[dict] = []
        self._part_cd = 0.0
        self._slider_drag = False

    def _n_items(self):
        return len(PracticeModeConfig.ALL_TYPES) + 4  # tipos + slider + count + start + back

    def handle_event(self, event) -> Optional[str]:
        """Devuelve 'start', 'back' o None."""
        n        = self._n_items()
        n_types  = len(PracticeModeConfig.ALL_TYPES)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
            elif event.key == pygame.K_UP:
                self._sel = (self._sel - 1) % n
            elif event.key == pygame.K_DOWN:
                self._sel = (self._sel + 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self._sel < n_types:
                    self.cfg.toggle(PracticeModeConfig.ALL_TYPES[self._sel][0])
                    self.game.sfx.play("ui_click")
                elif self._sel == n_types + 2:  # start
                    return "start"
                elif self._sel == n_types + 3:  # back
                    return "back"
            elif event.key == pygame.K_LEFT:
                if self._sel == n_types:       # slider
                    self.cfg.spawn_interval = max(self.SLIDER_MIN, self.cfg.spawn_interval - 1)
                elif self._sel == n_types + 1:  # count
                    self.cfg.spawn_count = max(1, self.cfg.spawn_count - 1)
            elif event.key == pygame.K_RIGHT:
                if self._sel == n_types:
                    self.cfg.spawn_interval = min(self.SLIDER_MAX, self.cfg.spawn_interval + 1)
                elif self._sel == n_types + 1:
                    self.cfg.spawn_count = min(20, self.cfg.spawn_count + 1)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)

        if event.type == pygame.MOUSEMOTION and self._slider_drag:
            self._handle_slider_drag(event.pos[0])

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._slider_drag = False

        return None

    def _handle_click(self, pos) -> Optional[str]:
        mx, my  = pos
        n_types = len(PracticeModeConfig.ALL_TYPES)
        layout  = self._build_layout()

        for i, (etype, label, col, rect) in enumerate(layout["checkboxes"]):
            if rect.collidepoint(mx, my):
                self.cfg.toggle(etype)
                self._sel = i
                self.game.sfx.play("ui_click")
                return None

        sr = layout["slider_rect"]
        if sr.collidepoint(mx, my):
            self._slider_drag = True
            self._sel = n_types
            self._handle_slider_drag(mx)
            return None

        for side, rect in layout["count_arrows"]:
            if rect.collidepoint(mx, my):
                self._sel = n_types + 1
                if side == "left":
                    self.cfg.spawn_count = max(1, self.cfg.spawn_count - 1)
                else:
                    self.cfg.spawn_count = min(20, self.cfg.spawn_count + 1)
                self.game.sfx.play("ui_click")
                return None

        if layout["btn_start"].collidepoint(mx, my):
            return "start"
        if layout["btn_back"].collidepoint(mx, my):
            return "back"

        return None

    def _handle_slider_drag(self, mx):
        layout = self._build_layout()
        sr = layout["slider_rect"]
        t  = max(0.0, min(1.0, (mx - sr.x) / sr.width))
        self.cfg.spawn_interval = self.SLIDER_MIN + t * (self.SLIDER_MAX - self.SLIDER_MIN)

    def _build_layout(self) -> dict:
        """Calcula y devuelve todos los rects del UI de practica."""
        PANEL_W = 760
        PANEL_X = SCREEN_W // 2 - PANEL_W // 2
        PANEL_Y = 60
        PANEL_H = SCREEN_H - 120

        n_types = len(PracticeModeConfig.ALL_TYPES)
        COLS    = 2
        ROWS    = (n_types + 1) // 2
        CB_W, CB_H = (PANEL_W - 60) // COLS, 48

        checkboxes = []
        for i, (etype, label, col) in enumerate(PracticeModeConfig.ALL_TYPES):
            row, col_idx = divmod(i, COLS)
            cx  = PANEL_X + 30 + col_idx * (CB_W + 10)
            cy  = PANEL_Y + 100 + row * (CB_H + 8)
            checkboxes.append((etype, label, col, pygame.Rect(cx, cy, CB_W, CB_H)))

        slider_y    = PANEL_Y + 100 + ROWS * (CB_H + 8) + 24
        slider_rect = pygame.Rect(PANEL_X + 120, slider_y + 16, PANEL_W - 200, 18)

        count_y = slider_y + 60
        btn_l   = pygame.Rect(PANEL_X + 120, count_y + 10, 36, 32)
        btn_r   = pygame.Rect(PANEL_X + 120 + 100, count_y + 10, 36, 32)

        btn_y     = PANEL_Y + PANEL_H - 64
        btn_start = pygame.Rect(PANEL_X + PANEL_W // 2 - 180, btn_y, 170, 44)
        btn_back  = pygame.Rect(PANEL_X + PANEL_W // 2 + 20,  btn_y, 130, 44)

        return {
            "panel":        pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H),
            "checkboxes":   checkboxes,
            "slider_rect":  slider_rect,
            "slider_y":     slider_y,
            "count_y":      count_y,
            "count_arrows": [("left", btn_l), ("right", btn_r)],
            "btn_start":    btn_start,
            "btn_back":     btn_back,
        }

    def update(self, dt):
        self._anim_t  += dt
        self._part_cd -= dt
        if self._part_cd <= 0:
            self._part_cd = random.uniform(0.05, 0.15)
            r   = random.randint(0, len(PracticeModeConfig.ALL_TYPES) - 1)
            col = PracticeModeConfig.ALL_TYPES[r][2]
            self._particles.append({
                "x": random.uniform(0, SCREEN_W),
                "y": random.uniform(0, SCREEN_H),
                "vx": random.uniform(-0.2, 0.2),
                "vy": random.uniform(-0.4, -0.1),
                "life": random.uniform(2.0, 4.0),
                "max_life": 4.0,
                "col": col,
                "sz": random.randint(1, 3),
            })
        alive = []
        for p in self._particles:
            p["life"] -= dt
            p["x"] += p["vx"] * dt * 60
            p["y"] += p["vy"] * dt * 60
            if p["life"] > 0:
                alive.append(p)
        self._particles = alive

    def draw(self, surf):
        # Fondo oscuro semi-transparente
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((2, 4, 16, 240))
        surf.blit(ov, (0, 0))

        # Particulas de fondo
        for p in self._particles:
            alpha = int(180 * p["life"] / p["max_life"])
            gs = pygame.Surface((p["sz"]*2, p["sz"]*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*p["col"], alpha), (p["sz"], p["sz"]), p["sz"])
            surf.blit(gs, (int(p["x"]) - p["sz"], int(p["y"]) - p["sz"]))

        layout  = self._build_layout()
        panel   = layout["panel"]
        rm      = self.rm
        t       = self._anim_t
        n_types = len(PracticeModeConfig.ALL_TYPES)

        # Panel glassmorphism
        glass = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        glass.fill((8, 10, 30, 210))
        surf.blit(glass, (panel.x, panel.y))
        pulse_col = (
            int(40 + 20 * math.sin(t * 2)),
            int(60 + 20 * math.sin(t * 1.5)),
            int(180 + 40 * math.sin(t)),
        )
        pygame.draw.rect(surf, pulse_col, panel, 2, border_radius=14)

        # Titulo
        title_s = rm.get_font(30, True).render("MODO PRACTICA", True, (0, 210, 255))
        surf.blit(title_s, (SCREEN_W // 2 - title_s.get_width() // 2, panel.y + 14))

        sub_s = rm.get_font(13).render(
            "Habilidades ilimitadas  |  Sinergias desbloqueadas  |  Sin Game Over",
            True, (0, 160, 180))
        surf.blit(sub_s, (SCREEN_W // 2 - sub_s.get_width() // 2, panel.y + 50))

        # Seccion tipos de enemigos
        sec1 = rm.get_font(14, True).render("TIPOS DE ENEMIGOS", True, (100, 140, 200))
        surf.blit(sec1, (panel.x + 30, panel.y + 78))

        for i, (etype, label, col, rect) in enumerate(layout["checkboxes"]):
            enabled = self.cfg.enabled.get(etype, True)
            sel     = (i == self._sel)

            # Card background: filled with enemy colour when enabled
            if enabled:
                fill_alpha = 190 if sel else 130
                card_bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                card_bg.fill((*col, fill_alpha))
                surf.blit(card_bg, (rect.x, rect.y))
                # Darkening overlay so text stays readable
                inner = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                inner.fill((0, 0, 0, 90))
                surf.blit(inner, (rect.x, rect.y))
                border_col = tuple(min(255, c + 80) for c in col) if sel else col
            else:
                # Disabled: plain dark card
                pygame.draw.rect(surf, (18, 18, 35), rect, border_radius=8)
                border_col = (110, 110, 130) if sel else (45, 45, 65)

            pygame.draw.rect(surf, border_col, rect, 2, border_radius=8)

            # Coloured square indicator on the left
            sq = pygame.Rect(rect.x + 10, rect.centery - 12, 24, 24)
            if enabled:
                pygame.draw.rect(surf, col, sq, border_radius=4)
                pygame.draw.rect(surf, WHITE, sq, 1, border_radius=4)
            else:
                pygame.draw.rect(surf, (35, 35, 55), sq, border_radius=4)
                pygame.draw.rect(surf, (60, 60, 80), sq, 1, border_radius=4)

            # Enemy name label
            lbl_col = WHITE if enabled else (70, 70, 90)
            lbl     = rm.get_font(15, True).render(label, True, lbl_col)
            surf.blit(lbl, (rect.x + 44, rect.centery - lbl.get_height() // 2 - 4))

            # Stats tip
            tips = {
                "scout":    "HP:30  Vel:3.5",
                "fighter":  "HP:60  Vel:2.8",
                "kamikaze": "HP:20  Vel:8.5  Explota al contacto",
                "sniper":   "HP:35  Vel:3.8  Bala de alta velocidad",
                "heavy":    "HP:120  Vel:2   Rafagas de 3 balas",
                "carrier":  "HP:180  Vel:1.8 Genera drones",
                "boss":     "HP:280  IA avanzada",
                "titan":    "HP:600  JEFE FINAL",
            }
            tip_col = (210, 210, 210) if enabled else (55, 55, 70)
            tip = rm.get_font(11).render(tips.get(etype, ""), True, tip_col)
            surf.blit(tip, (rect.x + 44, rect.centery + 4))

        # Slider de intervalo
        s_y = layout["slider_y"]
        sl  = rm.get_font(14, True).render("INTERVALO DE OLEADA", True, (100, 140, 200))
        surf.blit(sl, (panel.x + 30, s_y))
        sr  = layout["slider_rect"]
        t_r = (self.cfg.spawn_interval - self.SLIDER_MIN) / (self.SLIDER_MAX - self.SLIDER_MIN)
        pygame.draw.rect(surf, (20, 20, 50), sr, border_radius=6)
        fill_w = int(sr.width * t_r)
        if fill_w > 0:
            pygame.draw.rect(surf, (0, 120, 220),
                             pygame.Rect(sr.x, sr.y, fill_w, sr.height), border_radius=6)
        pygame.draw.rect(surf, (60, 100, 200), sr, 1, border_radius=6)
        hx = sr.x + fill_w
        pygame.draw.circle(surf, (0, 200, 255), (hx, sr.centery), 10)
        pygame.draw.circle(surf, WHITE, (hx, sr.centery), 10, 2)
        val_s = rm.get_font(14, True).render(f"{self.cfg.spawn_interval:.0f}s", True, CYAN)
        surf.blit(val_s, (sr.right + 12, sr.centery - val_s.get_height() // 2))
        hint_sl = rm.get_font(11).render("Flecha Izquierda / Derecha para ajustar  (3 s - 25 s)",
                                          True, (60, 80, 110))
        surf.blit(hint_sl, (sr.x, s_y + 38))

        # Cantidad de enemigos por oleada
        c_y   = layout["count_y"]
        c_sel = (self._sel == n_types + 1)
        cl    = rm.get_font(14, True).render("ENEMIGOS POR OLEADA", True, (100, 140, 200))
        surf.blit(cl, (panel.x + 30, c_y))
        for side, r2 in layout["count_arrows"]:
            hover = r2.collidepoint(*pygame.mouse.get_pos())
            bg2   = (30, 60, 120) if hover else (15, 25, 60)
            pygame.draw.rect(surf, bg2, r2, border_radius=6)
            pygame.draw.rect(surf, CYAN, r2, 1, border_radius=6)
            ch = rm.get_font(18, True).render("<" if side == "left" else ">", True, CYAN)
            surf.blit(ch, (r2.centerx - ch.get_width() // 2, r2.centery - ch.get_height() // 2))
        cnt_s  = rm.get_font(20, True).render(str(self.cfg.spawn_count), True,
                                               YELLOW if c_sel else WHITE)
        mid_x  = (layout["count_arrows"][0][1].right + layout["count_arrows"][1][1].x) // 2
        surf.blit(cnt_s, (mid_x - cnt_s.get_width() // 2, c_y + 10))

        # Botones
        bs  = layout["btn_start"]
        bb  = layout["btn_back"]
        mx_p, my_p = pygame.mouse.get_pos()
        has_enemies = bool(self.cfg.get_enabled_types())
        s_sel = (self._sel == n_types + 2)

        start_col  = (0, 80, 180) if has_enemies else (20, 20, 40)
        start_bord = CYAN if (s_sel or bs.collidepoint(mx_p, my_p)) and has_enemies \
                          else ((40, 80, 160) if has_enemies else (40, 40, 60))
        pygame.draw.rect(surf, start_col,  bs, border_radius=10)
        pygame.draw.rect(surf, start_bord, bs, 2, border_radius=10)
        st_txt = rm.get_font(17, True).render(
            "COMENZAR" if has_enemies else "Selecciona enemigos",
            True, WHITE if has_enemies else (80, 80, 100))
        surf.blit(st_txt, (bs.centerx - st_txt.get_width() // 2,
                           bs.centery - st_txt.get_height() // 2))

        b_sel = (self._sel == n_types + 3)
        back_bord = (180, 40, 40) if (b_sel or bb.collidepoint(mx_p, my_p)) else (80, 25, 25)
        pygame.draw.rect(surf, (50, 15, 15), bb, border_radius=10)
        pygame.draw.rect(surf, back_bord,   bb, 2, border_radius=10)
        bk_txt = rm.get_font(16).render("Volver", True, (200, 100, 100))
        surf.blit(bk_txt, (bb.centerx - bk_txt.get_width() // 2,
                           bb.centery - bk_txt.get_height() // 2))

        hint2 = rm.get_font(12).render(
            "Arriba / Abajo para navegar  |  ESPACIO para seleccionar  |  ESC para volver",
            True, (40, 55, 80))
        surf.blit(hint2, (SCREEN_W // 2 - hint2.get_width() // 2, SCREEN_H - 24))


class MainMenu:
    MODES = [GAMEMODE_CLASSIC, GAMEMODE_SURVIVAL, GAMEMODE_TIMEATTACK, GAMEMODE_PRACTICE]
    MODE_DESC = {
        GAMEMODE_CLASSIC:    "Oleadas infinitas. Construye tu nave y supera tu record.",
        GAMEMODE_SURVIVAL:   "Enemigos aparecen sin parar. Cuanto tiempo aguantas?",
        GAMEMODE_TIMEATTACK: "3 minutos. Maxima puntuacion posible.",
        GAMEMODE_PRACTICE:   "Skills 8 pts. Sinergias desbloqueadas. Elige tus enemigos.",
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
                if self.game.game_mode == GAMEMODE_PRACTICE:
                    self.game.state = GameState.PRACTICE_SETUP
                else:
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
            if getattr(self, "_score_btn", None) and self._score_btn.collidepoint(event.pos):
                self.game.sfx.play("ui_click", 0.2)
                self.game._scoreboard_open = True
                return
            if getattr(self, "_help_btn", None) and self._help_btn.collidepoint(event.pos):
                self.game.controls_guide.toggle()
                return
            if self._btn_rects:
                play_btn = self._btn_rects[0]
                if play_btn.collidepoint(event.pos):
                    self.game.sfx.play("ui_click")
                    self.game.game_mode = self.MODES[self.mode_sel]
                    if self.game.game_mode == GAMEMODE_PRACTICE:
                        self.game.state = GameState.PRACTICE_SETUP
                    else:
                        self.game._begin_warp()
                    return
                if len(self._btn_rects) > 1 and self._btn_rects[1].collidepoint(event.pos):
                    self.game.sfx.play("ui_click", 0.2)
                    self.game.running = False
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
        play_t = rm.get_font(20,True).render("JUGAR  [ENTER]", True, WHITE)
        surf.blit(play_t,(py_btn.centerx-play_t.get_width()//2,
                          py_btn.centery-play_t.get_height()//2))

        ex_btn = pygame.Rect(SCREEN_W//2-80,434,160,38)
        pygame.draw.rect(surf,(40,10,10),ex_btn,border_radius=8)
        pygame.draw.rect(surf,(80,20,20),ex_btn,1,border_radius=8)
        ex_t = rm.get_font(16).render("Salir  [ESC]", True,(160,80,80))
        surf.blit(ex_t,(ex_btn.centerx-ex_t.get_width()//2,
                        ex_btn.centery-ex_t.get_height()//2))

        self._btn_rects = [py_btn, ex_btn]

        help_btn = pygame.Rect(SCREEN_W - 170, SCREEN_H - 56, 154, 40)
        mx_h, my_h = pygame.mouse.get_pos()
        help_hov   = help_btn.collidepoint(mx_h, my_h)
        hbg = (0, 60, 100) if help_hov else (0, 30, 60)
        pygame.draw.rect(surf, hbg, help_btn, border_radius=8)
        pygame.draw.rect(surf, (0, 140, 200) if help_hov else (0, 80, 130), help_btn, 1, border_radius=8)
        ht = rm.get_font(14, True).render("CONTROLES", True, (0, 200, 255) if help_hov else (0, 140, 180))
        surf.blit(ht, (help_btn.centerx - ht.get_width()//2, help_btn.centery - ht.get_height()//2))
        self._help_btn = help_btn

        # Scoreboard button: positioned to the left of the help button.
        score_btn = pygame.Rect(SCREEN_W - 340, SCREEN_H - 56, 160, 40)
        score_hov = score_btn.collidepoint(mx_h, my_h)
        sbg = (60, 40, 0) if score_hov else (30, 20, 0)
        pygame.draw.rect(surf, sbg, score_btn, border_radius=8)
        pygame.draw.rect(surf, (GOLD[0], GOLD[1], GOLD[2]) if score_hov else (120, 100, 0),
                         score_btn, 1, border_radius=8)
        st2 = rm.get_font(14, True).render("PUNTUACIONES", True,
                                           GOLD if score_hov else (160, 130, 0))
        surf.blit(st2, (score_btn.centerx - st2.get_width() // 2,
                        score_btn.centery - st2.get_height() // 2))
        self._score_btn = score_btn

        nav = rm.get_font(13).render("◄ ► Cambiar modo de juego  |  [N] Música  |  [X] Nexo ", True,(50,55,70))
        surf.blit(nav,(SCREEN_W//2-nav.get_width()//2, 488))

        if self.game.sfx.music_muted:
            mt = rm.get_font(13,True).render("MÚSICA DESACTIVADA", True,(120,50,50))
            surf.blit(mt,(SCREEN_W//2-mt.get_width()//2, 510))

        seed_t = rm.get_font(12).render(f"Seed: {self.game.seed}", True,(40,44,58))
        surf.blit(seed_t,(SCREEN_W//2-seed_t.get_width()//2, SCREEN_H-26))


class Game:
    """
    Central controller.  Owns all subsystems, the main loop, event dispatch,
    update orchestration and the draw pipeline.  All game objects reference
    self.game to access shared services (pool, camera, sfx, etc.).
    """
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
        self._practice_cfg   = PracticeModeConfig()
        self.practice_menu   = PracticeModeMenu(self)
        self.main_menu       = MainMenu(self)
        self.controls_guide  = ControlsGuide()
        self.scoreboard          = Scoreboard()
        self._scoreboard_open    = False

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
        self.eco           = EcoEvolution()
        self.ai_log        = AILog()
        self._creatures: List[SpaceCreature] = []
        self._gravity_zones: List[GravityZone] = []
        self._modules: List[ShipModule] = []
        self._creature_spawn_cd = 8.0
        self._nebula_flash_cd   = 0.0
        self._cam_shake         = CameraShake()
        self._chroma_cd         = 0.0
        self._alert_waves: List[AlertWave] = []
        self._orbital_bodies: List[OrbitalBody] = []
        self._worm_boss: Optional[SegmentedWormBoss] = None
        self._worm_spawn_wave   = 10
        self._ghost_ship: Optional[ShadowShip] = None
        self._nebula_terrain    = NebulaTerrainSystem(self.world_gen.noise)
        self._mission_log       = MissionLog()
        self.nexus              = DataNexus()
        self.hack_sys           = HackSystem()
        self.faction_war        = FactionWarManager(self)
        self._dyn_camera        = DynamicCamera()
        self._motion_trail      = MotionTrail()
        self._bullet_hell_boss: Optional[BulletHellBoss] = None
        self._bhb_spawn_wave    = 7
        self._nexus_menu_open   = False
        self._deferred_light    = DeferredLighting()
        self._bullet_time       = BulletTimeSystem()
        self._parallax_bg       = ParallaxBackground(self.seed)
        self._localized_sparks  = LocalizedSparks()
        self._audio_muffle_cd   = 0.0
        self.allied_fleet       = AlliedFleet(self)
        self._tesla_dmg_cd      = 0.0
        self.sfx.play_music("menu")

    def _make_enemy_pool(self) -> "ObjectPool":
        """Build the shared enemy pool with pre-allocated instances of each subclass."""
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
        """Trigger the warp transition animation and silently initialise a new run in the background."""
        self._warp = WarpTransition(SCREEN_W, SCREEN_H)
        self._start_game()
        self.state = GameState.WARP
        self.sfx.stop_music()
        self.sfx.play("warp")

    def _build_nebula(self):
        """Generate a low-resolution nebula tint surface centred on the player's current position."""
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
        """Main game loop: caps dt at 50 ms, dispatches events, updates and draws."""
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
        """Route pygame events to the appropriate state handler."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False

            elif self.state == GameState.MENU:
                if getattr(self, "controls_guide", None) and self.controls_guide.open:
                    self.controls_guide.handle_event(ev)
                elif getattr(self, "_scoreboard_open", False):
                    # Route events to the scoreboard overlay; close it on ESC or X.
                    if self.scoreboard.handle_event(ev):
                        self._scoreboard_open = False
                elif getattr(self, "_nexus_menu_open", False):
                    if self.nexus.handle_event(ev, ai_log=getattr(self, "ai_log", None)):
                        self._nexus_menu_open = False
                else:
                    self.main_menu.handle_event(ev)
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_n:
                            self.sfx.toggle_music()
                        elif ev.key == pygame.K_x:
                            self._nexus_menu_open = True

            elif self.state == GameState.WARP:
                pass

            elif self.state == GameState.PLAYING:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    elif ev.key == pygame.K_2:
                        self.state = GameState.SKILL
                    elif ev.key == pygame.K_m:
                        self.sfx.toggle_mute()
                    elif ev.key == pygame.K_n:
                        self.sfx.toggle_music()
                    elif ev.key == pygame.K_e:
                        self.hack_sys.activate(self)
                    elif ev.key == pygame.K_f:
                        af = getattr(self, "allied_fleet", None)
                        if af: af.summon()

            elif self.state == GameState.SKILL:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_2:
                    self.state = GameState.PLAYING
                else:
                    self.skill_screen.handle_event(ev)

            elif self.state == GameState.PAUSED:
                action = self.pause_menu.handle_event(ev)
                if action == "Continuar":
                    self.state = GameState.PLAYING
                elif action == "Árbol de Habilidades":
                    self.state = GameState.SKILL
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

            elif self.state == GameState.PRACTICE_SETUP:
                action = self.practice_menu.handle_event(ev)
                if action == "start":
                    self.sfx.play("ui_click")
                    self._begin_warp()
                elif action == "back":
                    self.game_mode = GAMEMODE_CLASSIC
                    self.state = GameState.MENU
                    self.sfx.play_music("menu")

    def _update(self, dt):
        """Advance all game systems by dt seconds. Skips most logic in non-PLAYING states."""
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

        dt = self._bullet_time.update(dt, p, ai_log=self.ai_log)

        self.camera += (p.transform.pos - Vec2(SCREEN_W,SCREEN_H)/2 - self.camera) * min(dt*8,1.0)

        if self.game_mode == GAMEMODE_TIMEATTACK:
            self._ta_time += dt
            if self._ta_time >= self._ta_limit:
                self._snapshot_stats_and_ghost()
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

        if (self.game_mode == GAMEMODE_CLASSIC and
                self.wave_manager.wave > 0 and
                len(active_en) == 0 and
                self.wave_manager.timer < self.wave_manager.wave_interval - 2.0):
            self.wave_manager.timer = self.wave_manager.wave_interval

        if self.game_mode == GAMEMODE_TIMEATTACK:
            if (self.wave_manager.wave > 0 and
                    len(active_en) == 0 and
                    self.wave_manager.timer < self.wave_manager.wave_interval - 2.0):
                self.wave_manager.timer = self.wave_manager.wave_interval

        dead_b = [b for b in list(self.bullet_pool.active) if not b.update(dt, self)]
        for b in dead_b:
            self.bullet_pool.release(b)

        if hasattr(self, "nexus") and self.nexus.has_synergy("laser_shield"):
            for b in self.bullet_pool.active:
                if b.owner == "player" and not getattr(b, "_bounced", False):
                    bsx = b.rect.centerx - int(self.camera.x)
                    bsy = b.rect.centery - int(self.camera.y)
                    if bsx <= 0 or bsx >= SCREEN_W:
                        b.vel.x = -b.vel.x
                        b._bounced = True
                        b.color = GOLD
                    elif bsy <= 0 or bsy >= SCREEN_H:
                        b.vel.y = -b.vel.y
                        b._bounced = True
                        b.color = GOLD

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

        self._mission_log.update(dt, p)

        self._cam_shake.update(dt)

        self._chroma_cd = max(0.0, self._chroma_cd - dt)

        for aw in self._alert_waves:
            aw.update(dt)
        self._alert_waves = [aw for aw in self._alert_waves if aw.active]

        cx_ob = int(p.transform.pos.x // SECTOR_SIZE)
        cy_ob = int(p.transform.pos.y // SECTOR_SIZE)
        self._orbital_bodies = []
        for ddx in range(-3, 4):
            for ddy in range(-3, 4):
                for ob in self.world_gen.get_orbital_bodies(cx_ob+ddx, cy_ob+ddy):
                    self._orbital_bodies.append(ob)
                    ob.update(dt)
                    gf = ob.gravity_force(p.transform.pos, dt)
                    p.transform.vel += gf
                    spd = p.transform.vel.length()
                    if spd > MAX_SPEED_PLAYER * 1.5:
                        sk_lv = self.skill_tree.skills.get("slingshot")
                        cap   = PLANET_SLINGSHOT_CAP if (sk_lv and sk_lv.level > 0) else MAX_SPEED_PLAYER * 2.0
                        if spd > cap:
                            p.transform.vel = p.transform.vel.normalize() * cap
                    for e in active_en:
                        e.transform.vel += ob.gravity_force(e.transform.pos, dt) * 0.5
                    for b in self.bullet_pool.active:
                        bpos = Vec2(b.rect.centerx, b.rect.centery)
                        bgf  = ob.gravity_force(bpos, dt)
                        b.vel += bgf * 1.8

        self._nebula_terrain.update(p.transform.pos, p, dt)

        if self._worm_boss is None or not self._worm_boss.active:
            if self.wave_manager.wave >= self._worm_spawn_wave:
                self._worm_boss = SegmentedWormBoss(self)
                ang = random.uniform(0, math.pi*2)
                dist = 600
                self._worm_boss.spawn(
                    p.transform.pos.x + math.cos(ang)*dist,
                    p.transform.pos.y + math.sin(ang)*dist
                )
                self._worm_spawn_wave += 12
        if self._worm_boss and self._worm_boss.active:
            self._worm_boss.update(dt)

        if self._ghost_ship and self._ghost_ship.active:
            self._ghost_ship.update(dt)

        self.ai_log.update(dt, p, self.eco)

        self.hack_sys.update(dt, self)

        self.faction_war.update(dt)

        af = getattr(self, "allied_fleet", None)
        if af: af.update(dt)

        self._dyn_camera.update(dt, p, self)

        self._deferred_light.update(dt)

        if self._audio_muffle_cd > 0:
            self._audio_muffle_cd -= dt
            if self._audio_muffle_cd <= 0:
                self.sfx.restore_music_volume()

        self._motion_trail.update(dt, p)

        if (self._bullet_hell_boss is None or not self._bullet_hell_boss.active):
            if self.wave_manager.wave >= self._bhb_spawn_wave:
                self._bullet_hell_boss = BulletHellBoss(self)
                ang  = random.uniform(0, math.pi*2)
                dist = 650
                self._bullet_hell_boss.spawn(
                    p.transform.pos.x + math.cos(ang)*dist,
                    p.transform.pos.y + math.sin(ang)*dist
                )
                self._bhb_spawn_wave += 10
        if self._bullet_hell_boss and self._bullet_hell_boss.active:
            self._bullet_hell_boss.update(dt)

        self._localized_sparks.update(dt, p)

        for e in [e for e in self.enemy_pool.active if e.active]:
            if e.etype in ("titan", "boss"):
                dist_to = (e.transform.pos - p.transform.pos).length()
                if dist_to < SHAKE_TITAN_DIST:
                    proximity = 1.0 - dist_to / SHAKE_TITAN_DIST
                    self._cam_shake.add(
                        Vec2(random.uniform(-1,1), random.uniform(-1,1)),
                        SHAKE_TITAN_STRENGTH * proximity * dt * 8
                    )

        if hasattr(self, "faction_war") and self.faction_war.buff_active:
            bonus = self.faction_war.speed_buff
            base  = MAX_SPEED_PLAYER * self.skill_tree.get_stat("speed")
            p.physics.max_speed = max(p.physics.max_speed, base * bonus)

        if (hasattr(self, "nexus") and self.nexus.has_synergy("overdrive") and
                p.transform.vel.length() > MAX_SPEED_PLAYER * 0.7):
            mt2 = getattr(self, "_motion_trail", None)
            if mt2 and len(mt2._history) >= 3:
                trail_pos = Vec2(*mt2._history[-2][:2])
                for e in [e for e in self.enemy_pool.active if e.active]:
                    if (e.transform.pos - trail_pos).length() < 30:
                        e.health.take_damage(2)
                        self._particles_spawn(e.transform.pos, CYAN, 2)

        # ── Tesla Link damage: enemies inside a nano-bot lightning arc take damage ──
        active_nbs2 = [nb for nb in p._nano_bots if nb.active]
        TESLA_DIST2 = 140
        TESLA_DMG_CD = getattr(self, "_tesla_dmg_cd", 0.0)
        TESLA_DMG_CD -= dt
        self._tesla_dmg_cd = max(0.0, TESLA_DMG_CD)
        if TESLA_DMG_CD <= 0 and len(active_nbs2) >= 2:
            for i in range(len(active_nbs2)):
                for j in range(i+1, len(active_nbs2)):
                    nb_a2 = active_nbs2[i]
                    nb_b2 = active_nbs2[j]
                    pa2   = Vec2(p.transform.pos.x + math.cos(nb_a2.angle)*NANO_BOT_ORBIT_R,
                                 p.transform.pos.y + math.sin(nb_a2.angle)*NANO_BOT_ORBIT_R)
                    pb3   = Vec2(p.transform.pos.x + math.cos(nb_b2.angle)*NANO_BOT_ORBIT_R,
                                 p.transform.pos.y + math.sin(nb_b2.angle)*NANO_BOT_ORBIT_R)
                    if (pa2 - pb3).length() < TESLA_DIST2:
                        seg_rect = pygame.Rect(
                            min(pa2.x, pb3.x) - 4, min(pa2.y, pb3.y) - 4,
                            abs(pa2.x - pb3.x) + 8, abs(pa2.y - pb3.y) + 8
                        )
                        for e in [e for e in self.enemy_pool.active if e.active]:
                            if e.rect.colliderect(seg_rect):
                                dead = e.health.take_damage(3)
                                self._particles_spawn(e.transform.pos, (80, 200, 255), 3)
                                if dead:
                                    e.active = False
                                    self.enemy_pool.release(e)
                                    p.score += 80
                                    p.add_xp(20)
                                    self.sfx.play("explosion_small")
            self._tesla_dmg_cd = 0.18  # damage tick every 0.18s

        self._creature_spawn_cd -= dt
        if self._creature_spawn_cd <= 0:
            self._creature_spawn_cd = random.uniform(15.0, 30.0)
            c = SpaceCreature()
            ang  = random.uniform(0, math.pi*2)
            dist = random.uniform(400, 700)
            c.spawn(p.transform.pos.x + math.cos(ang)*dist,
                    p.transform.pos.y + math.sin(ang)*dist)
            self._creatures.append(c)
        for c in self._creatures:
            c.update(dt)
        self._creatures = [c for c in self._creatures if c.active]

        cx_gz = int(p.transform.pos.x // SECTOR_SIZE)
        cy_gz = int(p.transform.pos.y // SECTOR_SIZE)
        self._gravity_zones = []
        in_nebula = False
        for ddx in range(-2, 3):
            for ddy in range(-2, 3):
                for gz in self.world_gen.get_gravity_zones(cx_gz+ddx, cy_gz+ddy):
                    self._gravity_zones.append(gz)
                    gz.update(dt)
                    if gz.type == GravityZone.TYPE_BLACKHOLE and gz.in_zone(p.transform.pos):
                        delta = gz.apply(p.transform.pos, p.transform.vel, dt)
                        p.transform.vel += delta
                        if not gz._warned:
                            gz._warned = True
                            self.ai_log.push_zone()
                    if gz.type == GravityZone.TYPE_WHITEHOLE and gz.in_zone(p.transform.pos):
                        delta = gz.apply(p.transform.pos, p.transform.vel, dt)
                        p.transform.vel += delta
                        if not gz._warned:
                            gz._warned = True
                            self.ai_log._push("⬤ AGUJERO BLANCO — Zona de repulsión activa.", 4.5)
                    if gz.type == GravityZone.TYPE_NEBULA and gz.in_zone(p.transform.pos):
                        in_nebula = True
                    for e in active_en:
                        if gz.type == GravityZone.TYPE_BLACKHOLE and gz.in_zone(e.transform.pos):
                            delta = gz.apply(e.transform.pos, e.transform.vel, dt)
                            e.transform.vel += delta
                        elif gz.type == GravityZone.TYPE_WHITEHOLE and gz.in_zone(e.transform.pos):
                            delta = gz.apply(e.transform.pos, e.transform.vel, dt)
                            e.transform.vel += delta
                    # White hole deflects bullets (projectile scatter)
                    if gz.type == GravityZone.TYPE_WHITEHOLE:
                        for b in self.bullet_pool.active:
                            bpos = Vec2(b.rect.centerx, b.rect.centery)
                            if gz.in_zone(bpos):
                                bdelta = gz.apply(bpos, b.vel, dt)
                                b.vel += bdelta * 2.0
        if in_nebula:
            max_spd = MAX_SPEED_PLAYER * NEBULA_SLOW_FACTOR
            if p.transform.vel.length() > max_spd:
                p.transform.vel = p.transform.vel.normalize() * max_spd

        for mod in self._modules:
            mod.update(dt)
        self._modules = [m for m in self._modules if m.active]
        for mod in list(self._modules):
            if mod.rect.colliderect(p.rect):
                if p.modules.collect(mod.mtype):
                    mod.active = False
                    self.ai_log.push_module()
                    if mod.mtype == "armor":
                        p.health.max_hp += 25
                        p.health.hp = min(p.health.hp + 25, p.health.max_hp)
                    self.sfx.play("skill_upgrade")

        for c in list(self._creatures):
            for b in list(self.bullet_pool.active):
                if b.owner == "player" and b.rect.colliderect(c.rect):
                    dead = c.take_damage(b.damage)
                    self._particles_spawn(c.pos, (0, 220, 140), 5)
                    self.bullet_pool.release(b)
                    if dead:
                        c.active = False
                        p.score += 150
                        p.add_xp(55)
                        if random.random() < MODULE_DROP_CHANCE:
                            mtype = random.choice(list(ShipModule.TYPES.keys()))
                            self._modules.append(ShipModule(c.pos.x, c.pos.y, mtype))
                    break

        if p.health.hp <= 0:
            self._snapshot_stats_and_ghost()
            self.state = GameState.GAME_OVER

    def _spawn_titan(self):
        """Pull a TitanBoss from the pool and spawn it at a random distance from the player."""
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

    def _snapshot_stats_and_ghost(self):
        """Capture end-of-run statistics, save the ghost run and generate the mission chronicle."""
        self._snapshot_stats()
        GhostRun.save(self.player, self.wave_manager.wave,
                      (int(self.player.transform.pos.x//SECTOR_SIZE),
                       int(self.player.transform.pos.y//SECTOR_SIZE)))
        self._final_stats["chronicle"] = self._mission_log.generate_chronicle(self._final_stats)
        self._final_stats["heatmap_pos"] = list(self._mission_log._positions[-200:])
        self.scoreboard.add_entry(self._final_stats)  # Persist run result to the high-score table.

    def _snapshot_stats(self):
        """Populate _final_stats dict with all relevant end-of-run metrics."""
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
            "data_frags":  self.nexus.fragments,
        }

    def _active_enemy_count(self) -> int:
        """Return the number of currently active enemy instances in the pool."""
        return sum(1 for e in self.enemy_pool.active if e.active)

    def _spawn_survival_enemy(self):
        """Spawn a random cluster of enemies for Survival mode's continuous spawn loop."""
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
                if hasattr(self, "eco"): self.eco.apply_to_enemy(e)
                e.spawn(ex, ey)

    def _collisions(self, asteroids, enemies):
        """
        Resolve all collisions for one frame:
          - Player bullets vs enemies and asteroids
          - Enemy bullets vs player
          - Player vs ghost ship, worm boss, asteroids, bullet-hell boss
        Awards XP/score, releases bullets and triggers death effects.
        """
        p          = self.player
        to_release = []

        for bullet in list(self.bullet_pool.active):
            candidates = self.quadtree.retrieve(bullet)
            hit        = False
            for obj in candidates:
                if hit: break
                if isinstance(obj, Enemy) and obj.active and bullet.owner=="player":
                    if bullet.rect.colliderect(obj.rect):
                        shield = getattr(obj, "_eco_shield", 0.0)
                        eff_dmg = max(1, int(bullet.damage * (1.0 - shield)))
                        dead = obj.health.take_damage(eff_dmg)
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
                            self.eco.register_kill(obj.etype)
                            if hasattr(self, "_mission_log"):
                                self._mission_log.log_event(f"kill:{obj.etype}:wave{self.wave_manager.wave}")
                            self.skill_tree.save()
                            if random.random() < MODULE_DROP_CHANCE * 0.5:
                                mtype = random.choice(list(ShipModule.TYPES.keys()))
                                self._modules.append(ShipModule(obj.transform.pos.x, obj.transform.pos.y, mtype))

                            self._particles_spawn(obj.transform.pos, RED, 15)
                            if obj.etype == "titan":
                                self.sfx.play("explosion_boss")
                                for _ in range(3):
                                    self._particles_spawn(obj.transform.pos, PURPLE, 20)
                            elif obj.etype == "boss":
                                self.sfx.play("explosion_boss")
                                self._nebula_flash_cd = 0.18
                            elif obj.etype in ("heavy", "carrier"):
                                self.sfx.play("explosion")
                                self._nebula_flash_cd = 0.10
                            else:
                                self.sfx.play("explosion_small")
                            if random.random() < DATA_FRAG_DROP_CHANCE:
                                frags = 1 + (1 if obj.etype in ("boss","titan","carrier") else 0)
                                self.nexus.add_fragments(frags)
                                self.nexus.check_lore()
                            if getattr(obj, "_faction", None):
                                opp = FACTION_DRONE if obj._faction == FACTION_SWARM else FACTION_SWARM
                                self.faction_war.player_sided_with(opp)
                        if self.skill_tree.skills["pierce"].level == 0:
                            nb_sk = self.skill_tree.skills.get("nano_bots")
                            if nb_sk and nb_sk.level > 0 and not dead:
                                for nb in p._nano_bots:
                                    if not nb.active:
                                        nb.spawn(bullet.damage)
                                        break
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
                bpos = Vec2(bullet.rect.centerx, bullet.rect.centery)
                p.take_damage(bullet.damage, bullet_pos=bpos)
                self._particles_spawn(p.transform.pos, RED, 4)
                to_release.append(bullet)

        for b in set(to_release):
            if b in self.bullet_pool.active:
                self.bullet_pool.release(b)

        gs = self._ghost_ship
        if gs and gs.active and not gs._wreck:
            for bullet in list(self.bullet_pool.active):
                if bullet.owner == "player":
                    br = pygame.Rect(bullet.rect)
                    gr = pygame.Rect(int(gs.pos.x)-gs.RADIUS, int(gs.pos.y)-gs.RADIUS,
                                     gs.RADIUS*2, gs.RADIUS*2)
                    if br.colliderect(gr):
                        dead_g = gs.take_damage(bullet.damage)
                        self._particles_spawn(gs.pos, (180,80,255), 5)
                        if dead_g:
                            gs.active = False
                            p.score  += 1200
                            p.add_xp(400)
                            self._particles_spawn(gs.pos, PURPLE, 20)
                            self.sfx.play("explosion_boss")
                            for _ in range(2):
                                mt = random.choice(list(ShipModule.TYPES.keys()))
                                self._modules.append(ShipModule(gs.pos.x, gs.pos.y, mt))
                        to_release.append(bullet)
                        break
            if p.rect.colliderect(pygame.Rect(int(gs.pos.x)-gs.RADIUS, int(gs.pos.y)-gs.RADIUS,
                                               gs.RADIUS*2, gs.RADIUS*2)):
                p.take_damage(8)

        wb = self._worm_boss
        if wb and wb.active:
            for bullet in list(self.bullet_pool.active):
                if bullet.owner == "player":
                    for i, seg in enumerate(wb.segments):
                        if not seg.active: continue
                        if bullet.rect.colliderect(seg.rect):
                            wb.hit_segment(i, bullet.damage)
                            to_release.append(bullet)
                            break
            for seg in wb.segments:
                if seg.active and p.rect.colliderect(seg.rect):
                    p.take_damage(6)

        for a in asteroids:
            if p.rect.colliderect(a.rect):
                d = p.transform.pos - a.pos
                if d.length() > 0:
                    p.transform.vel += d.normalize() * 3
                p.take_damage(4)

        bhb = getattr(self, "_bullet_hell_boss", None)
        if bhb and bhb.active:
            for bullet in list(self.bullet_pool.active):
                if bullet.owner == "player":
                    br2 = pygame.Rect(int(bhb.pos.x)-bhb.RADIUS, int(bhb.pos.y)-bhb.RADIUS,
                                      bhb.RADIUS*2, bhb.RADIUS*2)
                    if bullet.rect.colliderect(br2):
                        dead_b2 = bhb.take_damage(bullet.damage)
                        self._particles_spawn(bhb.pos, (180, 80, 255), 6)
                        if dead_b2:
                            bhb.active = False
                            p.score   += 3500
                            p.add_xp(1000)
                            self.nexus.add_fragments(8)
                            self._particles_spawn(bhb.pos, PURPLE, 30)
                            self.sfx.play("explosion_boss")
                            self._nebula_flash_cd = 0.3
                            self.ai_log._push(" JEFE GEOMÉTRICO destruido. +8 Fragmentos de Datos.", 6.0)
                        if bullet in self.bullet_pool.active:
                            self.bullet_pool.release(bullet)
                        break

    def _particles_spawn(self, pos, color, count):
        """Emit count screen-space particles at world position pos."""
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
        dl = getattr(self, "_deferred_light", None)
        if dl and count >= 8:
            sx = int(pos.x - self.camera.x)
            sy = int(pos.y - self.camera.y)
            dl.add_flash(sx, sy, radius=max(20, count*3),
                         color=color[:3], life=0.35)

    def _update_particles(self, dt):
        """Advance all live particles; remove any that have expired."""
        alive = []
        for p in self._particles:
            p["life"] -= dt
            p["pos"]  += p["vel"] * dt * 60
            p["vel"]  *= 0.91
            if p["life"] > 0:
                alive.append(p)
        self._particles = alive

    def _draw(self, fps):
        """Select the correct draw routine for the current state and flip the display."""
        s   = self.screen
        shake = getattr(self, "_cam_shake", None)
        if shake and self.state == GameState.PLAYING:
            self.camera -= shake.offset
        if   self.state == GameState.PRACTICE_SETUP:
            self.practice_menu.update(self._last_dt)
            self.practice_menu.draw(s)
        elif self.state == GameState.MENU:
            self.main_menu.draw(s, self._last_dt)
            if getattr(self, "_nexus_menu_open", False):
                self.nexus.draw_menu_overlay(s, self.rm, self._last_dt)
            if getattr(self, "controls_guide", None) and self.controls_guide.open:
                self.controls_guide.draw(s)
            if getattr(self, "_scoreboard_open", False):
                # Draw the scoreboard overlay on top of everything else in the menu.
                self.scoreboard.draw(s)
        elif self.state == GameState.WARP:
            if self._warp:
                self._warp.draw(s)
        elif self.state == GameState.PLAYING:
            self._draw_world(s)
            dc = getattr(self, "_dyn_camera", None)
            if dc and abs(dc.zoom - 1.0) > 0.02:
                zoomed = dc.apply(s)
                s.blit(zoomed, (0, 0))
            chroma = getattr(self, "_chroma_cd", 0)
            if chroma > 0:
                strength = min(chroma / 0.35, 1.0)
                offset   = int(strength * 5)
                # Proper chromatic aberration: isolate R and B channels with offset
                chroma_src = s.copy()
                r_surf = chroma_src.copy()
                r_surf.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
                b_surf = chroma_src.copy()
                b_surf.fill((0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)
                r_surf.set_alpha(int(160 * strength))
                b_surf.set_alpha(int(160 * strength))
                s.blit(r_surf, (-offset, 0), special_flags=pygame.BLEND_RGB_ADD)
                s.blit(b_surf, (offset,  0), special_flags=pygame.BLEND_RGB_ADD)
            self.hud.draw(s, fps)
            bt = getattr(self, "_bullet_time", None)
            if bt:
                bt.draw_vignette(s)
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
        if shake and self.state == GameState.PLAYING:
            self.camera += shake.offset
        pygame.display.flip()

    def _draw_world(self, surf):
        """Render the full world layer: background, asteroids, enemies, bullets,
        particles, special objects and the deferred lighting pass."""
        surf.fill(DARK_BLUE)
        surf.blit(self._nebula_surf,(0,0))

        pb = getattr(self, "_parallax_bg", None)
        if pb:
            pb.draw(surf, self.camera)
        else:
            cx_s = int(self.player.transform.pos.x // SECTOR_SIZE)
            cy_s = int(self.player.transform.pos.y // SECTOR_SIZE)
            for ddx in range(-3,4):
                for ddy in range(-3,4):
                    for wx,wy,sz,br in self.world_gen.get_stars(cx_s+ddx,cy_s+ddy):
                        sx2 = int(wx - self.camera.x*0.28) % SCREEN_W
                        sy2 = int(wy - self.camera.y*0.28) % SCREEN_H
                        pygame.draw.circle(surf,(br,br,br),(sx2,sy2),sz)

        if getattr(self, "_nebula_flash_cd", 0) > 0:
            self._nebula_flash_cd -= self._last_dt
            alpha = int(min(1.0, self._nebula_flash_cd / 0.18) * 80)
            fl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            #l.fill((255, 120, 30, alpha))
            surf.blit(fl, (0, 0))

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

        for gz in getattr(self, "_gravity_zones", []):
            gz.draw(surf, self.camera)

        for ob in getattr(self, "_orbital_bodies", []):
            ob.draw(surf, self.camera)

        for aw in getattr(self, "_alert_waves", []):
            aw.draw(surf, self.camera)

        wb = getattr(self, "_worm_boss", None)
        if wb and wb.active:
            wb.draw(surf, self.camera)

        gs2 = getattr(self, "_ghost_ship", None)
        if gs2 and gs2.active:
            gs2.draw(surf, self.camera)

        for c in getattr(self, "_creatures", []):
            c.draw(surf, self.camera)

        for mod in getattr(self, "_modules", []):
            mod.draw(surf, self.camera)

        mt = getattr(self, "_motion_trail", None)
        if mt:
            mt.draw(surf, self.camera)

        ls2 = getattr(self, "_localized_sparks", None)
        if ls2:
            ls2.draw(surf, self.camera)

        self.player.draw(surf, self.camera)

        p   = self.player
        sx_p = int(p.transform.pos.x - self.camera.x)
        sy_p = int(p.transform.pos.y - self.camera.y)
        ShipVisualUpgrade.draw_extras(surf, p, sx_p, sy_p,
                                      math.radians(p.transform.angle))

        hs = getattr(self, "hack_sys", None)
        if hs:
            hs.draw_overlay(surf, self.camera, self.player.transform.pos)

        af2 = getattr(self, "allied_fleet", None)
        if af2: af2.draw(surf, self.camera)

        bhb2 = getattr(self, "_bullet_hell_boss", None)
        if bhb2 and bhb2.active:
            bhb2.draw(surf, self.camera)

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

        dl = getattr(self, "_deferred_light", None)
        if dl:
            dl.render(surf, self)

    def _draw_game_over(self, surf):
        rm = self.rm
        st = self._final_stats
        if not st:
            return

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
        motivation = messages[-1][1]
        for threshold, msg in messages:
            if score >= threshold:
                motivation = msg
                break

        skill_names = {
            "fire_rate":"Cadencia","bullet_dmg":"Daño","speed":"Velocidad",
            "shield":"Escudo","multi_shot":"Multidisparo","pierce":"Perforadora",
            "grav_pull":"Gravedad Cuántica","nano_bots":"Nano-Bots","slingshot":"Asistencia Grav.",
        }

        PAD     = 28
        CARD_W  = 860
        CARD_X  = SCREEN_W//2 - CARD_W//2
        SCROLL  = self._stats_scroll
        ROW_H   = 30

        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 10, 210))
        surf.blit(ov, (0, 0))

        content_h = 1400
        canvas    = pygame.Surface((CARD_W, content_h), pygame.SRCALPHA)

        y = 0

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

        sh("GAME OVER", 46, RED, y); y += 56
        mode_col = {
            GAMEMODE_CLASSIC: CYAN, GAMEMODE_SURVIVAL: ORANGE, GAMEMODE_TIMEATTACK: YELLOW
        }.get(st.get("mode",""), WHITE)
        sh(f"Modo: {st.get('mode','')}", 18, mode_col, y); y += 32
        divider(y); y += 14

        sh("ESTADÍSTICAS DE MISIÓN", 20, YELLOW, y, bold=True); y += 30
        divider(y, (60,60,100)); y += 10

        mins = int(st.get("play_time",0)//60)
        secs = int(st.get("play_time",0)%60)
        rows = [
            ("Puntuación final",  f"{st.get('score',0):,}",   YELLOW),
            ("Tiempo de misión",   f"{mins}m {secs:02d}s",     CYAN),
            ("Nivel alcanzado",    str(st.get("level",1)),     GREEN),
            ("Oleada máxima",      str(st.get("wave",0)),      (100,180,255)),
            ("Enemigos eliminados",str(st.get("total_kills",0)),(230,80,80)),
            ("Skill pts restantes",str(st.get("skill_pts",0)), PURPLE),
            ("Fragmentos de Datos",str(st.get("data_frags",0)), GOLD),
        ]
        for label, value, col in rows:
            left(label,  16, (180,180,200), y)
            right(value, 17, col, y)
            y += ROW_H
        y += 6; divider(y); y += 14

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
                bar_w = min(200, count * 8)
                pygame.draw.rect(canvas, (30,30,50),  (CARD_W//2-80, y+4, 200, 12), border_radius=4)
                pygame.draw.rect(canvas, (*col, 180), (CARD_W//2-80, y+4, bar_w, 12), border_radius=4)
                y += ROW_H - 4
        y += 10; divider(y); y += 14

        sh("MEJORAS CONSEGUIDAS", 18, YELLOW, y, bold=True); y += 28
        divider(y, (60,60,100)); y += 10

        skills = st.get("skills", {})
        skill_max = {
            "fire_rate":5,"bullet_dmg":5,"speed":4,"shield":3,
            "multi_shot":3,"pierce":2,
            "grav_pull":3,"nano_bots":1,"slingshot":2,
        }
        for sk, lv in skills.items():
            max_lv = skill_max.get(sk, 5)
            name   = skill_names.get(sk, sk)
            col    = GREEN if lv >= max_lv else (CYAN if lv > 0 else GRAY)
            left(f"  {name}", 15, col, y)
            for pip in range(max_lv):
                px2 = CARD_W - PAD - (max_lv-pip)*22
                pc  = YELLOW if pip < lv else (40,40,60)
                pygame.draw.circle(canvas, pc, (px2, y+8), 7)
                pygame.draw.circle(canvas, WHITE, (px2, y+8), 7, 1)
            lv_txt = rm.get_font(13, True).render(f"Lv {lv}/{max_lv}", True, col)
            canvas.blit(lv_txt, (CARD_W - PAD - max_lv*22 - lv_txt.get_width() - 10, y+1))
            y += ROW_H - 2
        y += 12; divider(y); y += 18

        pygame.draw.rect(canvas, (8,8,28), (PAD-8, y-4, CARD_W-PAD*2+16, 62), border_radius=8)
        pygame.draw.rect(canvas, (60,40,120), (PAD-8, y-4, CARD_W-PAD*2+16, 62), 1, border_radius=8)
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
        for li, line in enumerate(lines2):
            lt = rm.get_font(14, li==0).render(line, True, (200,180,255))
            canvas.blit(lt, (PAD, y + li*20))
        y += max(40, len(lines2)*20) + 20

        chronicle = st.get("chronicle", [])
        if chronicle:
            sh("CRÓNICA DE MISIÓN", 18, (160,200,255), y, bold=True); y += 28
            divider(y, (40,40,100)); y += 10
            for line in chronicle:
                lt2 = rm.get_font(13).render(line, True, (150,170,210))
                canvas.blit(lt2, (PAD, y))
                y += 20
            y += 10

        actual_content_h = y + 10
        visible_h   = SCREEN_H - 100
        card_y_top  = 50
        max_scroll  = max(0, actual_content_h - visible_h)
        self._stats_scroll = min(self._stats_scroll, max_scroll)
        SCROLL = self._stats_scroll

        card_bg = pygame.Surface((CARD_W + 4, visible_h + 4), pygame.SRCALPHA)
        pygame.draw.rect(card_bg, (6,6,22,240), (0,0,CARD_W+4,visible_h+4), border_radius=10)
        pygame.draw.rect(card_bg, (40,40,80,200), (0,0,CARD_W+4,visible_h+4), 1, border_radius=10)
        surf.blit(card_bg, (CARD_X-2, card_y_top-2))

        cropped = canvas.subsurface((0, 0, CARD_W, min(actual_content_h, content_h)))
        clip_surf = pygame.Surface((CARD_W, visible_h), pygame.SRCALPHA)
        clip_surf.fill((0,0,0,0))
        clip_surf.blit(cropped, (0, -SCROLL))
        surf.blit(clip_surf, (CARD_X, card_y_top))

        ml = getattr(self, "_mission_log", None)
        if ml and len(ml._positions) > 2:
            ml.draw_heatmap(surf, 10, SCREEN_H - 160, 150, 110)

        if max_scroll > 0:
            sh_t = rm.get_font(12).render("↑↓ Desplazar", True, (80,80,100))
            surf.blit(sh_t, (CARD_X + CARD_W - sh_t.get_width() - 10, card_y_top + visible_h + 4))

        btn_y = SCREEN_H - 44
        def draw_btn(text, cx, col_bg, col_border, col_txt):
            bw, bh = 200, 36
            bx2 = cx - bw//2
            pygame.draw.rect(surf, col_bg,     (bx2, btn_y, bw, bh), border_radius=8)
            pygame.draw.rect(surf, col_border, (bx2, btn_y, bw, bh), 2, border_radius=8)
            t2 = rm.get_font(16, True).render(text, True, col_txt)
            surf.blit(t2, (cx - t2.get_width()//2, btn_y + bh//2 - t2.get_height()//2))

        draw_btn("ENTER  Reintentar", SCREEN_W//2 - 120, (0,50,120),(0,150,220), WHITE)
        draw_btn("ESC  Menú principal", SCREEN_W//2 + 120, (60,10,10),(180,40,40), (220,120,120))

    def _start_game(self):
        """Reset all per-run state without rebuilding persistent singletons (nexus, sfx)."""
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
        self.eco               = EcoEvolution()
        self.ai_log            = AILog()
        self._creatures        = []
        self._gravity_zones    = []
        self._modules          = []
        self._creature_spawn_cd = 8.0
        self._nebula_flash_cd   = 0.0
        self.hack_sys          = HackSystem()
        self.faction_war       = FactionWarManager(self)
        self._dyn_camera       = DynamicCamera()
        self._motion_trail     = MotionTrail()
        self._bullet_hell_boss  = None
        self._bhb_spawn_wave    = 7
        self._deferred_light   = DeferredLighting()
        self._bullet_time      = BulletTimeSystem()
        self._localized_sparks = LocalizedSparks()
        self._audio_muffle_cd  = 0.0
        self.allied_fleet      = AlliedFleet(self)
        self._tesla_dmg_cd     = 0.0
        self.wave_manager.timer = self.wave_manager.wave_interval - 4.0

        # Aplicar configuracion del Modo Practica
        if self.game_mode == GAMEMODE_PRACTICE:
            cfg = getattr(self, "_practice_cfg", None)
            # Puntos de habilidad ilimitados (simulados como 99)
            self.skill_tree.points = 99
            # Desbloquear todas las sinergias del Nexo temporalmente
            self._practice_orig_synergies = dict(self.nexus.synergies)
            for sid in self.nexus.synergies:
                self.nexus.synergies[sid] = True
            # Configurar WaveManager con los tipos seleccionados
            if cfg:
                self.wave_manager._practice_types    = cfg.get_enabled_types()
                self.wave_manager._practice_interval = cfg.spawn_interval
                self.wave_manager._practice_count    = cfg.spawn_count

        if self.state != GameState.WARP:
            self.state = GameState.PLAYING
            track_map = {
                GAMEMODE_CLASSIC:    "classic",
                GAMEMODE_SURVIVAL:   "survival",
                GAMEMODE_TIMEATTACK: "timeattack",
                GAMEMODE_PRACTICE:   "classic",
            }
            self.sfx.play_music(track_map.get(self.game_mode, "classic"))


if __name__ == "__main__":
    # Instantiate the Game controller and enter the main loop.
    game = Game()
    game.run()
