# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

import logging
import os
import random
import socket
import select
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

import pygame
from .state import State

if TYPE_CHECKING:
    from client import LocalPygameClient

logger = logging.getLogger(__name__)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

UDP_IP = "0.0.0.0"
UDP_PORT1 = 5005
UDP_PORT2 = 5006

GESTURES = {
    "11111": "ABERTO",
    "01100": "PAZ",
    "10000": "JOIA",
    "00001": "MINDINHO",
    "10001": "HANG_LOOSE",
    "11100": "TRES",
    "11110": "QUATRO",
    "01001": "ESPECIAL",
}
GESTURE_KEYS = ["11111", "01100", "10000", "00001", "10001", "11100", "11110"]


class Player:
    def __init__(self):
        self.hp = 100
        self.special_charges = 0
        self.max_special_charges = 2
        self.last_sequence_end_symbol = None
        self.target_sequence = self.generate_new_sequence(4)
        self.current_step = 0
        self.sequence_start_time = pygame.time.get_ticks()

    def generate_new_sequence(self, length):
        available_first = [k for k in GESTURE_KEYS if k != self.last_sequence_end_symbol]
        first_symbol = random.choice(available_first)
        
        remaining = [k for k in GESTURE_KEYS if k != first_symbol]
        rest = random.sample(remaining, length - 1)
        
        seq = [first_symbol] + rest
        self.last_sequence_end_symbol = seq[-1]
        return seq

    def reset_sequence(self):
        self.current_step = 0
        self.sequence_start_time = pygame.time.get_ticks()
        self.target_sequence = self.generate_new_sequence(4)

    def check_timeout(self, current_time, timeout_ms=10000):
        if (current_time - self.sequence_start_time) > timeout_ms:
            import hardware
            hardware.error_sound()
            self.reset_sequence()
            return True
        return False


class CombatPhase(Enum):
    BEGIN = auto()
    ACTION = auto()
    END = auto()


class BattleState(State):
    name = "CombatState"

    def __init__(self, client: LocalPygameClient, input_mode="UDP") -> None:
        super().__init__(client)
        self.input_mode = input_mode

        import hardware
        hardware.init_hardware()

        self.font = pygame.font.SysFont("Arial", 20)
        self.hud_font = pygame.font.SysFont("Arial", 15)
        self.big_font = pygame.font.SysFont("Arial", 45)
        self.alert_font = pygame.font.SysFont("Arial", 16, bold=True)

        self.gesture_images = {}
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        for key in GESTURES.keys():
            img_path = os.path.join(assets_dir, f"{key}.png")
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.smoothscale(img, (45, 60))
                self.gesture_images[key] = img

        self.p1 = Player()
        self.p2 = Player()

        # Nomes para display (mesmo do original, mas adaptado para o novo modelo)
        self.p1_name = "Pikachu (P1)"
        self.p2_name = "Charmander (P2)"

        if self.input_mode == "UDP":
            self.sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock1.bind((UDP_IP, UDP_PORT1))
            self.sock1.setblocking(False)

            self.sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock2.bind((UDP_IP, UDP_PORT2))
            self.sock2.setblocking(False)

            self.sockets_list = [self.sock1, self.sock2]

        # -------------------------------------------------------------
        # CARREGAMENTO DOS CAMINHOS DOS ARQUIVOS E SPRITES
        # -------------------------------------------------------------
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bg_path = os.path.join(BASE_DIR, "assets", "gradient_blue.png")
        sheet_path = os.path.join(BASE_DIR, "assets", "cobble_island_sheet.png")
        bicho1_path = os.path.join(BASE_DIR, "assets", "seven.png")
        bicho2_path = os.path.join(BASE_DIR, "assets", "six.png")

        screen_size = self.client.surface.get_size()

        if os.path.exists(bg_path):
            raw_bg = pygame.image.load(bg_path).convert()
            self.background_surface = pygame.transform.scale(raw_bg, screen_size)
        else:
            self.background_surface = None

        self.island_back = None
        self.island_front = None

        if os.path.exists(sheet_path):
            sheet = pygame.image.load(sheet_path).convert_alpha()
            sheet_width = sheet.get_width()
            sheet_height = sheet.get_height()

            SCALE = 2.5
            w = sheet_width // 2
            h = sheet_height

            # Plataforma Inimigo
            self.island_back = pygame.transform.smoothscale(
                sheet.subsurface(pygame.Rect(0, 0, w, h)),
                (int(w * SCALE), int(h * SCALE)),
            )
            # Plataforma Jogador
            self.island_front = pygame.transform.smoothscale(
                sheet.subsurface(pygame.Rect(w, 0, w, h)),
                (int(w * SCALE), int(h * SCALE)),
            )

        MON_SCALE = 0.35
        # Bicho 1 (Geralmente Inimigo/Oponente)
        if os.path.exists(bicho1_path):
            raw_b1 = pygame.image.load(bicho1_path).convert_alpha()
            self.bicho1_sprite = pygame.transform.smoothscale(
                raw_b1,
                (
                    int(raw_b1.get_width() * MON_SCALE),
                    int(raw_b1.get_height() * MON_SCALE),
                ),
            )
        else:
            self.bicho1_sprite = None

        # Bicho 2 (Geralmente Jogador)
        if os.path.exists(bicho2_path):
            raw_b2 = pygame.image.load(bicho2_path).convert_alpha()
            self.bicho2_sprite = pygame.transform.smoothscale(
                raw_b2,
                (
                    int(raw_b2.get_width() * MON_SCALE),
                    int(raw_b2.get_height() * MON_SCALE),
                ),
            )
        else:
            self.bicho2_sprite = None

        self.phase: CombatPhase = CombatPhase.BEGIN
        self.message_text: str = ""
        self.message_timer: float = 0.0
        self.is_displaying_message: bool = False

    def _set_message(self, text: str, duration: float = 2.0) -> None:
        self.message_text = text
        self.message_timer = duration
        self.is_displaying_message = True

    def process_gesture(self, player_id, gesture_str):
        if self.phase != CombatPhase.ACTION:
            return

        player = self.p1 if player_id == 1 else self.p2
        opponent = self.p2 if player_id == 1 else self.p1
        attacker_name = self.p1_name if player_id == 1 else self.p2_name

        if gesture_str == "01001" and player.special_charges >= player.max_special_charges:
            import hardware
            hardware.special_sound()
            player.special_charges = 0
            if player_id == 1:
                opponent.hp -= 20
                opponent.reset_sequence()
                self._set_message(f"{attacker_name} usou o ESPECIAL! Oponente atordoado!", duration=3.0)
            else:
                opponent.hp -= 25
                player.hp = min(100, player.hp + 25)
                self._set_message(f"{attacker_name} usou o ESPECIAL! Curou 25 HP!", duration=3.0)
            return

        if gesture_str == player.target_sequence[player.current_step]:
            player.current_step += 1
            if player.current_step >= len(player.target_sequence):
                import hardware
                hardware.success_sound()
                
                opponent.hp -= 25
                if player.special_charges < player.max_special_charges:
                    player.special_charges += 1
                player.reset_sequence()

                self._set_message(
                    f"{attacker_name} completou a sequência e atacou!", duration=2.0
                )

    def handle_input_keyboard(self, event):
        if event.key == pygame.K_q:
            self.process_gesture(1, "11111")
        elif event.key == pygame.K_w:
            self.process_gesture(1, "01100")
        elif event.key == pygame.K_e:
            self.process_gesture(1, "10000")
        elif event.key == pygame.K_r:
            self.process_gesture(1, "00001")
        elif event.key == pygame.K_t:
            self.process_gesture(1, "10001")
        elif event.key == pygame.K_y:
            self.process_gesture(1, "11100")
        elif event.key == pygame.K_u:
            self.process_gesture(1, "11110")
        elif event.key == pygame.K_a:
            self.process_gesture(1, "01001")

        elif event.key == pygame.K_z:
            self.process_gesture(2, "11111")
        elif event.key == pygame.K_x:
            self.process_gesture(2, "01100")
        elif event.key == pygame.K_c:
            self.process_gesture(2, "10000")
        elif event.key == pygame.K_v:
            self.process_gesture(2, "00001")
        elif event.key == pygame.K_b:
            self.process_gesture(2, "10001")
        elif event.key == pygame.K_n:
            self.process_gesture(2, "11100")
        elif event.key == pygame.K_m:
            self.process_gesture(2, "11110")
        elif event.key == pygame.K_l:
            self.process_gesture(2, "01001")

    def process_event(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.phase == CombatPhase.END:
                    if event.key == pygame.K_RETURN:
                        self.client.state_manager.pop()
                        return
                    elif event.key == pygame.K_SPACE:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        return
                if self.input_mode == "KEYBOARD":
                    self.handle_input_keyboard(event)

    def handle_input_udp(self):
        try:
            readable, _, _ = select.select(self.sockets_list, [], [], 0)
            for s in readable:
                data, addr = s.recvfrom(1024)
                msg_raw = data.decode("utf-8").strip()
                porta = s.getsockname()[1]

                # Trata prefixos antigos por garantia
                if msg_raw.startswith("P1:"):
                    msg_raw = msg_raw.split(":", 1)[1]
                elif msg_raw.startswith("P2:"):
                    msg_raw = msg_raw.split(":", 1)[1]

                # Se o script da câmera envia o array Python puro tipo "[1, 0, 1, 1, 0]", converte para "10110"
                msg_clean = (
                    msg_raw.replace("[", "")
                    .replace("]", "")
                    .replace(", ", "")
                    .replace(",", "")
                )

                if porta == UDP_PORT1:
                    print(f"Recebido no raspberry (P1): {msg_clean}")
                    self.process_gesture(1, msg_clean)
                elif porta == UDP_PORT2:
                    print(f"Recebido no raspberry (P2): {msg_clean}")
                    self.process_gesture(2, msg_clean)

        except BlockingIOError:
            pass
        except Exception as e:
            logger.error(f"UDP Error: {e}")

    def check_logic(self):
        current_time = pygame.time.get_ticks()
        if self.p1.check_timeout(current_time):
            pass  # Pode adicionar um efeito sonoro ou visual de erro aqui
        if self.p2.check_timeout(current_time):
            pass

        if self.p1.hp <= 0 and self.phase != CombatPhase.END:
            self._set_message(
                f"{self.p1_name} desmaiou! {self.p2_name} Venceu!", duration=5.0
            )
            self.phase = CombatPhase.END
            self.end_time = pygame.time.get_ticks()
        elif self.p2.hp <= 0 and self.phase != CombatPhase.END:
            self._set_message(
                f"{self.p2_name} desmaiou! {self.p1_name} Venceu!", duration=5.0
            )
            self.phase = CombatPhase.END
            self.end_time = pygame.time.get_ticks()

    def update(self, dt: float) -> None:
        super().update(dt)

        if self.is_displaying_message:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.is_displaying_message = False

        if self.phase == CombatPhase.BEGIN and not self.is_displaying_message:
            self.phase = CombatPhase.ACTION
            # Reset timer de ambos os jogadores quando a ação começar
            self.p1.reset_sequence()
            self.p2.reset_sequence()

        if self.phase == CombatPhase.ACTION:
            if self.input_mode == "UDP":
                self.handle_input_udp()
            self.check_logic()
            
            import hardware
            hardware.update_lcd(self.p1.hp, self.p2.hp)

    def draw_player_hud(self, surface, player, x_offset, color, align_right=False):
        # Barra de HP
        pygame.draw.rect(surface, WHITE, (x_offset, 30, 300, 25))
        hp_width = max(0, (player.hp / 100) * 300)
        hp_x = x_offset
        if align_right:
            hp_x = x_offset + (300 - hp_width)

        pygame.draw.rect(
            surface, GREEN if player.hp > 30 else RED, (hp_x, 30, hp_width, 25)
        )

        # Sequência alvo
        box_w = 70
        box_h = 60
        spacing = 75
        for i, gesture_bits in enumerate(player.target_sequence):
            icon_x = x_offset + (i * spacing)

            icon_y = 70

            if i < player.current_step:
                box_color = GREEN
                text_color = BLACK
            elif i == player.current_step:
                box_color = YELLOW
                text_color = BLACK
            else:
                box_color = GRAY
                text_color = WHITE

            pygame.draw.rect(
                surface, box_color, (icon_x, icon_y, box_w, box_h), border_radius=5
            )
            if i == player.current_step:
                pygame.draw.rect(
                    surface, WHITE, (icon_x, icon_y, box_w, box_h), 3, border_radius=5
                )

            if self.input_mode == "KEYBOARD":
                if player == self.p1:
                    keys_map = {"11111": "Q", "01100": "W", "10000": "E", "00001": "R", "10001": "T", "11100": "Y", "11110": "U"}
                else:
                    keys_map = {"11111": "Z", "01100": "X", "10000": "C", "00001": "V", "10001": "B", "11100": "N", "11110": "M"}
                
                gesture_name = keys_map.get(gesture_bits, "???")
                words = gesture_name.split()
                for w_idx, word in enumerate(words):
                    text_surf = self.hud_font.render(word, True, text_color)
                    text_rect = text_surf.get_rect(
                        center=(
                            icon_x + box_w // 2,
                            icon_y + 30 + (w_idx * 15) - (len(words) - 1) * 7,
                        )
                    )
                    surface.blit(text_surf, text_rect)
            else:
                img = self.gesture_images.get(gesture_bits)
                if img:
                    img_rect = img.get_rect(center=(icon_x + box_w // 2, icon_y + box_h // 2))
                    surface.blit(img, img_rect)
                else:
                    # fallback to text if image missing
                    gesture_name = GESTURES.get(gesture_bits, "???")
                    words = gesture_name.split()
                    for w_idx, word in enumerate(words):
                        text_surf = self.hud_font.render(word, True, text_color)
                        text_rect = text_surf.get_rect(
                            center=(
                                icon_x + box_w // 2,
                                icon_y + 30 + (w_idx * 15) - (len(words) - 1) * 7,
                            )
                        )
                        surface.blit(text_surf, text_rect)

        # Barra de tempo (10 segundos)
        if self.phase == CombatPhase.END:
            current_time = getattr(self, "end_time", pygame.time.get_ticks())
        else:
            current_time = pygame.time.get_ticks()
            
        time_elapsed = current_time - player.sequence_start_time
        time_left_ratio = 1.0 - (time_elapsed / 10000.0)
        if time_left_ratio < 0:
            time_left_ratio = 0

        timer_w = 300
        timer_x = x_offset
        pygame.draw.rect(surface, RED, (timer_x, 140, timer_w, 10))

        active_timer_w = int(timer_w * time_left_ratio)
        active_timer_x = timer_x

        pygame.draw.rect(surface, WHITE, (active_timer_x, 140, active_timer_w, 10))

        # Bolinhas de Especial (Special)
        special_y = 165
        for i in range(player.max_special_charges):
            cx = timer_x + 15 + (i * 30)
            
            if i < player.special_charges:
                color = YELLOW if player.special_charges >= player.max_special_charges else (100, 200, 255)
            else:
                color = GRAY
                
            pygame.draw.circle(surface, color, (cx, special_y), radius=10)
            pygame.draw.circle(surface, WHITE, (cx, special_y), radius=10, width=2)

        if player.special_charges >= player.max_special_charges:
            spec_key = "A" if player == self.p1 else "L"
            txt = f"ESPECIAL PRONTO! [{spec_key}]" if self.input_mode == "KEYBOARD" else "ESPECIAL PRONTO! [ROCK 🤟]"
            
            t_surf = self.alert_font.render(txt, True, YELLOW)
            x_pos = timer_x + 70
            if align_right:
                x_pos = timer_x + timer_w - t_surf.get_width()
                
            y_pos = special_y - t_surf.get_height() // 2
            
            self.draw_text_with_shadow(surface, txt, x_pos, y_pos, self.alert_font, (255, 200, 0))

    def draw_text_with_shadow(
        self, surface, text, x, y, font, text_color, shadow_color=BLACK
    ):
        shadow = font.render(text, True, shadow_color)
        surface.blit(shadow, (x + 2, y + 2))
        main_text = font.render(text, True, text_color)
        surface.blit(main_text, (x, y))

    def draw(self, surface: pygame.Surface) -> None:
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        if self.background_surface:
            surface.blit(self.background_surface, (0, 0))
        else:
            surface.fill((40, 50, 60))

        if self.island_back:
            back_x = int(screen_w * 0.55)
            back_y = int(screen_h * 0.22)
            surface.blit(self.island_back, (back_x, back_y))
            if self.bicho1_sprite:
                island_w, island_h = self.island_back.get_size()
                sprite_w, sprite_h = self.bicho1_sprite.get_size()
                b1_x = back_x + (island_w // 2) - (sprite_w // 2)
                b1_y = back_y + int(island_h * 0.8) - sprite_h
                surface.blit(self.bicho1_sprite, (b1_x, b1_y))

        if self.island_front:
            front_x = int(screen_w * 0.05)
            front_y = int(screen_h * 0.50)
            surface.blit(self.island_front, (front_x, front_y))
            if self.bicho2_sprite:
                island_w, island_h = self.island_front.get_size()
                sprite_w, sprite_h = self.bicho2_sprite.get_size()
                b2_x = front_x + (island_w // 2) - (sprite_w // 2)
                b2_y = front_y + int(island_h * 0.7) - sprite_h
                surface.blit(self.bicho2_sprite, (b2_x, b2_y))

        # Desenhar interfaces HUD no topo
        self.draw_player_hud(surface, self.p1, 20, BLUE, align_right=False)
        self.draw_player_hud(surface, self.p2, screen_w - 320, RED, align_right=True)

        # Desenhar nomes próximos à barra de HP com sombreamento
        self.draw_text_with_shadow(surface, self.p1_name, 20, 5, self.font, WHITE)

        name2_surf = self.font.render(self.p2_name, True, WHITE)
        self.draw_text_with_shadow(
            surface,
            self.p2_name,
            screen_w - 20 - name2_surf.get_width(),
            5,
            self.font,
            WHITE,
        )

        if self.is_displaying_message:
            dialog_rect = pygame.Rect(20, screen_h - 140, screen_w - 40, 120)
            pygame.draw.rect(surface, (20, 20, 30), dialog_rect)
            pygame.draw.rect(surface, (255, 255, 255), dialog_rect, 3)
            txt_surface = self.font.render(self.message_text, True, (255, 255, 255))
            surface.blit(txt_surface, (dialog_rect.x + 20, dialog_rect.y + 20))

            if self.phase == CombatPhase.END:
                prompt = self.font.render(
                    "Pressione [ENTER] ou [ESPAÇO] para sair", True, (255, 255, 0)
                )
                surface.blit(prompt, (dialog_rect.x + 20, dialog_rect.y + 60))

        super().draw(surface)
