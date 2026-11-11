from pyModbusTCP.server import DataBank, ModbusServer
from pyModbusTCP.utils import encode_ieee, decode_ieee
from time import sleep
import random


class ServidorMODBUS():
    """
    Servidor Modbus TCP que emula uma bancada de bombeamento.

    Ordem de palavras dos floats: big-endian
    (registrador inicial = palavra alta, registrador seguinte = palavra baixa).
    """

    # Endereços do mapa de dados
    ADDR_TEMP_R = 700
    ADDR_TEMP_S = 702
    ADDR_TEMP_T = 704
    ADDR_TEMP_CARC = 706
    ADDR_PIT01 = 710
    ADDR_FIT01 = 712
    ADDR_FREQUENCIA = 830
    ADDR_CORRENTE_R = 840
    ADDR_TENSAO_RS = 847
    ADDR_FP_R = 868
    ADDR_SP_PID = 1302
    ADDR_HABILITA = 1328
    BIT_HABILITA = 6

    def __init__(self, host_ip, port):
        """
        Construtor
        """
        self._db = DataBank()
        self._server = ModbusServer(
            host=host_ip,
            port=port,
            no_block=True,
            data_bank=self._db
        )

        # Estado inicial da simulação
        self._temp_r = 25.0
        self._temp_s = 25.0
        self._temp_t = 25.0
        self._temp_carc = 30.0
        self._pressao = 1.2
        self._vazao = 0.0
        self._frequencia = 0.0
        self._corrente = 0.0
        self._tensao = 220.0
        self._fator_potencia = 0.90

        self._inicializar_registradores()

    def _inicializar_registradores(self):
        """
        Escreve os valores iniciais nas tabelas Modbus.
        """
        self._escrever_float(self.ADDR_TEMP_R, self._temp_r, 10)
        self._escrever_float(self.ADDR_TEMP_S, self._temp_s, 10)
        self._escrever_float(self.ADDR_TEMP_T, self._temp_t, 10)
        self._escrever_float(self.ADDR_TEMP_CARC, self._temp_carc, 10)
        self._escrever_float(self.ADDR_PIT01, self._pressao, 1)
        self._escrever_float(self.ADDR_FIT01, self._vazao, 1)

        self._db.set_holding_registers(self.ADDR_FREQUENCIA, [0])
        self._db.set_holding_registers(self.ADDR_CORRENTE_R, [0])
        self._db.set_holding_registers(self.ADDR_TENSAO_RS, [2200])
        self._db.set_holding_registers(self.ADDR_FP_R, [900])

        self._escrever_float(self.ADDR_SP_PID, 10.0, 1)
        self._db.set_holding_registers(self.ADDR_HABILITA, [0])

    @staticmethod
    def _float_para_registradores(valor):
        """
        Converte um float32 para dois registradores de 16 bits.
        Ordem: palavra alta primeiro, palavra baixa depois.
        """
        raw = encode_ieee(float(valor))
        palavra_alta = (raw >> 16) & 0xFFFF
        palavra_baixa = raw & 0xFFFF
        return [palavra_alta, palavra_baixa]

    @staticmethod
    def _registradores_para_float(registradores):
        """
        Converte dois registradores de 16 bits para float32.
        """
        raw = (registradores[0] << 16) | registradores[1]
        return decode_ieee(raw)

    def _escrever_float(self, endereco, valor_engenharia, div):
        """
        Aplica a escala e escreve um float32 em dois Holding Registers.

        Escrita: valor_numerico = valor_engenharia * Div
        """
        valor_numerico = float(valor_engenharia) * div
        self._db.set_holding_registers(
            endereco,
            self._float_para_registradores(valor_numerico)
        )

    def _ler_float(self, endereco, div):
        """
        Lê dois Holding Registers, decodifica float32 e aplica a escala.

        Leitura: valor_engenharia = valor_numerico / Div
        """
        registradores = self._db.get_holding_registers(endereco, 2)
        valor_numerico = self._registradores_para_float(registradores)
        return valor_numerico / div

    def _ler_habilita(self):
        """
        Lê o bit 6 do registrador 1328.
        """
        registrador = self._db.get_holding_registers(self.ADDR_HABILITA, 1)[0]
        return (registrador >> self.BIT_HABILITA) & 1

    def _atualizar_medicoes(self):
        """
        Atualiza as medições da bancada de bombeamento.

        Com o motor habilitado, a vazão se aproxima gradualmente do setpoint.
        Com o motor desabilitado, a vazão permanece constante.
        """
        habilitado = self._ler_habilita()
        setpoint = self._ler_float(self.ADDR_SP_PID, 1)

        if habilitado:
            erro = setpoint - self._vazao
            self._vazao += erro * 0.08
            self._vazao += random.uniform(-0.05, 0.05)

            if self._vazao < 0:
                self._vazao = 0.0

            self._frequencia = min(
                60.0, (self._vazao / max(setpoint, 0.1)) * 60.0)
            self._corrente = 1.5 + self._vazao * 0.25
            self._pressao = 0.8 + self._vazao * 0.08
            self._fator_potencia = min(0.98, 0.80 + self._vazao * 0.005)
        else:
            self._frequencia = 0.0
            self._corrente = 0.0
            self._pressao = 0.8

        # Variações graduais de temperatura
        self._temp_r += random.uniform(-0.05, 0.05)
        self._temp_s += random.uniform(-0.05, 0.05)
        self._temp_t += random.uniform(-0.05, 0.05)
        self._temp_carc += random.uniform(-0.03, 0.03)

        if habilitado:
            self._temp_r += self._vazao * 0.002
            self._temp_s += self._vazao * 0.002
            self._temp_t += self._vazao * 0.002
            self._temp_carc += self._vazao * 0.003

        # Escrita das medições float
        self._escrever_float(self.ADDR_TEMP_R, self._temp_r, 10)
        self._escrever_float(self.ADDR_TEMP_S, self._temp_s, 10)
        self._escrever_float(self.ADDR_TEMP_T, self._temp_t, 10)
        self._escrever_float(self.ADDR_TEMP_CARC, self._temp_carc, 10)
        self._escrever_float(self.ADDR_PIT01, self._pressao, 1)
        self._escrever_float(self.ADDR_FIT01, self._vazao, 1)

        # Escrita das medições inteiras com escala
        frequencia = max(0, min(65535, round(self._frequencia * 100)))
        corrente = max(0, min(65535, round(self._corrente * 10)))
        tensao = max(0, min(65535, round(self._tensao * 10)))
        fator_potencia = max(0, min(65535, round(self._fator_potencia * 1000)))

        self._db.set_holding_registers(self.ADDR_FREQUENCIA, [frequencia])
        self._db.set_holding_registers(self.ADDR_CORRENTE_R, [corrente])
        self._db.set_holding_registers(self.ADDR_TENSAO_RS, [tensao])
        self._db.set_holding_registers(self.ADDR_FP_R, [fator_potencia])

    def _imprimir_estado(self):
        """
        Imprime o estado atual das principais variáveis.
        """
        habilitado = self._ler_habilita()
        setpoint = self._ler_float(self.ADDR_SP_PID, 1)

        print("======================")
        print("Servidor MODBUS - Bancada de Bombeamento")
        print(f"Habilitado: {habilitado}")
        print(f"Setpoint de vazão: {setpoint:.2f} L/s")
        print(f"Vazão medida: {self._vazao:.2f} L/s")
        print(f"Pressão: {self._pressao:.2f} bar")
        print(f"Frequência: {self._frequencia:.2f} Hz")
        print(f"Corrente R: {self._corrente:.2f} A")
        print(f"Tensão R-S: {self._tensao:.2f} V")
        print(f"Fator de potência R: {self._fator_potencia:.3f}")
        print(f"Temperatura R: {self._temp_r:.2f} °C")
        print(f"Temperatura S: {self._temp_s:.2f} °C")
        print(f"Temperatura T: {self._temp_t:.2f} °C")
        print(f"Temperatura carcaça: {self._temp_carc:.2f} °C")

    def run(self):
        """
        Execução do servidor Modbus.
        """
        try:
            self._server.start()
            print("Servidor MODBUS em execução")

            while True:
                self._atualizar_medicoes()
                self._imprimir_estado()
                sleep(0.5)

        except Exception as e:
            print("Erro: ", e.args)
