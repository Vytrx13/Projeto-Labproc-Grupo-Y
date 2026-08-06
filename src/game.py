import pygame
import sys
import socket
import random

# config
WIDTH, HEIGHT = 1000, 600
FPS = 60


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

INPUT_MODE = "UDP"
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

GESTURES = {
    "11111": "ABERTO",
    "00000": "PUNHO",
    "01100": "PAZ",
    "01000": "APONTA",
    "10000": "JOIA",
    "01111": "QUATRO",
}
GESTURE_KEYS = list(GESTURES.keys())


class Player:
    def __init__(self, x_pos):
        self.hp = 100
        self.x_pos = x_pos
        self.target_sequence = self.generate_new_sequence(4)
        self.current_step = 0  # símbolo da sequência ele está agora
        self.sequence_start_time = pygame.time.get_ticks()

    def generate_new_sequence(self, length):
        return [random.choice(GESTURE_KEYS) for _ in range(length)]

    def reset_sequence(self):
        self.current_step = 0
        self.sequence_start_time = pygame.time.get_ticks()
        self.target_sequence = self.generate_new_sequence(4)

    def check_timeout(self, current_time, timeout_ms=10000):
        # se passou de 10s desde que a sequência apareceu, reseta o progresso e o tempo
        if (current_time - self.sequence_start_time) > timeout_ms:
            self.reset_sequence()
            return True
        return False


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Labproc Jogo 1x1")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 20)
        self.big_font = pygame.font.SysFont(None, 45)

        # jogadores
        self.p1 = Player(150)
        self.p2 = Player(790)

        # TODO: SUBSTITUIR PELOS SPRITES REAIS
        self.placeholder_p1_rect = pygame.Rect(self.p1.x_pos, 400, 60, 120)
        self.placeholder_p2_rect = pygame.Rect(self.p2.x_pos, 400, 60, 120)

        if INPUT_MODE == "UDP":
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((UDP_IP, UDP_PORT))
            self.sock.setblocking(False)

        self.running = True

    def process_gesture(self, player_id, gesture_str):
        """Processa a entrada de um gesto para o jogador especificado."""
        player = self.p1 if player_id == 1 else self.p2
        opponent = self.p2 if player_id == 1 else self.p1

        # verifica se o gesto recebido é igual ao gesto atual que ele precisa fazer
        if gesture_str == player.target_sequence[player.current_step]:
            player.current_step += 1

            # se completou toda a sequência
            if player.current_step >= len(player.target_sequence):
                opponent.hp -= 25  # Causa Dano
                player.target_sequence = player.generate_new_sequence(4)
                player.reset_sequence()
                print(f"Jogador {player_id} COMPLETOU A SEQUÊNCIA E ATACOU!")

    def handle_input_keyboard(self, event):
        """Mapeia teclas do teclado para as arrays de 5 bits

        JOGADOR 1:
        Q: ABERTO ("11111")
        W: PUNHO  ("00000")
        E: PAZ    ("01100")
        R: APONTA ("01000")
        T: JOIA   ("10000")
        Y: QUATRO ("01111")

        JOGADOR 2:
        U: ABERTO ("11111")
        I: PUNHO  ("00000")
        O: PAZ    ("01100")
        P: APONTA ("01000")
        J: JOIA   ("10000")
        K: QUATRO ("01111")
        """
        if event.key == pygame.K_q:
            self.process_gesture(1, "11111")
        elif event.key == pygame.K_w:
            self.process_gesture(1, "00000")
        elif event.key == pygame.K_e:
            self.process_gesture(1, "01100")
        elif event.key == pygame.K_r:
            self.process_gesture(1, "01000")
        elif event.key == pygame.K_t:
            self.process_gesture(1, "10000")
        elif event.key == pygame.K_y:
            self.process_gesture(1, "01111")

        elif event.key == pygame.K_u:
            self.process_gesture(2, "11111")
        elif event.key == pygame.K_i:
            self.process_gesture(2, "00000")
        elif event.key == pygame.K_o:
            self.process_gesture(2, "01100")
        elif event.key == pygame.K_p:
            self.process_gesture(2, "01000")
        elif event.key == pygame.K_j:
            self.process_gesture(2, "10000")
        elif event.key == pygame.K_k:
            self.process_gesture(2, "01111")

    def handle_input_udp(self):
        """Lê os dados chegando pela rede UDP (Formato esperado ex: 'P1:11111')"""
        try:
            data, addr = self.sock.recvfrom(1024)
            msg = data.decode("utf-8").strip()
            # msg exemplo: "P1:01100"
            if msg.startswith("P1:"):
                gesture = msg.split(":")[1]
                self.process_gesture(1, gesture)
            elif msg.startswith("P2:"):
                gesture = msg.split(":")[1]
                self.process_gesture(2, gesture)

        except BlockingIOError:
            pass

    def check_logic(self):
        current_time = pygame.time.get_ticks()

        # checa se o tempo de 10 segundos expirou para alguém
        if self.p1.check_timeout(current_time):
            print("Tempo do Jogador 1 esgotou! Sequência resetada.")
        if self.p2.check_timeout(current_time):
            print("Tempo do Jogador 2 esgotou! Sequência resetada.")

        # fim de jogo
        if self.p1.hp <= 0 or self.p2.hp <= 0:
            self.running = False
            print("Fim de Jogo!")

    def draw_player_hud(self, player, x_offset, color):
        """Desenha a UI de um jogador (Barra de vida, sequência, tempo)"""

        pygame.draw.rect(self.screen, WHITE, (x_offset, 30, 300, 25))
        hp_width = max(0, (player.hp / 100) * 300)
        pygame.draw.rect(
            self.screen, GREEN if player.hp > 30 else RED, (x_offset, 30, hp_width, 25)
        )

        # Desenhar Sequência Alvo (Os 4 passos)
        for i, gesture_bits in enumerate(player.target_sequence):
            # Posicionamento horizontal dos icones da sequência
            icon_x = x_offset + (i * 70)
            icon_y = 70

            if i < player.current_step:
                # já acertou
                box_color = GREEN
                text_color = BLACK
            elif i == player.current_step:
                # o que ele precisa acertar agora (destaque)
                box_color = YELLOW
                text_color = BLACK
            else:
                # futuros
                box_color = GRAY
                text_color = WHITE

            pygame.draw.rect(
                self.screen, box_color, (icon_x, icon_y, 60, 60), border_radius=5
            )
            if i == player.current_step:
                pygame.draw.rect(
                    self.screen, WHITE, (icon_x, icon_y, 60, 60), 3, border_radius=5
                )  # Borda

            # Nome do gesto para facilitar
            gesture_name = GESTURES.get(gesture_bits, "???")
            # Divide nome pra caber na caixinha se for grande
            words = gesture_name.split()
            for w_idx, word in enumerate(words):
                text_surf = self.font.render(word, True, text_color)
                self.screen.blit(text_surf, (icon_x + 5, icon_y + 10 + (w_idx * 15)))

            # TODO: adicionar PNG da silhueta da mão!

        # barra de tempo (10 segundos)
        current_time = pygame.time.get_ticks()
        time_elapsed = current_time - player.sequence_start_time
        time_left_ratio = 1.0 - (time_elapsed / 10000.0)  # 10000ms = 10s

        timer_w = 270
        pygame.draw.rect(self.screen, RED, (x_offset, 140, timer_w, 10))
        pygame.draw.rect(
            self.screen, WHITE, (x_offset, 140, timer_w * max(0, time_left_ratio), 10)
        )

    def draw(self):
        self.screen.fill(BLACK)

        self.draw_player_hud(self.p1, 50, BLUE)
        self.draw_player_hud(self.p2, 650, RED)  # 1000 - 300 - 50 = 650

        # jogadores (Temporário)
        pygame.draw.rect(self.screen, BLUE, self.placeholder_p1_rect)
        pygame.draw.rect(self.screen, RED, self.placeholder_p2_rect)

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if INPUT_MODE == "KEYBOARD" and event.type == pygame.KEYDOWN:
                    self.handle_input_keyboard(event)

            if INPUT_MODE == "UDP":
                self.handle_input_udp()

            self.check_logic()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
