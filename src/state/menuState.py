# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

import pygame
from .state import State
from .battleState import BattleState


class MenuState(State):
    name = "MenuState"

    def __init__(self, client) -> None:
        super().__init__(client)
        self.font = pygame.font.SysFont("Arial", 32)
        self.title_font = pygame.font.SysFont("Arial", 48)
        self.options = ["Modo Visão Computacional", "Modo Keyboard"]
        self.modes = ["UDP", "KEYBOARD"]
        self.selected_index = 0

    def process_event(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    selected_mode = self.modes[self.selected_index]
                    battleState = BattleState(self.client, input_mode=selected_mode)
                    self.client.state_manager.push(battleState)

    def update(self, dt: float) -> None:
        super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((30, 30, 40)) 
        
        title = self.title_font.render("Selecione o Modo de Jogo", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.rect.centerx, 150))
        surface.blit(title, title_rect)

        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected_index else (255, 255, 255)
            text = self.font.render(option, True, color)
            rect = text.get_rect(center=(self.rect.centerx, 250 + i * 50))
            surface.blit(text, rect)
            
            if i == self.selected_index:
                cursor = self.font.render(">", True, color)
                cursor_rect = cursor.get_rect(midright=(rect.left - 10, rect.centery))
                surface.blit(cursor, cursor_rect)

        super().draw(surface)
