"""
Vibrant Snake - A modern and kid-friendly implementation of the classic Snake game.
This single file contains all the game logic, including the engine, entities, UI, and assets.
"""
import pygame
import sys
import os
import json
import random
import math
from typing import Dict, Tuple, Optional, List, Callable
from datetime import datetime

# --- CONFIGURATION CONSTANTS ---

# Screen and Grid
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 32
GRID_WIDTH = 25
GRID_HEIGHT = 15
FPS = 60

# --- THEME & DESIGN CONSTANTS ---
# A more playful and vibrant color palette for the redesign.
PALETTE = {
    'background': (20, 22, 32),      # Dark Space Blue
    'grid_background': (30, 33, 48),
    'bouncy_wall': (115, 125, 255),    # Electric Blue
    'snake_head': (0, 255, 159),       # Spring Green
    'snake_body': (0, 225, 139),
    'apple': (255, 89, 89),            # Bright Red
    'banana': (255, 225, 89),          # Bright Yellow
    'berry': (89, 173, 255),           # Sky Blue
    'text_light': (240, 240, 240),
    'text_dark': (20, 22, 32),
    'shadow': (15, 16, 24),
    'button_normal': (85, 95, 255),    # Electric Blue
    'button_hover': (115, 125, 255),
    'accent1': (0, 255, 159),              # Spring Green for titles
    'accent2': (255, 89, 89),              # Bright Red for warnings
}

# Color-blind safe palette remains focused on high contrast
CB_PALETTE = {
    'snake_head': (0, 114, 178),     # Blue
    'snake_body': (0, 90, 150),
}

# Game Mechanics
DIFFICULTY_LEVELS = {
    'Easy': {'speed': 8, 'powerup_spawn_rate': 15000},
    'Normal': {'speed': 12, 'powerup_spawn_rate': 10000},
    'Hard': {'speed': 18, 'powerup_spawn_rate': 7000}
}
COMBO_WINDOW = 10000  # 10 seconds in milliseconds

# Effects
SCREEN_SHAKE_DURATION = 120  # ms
SCREEN_SHAKE_INTENSITY = 4   # pixels

# Food Config
FOOD_TYPES = {
    'apple': {'color': PALETTE['apple'], 'shape': 'circle'},
    'banana': {'color': PALETTE['banana'], 'shape': 'rect'},
    'berry': {'color': PALETTE['berry'], 'shape': 'circle'},
}

# Power-up Config
POWER_UP_CONFIG = {
    'slimy': {
        'duration': 5000,
        'color': (150, 255, 150),
        'letter': 'S'
    },
    'magnet': {
        'duration': 5000,
        'color': (255, 100, 255),
        'letter': 'M'
    }
}

# --- ASSET MANAGER ---

class AssetManager:
    """A class to manage all game assets."""
    def __init__(self):
        self.snake_skins: Dict[str, Dict[str, pygame.Surface]] = {}
        self.food_surfaces: Dict[str, pygame.Surface] = {}
        self.power_up_surfaces: Dict[str, pygame.Surface] = {}
        self.ui_icons: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self.fonts: Dict[str, Optional[pygame.font.Font]] = {}
        self.backgrounds: Dict[str, List] = {}
        self.load_assets()

    def load_assets(self) -> None:
        """Loads all assets required for the game."""
        self.load_fonts()
        self.create_snake_skins()
        self.create_food_surfaces()
        self.create_power_up_surfaces()
        self.create_ui_icons()
        self.create_sounds()
        self.create_backgrounds()
        self.generate_sprite_preview()

    def load_fonts(self):
        """Loads a custom font if available, otherwise falls back to default."""
        custom_font_path = 'assets/Fredoka-Regular.ttf'
        try:
            self.fonts['title'] = pygame.font.Font(custom_font_path, 120)
            self.fonts['header'] = pygame.font.Font(custom_font_path, 70)
            self.fonts['body'] = pygame.font.Font(custom_font_path, 40)
            self.fonts['small'] = pygame.font.Font(custom_font_path, 30)
            print("Custom font 'Fredoka-Regular.ttf' loaded successfully.")
        except FileNotFoundError:
            print(f"Warning: Custom font not found at '{custom_font_path}'. Falling back to default font.")
            self.fonts['title'] = pygame.font.Font(None, 120)
            self.fonts['header'] = pygame.font.Font(None, 70)
            self.fonts['body'] = pygame.font.Font(None, 40)
            self.fonts['small'] = pygame.font.Font(None, 30)

    def create_snake_skins(self):
        skins = {
            "Default": {"head": PALETTE['snake_head'], "body": PALETTE['snake_body']},
            "Tiger": {"head": (255, 165, 0), "body": (255, 140, 0), "pattern": (0,0,0)},
            "Rainbow": {"head": (255, 0, 0), "body": "rainbow"},
        }
        for name, colors in skins.items():
            self.snake_skins[name] = self._create_snake_surfaces(colors)
            self.snake_skins[name + " (CB)"] = self._create_snake_surfaces(colors, color_blind_mode=True)

    def _create_snake_surfaces(self, colors: Dict, color_blind_mode: bool = False) -> Dict:
        """Creates stylized surfaces for a single snake skin."""
        surfaces = {}
        head_color = CB_PALETTE['snake_head'] if color_blind_mode else colors['head']
        body_color = CB_PALETTE['snake_body'] if color_blind_mode else colors['body']
        
        # Head with eyes
        head_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(head_surf, head_color, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2 - 2)
        surfaces['head'] = head_surf
        surfaces['head_wide_eyes'] = self._add_eyes(head_surf.copy(), 'wide')
        surfaces['head_dizzy_eyes'] = self._add_eyes(head_surf.copy(), 'dizzy')
        surfaces['head_normal_eyes'] = self._add_eyes(head_surf.copy(), 'normal')
        
        # Body segments
        if body_color == "rainbow":
            body_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            for i, color in enumerate([(255,0,0), (255,165,0), (255,255,0), (0,128,0), (0,0,255), (75,0,130)]):
                pygame.draw.circle(body_surf, color, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2 - 3 - i*2)
            surfaces['body'] = body_surf
        else:
            body_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(body_surf, body_color, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2 - 3)
            if "pattern" in colors:
                pygame.draw.line(body_surf, colors['pattern'], (5, 5), (TILE_SIZE - 5, TILE_SIZE - 5), 3)
                pygame.draw.line(body_surf, colors['pattern'], (5, TILE_SIZE - 5), (TILE_SIZE - 5, 5), 3)
            surfaces['body'] = body_surf
        return surfaces

    def _add_eyes(self, surface, state='normal'):
        if state == 'wide':
            pygame.draw.circle(surface, (255, 255, 255), (TILE_SIZE // 2 - 6, TILE_SIZE // 2 - 5), 6)
            pygame.draw.circle(surface, (255, 255, 255), (TILE_SIZE // 2 + 6, TILE_SIZE // 2 - 5), 6)
            pygame.draw.circle(surface, (0, 0, 0), (TILE_SIZE // 2 - 5, TILE_SIZE // 2 - 4), 3)
            pygame.draw.circle(surface, (0, 0, 0), (TILE_SIZE // 2 + 7, TILE_SIZE // 2 - 4), 3)
        elif state == 'dizzy':
            pygame.draw.line(surface, (0,0,0), (TILE_SIZE // 2 - 8, TILE_SIZE // 2 - 8), (TILE_SIZE // 2 - 2, TILE_SIZE // 2 - 2), 2)
            pygame.draw.line(surface, (0,0,0), (TILE_SIZE // 2 - 8, TILE_SIZE // 2 - 2), (TILE_SIZE // 2 - 2, TILE_SIZE // 2 - 8), 2)
            pygame.draw.line(surface, (0,0,0), (TILE_SIZE // 2 + 2, TILE_SIZE // 2 - 8), (TILE_SIZE // 2 + 8, TILE_SIZE // 2 - 2), 2)
            pygame.draw.line(surface, (0,0,0), (TILE_SIZE // 2 + 2, TILE_SIZE // 2 - 2), (TILE_SIZE // 2 + 8, TILE_SIZE // 2 - 8), 2)
        else: # normal
            pygame.draw.circle(surface, (255, 255, 255), (TILE_SIZE // 2 - 5, TILE_SIZE // 2 - 5), 4)
            pygame.draw.circle(surface, (255, 255, 255), (TILE_SIZE // 2 + 5, TILE_SIZE // 2 - 5), 4)
            pygame.draw.circle(surface, (0, 0, 0), (TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4), 2)
            pygame.draw.circle(surface, (0, 0, 0), (TILE_SIZE // 2 + 6, TILE_SIZE // 2 - 4), 2)
        return surface

    def create_food_surfaces(self) -> None:
        """Creates stylized surfaces for food."""
        for name, config in FOOD_TYPES.items():
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(surf, config['color'], (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2 - 4)
            pygame.draw.circle(surf, (255, 255, 255, 90), (TILE_SIZE // 2 - 3, TILE_SIZE // 2 - 3), 4)
            self.food_surfaces[name] = surf

    def create_power_up_surfaces(self) -> None:
        """Creates surfaces for power-ups."""
        for name, config in POWER_UP_CONFIG.items():
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(surf, config['color'], (2, 2, TILE_SIZE-4, TILE_SIZE-4), border_radius=10)
            text_surf = self.fonts['small'].render(config['letter'], True, PALETTE['text_dark'])
            text_rect = text_surf.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
            surf.blit(text_surf, text_rect)
            self.power_up_surfaces[name] = surf
            
    def create_ui_icons(self) -> None:
        """Generates simple UI icons."""
        mute_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(mute_surf, PALETTE['button_normal'], (24, 24), 24)
        pygame.draw.line(mute_surf, PALETTE['accent2'], (8, 8), (40, 40), 4)
        self.ui_icons['mute'] = mute_surf

    def create_sounds(self) -> None:
        """Loads sound effects from the assets folder."""
        sound_files = {
            'eat': 'eat.wav', 'combo': 'combo.wav', 'powerup': 'powerup.wav',
            'game_over': 'game_over.wav', 'click': 'click.wav', 'bounce': 'bounce.wav',
            'new_highscore': 'highscore.wav', 'mission_complete': 'mission.wav',
            'background_music': 'music.ogg'
        }
        assets_dir = 'assets'
        for name, filename in sound_files.items():
            path = os.path.join(assets_dir, filename)
            try:
                if os.path.exists(path):
                    if 'music' in name:
                        pygame.mixer.music.load(path)
                        pygame.mixer.music.set_volume(0.3)
                    else:
                        self.sounds[name] = pygame.mixer.Sound(path)
            except pygame.error as e:
                print(f"Could not load sound '{filename}': {e}")
    
    def create_backgrounds(self):
        self.backgrounds['stars'] = [[random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1, 3)] for _ in range(100)]
        self.backgrounds['nebula'] = [] # Can be implemented later

    def generate_sprite_preview(self) -> None:
        """Generates a preview image of key sprites."""
        preview_surface = pygame.Surface((256, 128), pygame.SRCALPHA)
        preview_surface.fill(PALETTE['background'])
        preview_surface.blit(self.snake_skins['Default']['head_normal_eyes'], (20, 20))
        preview_surface.blit(self.snake_skins['Default']['body'], (20 + TILE_SIZE + 5, 20))
        preview_surface.blit(self.food_surfaces['apple'], (20, 70))
        preview_surface.blit(self.food_surfaces['banana'], (20 + TILE_SIZE + 5, 70))
        preview_surface.blit(self.power_up_surfaces['slimy'], (20 + 2*(TILE_SIZE + 5), 70))
        try:
            if not os.path.exists('assets'): os.makedirs('assets')
            pygame.image.save(preview_surface, 'assets/preview.png')
            print("Generated assets/preview.png")
        except Exception as e:
            print(f"Could not save sprite preview: {e}")


# --- GAME ENTITIES ---
class Snake:
    """Represents the snake entity."""
    def __init__(self, play_area: pygame.Rect):
        self.play_area = play_area
        self.body: List[pygame.Vector2] = [pygame.Vector2(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = pygame.Vector2(0, 0)
        self.new_block = False
        self.active_power_ups: dict[str, int] = {}
        self.eye_state = 'normal' # normal, wide, dizzy
        self.dizzy_timer = 0

    def update(self) -> None:
        """Updates the snake's position."""
        if self.direction.length() == 0: return
        
        if self.dizzy_timer > 0:
            self.dizzy_timer -= 1
            if self.dizzy_timer == 0: self.eye_state = 'normal'

        body_copy = self.body[:] if self.new_block else self.body[:-1]
        self.new_block = False
        new_head = self.body[0] + self.direction
        self.body = [new_head] + body_copy

    def grow(self): self.new_block = True
    def get_head_position(self): return self.body[0]
    def get_head_pixel_pos(self, origin: Tuple[int, int]):
        return (origin[0] + self.body[0].x * TILE_SIZE + TILE_SIZE / 2,
                origin[1] + self.body[0].y * TILE_SIZE + TILE_SIZE / 2)

    def check_collision(self, bouncy_walls: List) -> Optional[str]:
        """Checks for collisions with walls or self."""
        head = self.get_head_position()
        if head in bouncy_walls:
            return "bounce"
        if not (0 <= head.x < GRID_WIDTH and 0 <= head.y < GRID_HEIGHT):
            return "wall"
        if head in self.body[1:] and 'slimy' not in self.active_power_ups:
            return "self"
        return None

    def draw(self, surface: pygame.Surface, assets: AssetManager, origin: Tuple, offset: Tuple, skin: str, cb_mode: bool):
        skin_name = skin + " (CB)" if cb_mode else skin
        skin_assets = assets.snake_skins[skin_name]
        
        head_surface = skin_assets[f'head_{self.eye_state}_eyes']
        body_surface = skin_assets['body']

        for i, segment in enumerate(self.body):
            rect = pygame.Rect(origin[0] + offset[0] + int(segment.x * TILE_SIZE),
                                origin[1] + offset[1] + int(segment.y * TILE_SIZE),
                                TILE_SIZE, TILE_SIZE)
            surface.blit(head_surface if i == 0 else body_surface, rect)
        
    def add_power_up(self, power_up_type: str):
        duration = POWER_UP_CONFIG[power_up_type]['duration']
        self.active_power_ups[power_up_type] = pygame.time.get_ticks() + duration

    def update_power_ups(self):
        current_time = pygame.time.get_ticks()
        expired = [ptype for ptype, end_time in self.active_power_ups.items() if current_time >= end_time]
        for ptype in expired: del self.active_power_ups[ptype]

class Food:
    """Represents the food entity."""
    def __init__(self, play_area: pygame.Rect, snake_body: List[pygame.Vector2]):
        self.position = pygame.Vector2(0, 0)
        self.type = 'apple'
        self.color = FOOD_TYPES[self.type]['color']
        self.randomize_position(snake_body)

    def randomize_position(self, snake_body: List[pygame.Vector2]):
        self.type = random.choice(list(FOOD_TYPES.keys()))
        self.color = FOOD_TYPES[self.type]['color']
        available_pos = [pygame.Vector2(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT) if pygame.Vector2(x,y) not in snake_body]
        if available_pos: self.position = random.choice(available_pos)

    def draw(self, surface: pygame.Surface, assets: AssetManager, origin: Tuple, offset: Tuple):
        rect = pygame.Rect(origin[0] + offset[0] + int(self.position.x * TILE_SIZE),
                            origin[1] + offset[1] + int(self.position.y * TILE_SIZE),
                            TILE_SIZE, TILE_SIZE)
        surface.blit(assets.food_surfaces[self.type], rect)

class PowerUp:
    """Represents a power-up item."""
    def __init__(self, play_area: pygame.Rect, occupied: List[pygame.Vector2]):
        self.type = random.choice(list(POWER_UP_CONFIG.keys()))
        self.config = POWER_UP_CONFIG[self.type]
        self.position = pygame.Vector2(0,0)
        self.randomize_position(occupied)
    
    def randomize_position(self, occupied: List[pygame.Vector2]):
        available_pos = [pygame.Vector2(x,y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT) if pygame.Vector2(x,y) not in occupied]
        if available_pos: self.position = random.choice(available_pos)
    
    def draw(self, surface: pygame.Surface, assets: AssetManager, origin: Tuple, offset: Tuple):
        rect = pygame.Rect(origin[0] + offset[0] + int(self.position.x * TILE_SIZE),
                            origin[1] + offset[1] + int(self.position.y * TILE_SIZE),
                            TILE_SIZE, TILE_SIZE)
        surface.blit(assets.power_up_surfaces[self.type], rect)

class Particle:
    """A simple particle for effects."""
    def __init__(self, pos: Tuple[float, float], color: Tuple[int, int, int], lifespan: int = 45):
        self.pos = list(pos)
        self.color = color
        self.vel = [random.uniform(-4, 4), random.uniform(-5, -1)]
        self.lifespan = random.randint(lifespan - 15, lifespan + 15)
        self.max_lifespan = self.lifespan
        self.alive = True
    
    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.vel[1] += 0.1 # Gravity
        self.lifespan -= 1
        if self.lifespan <= 0: self.alive = False
    
    def draw(self, surface: pygame.Surface, offset: Tuple[int, int]):
        alpha = int(255 * (self.lifespan / self.max_lifespan))
        temp_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(temp_surf, self.color + (alpha,), (6, 6), self.lifespan / 8)
        surface.blit(temp_surf, (self.pos[0] + offset[0] - 6, self.pos[1] + offset[1] - 6))

# --- UI MANAGER ---

class Button:
    """A clickable and animated UI button."""
    def __init__(self, rect: pygame.Rect, text: str, callback: Callable, assets: AssetManager, font_size: int = 50, enabled: bool = True):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.assets = assets
        self.font = assets.fonts['body'] if font_size == 50 else assets.fonts['small']
        self.is_hovered = False
        self.is_clicked = False
        self.scale = 1.0
        self.enabled = enabled

    def handle_event(self, event: pygame.event.Event):
        if not self.enabled: return
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.is_clicked = True; self.scale = 0.95
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.is_hovered and self.is_clicked:
            if self.assets.sounds.get('click'): self.assets.sounds['click'].play()
            self.callback()
            self.is_clicked = False
        elif event.type == pygame.MOUSEBUTTONUP: self.is_clicked = False
    
    def update(self):
        """Animates the button scale."""
        if self.is_hovered and not self.is_clicked and self.enabled:
            self.scale += (1.05 - self.scale) * 0.2
        else:
            self.scale += (1.0 - self.scale) * 0.2

    def draw(self, surface: pygame.Surface):
        self.update()
        scaled_rect = pygame.Rect(0,0, int(self.rect.width * self.scale), int(self.rect.height * self.scale))
        scaled_rect.center = self.rect.center
        
        color = PALETTE['button_hover'] if self.is_hovered else PALETTE['button_normal']
        if not self.enabled: color = (80, 80, 80)
        
        pygame.draw.rect(surface, PALETTE['shadow'], scaled_rect.move(0, 5), border_radius=15)
        pygame.draw.rect(surface, color, scaled_rect, border_radius=15)
        text_surf = self.font.render(self.text, True, PALETTE['text_light'] if self.enabled else (150,150,150))
        surface.blit(text_surf, text_surf.get_rect(center=scaled_rect.center))

class UIManager:
    """Manages all UI components and screens."""
    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.buttons: list[Button] = []

    def clear_buttons(self): self.buttons.clear()
    def handle_events(self, event: pygame.event.Event):
        for button in self.buttons: button.handle_event(event)

    def _draw_text(self, screen: pygame.Surface, text: str, font: pygame.font.Font,
                   pos: tuple, color, center: bool = True):
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=pos) if center else text_surf.get_rect(topleft=pos)
        screen.blit(text_surf, text_rect)

    def draw_playing_ui(self, screen: pygame.Surface, score: int, high_score: int, snake: Snake, mission):
        self._draw_text(screen, f"Score: {score}", self.assets.fonts['body'], (40, 40), PALETTE['text_light'], center=False)
        self._draw_text(screen, f"Best: {high_score}", self.assets.fonts['small'], (40, 80), PALETTE['text_light'], center=False)

        # Mission UI
        mission_text = f"Mission: {mission['text']} ({mission['progress']}/{mission['target']})"
        color = PALETTE['accent1'] if mission['completed'] else PALETTE['text_light']
        self._draw_text(screen, mission_text, self.assets.fonts['small'], (SCREEN_WIDTH // 2, 50), color)

        # Draw active power-ups
        for i, (ptype, end_time) in enumerate(snake.active_power_ups.items()):
            remaining_time = (end_time - pygame.time.get_ticks()) / 1000
            icon = self.assets.power_up_surfaces[ptype]
            screen.blit(icon, (SCREEN_WIDTH - 200, 40 + i * 50))
            self._draw_text(screen, f"{remaining_time:.1f}s", self.assets.fonts['small'], (SCREEN_WIDTH - 120, 55 + i * 50), PALETTE['text_light'])

    def setup_start_menu(self, **callbacks):
        self.clear_buttons()
        btn_w, btn_h, start_y = 400, 70, 250
        bottom_btn_w, bottom_btn_h = 220, 50
        bottom_y = SCREEN_HEIGHT - 80
        spacing = 20
        
        # Center the bottom row of buttons
        total_width = (bottom_btn_w * 3) + (spacing * 2)
        start_x = (SCREEN_WIDTH - total_width) // 2

        self.buttons = [
            Button(pygame.Rect((SCREEN_WIDTH - btn_w) // 2, start_y, btn_w, btn_h), "Start Game", callbacks['start_game_callback'], self.assets),
            Button(pygame.Rect((SCREEN_WIDTH - btn_w) // 2, start_y + 90, btn_w, btn_h), "Customize", callbacks['customize_callback'], self.assets),
            Button(pygame.Rect((SCREEN_WIDTH - btn_w) // 2, start_y + 180, btn_w, btn_h), f"Difficulty: {callbacks['difficulty']}", callbacks['toggle_difficulty_callback'], self.assets),
            
            # Bottom row
            Button(pygame.Rect(start_x, bottom_y, bottom_btn_w, bottom_btn_h), f"Colorblind: {'ON' if callbacks['cb_mode'] else 'OFF'}", callbacks['toggle_cb_mode_callback'], self.assets, 30),
            Button(pygame.Rect(start_x + bottom_btn_w + spacing, bottom_y, bottom_btn_w, bottom_btn_h), f"Music: {'OFF' if callbacks['is_muted'] else 'ON'}", callbacks['toggle_music_callback'], self.assets, 30),
            Button(pygame.Rect(start_x + 2 * (bottom_btn_w + spacing), bottom_y, bottom_btn_w, bottom_btn_h), f"Slow Mode: {'ON' if callbacks['slow_mode'] else 'OFF'}", callbacks['toggle_slow_mode_callback'], self.assets, 30)
        ]

    def draw_start_menu(self, screen: pygame.Surface):
        self._draw_text(screen, "Vibrant Snake", self.assets.fonts['title'], (SCREEN_WIDTH // 2, 150), PALETTE['accent1'])
        for button in self.buttons: button.draw(screen)

    def setup_customize_menu(self, unlocks, current_skin, **callbacks):
        self.clear_buttons()
        # Skin selection
        for i, skin in enumerate(unlocks['skins']):
            enabled = unlocks['skins'][skin]
            btn = Button(pygame.Rect(150, 200 + i * 80, 300, 60), skin, lambda s=skin: callbacks['select_skin'](s), self.assets, 30, enabled)
            self.buttons.append(btn)
        # Back button
        self.buttons.append(Button(pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 120, 300, 70), "Back", callbacks['back'], self.assets))

    def draw_customize_menu(self, screen, current_skin):
        self._draw_text(screen, "Customize", self.assets.fonts['header'], (SCREEN_WIDTH // 2, 100), PALETTE['text_light'])
        self._draw_text(screen, "Skins", self.assets.fonts['body'], (300, 150), PALETTE['accent1'])
        self._draw_text(screen, f"Current: {current_skin}", self.assets.fonts['small'], (300, 550), PALETTE['text_light'])
        for button in self.buttons: button.draw(screen)


    def setup_menu(self, **callbacks):
        self.clear_buttons()
        self.buttons = [
            Button(pygame.Rect((SCREEN_WIDTH - 300) // 2, 400 + i * 90, 300, 70), text, cb, self.assets)
            for i, (text, cb) in enumerate(callbacks.items())
        ]

    def draw_paused_menu(self, screen: pygame.Surface):
        self._draw_text(screen, "Paused", self.assets.fonts['header'], (SCREEN_WIDTH // 2, 200), PALETTE['text_light'])
        for button in self.buttons: button.draw(screen)

    def draw_game_over_menu(self, screen, score, high_score, new_high_score):
        self._draw_text(screen, "Game Over", self.assets.fonts['header'], (SCREEN_WIDTH // 2, 200), PALETTE['accent2'])
        if new_high_score:
            self._draw_text(screen, "New High Score!", self.assets.fonts['body'], (SCREEN_WIDTH // 2, 260), PALETTE['accent1'])
        self._draw_text(screen, f"Your Score: {score}", self.assets.fonts['body'], (SCREEN_WIDTH // 2, 320), PALETTE['text_light'])
        self._draw_text(screen, f"Best: {high_score}", self.assets.fonts['small'], (SCREEN_WIDTH // 2, 370), PALETTE['text_light'])
        for button in self.buttons: button.draw(screen)

# --- GAME ENGINE ---

class Game:
    """The main class representing the Snake game."""
    def __init__(self, resolution: Tuple[int, int] = (1280, 720)):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode(resolution)
        pygame.display.set_caption("Vibrant Snake")
        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.ui_manager = UIManager(self.assets)
        self.game_state: str = ""
        self.score: int = 0
        self.player_data = self.load_player_data()
        self.high_score = self.player_data['high_score']
        self.difficulty: str = "Normal"
        self.color_blind_mode: bool = False
        self.slow_mode: bool = False
        self.is_muted: bool = False
        self.snake: Optional[Snake] = None
        self.food: Optional[Food] = None
        self.power_ups: list[PowerUp] = []
        self.particles: list[Particle] = []
        self.new_high_score = False
        self.current_mission = {}
        self.current_skin = self.player_data['current_skin']
        
        self.bouncy_walls = []
        self.generate_bouncy_walls()

        self.transition_alpha = 255
        self.combo_timer, self.combo_count, self.screen_shake_timer, self.power_up_spawn_timer = 0, 0, 0, 0
        self.set_state("start_menu")

    def set_state(self, new_state: str):
        self.game_state = new_state
        if new_state == "start_menu":
            self.ui_manager.setup_start_menu(
                difficulty=self.difficulty, cb_mode=self.color_blind_mode, slow_mode=self.slow_mode, is_muted=self.is_muted,
                start_game_callback=self.start_new_game, customize_callback=lambda: self.set_state('customize'),
                toggle_difficulty_callback=self.toggle_difficulty, toggle_cb_mode_callback=self.toggle_cb_mode,
                toggle_slow_mode_callback=self.toggle_slow_mode, toggle_music_callback=self.toggle_mute)
        elif new_state == "customize":
             self.ui_manager.setup_customize_menu(self.player_data['unlocks'], self.current_skin,
                select_skin=self.select_skin, back=lambda: self.set_state('start_menu'))
        elif new_state == "paused":
            self.ui_manager.setup_menu(Resume=lambda: self.set_state('playing'),
                 Restart=self.start_new_game, Menu=lambda: self.set_state('start_menu'))
        elif new_state == "game_over":
            self.ui_manager.setup_menu(**{'Play Again': self.start_new_game, 'Main Menu': lambda: self.set_state('start_menu')})

    def start_new_game(self, daily_challenge: bool = False):
        """Initializes a new game session."""
        play_area = self.get_play_area_rect()
        self.snake = Snake(play_area)
        self.food = Food(play_area, self.snake.body)
        self.power_ups.clear(); self.particles.clear()
        self.score = 0; self.new_high_score = False
        speed = DIFFICULTY_LEVELS[self.difficulty]['speed']
        self.snake_update_interval = 1000 / (speed * 0.5 if self.slow_mode else speed)
        self.last_snake_update = pygame.time.get_ticks()
        self.generate_mission()
        self.set_state("playing")
        self.combo_timer, self.combo_count = 0, 0
        self.power_up_spawn_timer = pygame.time.get_ticks()
        
    def get_play_area_rect(self) -> pygame.Rect:
        return pygame.Rect((self.screen.get_width() - GRID_WIDTH * TILE_SIZE) // 2,
                            (self.screen.get_height() - GRID_HEIGHT * TILE_SIZE) // 2,
                            GRID_WIDTH * TILE_SIZE, GRID_HEIGHT * TILE_SIZE)

    def run(self):
        """The main game loop."""
        if not self.is_muted:
            pygame.mixer.music.play(-1, fade_ms=1000)
            
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: running = False
                self.handle_input(event)
            self.update()
            self.render()
            self.clock.tick(FPS)
        self.save_player_data()
        pygame.quit()
        sys.exit()

    def handle_input(self, event):
        if self.game_state in ["start_menu", "game_over", "paused", "customize"]:
            self.ui_manager.handle_events(event)
        if event.type != pygame.KEYDOWN: return
        if event.key == pygame.K_m: self.toggle_mute()
        
        if self.game_state == "playing":
            if event.key in [pygame.K_p, pygame.K_ESCAPE]: self.set_state("paused")
            dir_map = {
                (pygame.K_UP, pygame.K_w): pygame.Vector2(0, -1), (pygame.K_DOWN, pygame.K_s): pygame.Vector2(0, 1),
                (pygame.K_LEFT, pygame.K_a): pygame.Vector2(-1, 0), (pygame.K_RIGHT, pygame.K_d): pygame.Vector2(1, 0),
            }
            for keys, direction in dir_map.items():
                if event.key in keys and (self.snake.direction.length() == 0 or self.snake.direction.dot(direction) == 0):
                    self.snake.direction = direction; break

    def update(self):
        if self.game_state != "playing": return
        now = pygame.time.get_ticks()
        if now - self.last_snake_update > self.snake_update_interval:
            self.snake.update(); self.last_snake_update = now
        
        if self.snake.get_head_position() == self.food.position: self.eat_food()
        
        for p_up in self.power_ups[:]:
            if self.snake.get_head_position() == p_up.position:
                self.snake.add_power_up(p_up.type)
                self.power_ups.remove(p_up)
                if self.assets.sounds.get('powerup'): self.assets.sounds['powerup'].play()
        
        collision_type = self.snake.check_collision(self.bouncy_walls)
        if collision_type == "bounce": self.handle_bounce()
        elif collision_type is not None: self.game_over(); return
        
        if self.combo_timer > 0: self.combo_timer -= self.clock.get_time()
        else: self.combo_count = 0
        if self.screen_shake_timer > 0: self.screen_shake_timer -= self.clock.get_time()
        
        self.update_snake_expression()
        self.snake.update_power_ups()
        self.spawn_power_ups()
        for p in self.particles[:]:
            p.update()
            if not p.alive: self.particles.remove(p)

    def eat_food(self):
        self.player_data['total_food_eaten'] += 1
        self.update_mission(self.food.type)
        self.snake.grow()
        self.score += 10
        self.food.randomize_position(self.snake.body)
        if self.assets.sounds.get('eat'): self.assets.sounds['eat'].play()
        
        for _ in range(20): self.particles.append(Particle(self.snake.get_head_pixel_pos(self.get_play_area_rect().topleft), self.food.color))

        self.combo_count = self.combo_count + 1 if self.combo_timer > 0 else 1
        self.combo_timer = COMBO_WINDOW
        
        if self.combo_count >= 3:
            self.score += 30; self.combo_count = 0; self.screen_shake_timer = SCREEN_SHAKE_DURATION
            self.snake.eye_state = 'dizzy'; self.snake.dizzy_timer = 30 # half a second
            if self.assets.sounds.get('combo'): self.assets.sounds['combo'].play()

    def spawn_power_ups(self):
        now = pygame.time.get_ticks()
        rate = DIFFICULTY_LEVELS[self.difficulty]['powerup_spawn_rate']
        if now - self.power_up_spawn_timer > rate and len(self.power_ups) < 2:
            self.power_ups.append(PowerUp(self.get_play_area_rect(), self.snake.body + [self.food.position]))
            self.power_up_spawn_timer = now

    def game_over(self):
        if self.assets.sounds.get('game_over'): self.assets.sounds['game_over'].play()
        if self.score > self.high_score:
            self.high_score = self.score
            self.player_data['high_score'] = self.score
            self.new_high_score = True
            if self.assets.sounds.get('new_highscore'): self.assets.sounds['new_highscore'].play()
            for _ in range(100):
                self.particles.append(Particle((random.randint(0, SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT)), 
                    (random.randint(200,255), random.randint(200,255), random.randint(200,255)), lifespan=120))
        self.check_unlocks()
        self.save_player_data()
        self.set_state("game_over")

    def load_player_data(self) -> dict:
        default_data = {
            "high_score": 0, "total_food_eaten": 0, "current_skin": "Default",
            "unlocks": {"skins": {"Default": True, "Tiger": False, "Rainbow": False}, "themes": {}}
        }
        try:
            with open("player_data.json", "r") as f: 
                data = json.load(f)
                # Ensure all keys from default_data are present
                for key, value in default_data.items():
                    data.setdefault(key, value)
                return data
        except (FileNotFoundError, json.JSONDecodeError): return default_data

    def save_player_data(self):
        try:
            with open("player_data.json", "w") as f: json.dump(self.player_data, f, indent=4)
        except IOError: print("Error saving player data.")

    def check_unlocks(self):
        if self.high_score >= 100 and not self.player_data['unlocks']['skins']['Tiger']:
            self.player_data['unlocks']['skins']['Tiger'] = True
        if self.player_data['total_food_eaten'] >= 250 and not self.player_data['unlocks']['skins']['Rainbow']:
            self.player_data['unlocks']['skins']['Rainbow'] = True

    def generate_bouncy_walls(self):
        self.bouncy_walls.clear()
        for i in range(5):
            self.bouncy_walls.append(pygame.Vector2(0, GRID_HEIGHT // 2 - 2 + i))
            self.bouncy_walls.append(pygame.Vector2(GRID_WIDTH - 1, GRID_HEIGHT // 2 - 2 + i))

    def handle_bounce(self):
        head = self.snake.get_head_position()
        if head.x == 0: self.snake.direction.x = 1
        elif head.x == GRID_WIDTH - 1: self.snake.direction.x = -1
        if self.assets.sounds.get('bounce'): self.assets.sounds['bounce'].play()

    def update_snake_expression(self):
        if self.snake.eye_state == 'dizzy': return
        is_near_powerup = False
        head = self.snake.get_head_position()
        for p_up in self.power_ups:
            if head.distance_to(p_up.position) < 4:
                is_near_powerup = True; break
        self.snake.eye_state = 'wide' if is_near_powerup else 'normal'

    def generate_mission(self):
        missions = [
            {"type": "eat_food_type", "food": "apple", "target": 7, "reward": 50},
            {"type": "eat_food_type", "food": "banana", "target": 5, "reward": 50},
            {"type": "get_combo", "target": 4, "reward": 75},
        ]
        chosen = random.choice(missions)
        self.current_mission = {"progress": 0, "completed": False, **chosen}
        if chosen['type'] == 'eat_food_type':
            self.current_mission['text'] = f"Eat {chosen['target']} {chosen['food'].title()}s"
        elif chosen['type'] == 'get_combo':
            self.current_mission['text'] = f"Get a combo of {chosen['target']}"

    def update_mission(self, food_type):
        if self.current_mission['completed']: return
        mission_type = self.current_mission['type']
        if mission_type == 'eat_food_type' and self.current_mission['food'] == food_type:
            self.current_mission['progress'] += 1
        # Combo mission progress is handled in eat_food
        if self.current_mission['progress'] >= self.current_mission['target']:
            self.current_mission['completed'] = True
            self.score += self.current_mission['reward']
            if self.assets.sounds.get('mission_complete'): self.assets.sounds['mission_complete'].play()
    
    def draw_background(self):
        self.screen.fill(PALETTE['background'])
        stars = self.assets.backgrounds['stars']
        for star in stars:
            star[0] -= star[2] * 0.5
            if star[0] < 0:
                star[0] = SCREEN_WIDTH; star[1] = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(self.screen, (255, 255, 255), (star[0], star[1]), star[2])

    def render(self):
        offset = (random.randint(-S, S), random.randint(-S, S)) if (S:=SCREEN_SHAKE_INTENSITY) and self.screen_shake_timer > 0 else (0,0)
        self.draw_background()

        if self.game_state == "start_menu": self.ui_manager.draw_start_menu(self.screen)
        elif self.game_state == "customize": self.ui_manager.draw_customize_menu(self.screen, self.current_skin)
        else:
            self.render_playing(offset)
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            if self.game_state in ["paused", "game_over"]:
                overlay.fill((0, 0, 0, 150)); self.screen.blit(overlay, (0,0))
            if self.game_state == "paused": self.ui_manager.draw_paused_menu(self.screen)
            elif self.game_state == "game_over": self.ui_manager.draw_game_over_menu(self.screen, self.score, self.high_score, self.new_high_score)
        
        if self.transition_alpha > 0:
            self.transition_alpha -= 15
            transition_surf = pygame.Surface(self.screen.get_size()); transition_surf.fill((0,0,0))
            transition_surf.set_alpha(self.transition_alpha); self.screen.blit(transition_surf, (0,0))

        pygame.display.flip()

    def render_playing(self, offset: Tuple[int, int]):
        play_area_rect = self.get_play_area_rect()
        play_area_surf = pygame.Surface(play_area_rect.size, pygame.SRCALPHA)
        play_area_surf.fill(PALETTE['grid_background'] + (200,))
        self.screen.blit(play_area_surf, play_area_rect.topleft)
        
        origin = play_area_rect.topleft
        # Draw bouncy walls
        for wall_pos in self.bouncy_walls:
             pygame.draw.rect(self.screen, PALETTE['bouncy_wall'], (origin[0] + wall_pos.x * TILE_SIZE, origin[1] + wall_pos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE), border_radius=5)

        self.snake.draw(self.screen, self.assets, origin, offset, self.current_skin, self.color_blind_mode)
        self.food.draw(self.screen, self.assets, origin, offset)
        for p_up in self.power_ups: p_up.draw(self.screen, self.assets, origin, offset)
        for p in self.particles: p.draw(self.screen, offset)

        self.ui_manager.draw_playing_ui(self.screen, self.score, self.high_score, self.snake, self.current_mission)
    
    def toggle_difficulty(self):
        levels = list(DIFFICULTY_LEVELS.keys())
        self.difficulty = levels[(levels.index(self.difficulty) + 1) % len(levels)]
        self.set_state("start_menu")

    def toggle_cb_mode(self): self.color_blind_mode = not self.color_blind_mode; self.set_state("start_menu")
    def toggle_slow_mode(self): self.slow_mode = not self.slow_mode; self.set_state("start_menu")
    def select_skin(self, skin_name): self.current_skin = skin_name; self.player_data['current_skin'] = skin_name; self.set_state("customize")

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            pygame.mixer.music.stop()
        else:
            pygame.mixer.music.play(-1, fade_ms=1000)
        self.set_state("start_menu")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # Important Note for Custom Font:
    # For the best experience, download the "Fredoka One" font from Google Fonts.
    # Create an 'assets' folder next to this script.
    # Place the font file 'FredokaOne-Regular.ttf' inside the 'assets' folder.
    # Also add the required .wav and .ogg sound files to the 'assets' folder.
    game = Game()
    game.run()


