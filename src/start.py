# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

import logging
import pygame

from client import LocalPygameClient
from state.menuState import MenuState


class DummyConfig:
    title: str = "Meu Jogo Pokémon"
    width: int = 800
    height: int = 600
    fps: int = 60


class DummyContext:
    resolution: tuple[int, int] = (800, 600)


def launch_game() -> None:

    print("Iniciando o jogo...")
    pygame.init()
    pygame.font.init()

    config = DummyConfig()
    context = DummyContext()

    client = LocalPygameClient.create(config, context)

    initial_state = MenuState(client)
    client.state_manager.push(initial_state)

    client.main()


if __name__ == "__main__":
    launch_game()
