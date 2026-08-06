# PokéGestures: Batalha de Visão Computacional

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-orange.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.x-red.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-3B+-c7053d.svg)

Este repositório contém o código-fonte e a documentação de um jogo interativo 1x1 baseado em visão computacional e hardware físico.

## Índice
- [Motivação](docs/motivacao.md)
- [Arquitetura](docs/arquitetura.md)
- [Requisitos](docs/requisitos.md)
- [Como Jogar](docs/como-jogar.md)
- [Instalação e Execução](#-instalação-e-execução)

## Descrição do Projeto

O sistema possui uma arquitetura distribuída: um computador principal utiliza as bibliotecas OpenCV e MediaPipe para processar os feeds de vídeo das câmeras, identificar os nós das mãos dos jogadores e extrair matrizes numéricas correspondentes aos gestos realizados. Esses dados são transmitidos em tempo real via rede local (protocolo UDP) para um computador central ou Raspberry Pi.

O Raspberry Pi atua como o motor lógico e gráfico do sistema, executando a interface do jogo utilizando a biblioteca Pygame para validar as sequências de gestos e gerenciar variáveis como tempo e pontos de vida.

## Instalação e Execução

### 1. Dependências
Certifique-se de instalar as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

### 2. Executando o Jogo (Motor Gráfico)
Para rodar a interface em Pygame:
```bash
python src/start.py
```
*(O jogo inicia no modo de entrada de teclado. Para alterar para detecção de câmera, mude `INPUT_MODE = "UDP"` no arquivo `src/state/battleState.py`)*

### 3. Executando o Módulo de Câmera (Visão Computacional)
Se o modo UDP estiver ativo, rode o processador de vídeo em um terminal paralelo:
```bash
python src/process-fingers.py
```

## Estrutura do Projeto
```text
Projeto-Labproc-Grupo-Y/
├── docs/                 # Documentação detalhada
│   ├── arquitetura.md
│   ├── como-jogar.md
│   ├── motivacao.md
│   └── requisitos.md
├── src/
│   ├── assets/           # Imagens e sprites
│   ├── state/            # Máquina de estados do Pygame (menu, batalha)
│   ├── client.py         # Motor principal de loop do jogo
│   ├── process-fingers.py# Script principal do MediaPipe (visão)
│   └── start.py          # Ponto de entrada do jogo
└── requirements.txt      # Dependências do projeto
```