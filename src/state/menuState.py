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
        self.text = self.font.render("Pressione ENTER para iniciar", True, (255, 255, 255))
        self.text_rect = self.text.get_rect(center=self.rect.center)

    def process_event(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    battleState = BattleState(self.client)
                    self.client.state_manager.change_state(battleState)
                    print("ENTER pressionado! Mudando de tela...")


    def update(self, dt: float) -> None:
        super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((30, 30, 40)) 
        surface.blit(self.text, self.text_rect)
        super().draw(surface)