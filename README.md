# Descrição do Projeto

Este repositório contém o código-fonte e a documentação de um jogo interativo 1x1 baseado em visão computacional e hardware físico. 

O sistema possui uma arquitetura distribuída: um computador principal (laptop) utiliza as bibliotecas OpenCV e MediaPipe para processar os feeds de vídeo das câmeras, identificar os nós das mãos dos jogadores e extrair matrizes numéricas correspondentes aos gestos realizados. Esses dados são transmitidos em tempo real via rede local (protocolo UDP) para um Raspberry Pi 3B+. 

O Raspberry Pi atua como o motor lógico e gráfico do sistema. Ele executa a interface do jogo utilizando a biblioteca Pygame para validar as sequências de gestos e gerenciar variáveis como tempo e pontos de vida. Simultaneamente, o Raspberry Pi controla componentes eletrônicos do kit FNK0054 (botões, buzzer e display LCD) por meio de seus pinos GPIO, integrando comandos físicos e feedback de hardware à mecânica digital do jogo.