# Atividade Prática — Modbus TCP com emulação de CLP

- Integrante 1: Ana Marcia Cruz Moreira - 201865132I

## Processo simulado
Bancada de bombeamento industrial.

Quando o bit 6 do registrador 1328 está em 1, a vazão medida se aproxima
gradualmente do setpoint escrito no par de registradores 1302–1303.
Quando o bit está em 0, a vazão permanece constante.

## Execução

Instalação:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Terminal 1 — servidor:

```bash
python main.py
```

Terminal 2 — cliente e demonstrações:

```bash
python main.py
```

IP: `localhost`  
Porta: `502`

## Mapa de dados

| Tag | Descrição | Tipo | Endereço | Registradores | Bit | Div | Multiplicador | Unidade |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `bc.temp_r` | Temperatura R | float32 | 700 | 2 | — | 10 | 0,1 | °C |
| `bc.temp_s` | Temperatura S | float32 | 702 | 2 | — | 10 | 0,1 | °C |
| `bc.temp_t` | Temperatura T | float32 | 704 | 2 | — | 10 | 0,1 | °C |
| `bc.temp_carc` | Temperatura da carcaça | float32 | 706 | 2 | — | 10 | 0,1 | °C |
| `bc.pit01` | Pressão | float32 | 710 | 2 | — | 1 | 1 | bar |
| `bc.fit01` | Vazão | float32 | 712 | 2 | — | 1 | 1 | L/s |
| `bc.frequencia` | Frequência | inteiro 16 bits | 830 | 1 | — | 100 | 0,01 | Hz |
| `bc.corrente_r` | Corrente R | inteiro 16 bits | 840 | 1 | — | 10 | 0,1 | A |
| `bc.tensao_rs` | Tensão R-S | inteiro 16 bits | 847 | 1 | — | 10 | 0,1 | V |
| `bc.fp_r` | Fator de potência R | inteiro 16 bits | 868 | 1 | — | 1000 | 0,001 | — |
| `bc.sp_pid` | Setpoint de vazão | float32 | 1302 | 2 | — | 1 | 1 | L/s |
| `bc.habilita` | Habilitar motor | inteiro 16 bits / bit | 1328 | 1 | 6 | 1 | 1 | — |

## Convenções

- Float32 ocupa dois Holding Registers consecutivos.
- Ordem de palavras: **big-endian**; o primeiro registrador contém a palavra alta.
- Leitura: `valor_engenharia = valor_numerico / Div`.
- Escrita: `valor_numerico = valor_engenharia * Div`.
- Para inteiros, o valor é arredondado com `round()` e limitado ao intervalo de 16 bits.
- Bits usam valores 0 ou 1, sem escala.

- Usei IA para ela comentar o código, separando o que cada parte faz, e também auxiliar a escrever o README.