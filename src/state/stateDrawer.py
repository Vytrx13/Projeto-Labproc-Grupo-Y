from __future__ import annotations


from pygame.surface import Surface

from .stateManager import StateManager
from .state import State


class StateDrawer:
    def __init__(
        self,
        surface: Surface,
        state_manager: StateManager,
    ) -> None:
        """
        Responsável por desenhar os estados ativos na superfície informada,
        respeitando a transparência e a ordem de empilhamento.
        """
        self.surface = surface
        self.state_manager = state_manager

    def draw(self) -> None:
        """Desenha todos os estados ativos de baixo para cima."""
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