# Atividade Prática — Interface gráfica com KivyMD para cliente Modbus TCP

- Integrante 1: Ana Marcia Cruz Moreira - 201865132I

## Processo simulado
Bancada de bombeamento industrial.

Quando o bit 6 do registrador 1328 está em 1, a vazão medida se aproxima
gradualmente do setpoint escrito no par de registradores 1302–1303.
Quando o bit está em 0, a vazão permanece constante.

## Alterações após a avaliação
Cliente principal migrado para PyModbus; servidor mantido em pyModbusTCP.

O cliente principal verifica resposta.isError() e trata exceções, None e False.

A nova versão cliente preserva a API antiga e só considera sucesso quando a escrita retorna exatamente True. As demonstrações verificam retornos antes de anunciar sucesso e não formatam None. Mantidos mapa, escalas e ordem de palavras dos floats. 

# Interface gráfica Modbus TCP com Python e KivyMD

Aplicação gráfica desenvolvida para realizar leitura e escrita de dados em um servidor Modbus TCP, utilizando Python e KivyMD.


## Execução

Instalação:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Terminal 1 — servidor:

```bash
python main.py
```

## Terminal 2 — interface gráfica

A partir da pasta principal:

```bash
python -m interface.main
```

## Conexão

Na interface, informe:
- IP: endereço do computador que executa o servidor.
- Porta: a mesma configurada em `servidor/main.py`.

IP: `localhost`  
Porta: `502`


## Observações

- O servidor deve estar em execução antes de conectar a interface.
- O IP e a porta devem corresponder à configuração do servidor.
- As medições do simulador são sobrescritas a cada ciclo. Para demonstrar escrita persistente, utilize o setpoint ou um registrador de teste não atualizado pelo processo.

### Leitura única

1. Deixe o checkbox de leitura recorrente desmarcado.
2. Escolha o tipo e o endereço.
3. Preencha os campos adicionais necessários.
4. Clique em `Ler / parar recorrência`.

A aplicação executa uma leitura e apresenta o resultado.

### Leitura recorrente

1. Marque o checkbox de leitura recorrente.
2. Informe o intervalo em segundos.
3. Clique em `Ler / parar recorrência`.

A aplicação utiliza o `Clock` do Kivy para agendar as leituras.

Para interromper:

- Clique novamente em `Ler / parar recorrência`.
- Desmarque a leitura recorrente.
- Desconecte do servidor.

O intervalo mínimo aceito pela interface é de `0,1` segundo.

As operações de rede são executadas em uma thread de trabalho, de forma serializada. Se uma operação ainda estiver em andamento, o ciclo de leitura agendado é ignorado, evitando o acúmulo de requisições.

As atualizações dos resultados são encaminhadas à thread da interface pelo `Clock`.



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

## Documentação

- Kivy: https://kivy.org/doc/stable/
- KivyMD: https://kivymd.readthedocs.io/en/latest/
- PyModbus: https://pymodbus.readthedocs.io/
- pyModbusTCP: https://pymodbustcp.readthedocs.io/

- Usei IA para ela comentar o código, separando o que cada parte faz, e também auxiliar a escrever o README.