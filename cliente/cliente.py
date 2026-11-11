from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import encode_ieee, decode_ieee


class ClienteMODBUS():
    """
    Classe de comunicação Modbus TCP.

    Contém apenas métodos de conexão, leitura, escrita e conversão de dados.
    Não possui menus nem chamadas input().
    """

    def __init__(self, server_ip, porta, timeout=3.0):
        """
        Construtor
        """
        self._cliente = ModbusClient(
            host=server_ip,
            port=porta,
            timeout=timeout
        )

    def abrir_conexao(self):
        """
        Abre a conexão com o servidor Modbus TCP.
        Retorna True em caso de sucesso e False em caso de falha.
        """
        try:
            return bool(self._cliente.open())
        except Exception as e:
            print(f"Erro ao abrir conexão: {e.args}")
            return False

    def fechar_conexao(self):
        """
        Encerra a conexão com o servidor Modbus TCP.
        """
        try:
            self._cliente.close()
            return True
        except Exception as e:
            print(f"Erro ao fechar conexão: {e.args}")
            return False

    def ler_holding_register(self, endereco):
        """
        Lê um Holding Register de 16 bits.

        Retorna o valor inteiro ou None em caso de falha.
        """
        try:
            resposta = self._cliente.read_holding_registers(endereco, 1)

            if resposta is None:
                print(f"Falha na leitura do registrador {endereco}.")
                return None

            return resposta[0]

        except Exception as e:
            print(f"Erro ao ler registrador {endereco}: {e.args}")
            return None

    def escrever_holding_register(self, endereco, valor):
        """
        Escreve um valor inteiro em um Holding Register.

        Retorna True em caso de sucesso e False em caso de falha.
        """
        try:
            if not 0 <= int(valor) <= 65535:
                print("Valor fora do intervalo de 16 bits: 0 a 65535.")
                return False

            resposta = self._cliente.write_single_register(
                endereco, int(valor))

            if resposta is None:
                print(f"Falha na escrita do registrador {endereco}.")
                return False

            return True

        except Exception as e:
            print(f"Erro ao escrever registrador {endereco}: {e.args}")
            return False

    def ler_float(self, endereco, div=1):
        """
        Lê um float32 armazenado em dois Holding Registers consecutivos
        e aplica a escala de engenharia.

        valor_engenharia = valor_numerico / Div

        Ordem de palavras: big-endian.
        """
        try:
            resposta = self._cliente.read_holding_registers(endereco, 2)

            if resposta is None or len(resposta) != 2:
                print(f"Falha na leitura do float no endereço {endereco}.")
                return None

            palavra_alta = resposta[0]
            palavra_baixa = resposta[1]
            raw = (palavra_alta << 16) | palavra_baixa

            valor_numerico = decode_ieee(raw)
            return valor_numerico / div

        except Exception as e:
            print(f"Erro ao ler float no endereço {endereco}: {e.args}")
            return None

    def escrever_float(self, endereco, valor_engenharia, div=1):
        """
        Aplica a escala e escreve um float32 em dois Holding Registers.

        valor_numerico = valor_engenharia * Div

        Ordem de palavras: big-endian.
        """
        try:
            valor_numerico = float(valor_engenharia) * div
            raw = encode_ieee(valor_numerico)

            palavra_alta = (raw >> 16) & 0xFFFF
            palavra_baixa = raw & 0xFFFF

            resposta = self._cliente.write_multiple_registers(
                endereco,
                [palavra_alta, palavra_baixa]
            )

            if resposta is None:
                print(f"Falha na escrita do float no endereço {endereco}.")
                return False

            return True

        except Exception as e:
            print(f"Erro ao escrever float no endereço {endereco}: {e.args}")
            return False

    def ler_bits(self, endereco):
        """
        Lê um Holding Register e retorna uma lista com os 16 bits.

        O índice 0 corresponde ao bit menos significativo.
        """
        valor = self.ler_holding_register(endereco)

        if valor is None:
            return None

        return [(valor >> bit) & 1 for bit in range(16)]

    def escrever_bit(self, endereco, bit, valor):
        """
        Altera apenas um bit de um Holding Register, preservando os demais.

        Retorna True em caso de sucesso e False em caso de falha.
        """
        if not 0 <= bit <= 15:
            print("Índice de bit inválido. Use um valor entre 0 e 15.")
            return False

        if valor not in (0, 1):
            print("Valor de bit inválido. Use 0 ou 1.")
            return False

        valor_atual = self.ler_holding_register(endereco)

        if valor_atual is None:
            return False

        if valor == 1:
            novo_valor = valor_atual | (1 << bit)
        else:
            novo_valor = valor_atual & ~(1 << bit)

        return self.escrever_holding_register(endereco, novo_valor)
