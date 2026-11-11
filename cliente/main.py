from cliente import ClienteMODBUS
from time import sleep


HOST = 'localhost'
PORTA = 502

# Endereços utilizados nas demonstrações
ADDR_TEMP_R = 700
ADDR_PIT01 = 710
ADDR_FIT01 = 712
ADDR_FREQUENCIA = 830
ADDR_CORRENTE_R = 840
ADDR_SP_PID = 1302
ADDR_HABILITA = 1328
BIT_HABILITA = 6


def mostrar_bits(bits):
    """
    Exibe os 16 bits de um registrador.
    """
    if bits is None:
        print("Não foi possível ler os bits.")
        return

    for indice, valor in enumerate(bits):
        print(f"Bit {indice:2d}: {valor}")


def demonstrar_leitura_medicoes(cliente):
    """
    Lê e identifica os 10 dados de medição da bancada.
    """
    print("\n### Leitura das medições ###")

    medicoes = [
        ("Temperatura R", ADDR_TEMP_R, 2, 10, "°C"),
        ("Temperatura S", 702, 2, 10, "°C"),
        ("Temperatura T", 704, 2, 10, "°C"),
        ("Temperatura carcaça", 706, 2, 10, "°C"),
        ("Pressão", ADDR_PIT01, 2, 1, "bar"),
        ("Vazão", ADDR_FIT01, 2, 1, "L/s"),
        ("Frequência", ADDR_FREQUENCIA, 1, 100, "Hz"),
        ("Corrente R", ADDR_CORRENTE_R, 1, 10, "A"),
        ("Tensão R-S", 847, 1, 10, "V"),
        ("Fator de potência R", 868, 1, 1000, "-"),
    ]

    for nome, endereco, quantidade, div, unidade in medicoes:
        if quantidade == 2:
            valor_numerico = cliente.ler_float(endereco, div)
        else:
            bruto = cliente.ler_holding_register(endereco)
            valor_numerico = None if bruto is None else bruto / div

        if valor_numerico is None:
            continue

        print(
            f"{nome:22s} | endereço {endereco:4d} | "
            f"Div {div:4d} | valor de engenharia: {valor_numerico:8.3f} {unidade}"
        )


def demonstrar_escala(cliente):
    """
    Demonstra a conversão de escala em um inteiro com Div diferente de 1.
    """
    print("\n### Demonstração de escala: frequência ###")

    bruto = cliente.ler_holding_register(ADDR_FREQUENCIA)

    if bruto is not None:
        div = 100
        multiplicador = 1 / div
        valor_engenharia = bruto / div

        print(f"Valor numérico recebido: {bruto}")
        print(f"Div: {div}")
        print(f"Multiplicador: {multiplicador}")
        print(f"Valor de engenharia: {valor_engenharia:.2f} Hz")


def demonstrar_float(cliente):
    """
    Escreve e lê um setpoint float32.
    """
    print("\n### Demonstração de float32: setpoint de vazão ###")

    valor_enviado = 12.75
    sucesso = cliente.escrever_float(ADDR_SP_PID, valor_enviado, div=1)

    if sucesso:
        valor_lido = cliente.ler_float(ADDR_SP_PID, div=1)
        print(f"Valor enviado: {valor_enviado} L/s")
        print(f"Valor lido:    {valor_lido} L/s")

        if valor_lido is not None:
            diferenca = abs(valor_lido - valor_enviado)

            if diferenca < 1e-3:
                print("O valor lido é equivalente ao valor enviado.")
            else:
                print("O valor lido difere do valor enviado.")


def demonstrar_bits(cliente):
    """
    Demonstra leitura dos 16 bits e escrita de um bit individual.
    """
    print("\n### Demonstração de bits: comando de habilitação ###")

    # Valor inicial com outros bits já ativados
    valor_inicial = 0b0000000000000011  # bits 0 e 1 ativados
    cliente.escrever_holding_register(ADDR_HABILITA, valor_inicial)

    print("Bits antes de habilitar o motor:")
    mostrar_bits(cliente.ler_bits(ADDR_HABILITA))

    print(f"\nAtivando o bit {BIT_HABILITA}...")
    cliente.escrever_bit(ADDR_HABILITA, BIT_HABILITA, 1)

    print("Bits depois de habilitar o motor:")
    mostrar_bits(cliente.ler_bits(ADDR_HABILITA))

    print(f"\nDesativando o bit {BIT_HABILITA}...")
    cliente.escrever_bit(ADDR_HABILITA, BIT_HABILITA, 0)

    print("Bits depois de desabilitar o motor:")
    mostrar_bits(cliente.ler_bits(ADDR_HABILITA))


def demonstrar_simulacao(cliente):
    """
    Altera o setpoint, habilita o motor e acompanha a vazão.
    """
    print("\n### Demonstração da simulação ###")

    cliente.escrever_float(ADDR_SP_PID, 15.0, div=1)
    cliente.escrever_bit(ADDR_HABILITA, BIT_HABILITA, 1)

    print("Motor habilitado. Setpoint = 15.0 L/s")

    for i in range(5):
        vazao = cliente.ler_float(ADDR_FIT01, div=1)
        print(f"Leitura {i + 1}: vazão = {vazao:.2f} L/s")
        sleep(1)

    cliente.escrever_bit(ADDR_HABILITA, BIT_HABILITA, 0)
    print("Motor desabilitado.")


if __name__ == "__main__":
    cliente = ClienteMODBUS(HOST, PORTA)

    if not cliente.abrir_conexao():
        print("Não foi possível conectar ao servidor Modbus TCP.")
        exit(1)

    try:
        demonstrar_leitura_medicoes(cliente)
        demonstrar_escala(cliente)
        demonstrar_float(cliente)
        demonstrar_bits(cliente)
        demonstrar_simulacao(cliente)

    finally:
        cliente.fechar_conexao()
        print("\nConexão encerrada.")
