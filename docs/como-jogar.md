# Como Jogar

O jogo é uma batalha de reflexos e precisão. Cada jogador precisa reproduzir uma sequência de gestos que aparece na tela o mais rápido possível para causar dano no oponente.

## Os Gestos (Modo Câmera)
O sistema reconhece os seguintes padrões baseados na abertura dos dedos:
- **PUNHO**: `00000` (Mão completamente fechada)
- **ABERTO**: `11111` (Mão espalmada)
- **APONTA**: `01000` (Apenas o indicador esticado)
- **PAZ / V**: `01100` (Indicador e médio esticados)
- **QUATRO**: `01111` (Todos os dedos menos o polegar)
- **JOIA**: `10000` (Apenas polegar para cima)

*(As câmeras processam a posição dos nós dos seus dedos usando Inteligência Artificial - MediaPipe - para inferir se o dedo está esticado ou dobrado).*

## Modo Teclado (Fallback)
Se estiver testando sem a câmera conectada (`INPUT_MODE = "KEYBOARD"`), utilize as seguintes teclas para emular os gestos:

**Jogador 1:**
- `Q`: ABERTO
- `W`: PUNHO
- `E`: PAZ
- `R`: APONTA
- `T`: JOIA
- `Y`: QUATRO

**Jogador 2:**
- `U`: ABERTO
- `I`: PUNHO
- `O`: PAZ
- `P`: APONTA
- `J`: JOIA
- `K`: QUATRO

## Regras da Batalha
1. **Sequência Alvo**: Você tem 4 gestos com os nomes aparecendo na sua interface. O que estiver destacado pela borda branca e pela caixa amarela é o passo atual que você precisa acertar.
2. **Temporizador**: Você tem exatos **10 segundos** para concluir todos os 4 passos. Se a barra vermelha acabar antes de você completar os 4 passos, sua sequência reseta e você perde o progresso (voltando ao passo 1).
3. **Dano**: Completar os 4 gestos em sequência causa **25 de Dano** no HP do adversário instantaneamente.
4. **Fim de Jogo**: O primeiro a zerar o HP (vida) do outro Pokémon vence a rodada!
