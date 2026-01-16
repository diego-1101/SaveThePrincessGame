import pgzrun
import math
import random
import pygame

# --- CONFIGURAÇÃO GERAL ---
WIDTH = 800
HEIGHT = 600
TITLE = "Save The Princess - Final"
BLOCK_SIZE = 40  # Tamanho do grid
SCALE_FACTOR = 1  # Escala dos personagens
# Cores
COLOR_BG = (20, 20, 30)
COLOR_TEXT = (255, 255, 255)
COLOR_BTN = (60, 60, 80)

# Física (Ajustável)
GRAVITY = 0.6
GRAVITY_CARRYING = GRAVITY * 1.3
PLAYER_SPEED = 4
PLAYER_SPEED_CARRYING = PLAYER_SPEED * 0.7
JUMP_STRENGTH = -12

# Estados
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_GAME_OVER = "GAME_OVER"
STATE_VICTORY = "VICTORY"

# --- HELPER: Escala Automática ---
def get_scaled_actor(image_name, pos=(0,0)):
    """Cria um Actor e já aplica a escala para ele não ficar gigante."""
    actor = Actor(image_name, pos)
    # Redimensiona a surface interna do Pygame
    w = int(actor.width * SCALE_FACTOR)
    h = int(actor.height * SCALE_FACTOR)
    actor._surf = pygame.transform.scale(actor._surf, (w, h))
    actor._update_pos()
    return actor

def scale_existing_actor(actor):
    """Aplica escala em um actor já existente."""
    w = int(actor.width * SCALE_FACTOR)
    h = int(actor.height * SCALE_FACTOR)
    actor._surf = pygame.transform.scale(actor._surf, (w, h))
    actor._update_pos()

# --- CLASSES ---

class AnimatedSprite:
    def __init__(self, x, y, image_base, frame_count_idle=1):
        self.x = x
        self.y = y
        self.image_base = image_base
        self.current_anim = "idle"
        self.frame_index = 0
        self.timer = 0
        self.anim_speed = 0.15
        
        # Dicionario de frames: "idle" -> ["knight_idle_1", ...]
        self.animations = {}
        # Inicializa com idle padrao
        self.actor = get_scaled_actor(f"{image_base}_idle_1", (x, y))

    def add_anim(self, name, prefix, count):
        frames = [f"{prefix}_{i}" for i in range(1, count + 1)]
        self.animations[name] = frames

    def update_anim(self, dt):
        frames = self.animations.get(self.current_anim)
        if not frames: return

        self.timer += dt
        if self.timer >= self.anim_speed:
            self.timer = 0
            self.frame_index = (self.frame_index + 1) % len(frames)
            
            # Atualiza imagem e REAPLICA escala
            img_name = frames[self.frame_index]
            self.actor.image = img_name
            scale_existing_actor(self.actor)

    def draw(self):
        # Desenha usando coordenadas corrigidas (pes = bottom-center)
        # Calcula offset baseado no tamanho ATUAL do sprite escalado
        half_h = self.actor.height // 2
        self.actor.pos = (self.x, self.y - half_h)
        self.actor.draw()

class Player(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__(x, y, "knight")
        # Configurar animacoes
        self.add_anim("idle", "knight_idle", 3)
        self.add_anim("run", "knight_run", 4)
        self.add_anim("jump", "knight_jump", 2)
        self.add_anim("idle_carry", "knight_princess_idle", 3)
        self.add_anim("run_carry", "knight_princess_run", 4)
        self.add_anim("jump_carry", "knight_princess_jump", 2)
        
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.carrying = False
        self.lives = 3
        self.start_pos = (x, y)
        self.invul_timer = 0

    def update(self, dt, platforms):
        # Configurar velocidade e input
        speed = PLAYER_SPEED_CARRYING if self.carrying else PLAYER_SPEED
        dx = 0
        if keyboard.left: dx = -speed
        elif keyboard.right: dx = speed

        # Gravidade preliminar
        grav = GRAVITY_CARRYING if self.carrying else GRAVITY
        self.vy += grav
        
        # --- MOVIMENTO HORIZONTAL ---
        self.x += dx
        
        # Manter nos limites da tela (Backup)
        if self.x < 15: self.x = 15
        if self.x > WIDTH - 15: self.x = WIDTH - 15
        
        # Hitbox Horizontal
        w, h = 30, 50
        rect_x = pygame.Rect(self.x - w//2, self.y - h, w, h)
        
        for p in platforms:
            if rect_x.colliderect(p):
                # Colisao Lateral
                if dx > 0: # Indo pra direita
                    self.x = p.left - w//2
                    rect_x.left = self.x - w//2 # Atualiza rect para proxima checagem (opcional)
                elif dx < 0: # Indo pra esquerda
                    self.x = p.right + w//2
                    rect_x.left = self.x - w//2
        
        # --- MOVIMENTO VERTICAL ---
        self.y += self.vy
        
        # Hitbox Vertical (usando X ja corrigido)
        rect_y = pygame.Rect(self.x - w//2, self.y - h, w, h)
        self.on_ground = False
        
        for p in platforms:
            if rect_y.colliderect(p):
                # Colisao Vertical
                if self.vy > 0: # Caindo
                    # Checagem extra: so aterriza se os pes (self.y) nao estiverem muito abaixo do topo
                    # Isso evita ser " puxado" para o topo de uma parede lateral
                    # A tolerancia ajuda a subir degrauzinhos pequenos mas barra paredes altas
                    if (self.y - self.vy) <= p.top + 10: 
                        self.y = p.top
                        self.vy = 0
                        self.on_ground = True
                elif self.vy < 0: # Batendo a cabeca
                    self.y = p.bottom + h
                    self.vy = 0
                    
        # Chão (Safety net)
        if self.y > HEIGHT:
            self.y = HEIGHT
            self.vy = 0
            self.on_ground = True

        # 5. Pulo
        if self.on_ground and keyboard.space:
            self.vy = JUMP_STRENGTH
            play_sfx("jump")

        # 6. Escolha de Animação
        suffix = "_carry" if self.carrying else ""
        if not self.on_ground:
            self.current_anim = "jump" + suffix
        elif dx != 0:
            self.current_anim = "run" + suffix
        else:
            self.current_anim = "idle" + suffix
            
        self.update_anim(dt)
        
        # Invulnerabilidade
        if self.invul_timer > 0:
            self.invul_timer -= dt

    def hit(self):
        if self.invul_timer <= 0:
            self.lives -= 1
            self.invul_timer = 1.0 # 1s invul
            # Resetar pos? Opcional. Vamos manter pos
            # self.x, self.y = self.start_pos 

class Princess(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__(x, y, "princess")
        self.add_anim("idle", "princess_idle", 3)
        self.picked = False

    def update(self, dt):
        self.update_anim(dt)
    
    def draw(self):
        if not self.picked:
            super().draw()

# --- INIMIGOS ---

class FireEnemy(AnimatedSprite):
    """Inimigo Fogo: Anda Dir(2s), Atira, Anda Esq(2s), Atira."""
    def __init__(self, x, y):
        super().__init__(x, y, "fire_monster")
        self.add_anim("idle", "fire_monster_idle", 2)
        self.add_anim("walk", "fire_monster_walk", 2)
        self.state = 0 # 0=Dir, 1=Wait1, 2=Esq, 3=Wait2
        self.timer_action = 0
        self.projectiles = []
        
    def update(self, dt, player_obj): # player_obj nao usado mas mantido padrao
        self.timer_action += dt
        self.update_anim(dt)
        
        if self.state == 0: # Dir 2s
            self.x += 1
            self.current_anim = "walk"
            if self.timer_action > 2.0:
                self.state = 1
                self.timer_action = 0
        elif self.state == 1: # Wait 1s -> Shoot
            self.current_anim = "idle"
            if self.timer_action > 1.0:
                play_sfx("fireball")
                # Cria projetil
                p = Actor("fireball", (self.x, self.y))
                scale_existing_actor(p)
                self.projectiles.append({"actor": p, "vx": 5}) # Dir
                self.state = 2
                self.timer_action = 0
        elif self.state == 2: # Esq 2s
            self.x -= 1
            self.current_anim = "walk"
            if self.timer_action > 2.0:
                self.state = 3
                self.timer_action = 0
        elif self.state == 3: # Wait 1s -> Shoot
            self.current_anim = "idle"
            if self.timer_action > 1.0:
                play_sfx("fireball")
                p = Actor("fireball", (self.x, self.y))
                scale_existing_actor(p)
                self.projectiles.append({"actor": p, "vx": -5}) # Esq
                self.state = 0
                self.timer_action = 0

        # Update projeteis
        for p in self.projectiles[:]:
            p["actor"].x += p["vx"]
            # Remove se sair da tela
            if p["actor"].x < 0 or p["actor"].x > WIDTH:
                self.projectiles.remove(p)

    def draw(self):
        super().draw()
        for p in self.projectiles:
            p["actor"].draw()

class SwordEnemy(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__(x, y, "sword_monster")
        self.add_anim("idle", "sword_monster_idle", 2)
        self.add_anim("walk", "sword_monster_walk", 2)
        self.projectiles = []
        self.move_timer = 0
        self.target_x = x
        self.const_y = y
        self.timer_action = 0
        
    def update(self, dt, player):
        self.update_anim(dt)
        self.timer_action += dt
        
        # Comportamento: jogar espada para esquerda a cada 3s
        if self.timer_action > 3.0:
            self.timer_action = 0
            play_sfx("sword_throw")
            # Joga espada esquerda
            p = Actor("sword", (self.x, self.y))
            scale_existing_actor(p)
            self.projectiles.append({"actor": p, "vx": -6}) # Esquerda
            
        # Movimento Aleatorio (manter simples)
        if abs(self.x - self.target_x) < 5:
            if random.random() < 0.02:
                # Mantem na area direita mas aleatorio
                self.target_x = random.randint(400, 750) 
        else:
            self.current_anim = "walk"
            dir_move = 1 if self.target_x > self.x else -1
            self.x += dir_move * 1.5
            
        # Movimento Aleatorio
        if abs(self.x - self.target_x) < 5:
            if random.random() < 0.02:
                self.target_x = random.randint(400, 750) # Area direita
        else:
            self.current_anim = "walk"
            dir_move = 1 if self.target_x > self.x else -1
            self.x += dir_move * 1.5

        # Update projeteis
        for p in self.projectiles[:]:
            p["actor"].x += p["vx"]
            if p["actor"].x < 0 or p["actor"].x > WIDTH:
                self.projectiles.remove(p)

    def draw(self):
        super().draw()
        for p in self.projectiles:
            p["actor"].draw()

# --- JOGO MAPA ---

# W=Parede, K=Princesa, C=Castelo(Spawn), S=Sword, F=Fire, P=Plataforma
LEVEL_MAP = [
    "WWWWWWWWWWWWWWWWWWWW", # Topo (Borda)
    "W                  W", # Princesa no canto superior esquerdo
    "W                  W", # Plataforma do castelo da princesa
    "W                  W",
    "W                  W", 
    "W                  W", 
    "W             KS   W",
    "W          PPCCCPPPW", 
    "W        P         W", 
    "W  F               W",# Inimigo de Fogo na plataforma esquerda
    "WPPPPPP            W", # Plataforma onde o monstro de fogo está
    "W      P           W", 
    "W         PPPPPP   W",
    "WC                 W", # Spawn do Herói no castelo inferior
    "WWWWWWWWWWWWWWWWWWWW"  # Chão base
]




class Game:
    def __init__(self):
        self.state = STATE_MENU
        self.music_on = True
        
        # Botoes UI (Definidos no init para nao recriar sempre)
        cx, cy = WIDTH//2, HEIGHT//2
        self.btn_start = pygame.Rect(cx-100, cy-50, 200, 50)
        self.btn_sound = pygame.Rect(cx-100, cy+20, 200, 50)
        self.btn_exit = pygame.Rect(cx-100, cy+90, 200, 50)
        self.btn_home = pygame.Rect(WIDTH-50, 10, 40, 40)
        self.btn_sound_small = pygame.Rect(WIDTH-100, 10, 40, 40)
        
        # Inicializa o jogo vazio ou com padroes, mas o reset real eh no start
        self.platforms = []
        self.enemies = []

    def reset_game(self):
        # Reinicia variaveis do jogo, mantendo configuracoes (music_on)
        self.walls = []
        self.platforms = []
        self.castles = []
        self.enemies = []
        
        # Carregar Nivel
        for r, row in enumerate(LEVEL_MAP):
            for c, char in enumerate(row):
                x = c * BLOCK_SIZE + (BLOCK_SIZE // 2)
                y = r * BLOCK_SIZE + (BLOCK_SIZE // 2)
                
                # Blocos Solidos
                rect = pygame.Rect(c*BLOCK_SIZE, r*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                
                if char == "W":
                    self.walls.append(rect)
                elif char == "P":
                    self.platforms.append(rect)
                elif char == "C":
                    self.castles.append(rect)
                    # Candidato a spawn? (Linha de baixo)
                    if r > 10:
                        self.spawn_pos = (x, r * BLOCK_SIZE)
                        self.spawn_rect_area = pygame.Rect(c*BLOCK_SIZE, r*BLOCK_SIZE, BLOCK_SIZE*2, BLOCK_SIZE)

                # Entidades
                elif char == "K": # Princess (K de Knight's goal?)
                    self.princess = Princess(x, y + 10) 
                
                elif char == "F":
                    self.enemies.append(FireEnemy(x, y + 10))
                
                elif char == "S":
                    self.enemies.append(SwordEnemy(x, y + 10))

        # Definir Spawn Final
        if hasattr(self, 'spawn_pos'):
            self.player = Player(self.spawn_pos[0], self.spawn_pos[1])
            self.spawn_rect = self.spawn_rect_area
        else:
             # Fallback
             self.player = Player(100, 520)
             self.spawn_rect = pygame.Rect(80, 520, 80, 40)
        
        # Reset musica se necessario
        if self.music_on:
             play_bgm()

        # Fallback se nao achou spawn
        if not hasattr(self, 'player'):
             self.player = Player(100, 500)

        # Botoes UI
        cx, cy = WIDTH//2, HEIGHT//2
        self.btn_start = pygame.Rect(cx-100, cy-50, 200, 50)
        self.btn_sound = pygame.Rect(cx-100, cy+20, 200, 50)
        self.btn_exit = pygame.Rect(cx-100, cy+90, 200, 50)
        
        self.btn_home = pygame.Rect(WIDTH-50, 10, 40, 40)
        self.btn_sound_small = pygame.Rect(WIDTH-100, 10, 40, 40)

    def draw(self):
        screen.clear()
        screen.fill(COLOR_BG)
        
        if self.state == STATE_MENU:
            screen.draw.text("Save The Princess", center=(WIDTH//2, 100), fontsize=60, color="orange")
            # Botoes
            lbl_som = "SOM LIGADO" if self.music_on else "SOM DESLIGADO"
            for btn, txt in [(self.btn_start, "JOGAR"), (self.btn_sound, lbl_som), (self.btn_exit, "SAIR")]:
                screen.draw.filled_rect(btn, COLOR_BTN)
                screen.draw.text(txt, center=btn.center, fontsize=30)
                
        elif self.state == STATE_PLAYING:
            # Mapa
            if hasattr(self, 'spawn_rect'):
                screen.draw.filled_rect(self.spawn_rect, (0, 100, 0))
            
            # Desenha Wall (W)
            for w in self.walls:
                screen.draw.filled_rect(w, (40, 40, 50)) # Parede escura
            
            # Desenha Platform (P)
            for p in self.platforms:
                screen.draw.filled_rect(p, (100, 100, 120)) # Plataforma cinza
                
            # Desenha Castle (C)
            for c in self.castles:
                screen.draw.filled_rect(c, (80, 50, 50)) # Castelo avermelhado/marrom
                
            self.princess.draw()
            self.player.draw()
            for e in self.enemies: e.draw()
            
            # UI
            screen.draw.text(f"VIDAS: {self.player.lives}", (10, 10), color="red", fontsize=30)
            
            # Botoes UI
            screen.draw.filled_rect(self.btn_home, COLOR_BTN)
            screen.draw.text("M", center=self.btn_home.center)
            screen.draw.filled_rect(self.btn_sound_small, COLOR_BTN)
            screen.draw.text("S", center=self.btn_sound_small.center)
            
        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            msg = "VITORIA!" if self.state == STATE_VICTORY else "FIM DE JOGO"
            color = "gold" if self.state == STATE_VICTORY else "red"
            screen.draw.text(msg, center=(WIDTH//2, HEIGHT//2), fontsize=80, color=color)
            
            # Botao Back
            back_btn = pygame.Rect(WIDTH//2-100, HEIGHT//2+100, 200, 50)
            screen.draw.filled_rect(back_btn, COLOR_BTN)
            screen.draw.text("Voltar ao Menu", center=back_btn.center)

    def update(self, dt):
        if self.state == STATE_PLAYING:
            # Combina colisoes
            all_platforms = self.walls + self.platforms + self.castles
            self.player.update(dt, all_platforms)
            self.princess.update(dt)
            for e in self.enemies: e.update(dt, self.player)
            
            # Colisao Princesa
            if not self.player.carrying:
                # Distancia simples
                d = ((self.player.x - self.princess.x)**2 + (self.player.y - self.princess.y)**2)**0.5
                if d < 50:
                    self.player.carrying = True
                    self.princess.picked = True
                    play_sfx("collect")
            
            # Vitoria
            if self.player.carrying:
                rect = pygame.Rect(self.player.x, self.player.y, 10, 10)
                if rect.colliderect(self.spawn_rect):
                    self.state = STATE_VICTORY
                    play_sfx("collect")

            # Dano Inimigos
            p_rect = pygame.Rect(self.player.x-15, self.player.y-25, 30, 50)
            for e in self.enemies:
                # Corpo
                e_rect = pygame.Rect(e.x-20, e.y-20, 40, 40)
                if p_rect.colliderect(e_rect):
                    self.player.hit()
                # Projeteis
                for p in e.projectiles:
                    pr = pygame.Rect(p["actor"].x-10, p["actor"].y-10, 20, 20)
                    if p_rect.colliderect(pr):
                        self.player.hit()
                        e.projectiles.remove(p)

            if self.player.lives <= 0:
                self.state = STATE_GAME_OVER

    def on_mouse_down(self, pos):
        if self.state == STATE_MENU:
            if self.btn_start.collidepoint(pos):
                self.reset_game() # Usa reset, nao init, pra manter settings
                self.state = STATE_PLAYING
                # Musica ja tratada no reset_game
            elif self.btn_sound.collidepoint(pos):
                self.music_on = not self.music_on
                if self.music_on: play_bgm()
                else: stop_bgm()
            elif self.btn_exit.collidepoint(pos):
                exit()
                
        elif self.state == STATE_PLAYING:
            if self.btn_home.collidepoint(pos):
                self.state = STATE_MENU
                stop_bgm()
            elif self.btn_sound_small.collidepoint(pos):
                self.music_on = not self.music_on
                if self.music_on: play_bgm()
                else: stop_bgm()
                
        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            # Back (Hardcoded rect acima)
            back_btn = pygame.Rect(WIDTH//2-100, HEIGHT//2+100, 200, 50)
            if back_btn.collidepoint(pos):
                self.state = STATE_MENU
                stop_bgm()

game = Game()

# --- AUDIO ---
def play_sfx(name):
    if game.music_on:
        try: getattr(sounds, name).play()
        except: pass

def play_bgm():
    try: 
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load('sounds/background.mp3')
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.5)
    except Exception as e:
        print(f"Erro ao tocar musica: {e}")

def stop_bgm():
    try: pygame.mixer.music.stop()
    except: pass

# --- HOOKS ---
def update(dt): game.update(dt)
def draw(): game.draw()
def on_mouse_down(pos): game.on_mouse_down(pos)

pgzrun.go()
