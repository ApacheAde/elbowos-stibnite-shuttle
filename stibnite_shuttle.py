#!/usr/bin/env python3
"""Stibnite Shuttle — neon needle-shaft arcade for ElbowOS. Python 3 + pygame.

Thread a silver shuttle through steel-grey stibnite needles. Scoop amber ore.
A / D or arrows steer. R restarts. Not a ROM, not an emulator.
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv and not RECORD
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if not PLAY:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get(
    "ELBOWOS_MP4", "/workspace/artifacts/STIBNITE_SHUTTLE_ElbowOS.mp4"
)
TITLE, HANDLE = "STIBNITE SHUTTLE", "x.com/ElbowOS"
GRAPHITE = (12, 14, 20)
RIB = (32, 36, 48)
STEEL = (176, 186, 198)
TIP = (255, 208, 48)
AMBER = (255, 146, 36)
CYAN = (52, 236, 214)
SCRAPE = (255, 72, 96)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        try:
            flags = 0 if PLAY else pygame.HIDDEN
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.canvas = pygame.Surface((W, H))
        self.big = pygame.font.SysFont("dejavusans", 68, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 46, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 32, bold=True)
        self.reset()

    def reset(self):
        self.t = 0.0
        self.score = 0
        self.combo = 0
        self.x = W * 0.52
        self.y = 1280
        self.flash = 0.0
        self.scroll = 0.0
        self.gates = []
        self.ores = []
        self.sparks = []
        self.dust = [
            {"x": random.uniform(60, W - 60), "y": random.uniform(0, H),
             "s": random.uniform(40, 120)}
            for _ in range(40)
        ]
        self.next_gate = 0.55
        self.gid = 0
        random.seed(23)
        for y in (160, 620, 1040):
            self.spawn_gate(y)

    def spawn_gate(self, y):
        gap = random.randint(320, 440)
        left = random.randint(90, W - gap - 90)
        self.gid += 1
        self.gates.append(
            {"y": y, "left": left, "gap": gap, "id": self.gid, "cleared": False}
        )
        self.ores.append({
            "x": left + gap * random.uniform(0.32, 0.68),
            "y": y, "taken": False, "gid": self.gid,
        })

    def burst(self, x, y, col):
        for i in range(12):
            a = math.tau * i / 12
            self.sparks.append({
                "x": x, "y": y,
                "vx": math.cos(a) * 320, "vy": math.sin(a) * 320,
                "life": 0.45, "col": col,
            })

    def update(self, dt, keys=None, auto=False):
        self.t += dt
        self.scroll += dt * 180
        self.flash = max(0.0, self.flash - dt)
        speed = 460 + min(200, self.t * 10)
        if auto:
            upcoming = [g for g in self.gates if g["y"] < self.y + 30]
            target = W * 0.5
            if upcoming:
                g = max(upcoming, key=lambda g: g["y"])
                target = g["left"] + g["gap"] * 0.5
                ore = next(
                    (o for o in self.ores if o["gid"] == g["id"] and not o["taken"]),
                    None,
                )
                if ore:
                    target = ore["x"]
            self.x += max(-1.0, min(1.0, (target - self.x) / 64.0)) * 1100 * dt
        else:
            ax = 0
            if keys:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    ax -= 1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    ax += 1
            self.x += ax * 900 * dt
        self.x = max(64, min(W - 64, self.x))
        self.next_gate -= dt
        if self.next_gate <= 0:
            self.spawn_gate(-90)
            self.next_gate = random.uniform(0.68, 0.95)
        for g in self.gates:
            g["y"] += speed * dt
        for o in self.ores:
            o["y"] += speed * dt
        for g in self.gates:
            if g["cleared"] or abs(g["y"] - self.y) > 28:
                continue
            g["cleared"] = True
            in_gap = g["left"] + 22 < self.x < g["left"] + g["gap"] - 22
            if in_gap:
                self.combo += 1
                self.score += 12 + self.combo * 2
                self.burst(self.x, self.y, CYAN)
            else:
                self.combo = 0
                self.flash = 0.28
                self.score = max(0, self.score - 8)
                self.burst(self.x, self.y, SCRAPE)
        for o in self.ores:
            if o["taken"]:
                continue
            if abs(o["y"] - self.y) < 50 and abs(o["x"] - self.x) < 58:
                o["taken"] = True
                self.score += 30
                self.combo += 1
                self.burst(o["x"], o["y"], AMBER)
        self.gates = [g for g in self.gates if g["y"] < H + 140]
        self.ores = [o for o in self.ores if o["y"] < H + 80 and not o["taken"]]
        for s in self.sparks:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["life"] -= dt
        self.sparks = [s for s in self.sparks if s["life"] > 0]
        for d in self.dust:
            d["y"] += d["s"] * dt
            if d["y"] > H:
                d["y"] = -10
                d["x"] = random.uniform(40, W - 40)

    def needle(self, surf, x, y, length, direction):
        tip_x = x + length if direction == 1 else x
        base = x if direction == 1 else x + length
        body = [
            (base, y - 26),
            (tip_x - direction * 48, y - 12),
            (tip_x, y),
            (tip_x - direction * 48, y + 12),
            (base, y + 26),
        ]
        pygame.draw.polygon(surf, (78, 86, 98), body)
        pygame.draw.polygon(surf, STEEL, body, 4)
        pygame.draw.line(surf, (220, 226, 232), (base, y - 8), (tip_x - direction * 50, y - 2), 2)
        pygame.draw.circle(surf, TIP, (int(tip_x), int(y)), 12)
        pygame.draw.circle(surf, (255, 244, 180), (int(tip_x), int(y)), 5)

    def hexagon(self, surf, x, y, r, col):
        pts = [
            (x + math.cos(math.tau * i / 6 - 0.2) * r,
             y + math.sin(math.tau * i / 6 - 0.2) * r)
            for i in range(6)
        ]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (255, 228, 150), pts, 3)

    def shuttle(self, surf, x, y):
        body = [(x, y - 52), (x + 38, y), (x, y + 52), (x - 38, y)]
        pygame.draw.polygon(surf, (210, 218, 226), body)
        pygame.draw.polygon(surf, CYAN, body, 5)
        pygame.draw.circle(surf, CYAN, (x, y), 14)
        pygame.draw.circle(surf, (236, 255, 252), (x, y), 6)
        pygame.draw.polygon(surf, TIP, [(x, y - 70), (x + 10, y - 48), (x - 10, y - 48)])

    def draw(self, surf):
        surf.fill(GRAPHITE)
        for i in range(16):
            yy = int((i * 150 - self.scroll) % (H + 150)) - 40
            pygame.draw.line(surf, RIB, (28, yy), (W - 28, yy), 2)
        pygame.draw.rect(surf, (22, 26, 34), (0, 0, 36, H))
        pygame.draw.rect(surf, (22, 26, 34), (W - 36, 0, 36, H))
        for d in self.dust:
            pygame.draw.circle(surf, (70, 78, 90), (int(d["x"]), int(d["y"])), 3)
        for g in self.gates:
            y = int(g["y"])
            self.needle(surf, 0, y, g["left"], 1)
            self.needle(surf, g["left"] + g["gap"], y, W - (g["left"] + g["gap"]), -1)
        for o in self.ores:
            self.hexagon(surf, int(o["x"]), int(o["y"]), 28, AMBER)
        for s in self.sparks:
            pygame.draw.circle(surf, s["col"], (int(s["x"]), int(s["y"])), 6)
        self.shuttle(surf, int(self.x), int(self.y))
        if self.flash > 0:
            shade = pygame.Surface((W, H), pygame.SRCALPHA)
            shade.fill((255, 60, 80, int(110 * self.flash / 0.28)))
            surf.blit(shade, (0, 0))
        banner = pygame.Surface((W, 300), pygame.SRCALPHA)
        banner.fill((8, 10, 16, 150))
        surf.blit(banner, (0, 0))
        title = self.big.render(TITLE, True, TIP)
        surf.blit(title, title.get_rect(center=(W // 2, 100)))
        score = self.mid.render(f"SCORE  {self.score}", True, CYAN)
        surf.blit(score, score.get_rect(center=(W // 2, 180)))
        combo = self.small.render(f"COMBO  x{self.combo}", True, STEEL)
        surf.blit(combo, combo.get_rect(center=(W // 2, 240)))
        foot = pygame.Surface((W, 180), pygame.SRCALPHA)
        foot.fill((8, 10, 16, 150))
        surf.blit(foot, (0, H - 180))
        hint = self.small.render("A / D   thread the needles", True, STEEL)
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 130)))
        handle = self.mid.render(HANDLE, True, AMBER)
        surf.blit(handle, handle.get_rect(center=(W // 2, H - 70)))

    def play(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(0.05, clock.tick(FPS) / 1000)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            self.update(dt, pygame.key.get_pressed(), auto=False)
            self.draw(self.canvas)
            self.screen.blit(self.canvas, (0, 0))
            pygame.display.flip()
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for _ in range(frames):
                self.update(1 / FPS, auto=True)
                self.draw(self.canvas)
                proc.stdin.write(pygame.image.tobytes(self.canvas, "RGB"))
        finally:
            if proc.stdin:
                proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0 or not os.path.isfile(OUT):
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1600:]}")
        print("wrote", OUT, "frames", frames)
        pygame.quit()


def main():
    game = Game()
    if PLAY:
        game.play()
    else:
        game.record()


if __name__ == "__main__":
    main()
