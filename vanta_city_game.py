"""Vanta City: a small, native, top-down open-world game."""
import json
import math
import random
from pathlib import Path

import pygame

WIDTH, HEIGHT = 1280, 760
WORLD_W, WORLD_H = 2200, 1600
SAVE_FILE = Path.home() / ".vanta_city_save.json"

DARK = (14, 19, 24)
WHITE = (239, 237, 224)
GOLD = (238, 185, 92)

JOBS = [
    ("01  THE FAST LANE", "Deliver a rare supercar to the marina.", 1800, "car"),
    ("02  ISLAND TIME", "Take the chopper to the private island.", 2600, "island"),
    ("03  ABOVE IT ALL", "Reach the helipad in the city hills.", 3400, "jet"),
    ("04  BLUE HORIZON", "Visit the yacht club on the coast.", 4200, "yacht"),
    ("05  CITY OF GOLD", "Build your reputation and own the skyline.", 5500, "impact"),
]


def load_save():
    try:
        data = json.loads(SAVE_FILE.read_text())
        return {"cash": max(0, int(data.get("cash", 25000))),
                "rep": max(0, int(data.get("rep", 0))),
                "completed": list(data.get("completed", []))}
    except (OSError, ValueError, TypeError):
        return {"cash": 25000, "rep": 0, "completed": []}


def save_game(state):
    try:
        SAVE_FILE.write_text(json.dumps(state))
    except OSError:
        pass


def label(surface, text, pos, size=18, color=WHITE, font=None):
    font = font or pygame.font.Font(None, size)
    surface.blit(font.render(str(text), True, color), (int(pos[0]), int(pos[1])))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("VANTA CITY — Open World")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big = pygame.font.Font(None, 64)
        self.small = pygame.font.Font(None, 18)
        self.state = "title"
        self.profile = load_save()
        # Spawn on the avenue that runs through the center of the illustrated map.
        self.player = pygame.Vector2(1360, 640)
        self.camera = pygame.Vector2(0, 0)
        self.in_car = False
        self.speed = 0
        self.heading = 0
        self.walk_clock = 0.0
        self.car = pygame.Vector2(1385, 640)
        map_path = Path(__file__).parent / "assets" / "vanta-city-map.png"
        self.city_art = pygame.image.load(str(map_path)).convert()
        self.city_art = pygame.transform.smoothscale(self.city_art, (WORLD_W, WORLD_H))
        self.city_minimap = pygame.transform.smoothscale(self.city_art, (158, 118))
        self.active_job = None
        self.message = "Welcome to Vanta City. Your story starts here."
        self.message_time = 4
        self.cash_piles = [pygame.Vector2(x, y) for x, y in
                           [(572, 359), (858, 359), (1144, 359), (1716, 359), (1360, 850), (1360, 937)]]
        self.park_rects = [pygame.Rect(900, 300, 210, 170), pygame.Rect(1450, 970, 270, 230), pygame.Rect(330, 1130, 190, 220)]
        self.buildings = []
        self._make_city()
        self.running = True

    def _make_city(self):
        rng = random.Random(8)
        # A readable street grid; blocks between broad avenues.
        for row in range(5):
            for col in range(7):
                x, y = 72 + col * 285, 72 + row * 285
                if any(r.colliderect(pygame.Rect(x, y, 190, 190)) for r in self.park_rects):
                    continue
                self.buildings.append((pygame.Rect(x, y, 190, 190), rng.choice([
                    (89, 102, 111), (125, 107, 87), (93, 100, 94), (116, 94, 81), (83, 103, 112)])))

    def notify(self, text):
        self.message, self.message_time = text, 3.2

    def start(self):
        self.state = "play"
        self.notify("VANTA CITY  •  Follow the gold marker to your next move.")

    def destination(self):
        if self.active_job is None:
            return None
        return {"car": pygame.Vector2(1716, 359), "island": pygame.Vector2(1390, 1335),
                "jet": pygame.Vector2(1716, 359), "yacht": pygame.Vector2(1980, 1280),
                "impact": pygame.Vector2(810, 655)}[JOBS[self.active_job][3]]

    def can_move_to(self, pos, radius=14):
        if pos.x < radius or pos.y < radius or pos.x >= WORLD_W-radius or pos.y >= WORLD_H-radius:
            return False
        # The illustrated map doubles as a simple collision mask: dark neutral
        # pixels are streets, while brighter roofs, parks and water are blocked.
        px = int(pos.x * self.city_art.get_width() / WORLD_W)
        py = int(pos.y * self.city_art.get_height() / WORLD_H)
        red, green, blue, _ = self.city_art.get_at((px, py))
        brightness = (red + green + blue) / 3
        return max(red, green, blue) - min(red, green, blue) < 34 and 28 <= brightness <= 112

    def update(self, dt):
        keys = pygame.key.get_pressed()
        # pygame's key states are bools; convert them before subtraction.
        # bool - bool raises TypeError on Python 3, which stopped the game loop.
        move = pygame.Vector2(
            int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
            int(keys[pygame.K_s]) - int(keys[pygame.K_w]),
        )
        if move.length_squared():
            move = move.normalize()
        if self.state == "play":
            if not self.in_car and move.length_squared():
                self.walk_clock += dt * 12
            if self.in_car:
                accel = 420 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 290
                throttle = int(keys[pygame.K_w]) - int(keys[pygame.K_s])
                steering = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
                self.speed += throttle * accel * dt
                self.speed *= max(0, 1 - dt * (1.25 if throttle else 2.7))
                self.speed = max(-130, min(440, self.speed))
                if abs(self.speed) > 7:
                    self.heading = (self.heading + steering * 118 * dt * (1 if self.speed >= 0 else -1)) % 360
                angle = math.radians(self.heading)
                direction = pygame.Vector2(math.sin(angle), -math.cos(angle))
                proposed = self.car + direction * self.speed * dt
                proposed.x = max(30, min(WORLD_W - 30, proposed.x))
                proposed.y = max(30, min(WORLD_H - 30, proposed.y))
                if self.can_move_to(proposed, 20):
                    self.car.update(proposed)
                else:
                    self.speed *= -0.18
                self.player.update(self.car)
            else:
                proposed = self.player.copy()
                proposed.x += move.x * 235 * dt
                if self.can_move_to(proposed):
                    self.player.x = max(25, min(WORLD_W - 25, proposed.x))
                proposed = self.player.copy()
                proposed.y += move.y * 235 * dt
                if self.can_move_to(proposed):
                    self.player.y = max(25, min(WORLD_H - 25, proposed.y))
            for pile in self.cash_piles[:]:
                if self.player.distance_to(pile) < 34:
                    self.cash_piles.remove(pile)
                    self.profile["cash"] += 500
                    save_game(self.profile)
                    self.notify("+ $500  •  Clean money, clean fit.")
            dest = self.destination()
            if dest and self.player.distance_to(dest) < 72:
                self.finish_job()
            self.camera.x = max(0, min(WORLD_W - WIDTH, self.player.x - WIDTH / 2))
            self.camera.y = max(0, min(WORLD_H - HEIGHT, self.player.y - HEIGHT / 2))
            if self.message_time > 0:
                self.message_time -= dt

    def finish_job(self):
        if self.active_job is None:
            return
        title, _, reward, _ = JOBS[self.active_job]
        if self.active_job not in self.profile["completed"]:
            self.profile["cash"] += reward
            self.profile["rep"] += 1
            self.profile["completed"].append(self.active_job)
            save_game(self.profile)
        self.notify(f"CONTRACT COMPLETE  •  {title}  •  +${reward:,}")
        self.active_job = None

    def exit_car(self):
        angle = math.radians(self.heading)
        forward = pygame.Vector2(math.sin(angle), -math.cos(angle))
        offsets = (forward * 48, -forward * 48, pygame.Vector2(48, 0), pygame.Vector2(-48, 0))
        for offset in offsets:
            candidate = self.car + offset
            if self.can_move_to(candidate):
                self.player.update(candidate)
                self.in_car = False
                self.speed = 0
                return
        self.notify("No safe place to get out here.")

    def draw_world(self):
        s = self.screen
        cam = self.camera
        s.fill((8, 18, 24))
        # The large illustrated city is the actual scrolling playfield.
        s.blit(self.city_art, (-int(cam.x), -int(cam.y)))
        for pile in self.cash_piles:
            p = pile - cam
            center = (int(p.x), int(p.y))
            pulse = 2 + int((pygame.time.get_ticks() // 160) % 3)
            pygame.draw.circle(s, (255, 219, 143), center, 17 + pulse, 2)
            pygame.draw.circle(s, (20, 23, 20), center, 13)
            pygame.draw.circle(s, GOLD, center, 10)
            label(s, "$", (center[0]-4, center[1]-8), 16, DARK)
        # Player vehicle: rotate the metallic coupe along its driving heading.
        cp = self.car - cam
        cp = (int(cp.x), int(cp.y))
        car_image = pygame.Surface((58, 86), pygame.SRCALPHA)
        pygame.draw.ellipse(car_image, (10, 14, 18), (3, 2, 52, 82))
        pygame.draw.rect(car_image, (12, 17, 20), (4, 3, 50, 76), border_radius=15)
        pygame.draw.rect(car_image, (177, 125, 67), (8, 6, 42, 70), border_radius=12)
        pygame.draw.rect(car_image, (224, 184, 113), (13, 10, 32, 6), border_radius=3)
        pygame.draw.rect(car_image, (38, 60, 70), (13, 20, 32, 18), border_radius=5)
        pygame.draw.rect(car_image, (27, 42, 49), (13, 44, 32, 16), border_radius=5)
        pygame.draw.line(car_image, (225, 199, 149), (29, 21), (29, 62), 2)
        for wy in (18, 62):
            pygame.draw.rect(car_image, (9, 12, 14), (0, wy, 7, 13), border_radius=3)
            pygame.draw.rect(car_image, (9, 12, 14), (51, wy, 7, 13), border_radius=3)
        rotated_car = pygame.transform.rotate(car_image, -self.heading)
        s.blit(rotated_car, rotated_car.get_rect(center=cp))
        if not self.in_car:
            p = self.player - cam
            px, py = int(p.x), int(p.y)
            pressed = pygame.key.get_pressed()
            moving = any(pressed[key] for key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d))
            stride = int(math.sin(self.walk_clock) * 3) if moving else 0
            pygame.draw.ellipse(s, (13, 17, 18), (px-13, py+9, 26, 12))
            pygame.draw.line(s, (30, 43, 49), (px-4, py+11), (px-5-stride, py+21), 4)
            pygame.draw.line(s, (30, 43, 49), (px+4, py+11), (px+5+stride, py+21), 4)
            pygame.draw.circle(s, (38, 47, 50), (px, py+7), 10)
            pygame.draw.rect(s, (42, 91, 115), (px-10, py-2, 20, 19), border_radius=6)
            pygame.draw.circle(s, (225, 180, 137), (px, py-8), 8)
            pygame.draw.arc(s, (48, 34, 28), (px-8, py-15, 16, 12), 0, math.pi, 3)
        dest = self.destination()
        if dest:
            p = dest - cam
            center = (int(p.x), int(p.y))
            pulse = 3 + int((pygame.time.get_ticks() // 180) % 5)
            pygame.draw.circle(s, (255, 205, 111), center, 20 + pulse, 2)
            pygame.draw.circle(s, (255, 205, 111), center, 5)

    def draw_hud(self):
        s = self.screen
        pygame.draw.rect(s,(12,17,21),(18,18,300,94),border_radius=10)
        label(s,"VANTA CITY",(34,28),25,GOLD)
        label(s,f"CASH   ${self.profile['cash']:,}",(34,59),22)
        label(s,f"REP   {self.profile['rep']}   •   {len(self.profile['completed'])}/5 contracts",(34,84),17,(190,199,196))
        # Compact city map
        box=pygame.Rect(WIDTH-188,18,170,130)
        pygame.draw.rect(s,(12,17,21),box,border_radius=9)
        s.blit(self.city_minimap, (box.x+6, box.y+6))
        pygame.draw.rect(s,(12,17,21),box,2,border_radius=9)
        pp=(box.x+12+self.player.x/WORLD_W*(box.w-24),box.y+12+self.player.y/WORLD_H*(box.h-24))
        pygame.draw.circle(s,GOLD,(int(pp[0]),int(pp[1])),5)
        if self.destination():
            d=self.destination(); dp=(box.x+12+d.x/WORLD_W*(box.w-24),box.y+12+d.y/WORLD_H*(box.h-24))
            pygame.draw.circle(s,(235,86,63),(int(dp[0]),int(dp[1])),4)
        if self.in_car:
            pygame.draw.rect(s,(12,17,21),(18,HEIGHT-74,190,52),border_radius=9)
            label(s,f"SPEED  {int(abs(self.speed)*.45)} MPH",(32,HEIGHT-59),22,GOLD)
        if self.message_time>0:
            w=min(WIDTH-60,max(340,self.font.size(self.message)[0]+36))
            rect=pygame.Rect((WIDTH-w)//2,HEIGHT-88,w,43)
            pygame.draw.rect(s,(13,19,22),rect,border_radius=8)
            label(s,self.message,(rect.x+16,rect.y+12),18)

    def draw_title(self):
        self.screen.fill((16,25,32))
        art=Path(__file__).parent/"assets"/"vanta-city-keyart.png"
        if art.exists():
            try:
                img=pygame.image.load(str(art)).convert()
                img=pygame.transform.smoothscale(img,(WIDTH,HEIGHT))
                self.screen.blit(img,(0,0))
                shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); shade.fill((5,10,15,125)); self.screen.blit(shade,(0,0))
            except pygame.error: pass
        label(self.screen,"VANTA CITY",(70,120),self.big.get_height()+4,GOLD,self.big)
        label(self.screen,"YOUR NAME. YOUR CITY. YOUR RULES.",(74,184),25)
        label(self.screen,"A native open-world game",(76,226),20,(214,215,207))
        pygame.draw.rect(self.screen,(15,22,26),(72,520,520,150),border_radius=12)
        label(self.screen,"ENTER  PLAY",(98,544),28,GOLD)
        label(self.screen,"WASD move / drive     E enter or exit car",(98,582),19)
        label(self.screen,"SHIFT boost     TAB contracts     ESC pause",(98,610),19)
        label(self.screen,f"Saved profile  •  ${self.profile['cash']:,}  •  {self.profile['rep']} reputation",(98,640),17,(191,200,197))

    def draw_contracts(self):
        shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); shade.fill((0,0,0,190)); self.screen.blit(shade,(0,0))
        label(self.screen,"CITY CONTRACTS",(90,66),48,GOLD,self.big)
        label(self.screen,"Choose a job. Reach its marker to collect the payout.",(94,126),22)
        for i,(title,desc,reward,_) in enumerate(JOBS):
            y=185+i*91
            done=i in self.profile["completed"]
            pygame.draw.rect(self.screen,(30,39,43) if not done else (28,53,45),(90,y,680,72),border_radius=9)
            label(self.screen,f"[{i+1}]  {title}",(111,y+12),24,GOLD if not done else (126,193,146))
            label(self.screen,desc,(111,y+42),18,(215,218,209))
            label(self.screen,"DONE" if done else f"${reward:,}",(670,y+23),21)
        label(self.screen,"Press 1–5 to accept a contract  •  TAB close",(94,665),20)

    def draw(self):
        if self.state == "title":
            self.draw_title()
        else:
            self.draw_world()
            self.draw_hud()
            if self.state == "contracts":
                self.draw_contracts()
            elif self.state == "pause":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 170))
                self.screen.blit(overlay, (0, 0))
                label(self.screen, "PAUSED", (WIDTH // 2 - 94, HEIGHT // 2 - 52), 56, GOLD, self.big)
                label(self.screen, "ESC resume  •  N new game  •  Q quit", (WIDTH // 2 - 170, HEIGHT // 2 + 14), 23)
        pygame.display.flip()

    def handle(self,event):
        if event.type==pygame.QUIT: self.running=False
        elif event.type==pygame.VIDEORESIZE:
            self.screen=pygame.display.set_mode((max(900,event.w),max(600,event.h)),pygame.RESIZABLE)
        elif event.type==pygame.KEYDOWN:
            if self.state=="title":
                if event.key in (pygame.K_RETURN,pygame.K_SPACE): self.start()
                elif event.key==pygame.K_q: self.running=False
            elif self.state=="contracts":
                if event.key==pygame.K_TAB: self.state="play"
                elif pygame.K_1<=event.key<=pygame.K_5:
                    index=event.key-pygame.K_1
                    if index<len(JOBS): self.active_job=index; self.state="play"; self.notify(f"Contract accepted: {JOBS[index][0]}")
            elif self.state=="pause":
                if event.key==pygame.K_ESCAPE: self.state="play"
                elif event.key==pygame.K_q: self.running=False
                elif event.key==pygame.K_n:
                    self.profile={"cash":25000,"rep":0,"completed":[]}; save_game(self.profile)
                    self.cash_piles=[pygame.Vector2(x,y) for x,y in [(572,359),(858,359),(1144,359),(1716,359),(1360,850),(1360,937)]]
                    self.active_job=None; self.in_car=False; self.speed=0; self.heading=0; self.player.update(1360,640); self.car.update(1385,640); self.state="play"
            elif self.state=="play":
                if event.key==pygame.K_ESCAPE: self.state="pause"
                elif event.key==pygame.K_TAB: self.state="contracts"
                elif event.key in (pygame.K_e,pygame.K_SPACE):
                    if self.in_car:
                        self.exit_car()
                    elif self.player.distance_to(self.car)<100:
                        self.in_car=True; self.player.update(self.car)
                    else: self.notify("Get close to your car to enter it.")
                elif event.key==pygame.K_F5: save_game(self.profile); self.notify("Game saved.")

    def run(self):
        while self.running:
            dt=min(self.clock.tick(60)/1000,0.04)
            for event in pygame.event.get(): self.handle(event)
            self.update(dt)
            self.draw()
        save_game(self.profile)
        pygame.quit()


if __name__=="__main__":
    Game().run()
