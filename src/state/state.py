# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from pygame.event import Event
    from pygame.surface import Surface

logger = logging.getLogger(__name__)


class State(ABC):
    name: str = "State"
    transparent: bool = False
    force_draw: bool = False

    def __init__(self, client: Any) -> None:
        self.client = client
        self.sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.rect: pygame.Rect = self.client.screen.get_rect()

    def process_event(self, events: list[Event]) -> None:
        pass

    def update(self, dt: float) -> None:
        self.sprites.update(dt)

    def draw(self, surface: Surface) -> None:
        self.sprites.draw(surface)

    def resume(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def shutdown(self) -> None:
        self.sprites.empty()