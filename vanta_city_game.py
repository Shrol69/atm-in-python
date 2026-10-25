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
    surface.blit(font.render(str(text), True, color), pos)


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
        self.player = pygame.Vector2(540, 570)
        self.camera = pygame.Vector2(0, 0)
        self.in_car = False
        self.speed = 0
        self.car = pygame.Vector2(540, 650)
        self.active_job = None
        self.message = "Welcome to Vanta City. Your story starts here."
        self.message_time = 4
        self.cash_piles = [pygame.Vector2(x, y) for x, y in
                           [(420, 690), (810, 520), (1190, 900), (1550, 610), (930, 1190), (1830, 1050)]]
        self.park_rects = [pygame.Rect(900, 300, 210, 170), pygame.Rect(1450, 970, 270, 230), pygame.Rect(330, 1130, 190, 220)]
        self.buildings = []
        self._make_city()
        self.running = True

    def _make_city(self):
        rng = random.Random(8)
        # A readable street grid; blocks between broad avenues.
        for row in range(5):
            for col in range(7):
                x, y = 150 + col * 285, 120 + row * 285
                if any(r.colliderect(pygame.Rect(x, y, 205, 205)) for r in self.park_rects):
                    continue
                self.buildings.append((pygame.Rect(x, y, 205, 205), rng.choice([
                    (89, 102, 111), (125, 107, 87), (93, 100, 94), (116, 94, 81), (83, 103, 112)])))

    def notify(self, text):
        self.message, self.message_time = text, 3.2

    def start(self):
        self.state = "play"
        self.notify("VANTA CITY  •  Follow the gold marker to your next move.")

    def destination(self):
        if self.active_job is None:
            return None
        return {"car": pygame.Vector2(1660, 390), "island": pygame.Vector2(1950, 1320),
                "jet": pygame.Vector2(1720, 260), "yacht": pygame.Vector2(2100, 800),
                "impact": pygame.Vector2(1100, 760)}[JOBS[self.active_job][3]]

    def can_move_to(self, pos, radius=14):
        body = pygame.Rect(int(pos.x-radius), int(pos.y-radius), radius*2, radius*2)
        return not any(body.colliderect(rect) for rect, _ in self.buildings)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        if move.length_squared():
            move = move.normalize()
        if self.state == "play":
            if self.in_car:
                accel = 420 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 290
                self.speed += move.y * accel * dt
                self.speed *= max(0, 1 - dt * (1.5 if move.y else 3.2))
                self.speed = max(-130, min(440, self.speed))
                direction = pygame.Vector2(move.x, 0)
                proposed = self.car.copy()
                proposed.x += direction.x * max(100, abs(self.speed)) * dt
                proposed.y += self.speed * dt
                proposed.x = max(30, min(WORLD_W - 30, proposed.x))
                proposed.y = max(30, min(WORLD_H - 30, proposed.y))
                if self.can_move_to(proposed, 20):
                    self.car.update(proposed)
                else:
                    self.speed = 0
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

    def draw_world(self):
        s = self.screen
        cam = self.camera
        s.fill((58, 89, 76))
        # Asphalt grid and pale lane markings
        for x in range(0, WORLD_W, 285):
            pygame.draw.rect(s, (43, 49, 54), (x - cam.x - 36, -cam.y, 72, HEIGHT + 2))
            for y in range(0, WORLD_H, 48):
                pygame.draw.line(s, (183, 168, 131), (x-cam.x, y-cam.y), (x-cam.x, y+22-cam.y), 2)
        for y in range(0, WORLD_H, 285):
            pygame.draw.rect(s, (43, 49, 54), (-cam.x, y - cam.y - 36, WIDTH + 2, 72))
            for x in range(0, WORLD_W, 48):
                pygame.draw.line(s, (183, 168, 131), (x-cam.x, y-cam.y), (x+22-cam.x, y-cam.y), 2)
        for rect in self.park_rects:
            r = rect.move(-cam.x, -cam.y)
            pygame.draw.rect(s, (66, 111, 77), r, border_radius=14)
            for x in range(r.left+24, r.right-12, 48):
                for y in range(r.top+20, r.bottom-12, 48):
                    pygame.draw.circle(s, (101, 143, 84), (x,y), 10)
        for rect, color in self.buildings:
            r = rect.move(-cam.x, -cam.y)
            if r.right < 0 or r.left > WIDTH or r.bottom < 0 or r.top > HEIGHT:
                continue
            pygame.draw.rect(s, (22, 28, 32), r.move(9, 11), border_radius=5)
            pygame.draw.rect(s, color, r, border_radius=5)
            pygame.draw.rect(s, tuple(min(255, c+28) for c in color), (r.x+8,r.y+8,r.w-16,22), border_radius=3)
            for wx in range(r.x+18, r.right-8, 30):
                for wy in range(r.y+42,r.bottom-8,34):
                    pygame.draw.rect(s, (208, 187, 131), (wx,wy,12,13), border_radius=2)
        for pile in self.cash_piles:
            p = pile - cam
            pygame.draw.circle(s, (15, 23, 20), p, 14)
            pygame.draw.circle(s, GOLD, p, 10)
            label(s, "$", (p.x-5,p.y-9), 17, DARK)
        # Car is available from the start and has a clear silhouette.
        cp = self.car - cam
        pygame.draw.rect(s, (17, 24, 30), (cp.x-24, cp.y-38, 48, 76), border_radius=12)
        pygame.draw.rect(s, (199, 153, 83), (cp.x-19, cp.y-34, 38, 68), border_radius=10)
        pygame.draw.rect(s, (64, 84, 91), (cp.x-14,cp.y-20,28,18),border_radius=5)
        pygame.draw.rect(s, (64, 84, 91), (cp.x-14,cp.y+5,28,16),border_radius=5)
        if not self.in_car:
            p = self.player - cam
            pygame.draw.circle(s,(20,25,29),(p.x,p.y+13),13)
            pygame.draw.circle(s,(232,194,143),(p.x,p.y-3),10)
            pygame.draw.rect(s,(184,63,51),(p.x-9,p.y+2,18,20),border_radius=6)
        dest = self.destination()
        if dest:
            p = dest - cam
            pygame.draw.circle(s, GOLD, p, 34, 3)
            pygame.draw.circle(s, GOLD, p, 7)

    def draw_hud(self):
        s = self.screen
        pygame.draw.rect(s,(12,17,21),(18,18,300,94),border_radius=10)
        label(s,"VANTA CITY",(34,28),25,GOLD)
        label(s,f"CASH   ${self.profile['cash']:,}",(34,59),22)
        label(s,f"REP   {self.profile['rep']}   •   {len(self.profile['completed'])}/5 contracts",(34,84),17,(190,199,196))
        # Compact city map
        box=pygame.Rect(WIDTH-188,18,170,130)
        pygame.draw.rect(s,(12,17,21),box,border_radius=9)
        pygame.draw.rect(s,(55,68,69),box.inflate(-16,-16),border_radius=5)
        for xx in range(box.x+25,box.right-10,29): pygame.draw.line(s,(102,110,105),(xx,box.y+12),(xx,box.bottom-12),2)
        for yy in range(box.y+25,box.bottom-10,27): pygame.draw.line(s,(102,110,105),(box.x+10,yy),(box.right-10,yy),2)
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
                    self.cash_piles=[pygame.Vector2(x,y) for x,y in [(420,690),(810,520),(1190,900),(1550,610),(930,1190),(1830,1050)]]
                    self.active_job=None; self.in_car=False; self.player.update(540,570); self.car.update(540,650); self.state="play"
            elif self.state=="play":
                if event.key==pygame.K_ESCAPE: self.state="pause"
                elif event.key==pygame.K_TAB: self.state="contracts"
                elif event.key in (pygame.K_e,pygame.K_SPACE):
                    if self.in_car:
                        self.in_car=False; self.player.update(self.car.x+48,self.car.y); self.speed=0
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
