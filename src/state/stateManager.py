# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import pygame
    from .state import State

logger = logging.getLogger(__name__)


class StateManager:
    """
    Gerenciador da Pilha de Estados (State Stack).
    
    Permite empilhar telas (ex: menu de pause sobre o jogo)
    e desempilhar mantendo o estado anterior preservado.
    """

    def __init__(self, client: Any) -> None:
        self.client = client
        self.active_states: List[State] = []

    def push(self, state: State) -> None:
        """Pausa o estado atual e coloca um novo no topo da pilha."""
        if self.active_states:
            self.active_states[-1].pause()

        logger.debug(f"Pushed state: {state.name}")
        self.active_states.append(state)
        state.resume()

    def pop(self) -> State | None:
        """Remove e destrói o estado do topo, reativando o anterior."""
        if not self.active_states:
            return None

        popped_state = self.active_states.pop()
        popped_state.pause()
        popped_state.shutdown()
        logger.debug(f"Popped state: {popped_state.name}")

        if self.active_states:
            self.active_states[-1].resume()

        return popped_state

    def change_state(self, state: State) -> None:
        """Substitui o estado do topo limpando toda a pilha."""
        while self.active_states:
            popped = self.active_states.pop()
            popped.pause()
            popped.shutdown()

        self.push(state)

    def update(self, dt: float) -> None:
        """Atualiza apenas o estado no topo da pilha."""
        if self.active_states:
            self.active_states[-1].update(dt)

    def process_event(self, events: list[pygame.event.Event]) -> None:
        """Repassa os eventos apenas para o estado ativo."""
        if self.active_states:
            self.active_states[-1].process_event(events)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Renderização em pilha inteligente:
        Calcula de cima para baixo quais telas são visíveis e as desenha de baixo para cima.
        """
        to_draw: List[State] = []
        full_screen = surface.get_rect()

        # Otimização: Varre do topo para a base buscando a primeira tela opaca que cobre tudo
        for state in reversed(self.active_states):
            to_draw.append(state)

            if (
                not state.transparent
                and state.rect == full_screen
                and not state.force_draw
            ):
                break

        # Renderiza do fundo para a frente para manter a ordem das camadas
        for state in reversed(to_draw):
            state.draw(surface)