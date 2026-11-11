from cliente.cliente import ClienteMODBUS

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
import math

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.selectioncontrol import MDCheckbox


class ModbusApp(MDApp):
    conectado = BooleanProperty(False)
    ocupado = BooleanProperty(False)
    recorrente = BooleanProperty(False)
    status = StringProperty("Desconectado")
    resultado = StringProperty("Nenhuma leitura realizada.")
    tipo = StringProperty("Float")

    def build(self):
        self.title = "Cliente Modbus TCP"
        self.theme_cls.primary_palette = "Blue"
        Window.size = (960, 860)
        self.cliente = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.evento = None
        self.encerrando = False
        return Builder.load_file(str(Path(__file__).with_name("interface.kv")))

    def executar(self, funcao, retorno):
        if self.ocupado or self.encerrando:
            return
        self.ocupado = True
        futuro = self.executor.submit(funcao)
        futuro.add_done_callback(lambda f: Clock.schedule_once(
            partial(self.finalizar, f, retorno), 0))

    def finalizar(self, futuro, retorno, dt):
        if self.encerrando:
            return
        self.ocupado = False
        try:
            valor = futuro.result()
        except Exception as erro:
            self.status = f"Erro: {erro}"
            self.parar_leitura()
            return
        retorno(valor)

    def conectar(self):
        try:
            ip = self.root.ids.ip.text.strip()
            porta = int(self.root.ids.porta.text)
            if not ip or not 1 <= porta <= 65535:
                raise ValueError("Informe IP/host e porta entre 1 e 65535.")
        except ValueError as erro:
            self.status = str(erro)
            return
        self.status = "Conectando..."

        def tarefa():
            cliente = ClienteMODBUS(ip, porta, timeout=2.0)
            if not cliente.abrir_conexao():
                cliente.fechar_conexao()
                return None
            if self.encerrando:
                cliente.fechar_conexao()
                return None
            return cliente

        def pronto(cliente):
            self.cliente = cliente
            self.conectado = cliente is not None
            self.status = "Conectado" if self.conectado else "Falha ao conectar. Confira servidor, IP e porta."
        self.executar(tarefa, pronto)

    def desconectar(self):
        self.parar_leitura()
        cliente = self.cliente
        if cliente is None:
            return

        def pronto(ok):
            self.cliente = None
            self.conectado = False
            self.status = "Desconectado" if ok else "Falha no fechamento da conexão."
        self.executar(cliente.fechar_conexao, pronto)

    def selecionar_tipo(self, tipo, ativo):
        if ativo:
            self.tipo = tipo

    def parametros(self):
        ids = self.root.ids
        endereco = int(ids.endereco.text)
        limite = 65534 if self.tipo == "Float" else 65535
        if not 0 <= endereco <= limite:
            raise ValueError(f"Endereço deve estar entre 0 e {limite}.")
        div = float(ids.divisor.text.replace(",", "."))
        if not math.isfinite(div) or div <= 0:
            raise ValueError("Div deve ser finito e positivo.")
        bits = []
        if self.tipo == "Bits":
            bits = [int(x.strip()) for x in ids.bits.text.split(",")]
            if not bits or len(bits) != len(set(bits)) or any(b < 0 or b > 15 for b in bits):
                raise ValueError(
                    "Informe bits distintos entre 0 e 15: exemplo 0,1,6.")
        return self.tipo, endereco, div, bits

    def ler(self, dt=0):
        if not self.conectado or self.ocupado:
            return
        try:
            tipo, endereco, div, bits = self.parametros()
        except ValueError as erro:
            self.status = f"Entrada inválida: {erro}"
            self.parar_leitura()
            return
        cliente = self.cliente

        def tarefa():
            if tipo == "Coil":
                return cliente.ler_coil(endereco)
            if tipo == "Holding":
                return cliente.ler_holding_register(endereco)
            if tipo == "Float":
                return cliente.ler_float(endereco, div)
            return cliente.ler_bits_selecionados(endereco, bits)

        def pronto(valor):
            if valor is None:
                self.status = "Falha na leitura. Verifique conexão e endereço."
                self.parar_leitura()
                return
            self.resultado = f"{tipo} | endereço {endereco} | valor: {valor}"
            self.status = "Leitura concluída"
        self.executar(tarefa, pronto)

    def iniciar_leitura(self):
        if self.evento:
            self.parar_leitura()
            self.status = "Leitura recorrente parada"
            return
        if not self.conectado:
            self.status = "Conecte ao servidor primeiro."
            return
        if self.recorrente:
            try:
                intervalo = float(
                    self.root.ids.intervalo.text.replace(",", "."))
                if not math.isfinite(intervalo) or intervalo < 0.1:
                    raise ValueError("Intervalo mínimo: 0,1 segundo.")
                self.parametros()
            except ValueError as erro:
                self.status = f"Entrada inválida: {erro}"
                return
            self.evento = Clock.schedule_interval(self.ler, intervalo)
        self.ler()

    def parar_leitura(self):
        if self.evento is not None:
            self.evento.cancel()
            self.evento = None

    def definir_recorrente(self, ativo):
        self.recorrente = ativo
        if not ativo:
            self.parar_leitura()

    def escrever(self):
        if not self.conectado or self.ocupado:
            return
        try:
            tipo, endereco, div, bits = self.parametros()
            texto = self.root.ids.valor.text.strip()
            if tipo == "Float":
                valor = float(texto.replace(",", "."))
                if not math.isfinite(valor):
                    raise ValueError("Float deve ser finito.")
            elif tipo == "Bits":
                valor = [int(x.strip()) for x in texto.split(",")]
                if len(valor) != len(bits) or any(v not in (0, 1) for v in valor):
                    raise ValueError(
                        "Informe um 0/1 para cada bit selecionado.")
            else:
                valor = int(texto)
                limite = 1 if tipo == "Coil" else 65535
                if not 0 <= valor <= limite:
                    raise ValueError(f"Valor deve estar entre 0 e {limite}.")
        except ValueError as erro:
            self.status = f"Entrada inválida: {erro}"
            return
        cliente = self.cliente

        def tarefa():
            if tipo == "Coil":
                return cliente.escrever_coil(endereco, valor)
            if tipo == "Holding":
                return cliente.escrever_holding_register(endereco, valor)
            if tipo == "Float":
                return cliente.escrever_float(endereco, valor, div)
            return cliente.escrever_bits(endereco, bits, valor)

        def pronto(ok):
            self.status = "Escrita concluída" if ok is True else "Falha na escrita."
        self.executar(tarefa, pronto)

    def on_stop(self):
        self.encerrando = True
        self.parar_leitura()

        def fechar():
            if self.cliente is not None:
                self.cliente.fechar_conexao()
        self.executor.submit(fechar)
        self.executor.shutdown(wait=False)


if __name__ == "__main__":
    ModbusApp().run()
