# Save The Princess

**Autor:** Diego de Sá Dias  
**Email:** diego.sa.dias11@gmail.com

## Sobre o Jogo

"Save The Princess" é um jogo de plataforma 2D desenvolvido em Python utilizando a biblioteca Pygame Zero. O objetivo é simples, mas desafiador: você controla um cavaleiro que deve escalar o cenário, resgatar a princesa presa no topo do castelo e trazê-la de volta em segurança para a zona verde (Spawn) na base do mapa.

### Mecânicas Principais:
*   **Resgate:** Ao tocar na princesa, você a carrega.
*   **Peso Extra:** Carregar a princesa torna o jogo mais difícil:
    *   Sua velocidade de movimento diminui (70% da normal).
    *   A gravidade aumenta, fazendo você cair mais rápido (30% mais forte).
*   **Inimigos:**
    *   **Monstro de Fogo:** Patrulha plataformas e atira bolas de fogo.
    *   **Monstro de Espada:** Lança espadas para tentar te derrubar.
*   **Vidas:** Você tem 3 vidas. Se for atingido por um inimigo ou projétil, você perde uma vida. Se as vidas acabarem, é Fim de Jogo.

## Como Rodar

Para jogar, você precisa ter o Python instalado e as bibliotecas necessárias.

1.  **Instale as dependências:**
    Abra o terminal na pasta do projeto e execute:
    ```bash
    pip install pgzero pygame
    ```

2.  **Execute o jogo:**
    No terminal, digite:
    ```bash
    pgzrun game.py
    ```

## Estrutura de Arquivos

*   `game.py`: O código principal do jogo.
*   `images/`: Pasta auxiliar contendo todos os sprites e gráficos (Cavaleiro, Princesa, Inimigos, Blocos, etc.).
*   `sounds/`: Pasta auxiliar contendo os efeitos sonoros e música de fundo.
