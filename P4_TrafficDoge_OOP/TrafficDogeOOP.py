#!/usr/bin/env python3
# traffic_dodge.py
# Turtle “Traffic Dodge”: move the player upward while cars move horizontally.
# Requirements covered:
# - Classes: Player, Car, CarManager, Scoreboard
# - Up arrow to move player up
# - Cars spawn randomly on lanes/directions and move; speed scales with level
# - Collision detection -> game over
# - Reaching top increases level, resets player, speeds up cars
# - Smooth animation via tracer(0)/update()
# Stretch:
# - Pause/resume (P), start screen (Space), persistent high score (highscore.txt)

import time
import random
from turtle import Turtle, Screen

# -----------------------
# Config / constants
# -----------------------
SCREEN_W = 600
SCREEN_H = 600
MARGIN = 40

PLAYER_STEP = 20
PLAYER_START_Y = -SCREEN_H // 2 + MARGIN
FINISH_Y =  SCREEN_H // 2 - MARGIN

LANE_STEP = 40  # space between horizontal lanes
LANES = list(range(PLAYER_START_Y + 20, FINISH_Y + 1, LANE_STEP))

BASE_SPAWN_CHANCE = 0.06  # per frame spawn probability (tune)
BASE_SPEED = 4.0          # base pixels per frame at level 1
SPEED_GROWTH = 0.8        # additive speed per level (tune)
COLLISION_DIST = 24       # distance threshold

HIGHSCORE_FILE = "highscore.txt"

# -----------------------
# Player
# -----------------------
class Player(Turtle):
    def __init__(self):
        super().__init__(shape="turtle")
        self.penup()
        self.setheading(90)
        self.reset_position()

    def reset_position(self):
        self.goto(0, PLAYER_START_Y)

    def move_up(self):
        self.sety(self.ycor() + PLAYER_STEP)

# -----------------------
# Car
# -----------------------
class Car(Turtle):
    def __init__(self, lane_y: int, direction: int):
        """
        direction: +1 for left->right, -1 for right->left
        """
        super().__init__(shape="square")
        self.penup()
        self.shapesize(stretch_wid=1, stretch_len=2)  # rectangle
        self.color(self._rand_color())
        self.y = lane_y
        self.direction = direction
        # start just off-screen
        if direction == 1:
            self.goto(-SCREEN_W//2 - 30, lane_y)
        else:
            self.goto(SCREEN_W//2 + 30, lane_y)

    @staticmethod
    def _rand_color():
        return random.choice(["royal blue", "tomato", "gold", "violet", "lime green", "orange red", "deep pink", "turquoise"])

    def move(self, speed: float):
        self.setx(self.xcor() + self.direction * speed)

    def off_screen(self) -> bool:
        return self.xcor() < -SCREEN_W//2 - 60 or self.xcor() > SCREEN_W//2 + 60

# -----------------------
# Car Manager
# -----------------------
class CarManager:
    def __init__(self):
        self.cars: list[Car] = []
        self.spawn_chance = BASE_SPAWN_CHANCE
        self.level_speed_bonus = 0.0

    def reset(self):
        for c in self.cars:
            c.hideturtle()
        self.cars.clear()
        self.level_speed_bonus = 0.0

    def set_level(self, level: int):
        # increase both spawn and speed slightly as level grows
        self.level_speed_bonus = (level - 1) * SPEED_GROWTH
        # keep spawn chance sensible
        self.spawn_chance = min(BASE_SPAWN_CHANCE + (level - 1) * 0.01, 0.18)

    def maybe_spawn(self):
        if random.random() < self.spawn_chance:
            lane_y = random.choice(LANES)
            direction = random.choice([-1, 1])  # both directions
            self.cars.append(Car(lane_y, direction))

    def move_all(self, base_speed: float = BASE_SPEED):
        speed = base_speed + self.level_speed_bonus
        for c in self.cars:
            c.move(speed)
        # prune off-screen
        self.cars = [c for c in self.cars if not c.off_screen()]

    def collision_with(self, turtle: Turtle) -> bool:
        for c in self.cars:
            if c.distance(turtle) < COLLISION_DIST:
                return True
        return False

# -----------------------
# Scoreboard
# -----------------------
class Scoreboard(Turtle):
    def __init__(self):
        super().__init__(visible=False)
        self.penup()
        self.color("black")
        self.level = 1
        self.high = self._load_highscore()

    # UI helpers
    def draw_hud(self, paused: bool, running: bool):
        self.clear()
        self.goto(-SCREEN_W//2 + 10, SCREEN_H//2 - 30)
        status = "PAUSED" if paused else ("RUNNING" if running else "READY")
        self.write(f"Level: {self.level}   High: {self.high}   [{status}]    (↑=move, P=pause, Q=quit)",
                   align="left", font=("Arial", 12, "normal"))

    def start_screen(self):
        self.clear()
        self.goto(0, 60)
        self.write("Turtle Traffic Dodge", align="center", font=("Arial", 24, "bold"))
        self.goto(0, 20)
        self.write("Reach the top to level up. Avoid the cars!",
                   align="center", font=("Arial", 14, "normal"))
        self.goto(0, -20)
        self.write("Controls: ↑ move up   P pause/resume   Q quit",
                   align="center", font=("Arial", 12, "normal"))
        self.goto(0, -60)
        self.write("Press SPACE to start", align="center", font=("Arial", 14, "bold"))

    def game_over(self):
        self.goto(0, 0)
        self.write("GAME OVER", align="center", font=("Arial", 24, "bold"))
        self.goto(0, -40)
        self.write("Press SPACE to play again, or Q to quit",
                   align="center", font=("Arial", 12, "normal"))

    def level_up(self):
        self.level += 1
        if self.level > self.high:
            self.high = self.level
            self._save_highscore(self.high)

    # persistence
    def _load_highscore(self) -> int:
        try:
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip() or "1")
        except Exception:
            return 1

    def _save_highscore(self, value: int):
        try:
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                f.write(str(value))
        except Exception:
            pass

# -----------------------
# Game Controller
# -----------------------
class Game:
    def __init__(self):
        self.screen = Screen()
        self.screen.setup(width=SCREEN_W, height=SCREEN_H)
        self.screen.title("Turtle Traffic Dodge")
        self.screen.tracer(0)

        self.player = Player()
        self.cars = CarManager()
        self.score = Scoreboard()

        # state flags
        self.running = False    # True while round is active
        self.paused = False
        self.game_over_state = False

        # controls
        self.screen.listen()
        self.screen.onkey(self._on_up, "Up")
        self.screen.onkey(self._toggle_pause, "p")
        self.screen.onkey(self._quit, "q")
        self.screen.onkey(self._start_or_restart, "space")

        # start screen
        self.score.start_screen()
        self.screen.update()

    # input handlers
    def _on_up(self):
        if self.running and not self.paused:
            self.player.move_up()

    def _toggle_pause(self):
        if self.running:
            self.paused = not self.paused
            self.score.draw_hud(self.paused, self.running)
            self.screen.update()

    def _quit(self):
        self.running = False
        self.screen.bye()

    def _start_or_restart(self):
        if not self.running:
            # reset state
            self.player.reset_position()
            self.cars.reset()
            self.score.level = 1
            self.game_over_state = False
            self.running = True
            self.paused = False
            self.loop()

    # main loop
    def loop(self):
        while self.running:
            start = time.perf_counter()

            if not self.paused:
                # HUD
                self.score.draw_hud(self.paused, self.running)

                # spawn & move cars
                self.cars.set_level(self.score.level)
                self.cars.maybe_spawn()
                self.cars.move_all()

                # collision
                if self.cars.collision_with(self.player):
                    self.running = False
                    self.game_over_state = True
                    self.score.game_over()

                # level complete
                if self.player.ycor() >= FINISH_Y:
                    self.score.level_up()
                    self.player.reset_position()

            self.screen.update()

            # frame limiting ~60 fps
            elapsed = time.perf_counter() - start
            sleep_for = max(0.0, (1/60) - elapsed)
            time.sleep(sleep_for)

        # when loop ends (game over or quit)
        if self.game_over_state:
            # wait for SPACE or Q
            while self.game_over_state:
                self.screen.update()
                time.sleep(0.05)

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    game = Game()
    # keep the window alive and process key events
    game.screen.mainloop()
