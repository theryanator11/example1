"""Grammar Invaders - a Python/Tkinter remake.

Controls
--------
WASD / Arrow keys : move
Space             : fire
P or Escape       : pause / open the upgrade bay
1-4               : answer a multiple-choice quiz
Enter             : start, restart, or dismiss a quiz result

The program intentionally uses only Python's standard library, so it can be
run with:

    python grammar_invaders.py
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


@dataclass(frozen=True)
class Question:
    prompt: str
    options: Tuple[str, ...]
    answer: str
    explanation: str


@dataclass(frozen=True)
class Upgrade:
    key: str
    name: str
    branch: str
    cost: int
    prereq: Optional[str]
    description: str
    effect: str


def round_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float,
               radius: float = 10, **kwargs: object) -> None:
    """Draw a rounded rectangle with primitives supported by standard Tk."""
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
    active: bool = True

    def update(self) -> None:
        self.x += self.dx
        self.y += self.dy
        if self.y < -30 or self.x < -30 or self.x > WIDTH + 30:
            self.active = False


class Enemy:
    """A small self-contained enemy with several movement and attack styles."""

    def __init__(self, game: "GrammarInvaders", x: float, kind: str) -> None:
        self.game = game
        self.x = x
        self.y = -50.0
        self.kind = kind
        self.active = True
        self.phase = random.random() * math.tau
        self.cooldown = random.randint(45, 100)

        if kind == "boss":
            self.size = 74
            self.max_health = 28 + game.level * 4
            self.color = "#e94f64"
        elif kind == "tank":
            self.size = 40
            self.max_health = 5 + game.level // 2
            self.color = "#8892a8"
        elif kind == "shooter":
            self.size = 34
            self.max_health = 2 + game.level // 3
            self.color = "#d46cff"
        elif kind == "zigzag":
            self.size = 32
            self.max_health = 1 + game.level // 4
            self.color = "#ffaf45"
        else:
            self.size = 32
            self.max_health = 1 + game.level // 4
            self.color = "#38d996"

        self.health = self.max_health
        self.start_x = x

    def update(self) -> None:
        self.phase += 0.07
        if self.kind == "grunt":
            self.y += 1.2 + self.game.level * 0.05
        elif self.kind == "zigzag":
            self.y += 1.0 + self.game.level * 0.04
            self.x = self.start_x + math.sin(self.phase * 1.7) * 85
        elif self.kind == "shooter":
            self.y += 0.68 + self.game.level * 0.03
            self.cooldown -= 1
            if self.cooldown <= 0 and 20 < self.y < HEIGHT - 170:
                self.game.enemy_lasers.append(
                    [self.x + self.size / 2, self.y + self.size, 0.0, 4.5]
                )
                self.cooldown = 95
        elif self.kind == "tank":
            self.y += 0.45
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.game.bombs.append([self.x + self.size / 2, self.y + self.size / 2])
                self.cooldown = 150
        else:  # boss
            if self.y < 60:
                self.y += 0.8
            else:
                self.x = WIDTH / 2 - self.size / 2 + math.sin(self.phase) * 230
                self.cooldown -= 1
                if self.cooldown <= 0:
                    self.game.enemy_lasers.append(
                        [self.x + self.size * 0.25, self.y + self.size, -1.2, 5.0]
                    )
                    self.game.enemy_lasers.append(
                        [self.x + self.size * 0.75, self.y + self.size, 1.2, 5.0]
                    )
                    self.cooldown = 65

        self.x = max(-self.size, min(WIDTH, self.x))

    def draw(self, canvas: tk.Canvas) -> None:
        x, y, s = self.x, self.y, self.size
        if self.kind == "grunt":
            canvas.create_polygon(
                x + s / 2, y, x + s, y + s * 0.35,
                x + s * 0.76, y + s, x + s * 0.24, y + s,
                x, y + s * 0.35, fill=self.color, outline="#b8ffe0", width=1
            )
            canvas.create_oval(x + s * 0.36, y + s * 0.35, x + s * 0.64,
                               y + s * 0.63, fill="#10233b", outline="")
        elif self.kind == "zigzag":
            canvas.create_polygon(x, y, x + s, y, x + s * 0.5, y + s,
                                  fill=self.color, outline="#ffe5ad", width=1)
        elif self.kind == "shooter":
            points = []
            for i in range(6):
                angle = math.pi / 3 * i
                points.extend((x + s / 2 + math.cos(angle) * s / 2,
                               y + s / 2 + math.sin(angle) * s / 2))
            canvas.create_polygon(*points, fill=self.color, outline="#f4d6ff", width=1)
            canvas.create_oval(x + s * .37, y + s * .37, x + s * .63,
                               y + s * .63, fill="#fff4a3", outline="")
        elif self.kind == "tank":
            round_rect(canvas, x, y, x + s, y + s, radius=10,
                                     fill=self.color, outline="#d5dded", width=2)
            canvas.create_rectangle(x + s * .25, y - 7, x + s * .75, y + 3,
                                    fill="#657087", outline="")
        else:
            round_rect(canvas, x, y, x + s, y + s * .72, radius=18,
                                     fill=self.color, outline="#ffb2bc", width=2)
            canvas.create_polygon(x, y + 13, x - 18, y + s * .35, x, y + s * .53,
                                  fill="#a82f55", outline="")
            canvas.create_polygon(x + s, y + 13, x + s + 18, y + s * .35,
                                  x + s, y + s * .53, fill="#a82f55", outline="")
            canvas.create_oval(x + s * .37, y + 12, x + s * .63, y + 36,
                               fill="#ffe66d", outline="")

        if self.kind in {"tank", "boss"}:
            bar_w = s
            canvas.create_rectangle(x, y - 12, x + bar_w, y - 7,
                                    fill="#351d34", outline="")
            canvas.create_rectangle(x, y - 12,
                                    x + bar_w * max(0, self.health) / self.max_health,
                                    y - 7, fill="#60e890", outline="")


class Player:
    def __init__(self, game: "GrammarInvaders") -> None:
        self.game = game
        self.x = WIDTH / 2 - 18
        self.y = HEIGHT - 100
        self.speed = 5.0
        self.cooldown = 0
        self.anim = 0
        self.max_health = 5
        self.health = 5
        self.shield_charges = 0
        self.damage = 1
        self.owned: Set[str] = set()

    def has(self, key: str) -> bool:
        return key in self.owned

    def update(self) -> None:
        keys = self.game.keys
        if "w" in keys or "up" in keys:
            self.y -= self.speed
        if "s" in keys or "down" in keys:
            self.y += self.speed
        if "a" in keys or "left" in keys:
            self.x -= self.speed
        if "d" in keys or "right" in keys:
            self.x += self.speed

        self.x = max(0, min(WIDTH - 36, self.x))
        self.y = max(70, min(HEIGHT - 60, self.y))
        self.anim += 1
        if self.cooldown > 0:
            self.cooldown -= 1
        if "space" in keys and self.cooldown == 0:
            self.shoot()
            self.cooldown = max(6, 15 - (2 if self.has("pulse_core") else 0))

    def shoot(self) -> None:
        cx = self.x + 18
        color = "#ffe66d" if not self.has("heavy_beam") else "#ff9f68"
        width = 7 if self.has("heavy_beam") else 5
        self.game.projectiles.append(
            Projectile(cx - width / 2, self.y - 4, 0, -9.5,
                       self.damage, width=width, height=18, color=color)
        )
        if self.has("twin_lasers"):
            self.game.projectiles.extend([
                Projectile(cx - 14, self.y + 7, -1.4, -9.0, self.damage),
                Projectile(cx + 9, self.y + 7, 1.4, -9.0, self.damage),
            ])
        if self.has("nova_barrage"):
            self.game.projectiles.extend([
                Projectile(cx - 25, self.y + 10, -3.0, -8.2, self.damage),
                Projectile(cx + 20, self.y + 10, 3.0, -8.2, self.damage),
            ])

    def take_damage(self, amount: int = 1) -> None:
        if self.shield_charges > 0:
            self.shield_charges -= 1
            self.game.pause_message = "Your shield absorbed the hit."
            return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.game.state = "gameover"

    def draw(self, canvas: tk.Canvas) -> None:
        draw_ship(canvas, self.x + 18, self.y + 22, 1.0, self)


def draw_ship(canvas: tk.Canvas, cx: float, cy: float, scale: float,
              player: Player) -> None:
    """Draw the ship from its upgrade set; every branch has visual effects."""
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
    if player.has("warp_drive"):
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
    if player.has("heavy_beam"):
        hull_color = "#b16cff"
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

    if player.has("twin_lasers"):
        for offset in (-12, 12):
            canvas.create_rectangle(cx + offset * s - 2 * s, top + 4 * s,
                                    cx + offset * s + 2 * s, top + 22 * s,
                                    fill="#ffe66d", outline="#fff6b0")
    if player.has("heavy_beam"):
        canvas.create_rectangle(cx - 5 * s, top - 7 * s, cx + 5 * s, top + 17 * s,
                                fill="#ff9f68", outline="#ffe4a3")
    if player.has("nova_barrage"):
        for offset in (-22, 22):
            canvas.create_oval(cx + offset * s - 5 * s, cy + 6 * s,
                               cx + offset * s + 5 * s, cy + 16 * s,
                               fill="#ffdb68", outline="#fff4be")

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


class GrammarInvaders:
    UPGRADES: Tuple[Upgrade, ...] = (
        Upgrade("pulse_core", "Pulse Core", "OFFENSE", 60, None,
                "Faster energy cycling.", "-2 fire cooldown"),
        Upgrade("twin_lasers", "Twin Lasers", "OFFENSE", 105, "pulse_core",
                "Adds two side cannons.", "+2 side shots"),
        Upgrade("heavy_beam", "Heavy Beam", "OFFENSE", 120, "pulse_core",
                "A larger, harder-hitting cannon.", "+1 damage"),
        Upgrade("nova_barrage", "Nova Barrage", "OFFENSE", 190, "twin_lasers",
                "Adds two angled launchers.", "+2 nova shots"),
        Upgrade("overcharge", "Overcharge", "OFFENSE", 220, "heavy_beam",
                "Turns the hull gold.", "+1 damage"),
        Upgrade("hull_plating", "Hull Plating", "DEFENSE", 55, None,
                "Reinforced armor panels.", "+1 max health"),
        Upgrade("aegis_shield", "Aegis Shield", "DEFENSE", 100, "hull_plating",
                "Stores one energy shield charge.", "+1 shield"),
        Upgrade("reactive_armor", "Reactive Armor", "DEFENSE", 115, "hull_plating",
                "Spiked armor punishes collisions.", "+1 max health"),
        Upgrade("guardian_field", "Guardian Field", "DEFENSE", 185, "aegis_shield",
                "A second shield charge and halo.", "+2 shield"),
        Upgrade("scout_thrusters", "Scout Thrusters", "MOBILITY", 50, None,
                "Small engines improve handling.", "+1 speed"),
        Upgrade("afterburner", "Afterburner", "MOBILITY", 95, "scout_thrusters",
                "Longer, brighter engine flame.", "+1 speed"),
        Upgrade("phase_fins", "Phase Fins", "MOBILITY", 110, "scout_thrusters",
                "Adds blue stabilizer fins.", "+1 speed"),
        Upgrade("warp_drive", "Warp Drive", "MOBILITY", 195, "afterburner",
                "Cyan warp ring and speed.", "+2 speed"),
        Upgrade("phase_drive", "Phase Drive", "MOBILITY", 200, "phase_fins",
                "A second mobility route.", "+2 speed"),
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Grammar Invaders — Verb Tense Mission")
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
        self.enemy_lasers: List[List[float]] = []
        self.bombs: List[List[float]] = []
        self.level = 1
        self.score = 0
        self.kills = 0
        self.kills_this_level = 0
        self.kills_since_quiz = 0
        self.spawn_timer = 0
        self.enemy_cap = 5
        self.boss_spawned = False
        self.banner_timer = 0
        self.pause_message = "Click an available node to spend score."
        self.upgrade_rects: Dict[str, Tuple[float, float, float, float]] = {}
        self.pause_buttons: Dict[str, Tuple[float, float, float, float]] = {}
        self.quiz_rects: List[Tuple[float, float, float, float]] = []
        self.current_question: Optional[Question] = None
        self.quiz_choices: List[str] = []
        self.quiz_answer = ""
        self.quiz_feedback = ""
        self.quiz_explanation = ""
        self.quiz_feedback_timer = 0
        self.questions = self.load_questions()
        self.stars = [
            [random.randrange(WIDTH), random.randrange(HEIGHT), random.choice((1, 1, 1, 2, 2, 3))]
            for _ in range(100)
        ]
        self.loop()

    @staticmethod
    def load_questions() -> List[Question]:
        return [
            Question("By the time the bell rang, Maya ___ her project.",
                      ("had finished", "has finished", "finishes", "will finish"),
                      "had finished", "The past perfect shows an earlier past action."),
            Question("Every Saturday, Luis ___ basketball with his cousins.",
                      ("practices", "practiced", "is practicing", "has practiced"),
                      "practices", "The simple present describes a repeated habit."),
            Question("Right now, the astronauts ___ the satellite.",
                      ("are repairing", "repaired", "repair", "have repaired"),
                      "are repairing", "The present progressive describes an action happening now."),
            Question("Last night, we ___ a documentary about volcanoes.",
                      ("watched", "watch", "are watching", "have watched"),
                      "watched", "The simple past describes a completed past action."),
            Question("Next month, our class ___ the science museum.",
                      ("will visit", "visits", "visited", "has visited"),
                      "will visit", "The simple future describes an action that will happen later."),
            Question("Since June, Priya ___ at the animal shelter.",
                      ("has volunteered", "volunteered", "is volunteering", "will volunteer"),
                      "has volunteered", "The present perfect connects a past action to the present."),
            Question("Which sentence uses the past progressive tense?",
                      ("The dog was chasing the ball.", "The dog chases the ball.",
                       "The dog has chased the ball.", "The dog will chase the ball."),
                      "The dog was chasing the ball.", "Was chasing is past progressive."),
            Question("Which sentence uses the future perfect tense?",
                      ("By Friday, we will have finished the model.",
                       "By Friday, we finish the model.",
                       "By Friday, we finished the model.",
                       "By Friday, we are finishing the model."),
                      "By Friday, we will have finished the model.",
                      "Will have finished is future perfect."),
            Question("When I arrived, the movie ___.",
                      ("had already started", "already starts", "is already starting", "will already start"),
                      "had already started", "The movie started before another past event."),
            Question("At 6 p.m. tomorrow, I ___ home from work.",
                      ("will be driving", "drove", "have driven", "drive"),
                      "will be driving", "The future progressive describes an action in progress in the future."),
            Question("They ___ three chapters so far this week.",
                      ("have read", "read yesterday", "are reading yesterday", "will read yesterday"),
                      "have read", "Have read is present perfect and fits so far this week."),
            Question("She ___ for an hour before the bus finally came.",
                      ("had been waiting", "waits", "will wait", "has waited tomorrow"),
                      "had been waiting", "Had been waiting is past perfect progressive."),
            Question("We ___ for the competition since September.",
                      ("have been practicing", "practiced tomorrow", "will practice yesterday", "practice last year"),
                      "have been practicing", "Have been practicing is present perfect progressive."),
            Question("Which sentence has a verb in the simple present tense?",
                      ("The train leaves at noon.", "The train left at noon.",
                       "The train is leaving at noon.", "The train will leave at noon."),
                      "The train leaves at noon.", "Leaves is simple present; it can describe a schedule."),
            Question("The teacher ___ the test papers before class began.",
                      ("had copied", "copies", "is copying", "will copy"),
                      "had copied", "Past perfect fits an action completed before another past action."),
            Question("I ___ this book twice already.",
                      ("have read", "read tomorrow", "am reading yesterday", "will read last week"),
                      "have read", "Already connects the completed action to the present."),
            Question("The runners ___ around the track when it started to rain.",
                      ("were jogging", "jog", "have jogged", "will jog"),
                      "were jogging", "Were jogging is past progressive."),
            Question("By the end of the semester, Nia ___ all six novels.",
                      ("will have read", "reads", "read", "is reading"),
                      "will have read", "Will have read is future perfect."),
            Question("Choose the sentence with correct tense consistency.",
                      ("I opened the door and saw the lights were flashing.",
                       "I opened the door and see the lights were flashing.",
                       "I open the door and saw the lights are flashing.",
                       "I will open the door and saw the lights flash."),
                      "I opened the door and saw the lights were flashing.",
                      "The sentence keeps the past-time frame consistent."),
            Question("The chef ___ dinner when the fire alarm rang.",
                      ("was preparing", "prepares", "has prepared", "will prepare"),
                      "was preparing", "Was preparing shows an ongoing past action interrupted by another event."),
        ]

    def reset_game(self) -> None:
        self.player = Player(self)
        self.projectiles.clear()
        self.enemies.clear()
        self.enemy_lasers.clear()
        self.bombs.clear()
        self.level = 1
        self.score = 0
        self.kills = 0
        self.kills_this_level = 0
        self.kills_since_quiz = 0
        self.spawn_timer = 0
        self.enemy_cap = 5
        self.boss_spawned = False
        self.banner_timer = 0
        self.pause_message = "Click an available node to spend score."
        self.quiz_feedback_timer = 0
        self.current_question = None
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
            star[1] += star[2] * 0.35
            if star[1] > HEIGHT:
                star[0] = random.randrange(WIDTH)
                star[1] = 0

        if self.state == "play":
            self.player.update()
            for projectile in self.projectiles:
                projectile.update()
            for enemy in self.enemies:
                enemy.update()
            self.update_enemy_projectiles()
            self.spawn_enemies()
            self.handle_collisions()
            self.projectiles = [p for p in self.projectiles if p.active]
            self.enemies = [e for e in self.enemies if e.active]
            if self.banner_timer > 0:
                self.banner_timer -= 1
        elif self.state == "quiz" and self.quiz_feedback_timer > 0:
            self.quiz_feedback_timer -= 1
            if self.quiz_feedback_timer == 0:
                self.finish_quiz()

    def update_enemy_projectiles(self) -> None:
        for laser in self.enemy_lasers:
            laser[0] += laser[2]
            laser[1] += laser[3]
        player_box = (self.player.x, self.player.y, 36, 48)
        kept_lasers = []
        for laser in self.enemy_lasers:
            if laser[1] > HEIGHT + 30:
                continue
            if self.intersects(player_box, (laser[0] - 3, laser[1] - 7, 6, 14)):
                self.player.take_damage()
                continue
            kept_lasers.append(laser)
        self.enemy_lasers = kept_lasers

        kept_bombs = []
        for bomb in self.bombs:
            bomb[1] += 2.2
            if bomb[1] >= HEIGHT - 100:
                if math.hypot(bomb[0] - (self.player.x + 18),
                              bomb[1] - (self.player.y + 22)) < 58:
                    self.player.take_damage()
                continue
            kept_bombs.append(bomb)
        self.bombs = kept_bombs

    @staticmethod
    def intersects(a: Tuple[float, float, float, float],
                   b: Tuple[float, float, float, float]) -> bool:
        return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and
                a[1] < b[1] + b[3] and a[1] + a[3] > b[1])

    def spawn_enemies(self) -> None:
        self.spawn_timer += 1
        interval = max(28, 72 - self.level * 4)
        if self.spawn_timer < interval or len(self.enemies) >= self.enemy_cap:
            return
        self.spawn_timer = 0
        if self.level >= 5 and self.level % 5 == 0 and not self.boss_spawned:
            self.enemies.append(Enemy(self, WIDTH / 2 - 37, "boss"))
            self.boss_spawned = True
            return
        kinds = ["grunt"]
        if self.level >= 2:
            kinds.append("zigzag")
        if self.level >= 3:
            kinds.append("shooter")
        if self.level >= 4:
            kinds.append("tank")
        x = random.randint(20, WIDTH - 52)
        self.enemies.append(Enemy(self, x, random.choice(kinds)))

    def handle_collisions(self) -> None:
        for projectile in self.projectiles:
            if not projectile.active:
                continue
            pbox = (projectile.x, projectile.y, projectile.width, projectile.height)
            for enemy in self.enemies:
                if not enemy.active:
                    continue
                ebox = (enemy.x, enemy.y, enemy.size, enemy.size)
                if self.intersects(pbox, ebox):
                    projectile.active = False
                    enemy.health -= projectile.damage
                    if enemy.health <= 0:
                        self.defeat_enemy(enemy)
                    break

        pbox = (self.player.x, self.player.y, 36, 48)
        for enemy in self.enemies:
            if not enemy.active:
                continue
            if enemy.y > HEIGHT + 5:
                enemy.active = False
                self.player.take_damage()
                continue
            if self.intersects(pbox, (enemy.x, enemy.y, enemy.size, enemy.size)):
                enemy.active = False
                self.player.take_damage()

    def defeat_enemy(self, enemy: Enemy) -> None:
        enemy.active = False
        self.score += 35 if enemy.kind == "boss" else 10
        self.kills += 1
        self.kills_this_level += 1
        self.kills_since_quiz += 1
        if self.kills_this_level >= 6 + self.level:
            self.kills_this_level = 0
            self.level += 1
            self.enemy_cap = min(14, self.enemy_cap + 1)
            self.banner_timer = 110
            self.boss_spawned = False
        if self.kills_since_quiz >= 5:
            self.kills_since_quiz = 0
            self.begin_quiz()

    def begin_quiz(self) -> None:
        self.current_question = random.choice(self.questions)
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
            self.quiz_feedback = "CORRECT! +35 score and +1 health"
        else:
            self.quiz_feedback = f"NOT QUITE — the answer was: {self.quiz_answer}"
        self.quiz_explanation = self.current_question.explanation if self.current_question else ""
        self.quiz_feedback_timer = 150

    def finish_quiz(self) -> None:
        self.quiz_feedback_timer = 0
        self.quiz_feedback = ""
        self.quiz_explanation = ""
        self.state = "play"

    def can_buy(self, upgrade: Upgrade) -> bool:
        return (upgrade.key not in self.player.owned and
                self.score >= upgrade.cost and
                (upgrade.prereq is None or upgrade.prereq in self.player.owned))

    def buy_upgrade(self, key: str) -> None:
        upgrade = next((u for u in self.UPGRADES if u.key == key), None)
        if upgrade is None:
            return
        if upgrade.key in self.player.owned:
            self.pause_message = f"{upgrade.name} is already installed."
            return
        if upgrade.prereq and upgrade.prereq not in self.player.owned:
            self.pause_message = "That node is locked. Install its parent first."
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
        elif upgrade.key == "pulse_core":
            pass
        elif upgrade.key in {"heavy_beam", "overcharge"}:
            self.player.damage += 1
        elif upgrade.key == "hull_plating":
            self.player.max_health += 1
            self.player.health += 1
        elif upgrade.key == "reactive_armor":
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
            self.pause_message = "Click an available node to spend score."
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
            for i, rect in enumerate(self.quiz_rects):
                if self.in_rect(x, y, rect):
                    self.answer_quiz(i)
                    break
        elif self.state == "paused":
            if self.in_rect(x, y, self.pause_buttons.get("resume", (0, 0, 0, 0))):
                self.toggle_pause()
                return
            if self.in_rect(x, y, self.pause_buttons.get("menu", (0, 0, 0, 0))):
                self.state = "menu"
                self.keys.clear()
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

        for enemy in self.enemies:
            enemy.draw(self.canvas)
        for bomb in self.bombs:
            self.canvas.create_oval(bomb[0] - 8, bomb[1] - 8, bomb[0] + 8,
                                    bomb[1] + 8, fill="#ff4d8d", outline="#ffc1dd")
        for laser in self.enemy_lasers:
            self.canvas.create_line(laser[0], laser[1] - 8, laser[0], laser[1] + 8,
                                    fill="#ff6c79", width=4)
        for projectile in self.projectiles:
            round_rect(self.canvas, projectile.x, projectile.y,
                                          projectile.x + projectile.width,
                                          projectile.y + projectile.height,
                                          radius=3, fill=projectile.color, outline="")
        self.player.draw(self.canvas)
        self.draw_hud()
        if self.banner_timer > 0:
            self.canvas.create_text(WIDTH / 2, 105, text=f"LEVEL {self.level}!",
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
        self.canvas.create_text(WIDTH / 2, 190, text="GRAMMAR INVADERS",
                                fill="#eaf7ff", font=("Arial", 45, "bold"))
        self.canvas.create_text(WIDTH / 2, 240, text="VERB TENSE MISSION",
                                fill="#64f2ff", font=("Arial", 20, "bold"))
        preview = Player(self)
        preview.anim = 15
        draw_ship(self.canvas, WIDTH / 2, 370, 2.4, preview)
        self.canvas.create_text(WIDTH / 2, 470,
                                text="Defend the sentence stream. Answer verb-tense questions to refuel.",
                                fill="#d8e8ff", font=("Arial", 15))
        self.canvas.create_text(WIDTH / 2, 500,
                                text="Upgrade branches are available only from the pause menu.",
                                fill="#aab6d8", font=("Arial", 13))
        round_rect(self.canvas, 385, 545, 715, 610, radius=18,
                                      fill="#2563a5", outline="#64f2ff", width=2)
        self.canvas.create_text(WIDTH / 2, 578, text="START MISSION  [ENTER]",
                                fill="#ffffff", font=("Arial", 20, "bold"))
        self.canvas.create_text(WIDTH / 2, 665,
                                text="WASD / Arrows move   •   SPACE fire   •   P or ESC pause",
                                fill="#9baad0", font=("Arial", 13))

    def draw_hud(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, 58, fill="#0b1230", outline="#273d78")
        self.canvas.create_text(18, 19, anchor="w", text=f"SCORE {self.score}",
                                fill="#ffe66d", font=("Arial", 15, "bold"))
        self.canvas.create_text(18, 42, anchor="w", text=f"LEVEL {self.level}   KILLS {self.kills}",
                                fill="#c9d8ff", font=("Arial", 12))
        health = "■" * self.player.health + "□" * (self.player.max_health - self.player.health)
        self.canvas.create_text(WIDTH - 18, 19, anchor="e", text=f"HULL {health}",
                                fill="#77f0a2", font=("Arial", 13, "bold"))
        self.canvas.create_text(WIDTH - 18, 42, anchor="e",
                                text=f"SHIELDS {self.player.shield_charges}   [P] PAUSE",
                                fill="#8edfff", font=("Arial", 12))

    def draw_pause(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#050817", stipple="gray50", outline="")
        round_rect(self.canvas, 18, 18, WIDTH - 18, HEIGHT - 18, radius=22,
                                      fill="#111a3d", outline="#6f8fff", width=2)
        self.canvas.create_text(42, 48, anchor="w", text="PAUSED  •  UPGRADE BAY",
                                fill="#ffffff", font=("Arial", 27, "bold"))
        self.canvas.create_text(42, 79, anchor="w",
                                text="Spend score here between waves. Click a node after its parent is installed.",
                                fill="#aabce8", font=("Arial", 12))

        self.canvas.create_text(120, 125, text="CURRENT SHIP", fill="#64f2ff",
                                font=("Arial", 11, "bold"))
        draw_ship(self.canvas, 120, 185, 1.65, self.player)
        self.canvas.create_text(120, 255, text=f"Score: {self.score}", fill="#ffe66d",
                                font=("Arial", 16, "bold"))
        self.canvas.create_text(120, 282, text=f"Hull: {self.player.health}/{self.player.max_health}",
                                fill="#77f0a2", font=("Arial", 12))
        self.canvas.create_text(120, 304, text=f"Speed: {self.player.speed:g}   Damage: {self.player.damage}",
                                fill="#d8e8ff", font=("Arial", 11))

        self.pause_buttons = {
            "resume": (42, 470, 198, 520),
            "menu": (42, 532, 198, 582),
        }
        self.draw_button(self.pause_buttons["resume"], "RESUME", "#2563a5")
        self.draw_button(self.pause_buttons["menu"], "QUIT TO MENU", "#3d315f")
        self.canvas.create_text(120, 635, text=self.pause_message, width=210,
                                fill="#d8e8ff", font=("Arial", 10), justify="center")

        branch_x = {"OFFENSE": 250, "DEFENSE": 535, "MOBILITY": 820}
        for branch, x in branch_x.items():
            self.canvas.create_text(x + 115, 112, text=branch, fill="#64f2ff",
                                    font=("Arial", 15, "bold"))
            branch_upgrades = [u for u in self.UPGRADES if u.branch == branch]
            root = next(u for u in branch_upgrades if u.prereq is None)
            first = [u for u in branch_upgrades if u.prereq == root.key]
            final = [u for u in branch_upgrades if u.prereq in {u2.key for u2 in first}]
            root_rect = (x + 58, 138, x + 172, 207)
            self.draw_upgrade_card(root, root_rect)
            for i, upgrade in enumerate(first):
                rect = (x + 4 + i * 132, 270, x + 122 + i * 132, 339)
                self.draw_upgrade_card(upgrade, rect)
                self.draw_edge(root_rect, rect)
            for i, upgrade in enumerate(final):
                parent = next((u for u in first if u.key == upgrade.prereq), first[0])
                parent_index = first.index(parent)
                rect = (x + 4 + parent_index * 132, 405, x + 122 + parent_index * 132, 474)
                self.draw_upgrade_card(upgrade, rect)
                parent_rect = (x + 4 + parent_index * 132, 270,
                               x + 122 + parent_index * 132, 339)
                self.draw_edge(parent_rect, rect)

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
        affordable = self.score >= upgrade.cost
        if owned:
            fill, outline, status = "#205a62", "#69f5d0", "OWNED"
        elif unlocked and affordable:
            fill, outline, status = "#244b78", "#ffe66d", "BUY"
        elif unlocked:
            fill, outline, status = "#252e55", "#7582ad", "NEED SCORE"
        else:
            fill, outline, status = "#1b203c", "#4b557c", "LOCKED"
        x1, y1, x2, y2 = rect
        round_rect(self.canvas, x1, y1, x2, y2, radius=11,
                                      fill=fill, outline=outline, width=2)
        title = upgrade.name.replace(" ", "\n")
        self.canvas.create_text((x1 + x2) / 2, y1 + 22, text=title,
                                fill="#ffffff" if unlocked else "#7d87a9",
                                font=("Arial", 10, "bold"), justify="center")
        self.canvas.create_text((x1 + x2) / 2, y1 + 51,
                                text=f"{status}  •  {upgrade.cost}",
                                fill="#ffe66d" if affordable and not owned else "#b8c4e9",
                                font=("Arial", 8, "bold"))
        self.canvas.create_text((x1 + x2) / 2, y1 + 64, text=upgrade.effect,
                                fill="#aabce8", font=("Arial", 7))

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
                                text="Choose the verb tense that completes the sentence.",
                                fill="#aabce8", font=("Arial", 13))
        if not self.current_question:
            return
        self.canvas.create_text(WIDTH / 2, 258, text=self.current_question.prompt,
                                fill="#ffffff", font=("Arial", 22, "bold"),
                                width=780, justify="center")
        self.quiz_rects = []
        for i, choice in enumerate(self.quiz_choices):
            x1 = 205 if i < 2 else 565
            y1 = 335 + (i % 2) * 92
            rect = (x1, y1, x1 + 330, y1 + 65)
            self.quiz_rects.append(rect)
            fill = "#274e78" if self.quiz_feedback_timer == 0 else "#202b52"
            round_rect(self.canvas, *rect, radius=14, fill=fill,
                                          outline="#8edfff", width=2)
            label = f"{i + 1}. {choice}"
            self.canvas.create_text((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2,
                                    text=label, fill="#ffffff", font=("Arial", 15, "bold"),
                                    width=305)
        if self.quiz_feedback_timer > 0:
            good = self.quiz_feedback.startswith("CORRECT")
            self.canvas.create_text(WIDTH / 2, 575, text=self.quiz_feedback,
                                    fill="#73f2a2" if good else "#ff8492",
                                    font=("Arial", 18, "bold"), width=800)
            self.canvas.create_text(WIDTH / 2, 615, text=self.quiz_explanation,
                                    fill="#d8e8ff", font=("Arial", 13), width=780)
            self.canvas.create_text(WIDTH / 2, 665, text="Press ENTER or wait to return to the mission.",
                                    fill="#aabce8", font=("Arial", 12))
        else:
            self.canvas.create_text(WIDTH / 2, 615, text="Click an answer or press 1, 2, 3, or 4.",
                                    fill="#aabce8", font=("Arial", 13))

    def draw_gameover(self) -> None:
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#050817", stipple="gray50", outline="")
        self.canvas.create_text(WIDTH / 2, 250, text="MISSION FAILED",
                                fill="#ff7182", font=("Arial", 48, "bold"))
        self.canvas.create_text(WIDTH / 2, 325, text=f"Final score: {self.score}   •   Kills: {self.kills}",
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
