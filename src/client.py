
from __future__ import annotations

import logging
import time
from enum import Enum, auto
from typing import Any

import pygame

from state.state import State
from state.stateDrawer import StateDrawer
from state.stateManager import StateManager


logger = logging.getLogger(__name__)


class ClientState(Enum):
    """Ciclo de vida do processo principal do jogo."""
    RUNNING = auto()
    EXITING = auto()
    DONE = auto()


class LocalPygameClient:
    """
    Cliente principal simplificado.
    Gerencia a janela, o Game Loop (Fixed Timestep) e a pilha de estados (State Stack).
    """

    @classmethod
    def create(cls, config, context: Any = None) -> LocalPygameClient:
        """Inicializa o cliente do jogo de forma segura."""
        try:
            client = LocalPygameClient(config, context)
            logger.info("Cliente inicializado com sucesso.")
            return client
        except Exception as e:
            logger.critical(f"Erro ao inicializar o cliente: {e}")
            raise

    def __init__(self, config, context: Any = None) -> None:
        self.config = config
        self.context = context
        self.state = ClientState.RUNNING

        # Configuração nativa de tela do Pygame
        resolution = getattr(context, "resolution", (800, 600))
        self.screen = pygame.display.get_surface()
        if self.screen is None:
            self.screen = pygame.display.set_mode(resolution)
        
        self.surface = self.screen

        # Gerenciadores do Motor de Estados
        self.state_manager = StateManager(self)
        self.state_drawer = StateDrawer(self.screen, self.state_manager)

    def main(self) -> None:
        target_fps = getattr(self.config, "fps", 60)
        frame_length = 1.0 / target_fps

        last_time = time.time()
        accumulator = 0.0

        while self.state != ClientState.DONE:
            if self.state == ClientState.RUNNING:
                now = time.time()
                dt = now - last_time
                last_time = now

                if dt > 0.25:
                    dt = 0.25

                accumulator += dt

                self.process_events()

                while accumulator >= frame_length:
                    self.update(frame_length)
                    accumulator -= frame_length

                self.draw()
                pygame.display.update()

            elif self.state == ClientState.EXITING:
                self.perform_cleanup()
                self.state = ClientState.DONE

    def process_events(self) -> None:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.state = ClientState.EXITING

        if self.state_manager.active_states:
            self.state_manager.active_states[-1].process_event(events)

    def update(self, dt: float) -> None:
        if hasattr(self.state_manager, "update"):
            self.state_manager.update(dt)
        elif self.state_manager.active_states:
            self.state_manager.active_states[-1].update(dt)

    def draw(self) -> None:
        to_draw: list[State] = []
        full_screen = self.surface.get_rect()
        for state in self.state_manager.active_states:
            to_draw.append(state)

            if (
                not state.transparent
                and state.rect == full_screen
                and not state.force_draw
            ):
                break

        for state in reversed(to_draw):
            state.draw(self.surface)

    def perform_cleanup(self) -> None:
        """Limpa recursos e fecha o Pygame com segurança ao sair."""
        logger.info("Encerrando a aplicação...")
        pygame.quit()