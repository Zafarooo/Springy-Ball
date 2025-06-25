# Springy Ball – mit Skin-Wechsler
import pygame, random, sys, time, os, json

class Settings:
    WIDTH, HEIGHT = 400, 600
    FPS = 60
    IMAGE_PATH = "images"
    HIGHSCORE_FILE = "highscore.json"
    SOUND_PATH = "sounds"

class Ball:
    def __init__(self, x, y, image):
        self.x, self.y = x, y
        self.vx, self.vy = 0, 0
        self.radius = 20
        self.gravity = 0.5
        self.jump_strength = -14
        self.teleporting = False
        self.teleport_time = 0
        self.image = image
        self.rect = image.get_rect(center=(self.x, self.y)) if image else None

    def move(self):
        if self.teleporting and time.time() - self.teleport_time < 2:
            return
        self.teleporting = False
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.x = max(self.radius, min(Settings.WIDTH - self.radius, self.x))

    def draw(self, screen):
        if self.image:
            self.rect.center = (int(self.x), int(self.y))
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.circle(screen, (0, 0, 255), (int(self.x), int(self.y)), self.radius)

class Platform:
    WIDTH, HEIGHT = 100, 25
    def __init__(self, x, y, speed, typ, images):
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.speed = speed
        self.type = typ
        self.image = images.get(typ)
        self.jumps = 0
        self.max_jumps = 1 if typ == "fragile" else float("inf")

    def move(self):
        self.rect.x += self.speed
        if self.rect.left <= 0 or self.rect.right >= Settings.WIDTH:
            self.speed *= -1

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            color = {"normal": (0, 200, 0), "fragile": (200, 0, 0), "teleport": (128, 0, 128)}.get(self.type)
            pygame.draw.rect(screen, color, self.rect)

class Game:
    def __init__(self):
        pygame.mixer.init()
        pygame.init()
        self.screen = pygame.display.set_mode((Settings.WIDTH, Settings.HEIGHT))
        pygame.display.set_caption("Springy Ball")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.day_mode = True
        self.skin_index = 0
        self.images = self.load_images()
        self.sounds = self.load_sounds()
        self.highscore = self.load_highscore()
        self.reset()

    def load_images(self):
        def load(name, size):
            path = os.path.join(Settings.IMAGE_PATH, name)
            try: return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
            except: return None
        return {
            "background_day": load("hinter1.png", (Settings.WIDTH, Settings.HEIGHT)),
            "background_night": load("hinter2.png", (Settings.WIDTH + 100, Settings.HEIGHT + 100)),
            "ball1": load("ball1.png", (60, 60)),
            "ball2": load("ball2.png", (60, 60)),
            "ball3": load("ball3.png", (60, 60)),
            "normal": load("plattform1.png", (Platform.WIDTH, Platform.HEIGHT)),
            "fragile": load("plattform2.png", (Platform.WIDTH, Platform.HEIGHT)),
            "teleport": load("plattform3.png", (Platform.WIDTH, Platform.HEIGHT))
        }

    def load_sounds(self):
        def load(name):
            path = os.path.join(Settings.SOUND_PATH, name)
            try: return pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Fehler beim Laden von {name}: {e}")
                return None
        return {
            "jump": load("jump.mp3"),
            "teleport": load("teleport.mp3"),
            "gameover": load("gameover.mp3")
        }

    def load_highscore(self):
        if os.path.exists(Settings.HIGHSCORE_FILE):
            with open(Settings.HIGHSCORE_FILE, 'r') as f:
                return json.load(f).get("highscore", 0)
        return 0

    def save_highscore(self):
        if self.score > self.highscore:
            with open(Settings.HIGHSCORE_FILE, 'w') as f:
                json.dump({"highscore": self.score}, f)

    def reset(self):
        self.score = 0
        self.game_over = False
        self.paused = True
        self.platforms = []
        self.generate_platforms()
        base = self.platforms[0]
        ball_key = ["ball1", "ball2", "ball3"][self.skin_index]
        self.ball = Ball(base.rect.centerx, base.rect.top - 40, self.images[ball_key])

    def generate_platforms(self):
        self.platforms.clear()
        y = Settings.HEIGHT - 50
        for i in range(8):
            x = random.randint(0, Settings.WIDTH - Platform.WIDTH)
            speed = 0 if i == 0 else random.choice([-1, 1]) * random.uniform(1.0, 2.0)
            typ = "normal" if i == 0 else random.choices(["normal", "fragile", "teleport"], [0.6, 0.3, 0.1])[0]
            self.platforms.append(Platform(x, y, speed, typ, self.images))
            y -= 70

    def run(self):
        while True:
            self.handle_events()
            if not self.paused and not self.game_over:
                self.update()
            self.draw()
            self.clock.tick(Settings.FPS)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.save_highscore()
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE: self.paused = False
                if e.key == pygame.K_p and not self.game_over: self.paused = not self.paused
                if e.key == pygame.K_r and self.game_over: self.reset()
                if e.key == pygame.K_s and self.game_over:
                    self.skin_index = (self.skin_index + 1) % 3
                    self.reset()
                if e.key == pygame.K_t: self.day_mode = not self.day_mode
                if e.key in [pygame.K_LEFT, pygame.K_a]: self.ball.vx = -6
                if e.key in [pygame.K_RIGHT, pygame.K_d]: self.ball.vx = 6
            if e.type == pygame.KEYUP and e.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d]:
                self.ball.vx = 0
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx = pygame.mouse.get_pos()[0]
                self.ball.vx = -6 if mx < Settings.WIDTH // 2 else 6
            if e.type == pygame.MOUSEBUTTONUP:
                self.ball.vx = 0

    def update(self):
        self.ball.move()
        rect = pygame.Rect(self.ball.x - self.ball.radius, self.ball.y - self.ball.radius,
                           self.ball.radius * 2, self.ball.radius * 2)
        for p in self.platforms[:]:
            p.move()
            if rect.colliderect(p.rect) and self.ball.vy >= 0 and self.ball.y < p.rect.top + self.ball.radius:
                if p.jumps < p.max_jumps:
                    if p.type == "teleport":
                        if self.sounds["teleport"]: self.sounds["teleport"].play()
                        self.ball.x = random.randint(self.ball.radius, Settings.WIDTH - self.ball.radius)
                        self.ball.y = random.randint(100, Settings.HEIGHT // 2)
                        self.ball.vy = 0
                        self.ball.teleporting = True
                        self.ball.teleport_time = time.time()
                    else:
                        if self.sounds["jump"]: self.sounds["jump"].play()
                        self.ball.vy = self.ball.jump_strength
                        self.score += 1
                    p.jumps += 1
                    if p.type == "fragile" and p.jumps >= p.max_jumps:
                        self.platforms.remove(p)

        if self.ball.y < Settings.HEIGHT // 3:
            offset = Settings.HEIGHT // 3 - self.ball.y
            self.ball.y = Settings.HEIGHT // 3
            for p in self.platforms:
                p.rect.y += offset
            self.score += 1

        self.platforms = [p for p in self.platforms if p.rect.y < Settings.HEIGHT]
        while len(self.platforms) < 8:
            y = min(p.rect.y for p in self.platforms) - 70
            x = random.randint(0, Settings.WIDTH - Platform.WIDTH)
            speed = random.choice([-1, 1]) * random.uniform(1.0, 2.0)
            typ = random.choices(["normal", "fragile", "teleport"], [0.6, 0.3, 0.1])[0]
            self.platforms.append(Platform(x, y, speed, typ, self.images))

        if self.ball.y > Settings.HEIGHT:
            if self.sounds["gameover"]: self.sounds["gameover"].play()
            self.save_highscore()
            self.game_over = True

    def draw(self):
        bg = self.images["background_day"] if self.day_mode else self.images["background_night"]
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill((255, 255, 255) if self.day_mode else (30, 30, 30))

        for p in self.platforms: p.draw(self.screen)
        self.ball.draw(self.screen)

        def show(text, y, color=(0, 0, 0)):
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (Settings.WIDTH // 2 - surf.get_width() // 2, y))

        show(f"Punkte: {self.score}", 10)
        show(f"Highscore: {self.highscore}", 35)

        if self.paused:
            show("PAUSE (P zum Fortsetzen)", Settings.HEIGHT // 2 + 20, (255, 0, 0))
        if self.game_over:
            show("Spiel vorbei! Drücke R", Settings.HEIGHT // 2 + 50, (255, 0, 0))
            show("S für Skin-Wechsel", Settings.HEIGHT // 2 + 80, (0, 0, 255))

        pygame.display.flip()

if __name__ == "__main__":
    Game().run()
