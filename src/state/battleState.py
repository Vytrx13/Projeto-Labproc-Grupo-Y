# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

import logging
import os
from collections import deque
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Dict, Optional

import pygame
from .state import State

if TYPE_CHECKING:
    from client import LocalPygameClient

logger = logging.getLogger(__name__)


class CombatPhase(Enum):
    """Fases do loop de combate."""
    BEGIN = auto()       # Apresentação dos Pokémon/Treinadores
    DECISION = auto()    # Jogador e IA escolhem seus golpes no menu
    ACTION = auto()      # Os golpes são executados na ordem de velocidade
    CHECK_HP = auto()    # Verifica se alguém desmaiou/ganhou XP
    END = auto()         # Fim do combate e transição de volta


class BattleState(State):
    """
    Estado responsável pela lógica e renderização da Batalha.
    Gerencia turnos, ordem de ação e caixa de texto bloqueante.
    """

    name = "CombatState"

    def __init__(self, client: LocalPygameClient) -> None:
        super().__init__(client)

        self.player_mon = {"name": "Pikachu", "hp": 50, "speed": 12}
        self.enemy_mon = {"name": "Charmander", "hp": 50, "speed": 10}

        # -------------------------------------------------------------
        # 1. CARREGAMENTO DOS CAMINHOS DOS ARQUIVOS
        # -------------------------------------------------------------
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        bg_path = os.path.join(BASE_DIR, "assets", "gradient_blue.png")
        sheet_path = os.path.join(BASE_DIR, "assets", "cobble_island_sheet.png")
        bicho1_path = os.path.join(BASE_DIR, "assets", "seven.png")
        bicho2_path = os.path.join(BASE_DIR, "assets", "six.png")

        screen_size = self.client.surface.get_size()

        # A) Fundo (Background)
        if os.path.exists(bg_path):
            raw_bg = pygame.image.load(bg_path).convert()
            self.background_surface = pygame.transform.scale(raw_bg, screen_size)
        else:
            self.background_surface = None

        # B) Plataformas (Islands)
        self.island_back = None
        self.island_front = None

        if os.path.exists(sheet_path):
            sheet = pygame.image.load(sheet_path).convert_alpha()
            sheet_width = sheet.get_width()
            sheet_height = sheet.get_height()

            SCALE = 2.5
            w = sheet_width // 2  # Metade da largura para cada plataforma
            h = sheet_height

            # Plataforma Oponente (Inimigo)
            self.island_back = pygame.transform.smoothscale(
                sheet.subsurface(pygame.Rect(0, 0, w, h)),
                (int(w * SCALE), int(h * SCALE))
            )

            # Plataforma Jogador
            self.island_front = pygame.transform.smoothscale(
                sheet.subsurface(pygame.Rect(w, 0, w, h)),
                (int(w * SCALE), int(h * SCALE))
            )

        # C) Sprites dos Monstros
        MON_SCALE = 0.35  # Ajuste a escala se quiser aumentar os sprites dos monstros

        # Bicho 1 (Geralmente Inimigo/Oponente)
        if os.path.exists(bicho1_path):
            raw_b1 = pygame.image.load(bicho1_path).convert_alpha()
            self.bicho1_sprite = pygame.transform.smoothscale(
                raw_b1, 
                (int(raw_b1.get_width() * MON_SCALE), int(raw_b1.get_height() * MON_SCALE))
            )
            
        else:
            self.bicho1_sprite = None

        # Bicho 2 (Geralmente Jogador)
        if os.path.exists(bicho2_path):
            raw_b2 = pygame.image.load(bicho2_path).convert_alpha()
            self.bicho2_sprite = pygame.transform.smoothscale(
                raw_b2, 
                (int(raw_b2.get_width() * MON_SCALE), int(raw_b2.get_height() * MON_SCALE))
            )
        else:
            self.bicho2_sprite = None
        # -------------------------------------------------------------

        # Controle da Máquina de Estados de Batalha
        self.phase: CombatPhase = CombatPhase.BEGIN

        # Filas para processamento
        self.action_queue: deque[Dict[str, Any]] = deque()

        # Sistema de Caixa de Texto / Animação Bloqueante
        self.message_text: str = ""
        self.message_timer: float = 0.0
        self.is_displaying_message: bool = False

        # Interface gráfica simples
        self.font = pygame.font.SysFont("Arial", 24)

        # Inicia o combate
        self._set_message(f"Um {self.enemy_mon['name']} selvagem apareceu!", duration=2.5)

    def _set_message(self, text: str, duration: float = 2.0) -> None:
        """Exibe uma mensagem na tela e bloqueia o avanço da lógica pelo tempo estipulado."""
        self.message_text = text
        self.message_timer = duration
        self.is_displaying_message = True

    def is_blocked(self) -> bool:
        """Verifica se o combate está esperando uma animação/texto terminar."""
        return self.is_displaying_message

    def process_event(self, events: list[pygame.event.Event]) -> None:
        """Trata botões do jogador."""
        if self.is_blocked():
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.message_timer = 0.0
            return

        if self.phase == CombatPhase.DECISION:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self._register_turn_actions(player_move="Atacar")
                    elif event.key == pygame.K_2:
                        self._register_turn_actions(player_move="Fugir")

    def _register_turn_actions(self, player_move: str) -> None:
        """Calcula a ordem das ações com base na velocidade dos Pokémon."""
        if player_move == "Fugir":
            self.action_queue.append({"user": "player", "action": "Fugir"})
        else:
            player_speed = self.player_mon.get("speed", 10)
            enemy_speed = self.enemy_mon.get("speed", 8)

            player_action = {"user": "player", "action": "Atacar", "move": player_move}
            enemy_action = {"user": "enemy", "action": "Atacar", "move": "Investida"}

            if player_speed >= enemy_speed:
                self.action_queue.append(player_action)
                self.action_queue.append(enemy_action)
            else:
                self.action_queue.append(enemy_action)
                self.action_queue.append(player_action)

        self.phase = CombatPhase.ACTION

    def update(self, dt: float) -> None:
        super().update(dt)

        if self.is_displaying_message:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.is_displaying_message = False

        if self.is_blocked():
            return

        self.update_combat_phase()

    def update_combat_phase(self) -> None:
        """Controla a transição entre as fases do combate."""

        if self.phase == CombatPhase.BEGIN:
            self.phase = CombatPhase.DECISION

        elif self.phase == CombatPhase.DECISION:
            pass

        elif self.phase == CombatPhase.ACTION:
            if self.action_queue:
                action = self.action_queue.popleft()
                self._execute_action(action)
            else:
                self.phase = CombatPhase.CHECK_HP

        elif self.phase == CombatPhase.CHECK_HP:
            if self.enemy_mon["hp"] <= 0:
                self._set_message(f"{self.enemy_mon['name']} desmaiou! Você venceu!", duration=3.0)
                self.phase = CombatPhase.END
            elif self.player_mon["hp"] <= 0:
                self._set_message(f"{self.player_mon['name']} desmaiou! Você perdeu...", duration=3.0)
                self.phase = CombatPhase.END
            else:
                self.phase = CombatPhase.DECISION

        elif self.phase == CombatPhase.END:
            self.client.state_manager.pop()

    def _execute_action(self, action: Dict[str, Any]) -> None:
        """Aplica o efeito de um golpe ou fuga e exibe a mensagem correspondente."""
        user = action["user"]
        act_type = action["action"]

        if act_type == "Fugir":
            self._set_message("Você fugiu com segurança!", duration=2.0)
            self.phase = CombatPhase.END
            return

        if user == "player":
            damage = 15
            self.enemy_mon["hp"] = max(0, self.enemy_mon["hp"] - damage)
            self._set_message(
                f"{self.player_mon['name']} usou {action['move']} causando {damage} de dano!",
                duration=2.0
            )
        else:
            damage = 10
            self.player_mon["hp"] = max(0, self.player_mon["hp"] - damage)
            self._set_message(
                f"{self.enemy_mon['name']} inimigo usou {action['move']} causando {damage} de dano!",
                duration=2.0
            )

    def draw(self, surface: pygame.Surface) -> None:
        """Renderiza o cenário, plataformas, monstros e a interface."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        # 1. BACKGROUND
        if self.background_surface:
            surface.blit(self.background_surface, (0, 0))
        else:
            surface.fill((40, 50, 60))

        # 2. PLATAFORMA E MONSTRO INIMIGO (Canto Superior Direito)
        if self.island_back:
            back_x = int(screen_w * 0.55)
            back_y = int(screen_h * 0.22)
            surface.blit(self.island_back, (back_x, back_y))

            # Desenha o Bicho 1 sobre a plataforma de trás
            if self.bicho1_sprite:
            # Largura e Altura para cálculo do centro
                island_w, island_h = self.island_back.get_size()
                sprite_w, sprite_h = self.bicho1_sprite.get_size()

                # Centraliza perfeitamente no Eixo X
                b1_x = back_x + (island_w // 2) - (sprite_w // 2)

                # Posiciona os pés no centro do topo da plataforma (Eixo Y)
                b1_y = back_y + int(island_h * 0.8) - sprite_h

                surface.blit(self.bicho1_sprite, (b1_x, b1_y))

        # 3. PLATAFORMA E MONSTRO DO JOGADOR (Canto Inferior Esquerdo)
        if self.island_front:
            front_x = int(screen_w * 0.05)
            front_y = int(screen_h * 0.50)
            surface.blit(self.island_front, (front_x, front_y))

            # Desenha o Bicho 2 sobre a plataforma da frente
           
            if self.bicho2_sprite:
                island_w, island_h = self.island_front.get_size()
                sprite_w, sprite_h = self.bicho2_sprite.get_size()

                b2_x = front_x + (island_w // 2) - (sprite_w // 2)

                b2_y = front_y + int(island_h * 0.7) - sprite_h

                surface.blit(self.bicho2_sprite, (b2_x, b2_y))

        e_info = f"{self.enemy_mon['name']} - HP: {self.enemy_mon['hp']}/50"
        e_surface = self.font.render(e_info, True, (0, 0, 0))
        surface.blit(e_surface, (450, 40))

        p_info = f"{self.player_mon['name']} - HP: {self.player_mon['hp']}/50"
        p_surface = self.font.render(p_info, True, (0, 0, 0))
        surface.blit(p_surface, (50, 240))

        # --- HUD E MENSAGENS ---
        dialog_rect = pygame.Rect(20, 420, 760, 160)
        pygame.draw.rect(surface, (20, 20, 30), dialog_rect)
        pygame.draw.rect(surface, (255, 255, 255), dialog_rect, 3)

        if self.is_displaying_message:
            txt_surface = self.font.render(self.message_text, True, (255, 255, 255))
            surface.blit(txt_surface, (dialog_rect.x + 20, dialog_rect.y + 20))
        elif self.phase == CombatPhase.DECISION:
            prompt = self.font.render("Pressione [1] para Atacar | Pressione [2] para Fugir", True, (255, 255, 0))
            surface.blit(prompt, (dialog_rect.x + 20, dialog_rect.y + 20))

        super().draw(surface)