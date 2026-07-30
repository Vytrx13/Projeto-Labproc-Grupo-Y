# Arquitetura Proposta

A arquitetura do sistema é baseada em três camadas operacionais distintas: Processamento de Visão, Transporte de Dados e Lógica/Hardware.

## Diagrama da Arquitetura

```mermaid
graph TD
    subgraph Laptop ["Laptop (Processamento de Visão)"]
        direction TB
        C1[Câmera Jogador 1] -->|Frames| MP1[OpenCV + MediaPipe]
        C2[Câmera Jogador 2] -->|Frames| MP2[OpenCV + MediaPipe]
        
        MP1 -->|Extração de Características| ARR1[Array P1 ex: 0,1,0,0,0]
        MP2 -->|Extração de Características| ARR2[Array P2 ex: 0,1,0,0,0]
        
        ARR1 --> UDP_TX[Socket UDP Emissor]
        ARR2 --> UDP_TX
    end

    subgraph Rede ["Rede Wi-Fi Local"]
        UDP_TX -->|Strings codificadas via UDP| UDP_RX[Socket UDP Receptor - Porta 5005]
    end

    subgraph Raspberry ["Raspberry Pi 3B+ (Motor do Jogo e Hardware)"]
        direction TB
        UDP_RX --> PYG[Loop Principal - Pygame]
        
        subgraph Logica ["Lógica Interna do Jogo"]
            PYG <--> FSM[Máquina de Estados: Checkpoints e Temporizador]
            FSM --> DANO[Cálculo de Dano e HP]
        end
        
        subgraph Hardware ["Kit FNK0054 (Pinos GPIO)"]
            BTN[Botões Físicos] -->|Interrupção / Leitura de Poderes| PYG
            JOY[Joystick Analógico] -->|Navegação de Menus| PYG
            FSM -->|Aciona| LED[LEDs Indicadores de Checkpoint]
            FSM -->|Aciona| BUZ[Buzzer de Feedback]
            DANO -->|Atualiza| LCD[Display LCD 16x2]
        end
        
        PYG -->|Atualização Visual| MON[Interface Gráfica / Monitor]
    end