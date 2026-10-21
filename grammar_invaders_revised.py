"""Grammar Invaders — expanded Python/Tkinter edition.

Controls
--------
WASD / Arrow keys : move
Space             : fire
Shift             : dodge (uses 20 fuel and grants brief invulnerability)
P or Escape       : pause / open the upgrade bay
1–4               : answer a grammar transmission
Enter             : start, restart, or dismiss feedback

No third-party packages are required:

    python grammar_invaders_revised.py
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import tkinter as tk
from typing import Dict, List, Optional, Set, Tuple


WIDTH = 1100
HEIGHT = 760
FPS_MS = 16
FUEL_DODGE_COST = 20.0


@dataclass(frozen=True)
class Question:
    prompt: str
    options: Tuple[str, ...]
    answer: str
    explanation: str
    difficulty: int


@dataclass(frozen=True)
class Upgrade:
    key: str
    name: str
    branch: str
    cost: int
    prereq: Optional[str]
    description: str
    effect: str
    exclusive_group: Optional[str] = None


def round_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float,
               radius: float = 10, **kwargs: object) -> None:
    """Canvas-rounded rectangle built from primitives available in standard Tk."""
    fill = kwargs.get("fill", "")
    outline = kwargs.get("outline", "")
    width = kwargs.get("width", 1)
    stipple = kwargs.get("stipple", "")
    r = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2,
                            fill=fill, outline="", stipple=stipple)
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r,
                            fill=fill, outline="", stipple=stipple)
    for cx, cy in ((x1 + r, y1 + r), (x2 - r, y1 + r),
                   (x1 + r, y2 - r), (x2 - r, y2 - r)):
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                           fill=fill, outline="", stipple=stipple)
    if outline:
        canvas.create_rectangle(x1, y1, x2, y2, fill="",
                                outline=outline, width=width)


@dataclass
class Projectile:
    x: float
    y: float
    dx: float
    dy: float
    damage: int
    width: int = 5
    height: int = 15
    color: str = "#ffe66d"
    homing: float = 0.0
    life: int = 180
    active: bool = True

    def update(self, game: "GrammarInvaders") -> None:
        if self.homing > 0:
            target = game.find_target(self.x, self.y)
            if target is not None:
                tx = target.x + target.size / 2
                ty = target.y + target.size / 2
                distance = max(1.0, math.hypot(tx - self.x, ty - self.y))
                speed = max(6.0, math.hypot(self.dx, self.dy))
                desired_x = (tx - self.x) / distance * speed
                desired_y = (ty - self.y) / distance * speed
                self.dx = self.dx * (1 - self.homing) + desired_x * self.homing
                self.dy = self.dy * (1 - self.homing) + desired_y * self.homing

        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        if self.life <= 0 or self.y < -50 or self.y > HEIGHT + 50 or self.x < -50 or self.x > WIDTH + 50:
            self.active = False


@dataclass
class EnemyShot:
    kind: str
    x: float
    y: float
    dx: float
    dy: float
    radius: float = 6
    homing: float = 0.0
    life: int = 260
    active: bool = True

    def update(self, game: "GrammarInvaders") -> None:
        if self.homing > 0:
            target_x = game.player.x + 18
            target_y = game.player.y + 22
            distance = max(1.0, math.hypot(target_x - self.x, target_y - self.y))
            speed = max(3.2, math.hypot(self.dx, self.dy))
            desired_x = (target_x - self.x) / distance * speed
            desired_y = (target_y - self.y) / distance * speed
            self.dx = self.dx * (1 - self.homing) + desired_x * self.homing
            self.dy = self.dy * (1 - self.homing) + desired_y * self.homing

        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        if self.life <= 0 or self.y < -40 or self.y > HEIGHT + 40 or self.x < -40 or self.x > WIDTH + 40:
            self.active = False

    def draw(self, canvas: tk.Canvas) -> None:
        if self.kind == "web":
            canvas.create_line(self.x - self.dx * 2, self.y - self.dy * 2,
                               self.x + self.dx * 2, self.y + self.dy * 2,
                               fill="#f1ebff", width=2)
            canvas.create_oval(self.x - self.radius, self.y - self.radius,
                               self.x + self.radius, self.y + self.radius,
                               fill="#b99cff", outline="#ffffff")
            canvas.create_line(self.x - self.radius, self.y,
                               self.x + self.radius, self.y,
                               fill="#ffffff", width=1)
        else:
            canvas.create_line(self.x, self.y - 8, self.x, self.y + 8,
                               fill="#ff6c79", width=4)


@dataclass
class TNTSpore:
    x: float
    y: float
    dx: float
    dy: float
    fuse: int = 95
    active: bool = True

    def update(self, game: "GrammarInvaders") -> None:
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.065
        self.fuse -= 1
        if self.fuse <= 0 or self.y > HEIGHT - 75:
            self.active = False
            game.trigger_explosion(self.x, self.y, 88)

    def draw(self, canvas: tk.Canvas) -> None:
        canvas.create_oval(self.x - 13, self.y - 13, self.x + 13, self.y + 13,
                           fill="#8e4138", outline="#ffcd68", width=2)
        canvas.create_rectangle(self.x - 10, self.y - 5, self.x + 10, self.y + 7,
                                fill="#c84b35", outline="#ffe0a3")
        canvas.create_text(self.x, self.y + 1, text="TNT", fill="#fff5cd",
                           font=("Arial", 7, "bold"))
        canvas.create_line(self.x, self.y - 13, self.x + 5, self.y - 20,
                           fill="#ffe66d", width=2)


@dataclass
class TentacleStrike:
    x: float
    warning: int = 48
    active_frames: int = 30
    width: float = 58
    hit_player: bool = False
    active: bool = True

    def update(self, game: "GrammarInvaders") -> None:
        if self.warning > 0:
            self.warning -= 1
            return
        if not self.hit_player:
            px = game.player.x + 18
            py = game.player.y + 22
            if abs(px - self.x) < self.width / 2 + 17 and py < HEIGHT - 45:
                game.player.take_damage()
                self.hit_player = True
        self.active_frames -= 1
        if self.active_frames <= 0:
            self.active = False

    def draw(self, canvas: tk.Canvas) -> None:
        if self.warning > 0:
            canvas.create_line(self.x, 82, self.x, HEIGHT - 48,
                               fill="#b48aff", width=2, dash=(5, 5))
            canvas.create_oval(self.x - self.width / 2, HEIGHT - 116,
                               self.x + self.width / 2, HEIGHT - 56,
                               outline="#d8c7ff", width=2, dash=(4, 3))
        else:
            canvas.create_line(self.x, 75, self.x, HEIGHT - 48,
                               fill="#7b3fa2", width=int(self.width))
            for y in range(100, HEIGHT - 70, 44):
                canvas.create_polygon(self.x - self.width / 2, y,
                                      self.x - self.width / 2 - 15, y + 12,
                                      self.x - self.width / 2, y + 23,
                                      fill="#f0ccff", outline="")
                canvas.create_polygon(self.x + self.width / 2, y,
                                      self.x + self.width / 2 + 15, y + 12,
                                      self.x + self.width / 2, y + 23,
                                      fill="#f0ccff", outline="")


@dataclass
class Explosion:
    x: float
    y: float
    radius: float
    life: int = 24
    damage_checked: bool = False
    active: bool = True

    def update(self, game: "GrammarInvaders") -> None:
        if not self.damage_checked:
            px = game.player.x + 18
            py = game.player.y + 22
            if math.hypot(px - self.x, py - self.y) < self.radius:
                game.player.take_damage()
            self.damage_checked = True
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self, canvas: tk.Canvas) -> None:
        scale = 1 - self.life / 24
        radius = max(8, self.radius * (0.4 + scale * 0.65))
        canvas.create_oval(self.x - radius, self.y - radius,
                           self.x + radius, self.y + radius,
                           outline="#ff884d", width=4)
        canvas.create_oval(self.x - radius * .62, self.y - radius * .62,
                           self.x + radius * .62, self.y + radius * .62,
                           outline="#ffe66d", width=3)


class Enemy:
    """Normal enemies, the original saucer boss, and the special boss types."""

    LEVEL_BOSS_KINDS = {"saucer_boss", "automaton_boss", "squid_boss", "spider_ufo"}
    BOSS_KINDS = LEVEL_BOSS_KINDS | {"spider_minion"}

    def __init__(self, game: "GrammarInvaders", x: float, kind: str,
                 y: Optional[float] = None) -> None:
        self.game = game
        self.x = x
        self.kind = kind
        self.active = True
        self.phase = random.random() * math.tau
        self.cooldown = random.randint(55, 100)
        self.contact_cooldown = 0
        self.attack_timer = 120
        self.summon_timer = 320
        self.lunge_timer = 0
        self.lunge_target: Tuple[float, float] = (x, 110)
        self.start_x = x

        if kind == "saucer_boss":
            self.size = 76
            self.max_health = 30 + game.level * 4
            self.color = "#e94f64"
            self.name = "INVADER SAUCER"
        elif kind == "automaton_boss":
            self.size = 106
            self.max_health = 140 + game.level * 6
            self.color = "#8e5a53"
            self.name = "ROTTING AUTOMATON"
        elif kind == "squid_boss":
            self.size = 128
            self.max_health = 250 + game.level * 7
            self.color = "#7b4bb8"
            self.name = "ABYSSAL SQUID"
        elif kind == "spider_ufo":
            self.size = 172
            self.max_health = 460 + game.level * 9
            self.color = "#6f8c62"
            self.name = "ZOMBIE SPIDER UFO"
        elif kind == "spider_minion":
            self.size = 58
            self.max_health = 34 + game.level * 2
            self.color = "#a68ad7"
            self.name = "WEB MINION"
        elif kind == "tank":
            self.size = 40
            self.max_health = 5 + game.level // 2
            self.color = "#8892a8"
            self.name = "TANK"
        elif kind == "shooter":
            self.size = 34
            self.max_health = 2 + game.level // 3
            self.color = "#d46cff"
            self.name = "SHOOTER"
        elif kind == "zigzag":
            self.size = 32
            self.max_health = 1 + game.level // 4
            self.color = "#ffaf45"
            self.name = "ZIGZAG"
        else:
            self.size = 32
            self.max_health = 1 + game.level // 4
            self.color = "#38d996"
            self.name = "GRUNT"

        self.health = self.max_health
        self.y = -float(self.size) if y is None else y

    @property
    def is_boss(self) -> bool:
        return self.kind in self.BOSS_KINDS

    @property
    def is_level_boss(self) -> bool:
        return self.kind in self.LEVEL_BOSS_KINDS

    def update(self) -> None:
        self.phase += 0.065
        if self.contact_cooldown > 0:
            self.contact_cooldown -= 1

        if self.kind == "grunt":
            self.y += 1.2 + self.game.level * 0.05
        elif self.kind == "zigzag":
            self.y += 1.0 + self.game.level * 0.04
            self.x = self.start_x + math.sin(self.phase * 1.7) * 85
        elif self.kind == "shooter":
            self.y += 0.68 + self.game.level * 0.03
            self.cooldown -= 1
            if self.cooldown <= 0 and 20 < self.y < HEIGHT - 170:
                self.game.enemy_shots.append(EnemyShot("laser", self.x + self.size / 2,
                                                        self.y + self.size, 0.0, 4.5))
                self.cooldown = 95
        elif self.kind == "tank":
            self.y += 0.45
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.game.tnt_spores.append(TNTSpore(self.x + self.size / 2,
                                                      self.y + self.size / 2,
                                                      random.uniform(-1.3, 1.3), 2.8, 82))
                self.cooldown = 185
        elif self.kind == "saucer_boss":
            self._update_saucer()
        elif self.kind == "automaton_boss":
            self._update_automaton()
        elif self.kind == "squid_boss":
            self._update_squid()
        elif self.kind == "spider_ufo":
            self._update_spider_ufo()
        elif self.kind == "spider_minion":
            self._update_spider_minion()

        self.x = max(-self.size, min(WIDTH, self.x))

    def _enter_arena(self, target_y: float) -> bool:
        if self.y < target_y:
            self.y += 1.2
            return True
        return False

    def _update_saucer(self) -> None:
        if self._enter_arena(62):
            return
        self.x = WIDTH / 2 - self.size / 2 + math.sin(self.phase) * 235
        self.cooldown -= 1
        if self.cooldown <= 0:
            self.game.enemy_shots.extend([
                EnemyShot("laser", self.x + self.size * .25, self.y + self.size, -1.2, 5.0),
                EnemyShot("laser", self.x + self.size * .75, self.y + self.size, 1.2, 5.0),
            ])
            self.cooldown = 64

    def _update_automaton(self) -> None:
        if self._enter_arena(72):
            return
        self.x = WIDTH / 2 - self.size / 2 + math.sin(self.phase * .7) * 190
        self.cooldown -= 1
        if self.cooldown <= 0:
            source_x = self.x + self.size / 2
            source_y = self.y + self.size * .72
            target_x = self.game.player.x + 18
            self.game.tnt_spores.append(TNTSpore(source_x, source_y,
                                                  (target_x - source_x) / 86,
                                                  2.0, 96))
            self.cooldown = 96

    def _update_squid(self) -> None:
        if self._enter_arena(85):
            return
        if self.lunge_timer > 0:
            self.x += (self.lunge_target[0] - self.x) * .17
            self.y += (self.lunge_target[1] - self.y) * .17
            self.lunge_timer -= 1
            if self.lunge_timer == 0:
                self.lunge_target = (WIDTH / 2 - self.size / 2, 90)
            return

        self.x = WIDTH / 2 - self.size / 2 + math.sin(self.phase * .75) * 185
        self.attack_timer -= 1
        if self.attack_timer <= 0:
            if random.random() < .58:
                target_x = self.game.player.x + 18
                for offset, delay in ((-100, 42), (0, 56), (100, 70)):
                    strike_x = max(45, min(WIDTH - 45, target_x + offset))
                    self.game.tentacles.append(TentacleStrike(strike_x, warning=delay))
                self.attack_timer = 132
            else:
                self.lunge_target = (max(20, min(WIDTH - self.size - 20,
                                                  self.game.player.x - self.size / 2 + 18)),
                                     max(120, self.game.player.y - 92))
                self.lunge_timer = 28
                self.attack_timer = 170

    def _update_spider_ufo(self) -> None:
        if self._enter_arena(68):
            return
        self.x = WIDTH / 2 - self.size / 2 + math.sin(self.phase * .55) * 210
        self.cooldown -= 1
        self.summon_timer -= 1
        if self.cooldown <= 0:
            for offset in (-42, 0, 42):
                start_x = self.x + self.size / 2 + offset
                self.game.enemy_shots.append(EnemyShot("web", start_x,
                                                        self.y + self.size * .68,
                                                        offset / 45, 3.6,
                                                        radius=8, homing=.105,
                                                        life=225))
            self.cooldown = 84
        if self.summon_timer <= 0:
            existing = sum(1 for e in self.game.enemies if e.active and e.kind == "spider_minion")
            if existing < 3:
                for offset in (-56, 56):
                    self.game.enemies.append(Enemy(self.game,
                                                   self.x + self.size / 2 + offset,
                                                   "spider_minion", self.y + self.size * .6))
            self.summon_timer = 340

    def _update_spider_minion(self) -> None:
        self.y += .4
        self.x += math.sin(self.phase * 1.6) * 1.8
        self.cooldown -= 1
        if self.cooldown <= 0:
            self.game.enemy_shots.append(EnemyShot("web", self.x + self.size / 2,
                                                    self.y + self.size, 0, 3.7,
                                                    radius=6, homing=.07, life=190))
            self.cooldown = 110

    def draw(self, canvas: tk.Canvas) -> None:
        x, y, s = self.x, self.y, self.size
        if self.kind == "grunt":
            canvas.create_polygon(x + s / 2, y, x + s, y + s * .35,
                                  x + s * .76, y + s, x + s * .24, y + s,
                                  x, y + s * .35, fill=self.color, outline="#b8ffe0")
            canvas.create_oval(x + s * .36, y + s * .35, x + s * .64, y + s * .63,
                               fill="#10233b", outline="")
        elif self.kind == "zigzag":
            canvas.create_polygon(x, y, x + s, y, x + s * .5, y + s,
                                  fill=self.color, outline="#ffe5ad")
        elif self.kind == "shooter":
            points: List[float] = []
            for i in range(6):
                angle = math.pi / 3 * i
                points.extend((x + s / 2 + math.cos(angle) * s / 2,
                               y + s / 2 + math.sin(angle) * s / 2))
            canvas.create_polygon(*points, fill=self.color, outline="#f4d6ff")
            canvas.create_oval(x + s * .37, y + s * .37, x + s * .63, y + s * .63,
                               fill="#fff4a3", outline="")
        elif self.kind == "tank":
            round_rect(canvas, x, y, x + s, y + s, radius=10,
                       fill=self.color, outline="#d5dded", width=2)
            canvas.create_rectangle(x + s * .25, y - 7, x + s * .75, y + 3,
                                    fill="#657087", outline="")
        elif self.kind == "saucer_boss":
            round_rect(canvas, x, y, x + s, y + s * .72, radius=18,
                       fill=self.color, outline="#ffb2bc", width=2)
            canvas.create_polygon(x, y + 13, x - 18, y + s * .35, x, y + s * .53,
                                  fill="#a82f55", outline="")
            canvas.create_polygon(x + s, y + 13, x + s + 18, y + s * .35,
                                  x + s, y + s * .53, fill="#a82f55", outline="")
            canvas.create_oval(x + s * .37, y + 12, x + s * .63, y + 36,
                               fill="#ffe66d", outline="")
        elif self.kind == "automaton_boss":
            round_rect(canvas, x, y + 18, x + s, y + s, radius=15,
                       fill="#6b5253", outline="#e6a56d", width=3)
            canvas.create_rectangle(x + 13, y + 5, x + s - 13, y + 48,
                                    fill="#797c6c", outline="#d8e0af", width=2)
            canvas.create_oval(x + 23, y + 15, x + 35, y + 27,
                               fill="#ff846b", outline="")
            canvas.create_oval(x + s - 35, y + 15, x + s - 23, y + 27,
                               fill="#ff846b", outline="")
            for ox, oy in ((8, 55), (s - 22, 68), (s * .45, 76)):
                canvas.create_oval(x + ox, y + oy, x + ox + 16, y + oy + 11,
                                   fill="#9e7f58", outline="#bcf18a")
            canvas.create_line(x + s * .25, y + s, x + s * .18, y + s + 18,
                               fill="#b9c0c9", width=7)
            canvas.create_line(x + s * .75, y + s, x + s * .82, y + s + 18,
                               fill="#b9c0c9", width=7)
        elif self.kind == "squid_boss":
            canvas.create_oval(x, y, x + s, y + s * .72,
                               fill="#7141a3", outline="#efd7ff", width=3)
            canvas.create_oval(x + s * .25, y + s * .22, x + s * .42, y + s * .42,
                               fill="#f4f4ff", outline="#1c1630")
            canvas.create_oval(x + s * .58, y + s * .22, x + s * .75, y + s * .42,
                               fill="#f4f4ff", outline="#1c1630")
            for i, offset in enumerate((-40, -18, 18, 40)):
                start_x = x + s / 2 + offset
                canvas.create_line(start_x, y + s * .58,
                                   start_x + math.sin(self.phase + i) * 25,
                                   y + s + 35, fill="#a371d6", width=12,
                                   smooth=True)
        elif self.kind == "spider_ufo":
            canvas.create_oval(x, y + 24, x + s, y + s * .77,
                               fill="#59734f", outline="#e5d3b0", width=3)
            canvas.create_oval(x + s * .25, y + 2, x + s * .75, y + s * .54,
                               fill="#824c4c", outline="#c3e6a4", width=3)
            canvas.create_oval(x + s * .39, y + 20, x + s * .61, y + 46,
                               fill="#fff071", outline="#2b1821")
            for i in range(8):
                side = -1 if i < 4 else 1
                row = i % 4
                sx = x + (s * .25 if side < 0 else s * .75)
                sy = y + 45 + row * 19
                canvas.create_line(sx, sy, sx + side * 42, sy + 25,
                                   sx + side * 58, sy + 64,
                                   fill="#8f9d6b", width=6, smooth=True)
        else:  # spider_minion
            canvas.create_oval(x, y, x + s, y + s * .68,
                               fill=self.color, outline="#f3e5ff", width=2)
            for side in (-1, 1):
                for row in range(3):
                    sy = y + 16 + row * 12
                    canvas.create_line(x + s / 2, sy, x + s / 2 + side * 30,
                                       sy + 18, fill="#d5c3ff", width=3)

        if self.kind in {"tank", *self.BOSS_KINDS}:
            self.draw_health_bar(canvas)

    def draw_health_bar(self, canvas: tk.Canvas) -> None:
        bar_w = self.size
        canvas.create_rectangle(self.x, self.y - 12, self.x + bar_w, self.y - 7,
                                fill="#351d34", outline="")
        canvas.create_rectangle(self.x, self.y - 12,
                                self.x + bar_w * max(0, self.health) / self.max_health,
                                self.y - 7, fill="#60e890", outline="")


class Player:
    def __init__(self, game: "GrammarInvaders") -> None:
        self.game = game
        self.x = WIDTH / 2 - 18
        self.y = HEIGHT - 100
        self.speed = 5.0
        self.cooldown = 0
        self.rocket_cooldown = 0
        self.anim = 0
        self.max_health = 5
        self.health = 5
        self.shield_charges = 0
        self.damage = 1
        self.fuel = 100.0
        self.max_fuel = 100.0
        self.dodge_timer = 0
        self.i_frames = 0
        self.dodge_dx = 0.0
        self.dodge_dy = -1.0
        self.last_move = (0.0, -1.0)
        self.owned: Set[str] = set()

    def has(self, key: str) -> bool:
        return key in self.owned

    def update(self) -> None:
        self.anim += 1
        self.fuel = min(self.max_fuel, self.fuel + .18)
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.rocket_cooldown > 0:
            self.rocket_cooldown -= 1
        if self.i_frames > 0:
            self.i_frames -= 1

        if self.dodge_timer > 0:
            self.x += self.dodge_dx * 15
            self.y += self.dodge_dy * 15
            self.dodge_timer -= 1
        else:
            dx = float(("d" in self.game.keys or "right" in self.game.keys) -
                       ("a" in self.game.keys or "left" in self.game.keys))
            dy = float(("s" in self.game.keys or "down" in self.game.keys) -
                       ("w" in self.game.keys or "up" in self.game.keys))
            if dx or dy:
                magnitude = math.hypot(dx, dy)
                dx /= magnitude
                dy /= magnitude
                self.last_move = (dx, dy)
                self.x += dx * self.speed
                self.y += dy * self.speed

        self.x = max(0, min(WIDTH - 36, self.x))
        self.y = max(70, min(HEIGHT - 60, self.y))
        if "space" in self.game.keys and self.cooldown == 0:
            self.shoot()
            self.cooldown = max(6, 15 - (2 if self.has("pulse_core") else 0))

    def try_dodge(self) -> None:
        if self.dodge_timer > 0 or self.fuel < FUEL_DODGE_COST:
            return
        dx = float(("d" in self.game.keys or "right" in self.game.keys) -
                   ("a" in self.game.keys or "left" in self.game.keys))
        dy = float(("s" in self.game.keys or "down" in self.game.keys) -
                   ("w" in self.game.keys or "up" in self.game.keys))
        if not dx and not dy:
            dx, dy = self.last_move
        magnitude = max(.1, math.hypot(dx, dy))
        self.dodge_dx = dx / magnitude
        self.dodge_dy = dy / magnitude
        self.last_move = (self.dodge_dx, self.dodge_dy)
        self.fuel -= FUEL_DODGE_COST
        self.dodge_timer = 10
        self.i_frames = 22

    def shoot(self) -> None:
        cx = self.x + 18
        if self.has("front_laser"):
            self.game.projectiles.append(Projectile(cx - 6, self.y - 12, 0, -11.5,
                                                     self.damage + 1, width=12, height=30,
                                                     color="#70f5ff"))
        else:
            self.game.projectiles.append(Projectile(cx - 2.5, self.y - 4, 0, -9.5,
                                                     self.damage, width=5, height=18,
                                                     color="#ffe66d"))

        if self.has("spread_cannon"):
            self.game.projectiles.extend([
                Projectile(cx - 15, self.y + 6, -2.3, -8.7, self.damage,
                           color="#ffe59b"),
                Projectile(cx + 10, self.y + 6, 2.3, -8.7, self.damage,
                           color="#ffe59b"),
            ])
        if self.has("nova_barrage"):
            self.game.projectiles.extend([
                Projectile(cx - 28, self.y + 11, -4.2, -7.8, self.damage,
                           color="#ffbf69"),
                Projectile(cx + 23, self.y + 11, 4.2, -7.8, self.damage,
                           color="#ffbf69"),
            ])
        if self.has("rocket_pod") and self.rocket_cooldown == 0:
            count = 2 if self.has("seeker_array") else 1
            for i in range(count):
                offset = (i - (count - 1) / 2) * 14
                self.game.projectiles.append(Projectile(cx + offset - 4, self.y + 3,
                                                         offset / 16, -6.4, self.damage + 2,
                                                         width=8, height=20, color="#ff8f66",
                                                         homing=.16, life=250))
            self.rocket_cooldown = 48

    def take_damage(self, amount: int = 1) -> bool:
        if self.i_frames > 0:
            return False
        if self.shield_charges > 0:
            self.shield_charges -= 1
            self.i_frames = 12
            return False
        self.health -= amount
        self.i_frames = 36
        if self.health <= 0:
            self.health = 0
            self.game.state = "gameover"
        return True

    def draw(self, canvas: tk.Canvas) -> None:
        if self.i_frames > 0 and self.anim % 4 < 2:
            return
        draw_ship(canvas, self.x + 18, self.y + 22, 1.0, self)
        if self.i_frames > 0:
            canvas.create_oval(self.x - 12, self.y - 15, self.x + 48, self.y + 58,
                               outline="#c2f7ff", width=2, dash=(4, 3))


def draw_ship(canvas: tk.Canvas, cx: float, cy: float, scale: float,
              player: Player) -> None:
    """Draw a visibly different ship for each weapon/defense/mobility route."""
    s = scale
    top = cy - 28 * s
    bottom = cy + 27 * s
    half = 18 * s

    flame = 8 + (5 if player.has("scout_thrusters") else 0)
    if player.has("afterburner"):
        flame += 10
    flame += int(3 * abs(math.sin(player.anim * .35)))
    canvas.create_polygon(cx - 7 * s, bottom, cx + 7 * s, bottom,
                          cx, bottom + flame * s, fill="#ff8c42", outline="")
    if player.has("warp_drive") or player.has("phase_drive"):
        canvas.create_oval(cx - 15 * s, bottom - 3 * s, cx + 15 * s,
                           bottom + 14 * s, outline="#64f2ff", width=max(1, int(2 * s)))

    if player.has("phase_fins"):
        canvas.create_polygon(cx - half, bottom - 8 * s, cx - 30 * s,
                              bottom + 7 * s, cx - 5 * s, top + 13 * s,
                              fill="#3977c8", outline="#8ce9ff")
        canvas.create_polygon(cx + half, bottom - 8 * s, cx + 30 * s,
                              bottom + 7 * s, cx + 5 * s, top + 13 * s,
                              fill="#3977c8", outline="#8ce9ff")

    hull_color = "#4e8fff"
    if player.has("pulse_core"):
        hull_color = "#5bc4ff"
    if player.has("front_laser"):
        hull_color = "#6e9dff"
    if player.has("overcharge"):
        hull_color = "#f6b23c"
    canvas.create_polygon(cx, top, cx + half, bottom, cx, bottom - 9 * s,
                          cx - half, bottom, fill=hull_color, outline="#d9f4ff",
                          width=max(1, int(1.5 * s)))

    if player.has("hull_plating"):
        canvas.create_polygon(cx - 12 * s, top + 20 * s, cx - 4 * s,
                              bottom - 8 * s, cx - 1 * s, bottom - 18 * s,
                              fill="#d4dbe9", outline="")
        canvas.create_polygon(cx + 12 * s, top + 20 * s, cx + 4 * s,
                              bottom - 8 * s, cx + 1 * s, bottom - 18 * s,
                              fill="#d4dbe9", outline="")
    if player.has("reactive_armor"):
        canvas.create_polygon(cx - half, cy + 5 * s, cx - 30 * s, cy + 10 * s,
                              cx - half, cy + 16 * s, fill="#ff6b6b", outline="")
        canvas.create_polygon(cx + half, cy + 5 * s, cx + 30 * s, cy + 10 * s,
                              cx + half, cy + 16 * s, fill="#ff6b6b", outline="")

    if player.has("front_laser"):
        canvas.create_rectangle(cx - 5 * s, top - 14 * s, cx + 5 * s, top + 18 * s,
                                fill="#70f5ff", outline="#f0ffff")
    if player.has("spread_cannon"):
        for offset in (-14, 14):
            canvas.create_rectangle(cx + offset * s - 2 * s, top + 4 * s,
                                    cx + offset * s + 2 * s, top + 22 * s,
                                    fill="#ffe66d", outline="#fff6b0")
    if player.has("nova_barrage"):
        for offset in (-23, 23):
            canvas.create_oval(cx + offset * s - 5 * s, cy + 5 * s,
                               cx + offset * s + 5 * s, cy + 15 * s,
                               fill="#ffbd69", outline="#fff4be")
    if player.has("rocket_pod"):
        for offset in (-19, 19):
            canvas.create_polygon(cx + offset * s - 4 * s, cy + 4 * s,
                                  cx + offset * s + 4 * s, cy + 4 * s,
                                  cx + offset * s, cy - 8 * s,
                                  fill="#ff8f66", outline="#ffe2b6")
    if player.has("seeker_array"):
        canvas.create_arc(cx - 12 * s, cy - 8 * s, cx + 12 * s, cy + 16 * s,
                          start=210, extent=120, style=tk.ARC,
                          outline="#ffda70", width=max(1, int(2 * s)))
    if player.has("pulse_core"):
        canvas.create_oval(cx - 6 * s, cy - 2 * s, cx + 6 * s, cy + 10 * s,
                           fill="#c5f9ff", outline="#ffffff")

    if player.has("aegis_shield"):
        canvas.create_oval(cx - 27 * s, top - 10 * s, cx + 27 * s,
                           bottom + 13 * s, outline="#78dfff", width=max(1, int(2 * s)))
    if player.has("guardian_field"):
        canvas.create_arc(cx - 34 * s, top - 17 * s, cx + 34 * s,
                          bottom + 20 * s, start=25, extent=130,
                          style=tk.ARC, outline="#a9a0ff", width=max(1, int(2 * s)))
        canvas.create_arc(cx - 34 * s, top - 17 * s, cx + 34 * s,
                          bottom + 20 * s, start=205, extent=130,
                          style=tk.ARC, outline="#a9a0ff", width=max(1, int(2 * s)))


def build_question_bank() -> List[Question]:
    """Create 128 fill-in-the-blank questions, grouped by escalating challenge."""
    questions: List[Question] = []

    def add(prompt: str, answer: str, wrong: Tuple[str, str, str],
            explanation: str, difficulty: int) -> None:
        options = (answer, *wrong)
        if len(set(options)) != 4:
            raise ValueError(f"Question needs four different choices: {prompt}")
        questions.append(Question(prompt, options, answer, explanation, difficulty))

    simple_scenes = [
        ("Maya", "calibrate", "calibrates", "calibrated", "calibrating", "the telescope before sunrise"),
        ("Jordan", "catalog", "catalogs", "cataloged", "cataloging", "the fossils in the museum lab"),
        ("the gardener", "trim", "trims", "trimmed", "trimming", "the hedges beside the library"),
        ("Lena", "sort", "sorts", "sorted", "sorting", "the food-bank donations"),
        ("the engineer", "inspect", "inspects", "inspected", "inspecting", "the bridge sensors"),
        ("Omar", "pack", "packs", "packed", "packing", "the supply drones for delivery"),
        ("the librarian", "label", "labels", "labeled", "labeling", "the new map collection"),
        ("the baker", "measure", "measures", "measured", "measuring", "the ingredients for the bread"),
        ("the mechanic", "repair", "repairs", "repaired", "repairing", "the delivery van"),
        ("Rina", "water", "waters", "watered", "watering", "the greenhouse seedlings"),
        ("the captain", "check", "checks", "checked", "checking", "the navigation lights"),
        ("Theo", "record", "records", "recorded", "recording", "the bird calls near the marsh"),
    ]
    for subject, base, present, past, ing, obj in simple_scenes:
        add(f"On most mornings, {subject} ___ {obj}.", present,
            (past, f"is {ing}", f"will {base}"),
            "The phrase 'on most mornings' describes a regular routine.", 1)
        add(f"Yesterday, {subject} ___ {obj}.", past,
            (present, f"is {ing}", f"will {base}"),
            "'Yesterday' tells you the action happened and ended in the past.", 1)
        add(f"Tomorrow, {subject} ___ {obj}.", f"will {base}",
            (present, past, f"is {ing}"),
            "'Tomorrow' points forward, so the form with 'will' fits.", 1)

    ongoing_scenes = [
        ("the students", "are", "were", "rehearse", "rehearsed", "rehearsing", "their debate in the auditorium"),
        ("Serena", "is", "was", "restore", "restored", "restoring", "an old painting in the studio"),
        ("the robots", "are", "were", "assemble", "assembled", "assembling", "the solar-panel frames"),
        ("the chef", "is", "was", "prepare", "prepared", "preparing", "dinner for the festival"),
        ("the hikers", "are", "were", "cross", "crossed", "crossing", "the wooden bridge"),
        ("Niko", "is", "was", "translate", "translated", "translating", "the old letter"),
        ("the musicians", "are", "were", "tune", "tuned", "tuning", "their instruments backstage"),
        ("the pilot", "is", "was", "guide", "guided", "guiding", "the rescue plane through clouds"),
        ("the volunteers", "are", "were", "paint", "painted", "painting", "the community mural"),
        ("Avery", "is", "was", "test", "tested", "testing", "the new water filter"),
        ("the scientists", "are", "were", "monitor", "monitored", "monitoring", "the ocean buoy"),
        ("the drummer", "is", "was", "practice", "practiced", "practicing", "the opening rhythm"),
    ]
    for subject, now_be, then_be, base, past, ing, obj in ongoing_scenes:
        present = base + ("s" if now_be == "is" else "")
        add(f"Right now, {subject} ___ {obj}.", f"{now_be} {ing}",
            (base, past, f"will {base}"),
            "'Right now' means the action is happening at this moment.", 2)
        add(f"When the alarm sounded, {subject} ___ {obj}.", f"{then_be} {ing}",
            (present, past, f"will {base}"),
            "The alarm interrupted an action that was already underway.", 2)
        add(f"At this time tomorrow, {subject} ___ {obj}.", f"will be {ing}",
            (present, past, f"{now_be} {ing}"),
            "The sentence asks what will be happening at a future time.", 2)

    completed_scenes = [
        ("the research team", "has", "map", "mapped", "mapped", "the cave system"),
        ("the technicians", "have", "install", "installed", "installed", "the new signal tower"),
        ("Aisha", "has", "write", "wrote", "written", "the first draft of her speech"),
        ("the hikers", "have", "find", "found", "found", "a safer path through the canyon"),
        ("the mayor", "has", "approve", "approved", "approved", "the park-renovation plan"),
        ("the divers", "have", "collect", "collected", "collected", "samples from the reef"),
        ("Milo", "has", "read", "read", "read", "all the clues in the case file"),
        ("the nurses", "have", "organize", "organized", "organized", "the medical supplies"),
        ("the director", "has", "choose", "chose", "chosen", "the final cast"),
        ("the explorers", "have", "build", "built", "built", "a shelter near the river"),
        ("Inez", "has", "learn", "learned", "learned", "the route to the observatory"),
        ("the players", "have", "practice", "practiced", "practiced", "the new strategy"),
    ]
    for subject, has_have, base, past, participle, obj in completed_scenes:
        add(f"Since January, {subject} ___ {obj}.", f"{has_have} {participle}",
            (past, "are still working", f"will {base}"),
            "'Since January' connects something that started earlier to the present.", 3)
        add(f"Before the storm began, {subject} ___ {obj}.", f"had {participle}",
            (past, f"{has_have} {participle}", f"will have {participle}"),
            "This action was already complete before the later past event.", 3)
        add(f"By next Friday, {subject} ___ {obj}.", f"will have {participle}",
            (f"{has_have} {participle}", past, f"will {base}"),
            "'By next Friday' means it will be complete before that future point.", 3)

    conditional_scenes = [
        ("the sensor", "improve", "improves", "improved", "improving", "improved", "its reading", "the team will repeat the test tomorrow", "the team arrives tomorrow"),
        ("the weather", "clear", "clears", "cleared", "clearing", "cleared", "over the runway", "the pilot will take off", "the pilot reaches the airport"),
        ("Mara", "finish", "finishes", "finished", "finishing", "finished", "the code review", "she will send the update", "the meeting starts tomorrow"),
        ("the gate", "open", "opens", "opened", "opening", "opened", "before noon", "the visitors will enter the garden", "the first tour begins"),
        ("the battery", "charge", "charges", "charged", "charging", "charged", "fully", "the rover will leave the station", "the sun rises tomorrow"),
        ("the bridge crew", "finish", "finishes", "finished", "finishing", "finished", "the safety check", "traffic will return to normal", "the mayor arrives"),
        ("the lab", "confirm", "confirms", "confirmed", "confirming", "confirmed", "the result", "the article will be published", "the editor reviews the report"),
        ("Noah", "find", "finds", "found", "finding", "found", "the missing key", "he will unlock the shed", "the caretaker comes back"),
        ("the crew", "repair", "repairs", "repaired", "repairing", "repaired", "the antenna", "the signal will return", "the broadcast begins tonight"),
        ("the river", "fall", "falls", "fell", "falling", "fallen", "below the marker", "the path will reopen", "the ranger checks it tomorrow"),
    ]
    for subject, base, present, past, ing, participle, obj, result, future_marker in conditional_scenes:
        add(f"If {subject} ___ {obj}, {result}.", present,
            (past, f"will {base}", f"is {ing}"),
            "After 'if,' use the ordinary form even though the result is in the future.", 4)
        add(f"By the time {future_marker}, {subject} ___ {obj}.", f"will have {participle}",
            (present, past, f"will {base}"),
            "The action must be finished before the future event named in the sentence.", 5)

    if len(questions) < 100:
        raise AssertionError("The question bank must contain at least 100 questions.")
    if len({question.prompt for question in questions}) != len(questions):
        raise AssertionError("Every grammar question must have a distinct prompt.")
    return questions


class GrammarInvaders:
    UPGRADES: Tuple[Upgrade, ...] = (
        Upgrade("pulse_core", "Pulse Core", "OFFENSE", 60, None,
                "Faster energy cycling.", "Faster fire rate"),
        Upgrade("front_laser", "Front Laser", "OFFENSE", 115, "pulse_core",
                "One powerful center-mounted beam.", "+1 center-beam damage", "primary_weapon"),
        Upgrade("spread_cannon", "Spread Cannon", "OFFENSE", 105, "pulse_core",
                "Two side shots fan away from the ship.", "+2 side shots", "primary_weapon"),
        Upgrade("rocket_pod", "Lock-On Rocket Pod", "OFFENSE", 145, "pulse_core",
                "Automatically homes in on the nearest target.", "Homing rocket"),
        Upgrade("overcharge", "Overcharge", "OFFENSE", 205, "front_laser",
                "Supercharges the focused weapon.", "+1 damage"),
        Upgrade("nova_barrage", "Nova Barrage", "OFFENSE", 190, "spread_cannon",
                "Adds two wide-angle launchers.", "+2 wide shots"),
        Upgrade("seeker_array", "Seeker Array", "OFFENSE", 210, "rocket_pod",
                "Fires a pair of lock-on rockets.", "Double rockets"),
        Upgrade("hull_plating", "Hull Plating", "DEFENSE", 55, None,
                "Reinforced armor panels.", "+1 max health"),
        Upgrade("aegis_shield", "Aegis Shield", "DEFENSE", 100, "hull_plating",
                "Stores an energy shield charge.", "+1 shield"),
        Upgrade("reactive_armor", "Reactive Armor", "DEFENSE", 115, "hull_plating",
                "Spiked armor resists close danger.", "+1 max health"),
        Upgrade("guardian_field", "Guardian Field", "DEFENSE", 185, "aegis_shield",
                "Adds a second protective charge.", "+2 shields"),
        Upgrade("scout_thrusters", "Scout Thrusters", "MOBILITY", 50, None,
                "Small engines improve handling.", "+1 speed"),
        Upgrade("afterburner", "Afterburner", "MOBILITY", 95, "scout_thrusters",
                "Longer, brighter engine flame.", "+1 speed"),
        Upgrade("phase_fins", "Phase Fins", "MOBILITY", 110, "scout_thrusters",
                "Adds blue stabilizer fins.", "+1 speed"),
        Upgrade("warp_drive", "Warp Drive", "MOBILITY", 195, "afterburner",
                "Cyan warp ring and handling boost.", "+2 speed"),
        Upgrade("phase_drive", "Phase Drive", "MOBILITY", 200, "phase_fins",
                "A second high-speed route.", "+2 speed"),
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Grammar Invaders — Verb Form Mission")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg="#070b22", highlightthickness=0)
        self.canvas.pack()
        self.canvas.focus_set()
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_click)

        self.keys: Set[str] = set()
        self.state = "menu"
        self.player = Player(self)
        self.projectiles: List[Projectile] = []
        self.enemies: List[Enemy] = []
        self.enemy_shots: List[EnemyShot] = []
        self.tnt_spores: List[TNTSpore] = []
        self.tentacles: List[TentacleStrike] = []
        self.explosions: List[Explosion] = []
        self.level = 1
        self.score = 0
        self.kills = 0
        self.kills_this_level = 0
        self.kills_since_quiz = 0
        self.spawn_timer = 0
        self.enemy_cap = 5
        # Number of sequential bosses already released for each five-level milestone.
        self.boss_stages_spawned: Dict[int, int] = {}
        self.banner_timer = 0
        self.pause_message = "Choose a branch, then click an available node."
        self.active_upgrade_branch = "OFFENSE"
        self.upgrade_rects: Dict[str, Tuple[float, float, float, float]] = {}
        self.pause_buttons: Dict[str, Tuple[float, float, float, float]] = {}
        self.branch_tabs: Dict[str, Tuple[float, float, float, float]] = {}
        self.quiz_rects: List[Tuple[float, float, float, float]] = []
        self.current_question: Optional[Question] = None
        self.quiz_choices: List[str] = []
        self.quiz_answer = ""
        self.quiz_feedback = ""
        self.quiz_explanation = ""
        self.quiz_feedback_timer = 0
        self.questions = build_question_bank()
        self.recent_question_prompts: List[str] = []
        self.stars = [
            [random.randrange(WIDTH), random.randrange(HEIGHT), random.choice((1, 1, 1, 2, 2, 3))]
            for _ in range(100)
        ]
        self.loop()

    def reset_game(self) -> None:
        self.player = Player(self)
        self.projectiles.clear()
        self.enemies.clear()
        self.enemy_shots.clear()
        self.tnt_spores.clear()
        self.tentacles.clear()
        self.explosions.clear()
        self.level = 1
        self.score = 0
        self.kills = 0
        self.kills_this_level = 0
        self.kills_since_quiz = 0
        self.spawn_timer = 0
        self.enemy_cap = 5
        self.boss_stages_spawned.clear()
        self.banner_timer = 0
        self.pause_message = "Choose a branch, then click an available node."
        self.active_upgrade_branch = "OFFENSE"
        self.quiz_feedback_timer = 0
        self.current_question = None
        self.recent_question_prompts.clear()
        self.state = "play"
        self.keys.clear()

    def start_game(self) -> None:
        self.reset_game()

    def loop(self) -> None:
        self.update()
        self.draw()
        self.root.after(FPS_MS, self.loop)

    def update(self) -> None:
        for star in self.stars:
            star[1] += star[2] * .35
            if star[1] > HEIGHT:
                star[0] = random.randrange(WIDTH)
                star[1] = 0

        if self.state == "play":
            self.player.update()
            for projectile in self.projectiles:
                projectile.update(self)
            for enemy in list(self.enemies):
                enemy.update()
            self.update_hazards()
            self.spawn_enemies()
            self.handle_collisions()
            self.projectiles = [p for p in self.projectiles if p.active]
            self.enemies = [e for e in self.enemies if e.active]
            self.enemy_shots = [shot for shot in self.enemy_shots if shot.active]
            self.tnt_spores = [spore for spore in self.tnt_spores if spore.active]
            self.tentacles = [tentacle for tentacle in self.tentacles if tentacle.active]
            self.explosions = [explosion for explosion in self.explosions if explosion.active]
            if self.banner_timer > 0:
                self.banner_timer -= 1
        elif self.state == "quiz" and self.quiz_feedback_timer > 0:
            self.quiz_feedback_timer -= 1
            if self.quiz_feedback_timer == 0:
                self.finish_quiz()

    def update_hazards(self) -> None:
        for shot in self.enemy_shots:
            shot.update(self)
            if shot.active and self.circle_hits_player(shot.x, shot.y, shot.radius + 5):
                self.player.take_damage()
                shot.active = False
        for spore in self.tnt_spores:
            spore.update(self)
        for tentacle in self.tentacles:
            tentacle.update(self)
        for explosion in self.explosions:
            explosion.update(self)

    def trigger_explosion(self, x: float, y: float, radius: float) -> None:
        self.explosions.append(Explosion(x, y, radius))

    def circle_hits_player(self, x: float, y: float, radius: float) -> bool:
        return math.hypot((self.player.x + 18) - x, (self.player.y + 22) - y) < radius + 15

    @staticmethod
    def intersects(a: Tuple[float, float, float, float],
                   b: Tuple[float, float, float, float]) -> bool:
        return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and
                a[1] < b[1] + b[3] and a[1] + a[3] > b[1])

    def find_target(self, x: float, y: float) -> Optional[Enemy]:
        targets = [enemy for enemy in self.enemies if enemy.active]
        if not targets:
            return None
        return min(targets, key=lambda enemy: math.hypot(
            enemy.x + enemy.size / 2 - x, enemy.y + enemy.size / 2 - y))

    def active_level_boss(self) -> Optional[Enemy]:
        return next((enemy for enemy in self.enemies
                     if enemy.active and enemy.is_level_boss), None)

    def boss_sequence_for_level(self) -> Tuple[str, ...]:
        """Keep the original saucer every five levels, then add special encounters."""
        if self.level % 5 != 0:
            return ()
        sequence = ["saucer_boss"]
        if self.level == 15:
            sequence.append("automaton_boss")
        elif self.level == 30:
            sequence.append("squid_boss")
        elif self.level == 40:
            sequence.append("spider_ufo")
        return tuple(sequence)

    def spawn_enemies(self) -> None:
        boss_sequence = self.boss_sequence_for_level()
        stage = self.boss_stages_spawned.get(self.level, 0)
        if stage < len(boss_sequence):
            if self.active_level_boss() is None:
                boss_kind = boss_sequence[stage]
                sizes = {"saucer_boss": 76, "automaton_boss": 106,
                         "squid_boss": 128, "spider_ufo": 172}
                self.enemies.append(Enemy(self, WIDTH / 2 - sizes[boss_kind] / 2, boss_kind))
                self.boss_stages_spawned[self.level] = stage + 1
            return

        if self.active_level_boss() is not None:
            return

        self.spawn_timer += 1
        interval = max(28, 72 - self.level * 4)
        if self.spawn_timer < interval or len(self.enemies) >= self.enemy_cap:
            return
        self.spawn_timer = 0
        kinds = ["grunt"]
        if self.level >= 2:
            kinds.append("zigzag")
        if self.level >= 3:
            kinds.append("shooter")
        if self.level >= 4:
            kinds.append("tank")
        self.enemies.append(Enemy(self, random.randint(20, WIDTH - 52), random.choice(kinds)))

    def handle_collisions(self) -> None:
        for projectile in self.projectiles:
            if not projectile.active:
                continue
            pbox = (projectile.x, projectile.y, projectile.width, projectile.height)
            for enemy in self.enemies:
                if not enemy.active:
                    continue
                if self.intersects(pbox, (enemy.x, enemy.y, enemy.size, enemy.size)):
                    projectile.active = False
                    enemy.health -= projectile.damage
                    if enemy.health <= 0:
                        self.defeat_enemy(enemy)
                    break

        pbox = (self.player.x, self.player.y, 36, 48)
        for enemy in self.enemies:
            if not enemy.active:
                continue
            if not enemy.is_boss and enemy.y > HEIGHT + 5:
                enemy.active = False
                self.player.take_damage()
                continue
            if self.intersects(pbox, (enemy.x, enemy.y, enemy.size, enemy.size)):
                if enemy.contact_cooldown == 0:
                    self.player.take_damage()
                    enemy.contact_cooldown = 45
                if not enemy.is_boss:
                    enemy.active = False

    def defeat_enemy(self, enemy: Enemy) -> None:
        if not enemy.active:
            return
        enemy.active = False
        if enemy.is_level_boss:
            self.score += 150
            self.pause_message = f"{enemy.name} defeated. The arena is clear."
            self.kills += 1
            # Bosses do not advance the level counter: this guarantees that a
            # special level can release its requested follow-up boss next.
            return
        elif enemy.kind == "spider_minion":
            self.score += 35
        else:
            self.score += 10

        self.kills += 1
        self.kills_this_level += 1
        self.kills_since_quiz += 1
        if self.kills_this_level >= 6 + self.level:
            self.kills_this_level = 0
            self.level += 1
            self.enemy_cap = min(14, self.enemy_cap + 1)
            self.banner_timer = 110
        if self.kills_since_quiz >= 5:
            self.kills_since_quiz = 0
            self.begin_quiz()

    def question_tier(self) -> int:
        if self.level <= 7:
            return 1
        if self.level <= 15:
            return 2
        if self.level <= 23:
            return 3
        if self.level <= 31:
            return 4
        return 5

    def choose_question(self) -> Question:
        tier = self.question_tier()
        unseen = [question for question in self.questions
                  if question.prompt not in self.recent_question_prompts]
        pool = unseen or self.questions
        current = [question for question in pool if question.difficulty == tier]
        earlier = [question for question in pool if question.difficulty < tier]
        if current and (not earlier or random.random() < .74):
            chosen = random.choice(current)
        else:
            chosen = random.choice(earlier or current or pool)
        self.recent_question_prompts.append(chosen.prompt)
        self.recent_question_prompts = self.recent_question_prompts[-18:]
        return chosen

    def begin_quiz(self) -> None:
        self.current_question = self.choose_question()
        self.quiz_choices = list(self.current_question.options)
        random.shuffle(self.quiz_choices)
        self.quiz_answer = self.current_question.answer
        self.quiz_feedback = ""
        self.quiz_explanation = ""
        self.quiz_feedback_timer = 0
        self.quiz_rects = []
        self.keys.clear()
        self.state = "quiz"

    def answer_quiz(self, index: int) -> None:
        if self.state != "quiz" or self.quiz_feedback_timer > 0:
            return
        if index < 0 or index >= len(self.quiz_choices):
            return
        correct = self.quiz_choices[index] == self.quiz_answer
        if correct:
            self.score += 35
            self.player.health = min(self.player.max_health, self.player.health + 1)
            self.quiz_feedback = "CORRECT! +35 score and +1 hull"
        else:
            self.quiz_feedback = f"NOT QUITE — the answer was: {self.quiz_answer}"
        self.quiz_explanation = self.current_question.explanation if self.current_question else ""
        self.quiz_feedback_timer = 150

    def finish_quiz(self) -> None:
        self.quiz_feedback_timer = 0
        self.quiz_feedback = ""
        self.quiz_explanation = ""
        self.state = "play"

    def group_conflict(self, upgrade: Upgrade) -> bool:
        if not upgrade.exclusive_group:
            return False
        return any(other.key in self.player.owned and
                   other.exclusive_group == upgrade.exclusive_group
                   for other in self.UPGRADES)

    def can_buy(self, upgrade: Upgrade) -> bool:
        return (upgrade.key not in self.player.owned and
                self.score >= upgrade.cost and
                not self.group_conflict(upgrade) and
                (upgrade.prereq is None or upgrade.prereq in self.player.owned))

    def buy_upgrade(self, key: str) -> None:
        upgrade = next((candidate for candidate in self.UPGRADES if candidate.key == key), None)
        if upgrade is None:
            return
        if upgrade.key in self.player.owned:
            self.pause_message = f"{upgrade.name} is already installed."
            return
        if upgrade.prereq and upgrade.prereq not in self.player.owned:
            self.pause_message = "That node is locked. Install its parent first."
            return
        if self.group_conflict(upgrade):
            self.pause_message = "You already chose the other primary weapon route."
            return
        if self.score < upgrade.cost:
            self.pause_message = f"You need {upgrade.cost - self.score} more score for {upgrade.name}."
            return

        self.score -= upgrade.cost
        self.player.owned.add(upgrade.key)
        if upgrade.key in {"scout_thrusters", "afterburner", "phase_fins"}:
            self.player.speed += 1
        elif upgrade.key in {"warp_drive", "phase_drive"}:
            self.player.speed += 2
        elif upgrade.key in {"front_laser", "overcharge"}:
            self.player.damage += 1
        elif upgrade.key in {"hull_plating", "reactive_armor"}:
            self.player.max_health += 1
            self.player.health += 1
        elif upgrade.key == "aegis_shield":
            self.player.shield_charges += 1
        elif upgrade.key == "guardian_field":
            self.player.shield_charges += 2
        self.pause_message = f"Installed {upgrade.name}: {upgrade.effect}"

    def toggle_pause(self) -> None:
        if self.state == "play":
            self.state = "paused"
            self.pause_message = "Paused safely. Bosses and hazards are frozen in place."
            self.keys.clear()
        elif self.state == "paused":
            self.state = "play"
            self.keys.clear()

    def on_key_press(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key in {"p", "escape"} and self.state in {"play", "paused"}:
            self.toggle_pause()
            return
        if self.state == "menu" and key in {"return", "space"}:
            self.start_game()
            return
        if self.state == "gameover" and key == "return":
            self.start_game()
            return
        if self.state == "quiz":
            if key in {"1", "2", "3", "4"}:
                self.answer_quiz(int(key) - 1)
            elif key == "return" and self.quiz_feedback_timer > 0:
                self.finish_quiz()
            return
        if self.state == "play":
            if key.startswith("shift"):
                self.player.try_dodge()
            else:
                self.keys.add(key)

    def on_key_release(self, event: tk.Event) -> None:
        self.keys.discard(event.keysym.lower())

    def on_click(self, event: tk.Event) -> None:
        x, y = event.x, event.y
        if self.state == "menu":
            if self.in_rect(x, y, (385, 545, 715, 610)):
                self.start_game()
        elif self.state == "gameover":
            if self.in_rect(x, y, (390, 505, 710, 570)):
                self.start_game()
        elif self.state == "quiz":
            for index, rect in enumerate(self.quiz_rects):
                if self.in_rect(x, y, rect):
                    self.answer_quiz(index)
                    break
        elif self.state == "paused":
            if self.in_rect(x, y, self.pause_buttons.get("resume", (0, 0, 0, 0))):
                self.toggle_pause()
                return
            if self.in_rect(x, y, self.pause_buttons.get("menu", (0, 0, 0, 0))):
                self.state = "menu"
                self.keys.clear()
                return
            for branch, rect in self.branch_tabs.items():
                if self.in_rect(x, y, rect):
                    self.active_upgrade_branch = branch
                    self.pause_message = f"Viewing the {branch.lower()} tree."
                    return
            for key, rect in self.upgrade_rects.items():
                if self.in_rect(x, y, rect):
                    self.buy_upgrade(key)
                    return

    @staticmethod
    def in_rect(x: float, y: float, rect: Tuple[float, float, float, float]) -> bool:
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def draw(self) -> None:
        self.canvas.delete("all")
        self.draw_background()
        if self.state == "menu":
            self.draw_menu()
            return

        for tentacle in self.tentacles:
            tentacle.draw(self.canvas)
        for explosion in self.explosions:
            explosion.draw(self.canvas)
        for spore in self.tnt_spores:
            spore.draw(self.canvas)
        for enemy in self.enemies:
            enemy.draw(self.canvas)
        for shot in self.enemy_shots:
            shot.draw(self.canvas)
        for projectile in self.projectiles:
            round_rect(self.canvas, projectile.x, projectile.y,
                       projectile.x + projectile.width, projectile.y + projectile.height,
                       radius=3, fill=projectile.color, outline="")
        self.player.draw(self.canvas)
        self.draw_hud()
        if self.banner_timer > 0:
            self.canvas.create_text(WIDTH / 2, 104, text=f"LEVEL {self.level}!",
                                    fill="#ffe66d", font=("Arial", 28, "bold"))
        if self.state == "paused":
            self.draw_pause()
        elif self.state == "quiz":
            self.draw_quiz()
        elif self.state == "gameover":
            self.draw_gameover()

    def draw_background(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#070b22", outline="")
        self.canvas.create_rectangle(0, HEIGHT * .55, WIDTH, HEIGHT,
                                     fill="#10113a", outline="")
        for x, y, size in self.stars:
            color = "#ffffff" if size == 1 else "#9eb8ff"
            self.canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")

    def draw_menu(self) -> None:
        self.canvas.create_text(WIDTH / 2, 185, text="GRAMMAR INVADERS",
                                fill="#eaf7ff", font=("Arial", 45, "bold"))
        self.canvas.create_text(WIDTH / 2, 235, text="VERB FORM MISSION",
                                fill="#64f2ff", font=("Arial", 20, "bold"))
        preview = Player(self)
        preview.anim = 15
        draw_ship(self.canvas, WIDTH / 2, 370, 2.4, preview)
        self.canvas.create_text(WIDTH / 2, 470,
                                text="Defend the sentence stream. Use the form that fits the timeline.",
                                fill="#d8e8ff", font=("Arial", 15))
        self.canvas.create_text(WIDTH / 2, 500,
                                text="Bosses every five levels • Shift dodge uses fuel • Pause for upgrades",
                                fill="#aab6d8", font=("Arial", 13))
        round_rect(self.canvas, 385, 545, 715, 610, radius=18,
                   fill="#2563a5", outline="#64f2ff", width=2)
        self.canvas.create_text(WIDTH / 2, 578, text="START MISSION  [ENTER]",
                                fill="#ffffff", font=("Arial", 20, "bold"))
        self.canvas.create_text(WIDTH / 2, 665,
                                text="WASD / Arrows move   •   SPACE fire   •   SHIFT dodge   •   P pause",
                                fill="#9baad0", font=("Arial", 13))

    def draw_hud(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, 60, fill="#0b1230", outline="#273d78")
        self.canvas.create_text(18, 18, anchor="w", text=f"SCORE {self.score}",
                                fill="#ffe66d", font=("Arial", 15, "bold"))
        self.canvas.create_text(18, 42, anchor="w", text=f"LEVEL {self.level}   KILLS {self.kills}",
                                fill="#c9d8ff", font=("Arial", 12))
        health = "■" * self.player.health + "□" * (self.player.max_health - self.player.health)
        self.canvas.create_text(WIDTH - 18, 18, anchor="e", text=f"HULL {health}",
                                fill="#77f0a2", font=("Arial", 13, "bold"))
        self.canvas.create_text(WIDTH - 18, 42, anchor="e",
                                text=f"SHIELDS {self.player.shield_charges}   [P] PAUSE",
                                fill="#8edfff", font=("Arial", 12))

        fuel_x, fuel_y, fuel_w = WIDTH / 2 - 82, 15, 164
        self.canvas.create_text(fuel_x - 10, fuel_y + 10, anchor="e", text="FUEL",
                                fill="#b8dfff", font=("Arial", 10, "bold"))
        self.canvas.create_rectangle(fuel_x, fuel_y, fuel_x + fuel_w, fuel_y + 18,
                                    fill="#17214b", outline="#80b7ff")
        self.canvas.create_rectangle(fuel_x + 2, fuel_y + 2,
                                    fuel_x + 2 + (fuel_w - 4) * self.player.fuel / self.player.max_fuel,
                                    fuel_y + 16, fill="#64e6f5", outline="")
        self.canvas.create_text(WIDTH / 2, fuel_y + 10, text=f"{int(self.player.fuel)}  [SHIFT: 20]",
                                fill="#071327", font=("Arial", 8, "bold"))

        boss = self.active_level_boss()
        if boss is not None:
            bar_x, bar_w = WIDTH / 2 - 235, 470
            self.canvas.create_text(WIDTH / 2, 81, text=boss.name,
                                    fill="#ffbdca", font=("Arial", 14, "bold"))
            self.canvas.create_rectangle(bar_x, 88, bar_x + bar_w, 101,
                                        fill="#351d34", outline="#ff8ca0")
            self.canvas.create_rectangle(bar_x + 2, 90,
                                        bar_x + 2 + (bar_w - 4) * max(0, boss.health) / boss.max_health,
                                        99, fill="#ef5d77", outline="")

    def draw_pause(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#050817", stipple="gray50", outline="")
        round_rect(self.canvas, 18, 18, WIDTH - 18, HEIGHT - 18, radius=22,
                   fill="#111a3d", outline="#6f8fff", width=2)
        self.canvas.create_text(42, 48, anchor="w", text="PAUSED  •  UPGRADE BAY",
                                fill="#ffffff", font=("Arial", 27, "bold"))
        self.canvas.create_text(42, 79, anchor="w",
                                text="The battlefield is frozen: your boss will not despawn or move while this menu is open.",
                                fill="#aabce8", font=("Arial", 12))

        self.canvas.create_text(130, 126, text="CURRENT SHIP", fill="#64f2ff",
                                font=("Arial", 11, "bold"))
        draw_ship(self.canvas, 130, 188, 1.62, self.player)
        self.canvas.create_text(130, 262, text=f"Score: {self.score}", fill="#ffe66d",
                                font=("Arial", 16, "bold"))
        self.canvas.create_text(130, 288, text=f"Hull: {self.player.health}/{self.player.max_health}",
                                fill="#77f0a2", font=("Arial", 12))
        self.canvas.create_text(130, 310,
                                text=f"Speed: {self.player.speed:g}\nDamage: {self.player.damage}\nFuel dodge: {int(FUEL_DODGE_COST)}",
                                fill="#d8e8ff", font=("Arial", 11), justify="center")

        self.pause_buttons = {
            "resume": (48, 470, 212, 522),
            "menu": (48, 535, 212, 587),
        }
        self.draw_button(self.pause_buttons["resume"], "RESUME", "#2563a5")
        self.draw_button(self.pause_buttons["menu"], "QUIT TO MENU", "#3d315f")
        self.canvas.create_text(130, 655, text=self.pause_message, width=205,
                                fill="#d8e8ff", font=("Arial", 10), justify="center")

        self.upgrade_rects = {}
        self.branch_tabs = {}
        tab_y = 114
        for index, branch in enumerate(("OFFENSE", "DEFENSE", "MOBILITY")):
            x1 = 275 + index * 255
            rect = (x1, tab_y, x1 + 228, tab_y + 38)
            self.branch_tabs[branch] = rect
            selected = branch == self.active_upgrade_branch
            round_rect(self.canvas, *rect, radius=12,
                       fill="#31558d" if selected else "#1b284f",
                       outline="#ffe66d" if selected else "#6f8fff", width=2)
            self.canvas.create_text((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2,
                                    text=branch, fill="#ffffff", font=("Arial", 13, "bold"))

        self.draw_upgrade_tree(self.active_upgrade_branch)

    def draw_upgrade_tree(self, branch: str) -> None:
        branch_upgrades = [upgrade for upgrade in self.UPGRADES if upgrade.branch == branch]
        root = next(upgrade for upgrade in branch_upgrades if upgrade.prereq is None)
        children = [upgrade for upgrade in branch_upgrades if upgrade.prereq == root.key]
        root_rect = (558, 180, 738, 270)
        self.draw_upgrade_card(root, root_rect)

        child_w, child_h, gap = 190, 98, 24
        total_w = len(children) * child_w + (len(children) - 1) * gap
        start_x = 275 + (760 - total_w) / 2
        child_rects: Dict[str, Tuple[float, float, float, float]] = {}
        for index, upgrade in enumerate(children):
            rect = (start_x + index * (child_w + gap), 348,
                    start_x + index * (child_w + gap) + child_w, 348 + child_h)
            child_rects[upgrade.key] = rect
            self.draw_edge(root_rect, rect)
            self.draw_upgrade_card(upgrade, rect)

        for child in children:
            descendants = [upgrade for upgrade in branch_upgrades if upgrade.prereq == child.key]
            if not descendants:
                continue
            parent = child_rects[child.key]
            descendant_w = 180
            for index, upgrade in enumerate(descendants):
                center = (parent[0] + parent[2]) / 2 + (index - (len(descendants) - 1) / 2) * 190
                rect = (center - descendant_w / 2, 545, center + descendant_w / 2, 645)
                self.draw_edge(parent, rect)
                self.draw_upgrade_card(upgrade, rect)

        self.canvas.create_text(650, 698,
                                text="Gold outline = affordable • teal = installed • dim = locked or needs score",
                                fill="#aabce8", font=("Arial", 10))

    def draw_edge(self, parent: Tuple[float, float, float, float],
                  child: Tuple[float, float, float, float]) -> None:
        self.canvas.create_line((parent[0] + parent[2]) / 2, parent[3],
                                (child[0] + child[2]) / 2, child[1],
                                fill="#53679d", width=2)

    def draw_upgrade_card(self, upgrade: Upgrade,
                          rect: Tuple[float, float, float, float]) -> None:
        self.upgrade_rects[upgrade.key] = rect
        owned = upgrade.key in self.player.owned
        unlocked = upgrade.prereq is None or upgrade.prereq in self.player.owned
        conflict = self.group_conflict(upgrade)
        affordable = self.score >= upgrade.cost
        if owned:
            fill, outline, status = "#205a62", "#69f5d0", "INSTALLED"
        elif conflict:
            fill, outline, status = "#292441", "#765e9b", "OTHER ROUTE"
        elif unlocked and affordable:
            fill, outline, status = "#244b78", "#ffe66d", "BUY"
        elif unlocked:
            fill, outline, status = "#252e55", "#7582ad", "NEED SCORE"
        else:
            fill, outline, status = "#1b203c", "#4b557c", "LOCKED"
        x1, y1, x2, y2 = rect
        round_rect(self.canvas, x1, y1, x2, y2, radius=12,
                   fill=fill, outline=outline, width=2)
        self.canvas.create_text((x1 + x2) / 2, y1 + 22, text=upgrade.name,
                                width=x2 - x1 - 16,
                                fill="#ffffff" if unlocked and not conflict else "#a4aace",
                                font=("Arial", 12, "bold"), justify="center")
        self.canvas.create_text((x1 + x2) / 2, y1 + 53,
                                text=f"{status}  •  {upgrade.cost}",
                                fill="#ffe66d" if affordable and not owned and not conflict else "#b8c4e9",
                                font=("Arial", 9, "bold"))
        self.canvas.create_text((x1 + x2) / 2, y1 + 75, text=upgrade.effect,
                                width=x2 - x1 - 14,
                                fill="#aabce8", font=("Arial", 9), justify="center")

    def draw_button(self, rect: Tuple[float, float, float, float],
                    text: str, fill: str) -> None:
        round_rect(self.canvas, *rect, radius=12, fill=fill,
                   outline="#8edfff", width=1)
        self.canvas.create_text((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2,
                                text=text, fill="#ffffff", font=("Arial", 11, "bold"))

    def draw_quiz(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#050817", stipple="gray50", outline="")
        box = (130, 105, WIDTH - 130, HEIGHT - 80)
        round_rect(self.canvas, *box, radius=24, fill="#111a3d",
                   outline="#64f2ff", width=2)
        self.canvas.create_text(WIDTH / 2, 150, text="INCOMING GRAMMAR TRANSMISSION",
                                fill="#ffe66d", font=("Arial", 23, "bold"))
        self.canvas.create_text(WIDTH / 2, 193,
                                text="Fill the blank with the verb form that makes the timeline make sense.",
                                fill="#aabce8", font=("Arial", 13))
        if self.current_question is None:
            return
        self.canvas.create_text(WIDTH / 2, 258, text=self.current_question.prompt,
                                fill="#ffffff", font=("Arial", 22, "bold"),
                                width=780, justify="center")
        self.quiz_rects = []
        for index, choice in enumerate(self.quiz_choices):
            x1 = 205 if index < 2 else 565
            y1 = 335 + (index % 2) * 92
            rect = (x1, y1, x1 + 330, y1 + 65)
            self.quiz_rects.append(rect)
            fill = "#274e78" if self.quiz_feedback_timer == 0 else "#202b52"
            round_rect(self.canvas, *rect, radius=14, fill=fill,
                       outline="#8edfff", width=2)
            self.canvas.create_text((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2,
                                    text=f"{index + 1}. {choice}", fill="#ffffff",
                                    font=("Arial", 15, "bold"), width=305)
        if self.quiz_feedback_timer > 0:
            good = self.quiz_feedback.startswith("CORRECT")
            self.canvas.create_text(WIDTH / 2, 575, text=self.quiz_feedback,
                                    fill="#73f2a2" if good else "#ff8492",
                                    font=("Arial", 18, "bold"), width=800)
            self.canvas.create_text(WIDTH / 2, 615, text=self.quiz_explanation,
                                    fill="#d8e8ff", font=("Arial", 13), width=780)
            self.canvas.create_text(WIDTH / 2, 665,
                                    text="Press ENTER or wait to return to the mission.",
                                    fill="#aabce8", font=("Arial", 12))
        else:
            self.canvas.create_text(WIDTH / 2, 615,
                                    text="Click an answer or press 1, 2, 3, or 4.",
                                    fill="#aabce8", font=("Arial", 13))

    def draw_gameover(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#050817", stipple="gray50", outline="")
        self.canvas.create_text(WIDTH / 2, 250, text="MISSION FAILED",
                                fill="#ff7182", font=("Arial", 48, "bold"))
        self.canvas.create_text(WIDTH / 2, 325,
                                text=f"Final score: {self.score}   •   Kills: {self.kills}",
                                fill="#eaf7ff", font=("Arial", 20))
        round_rect(self.canvas, 390, 505, 710, 570, radius=18,
                   fill="#3d315f", outline="#ff9fbd", width=2)
        self.canvas.create_text(WIDTH / 2, 538, text="PLAY AGAIN  [ENTER]",
                                fill="#ffffff", font=("Arial", 20, "bold"))


def main() -> None:
    root = tk.Tk()
    GrammarInvaders(root)
    root.mainloop()


if __name__ == "__main__":
    main()
