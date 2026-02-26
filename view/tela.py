import sys
from view.style import STYLE
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QCheckBox,
    QScrollArea, QFrame, QProgressBar, QTextEdit,
    QSplitter, QMessageBox, QGridLayout, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from pathlib import Path
from view.view_interface import ViewInterface


class Worker(QThread):
    sinal_log = pyqtSignal(str, str)
    sinal_progresso = pyqtSignal(int, int, str)
    sinal_finalizado = pyqtSignal(bool, str)

    def __init__(self, controlador, diretorio, clientes, modo):
        super().__init__()
        self.controlador = controlador
        self.diretorio = diretorio
        self.clientes = clientes
        self.modo = modo

    def run(self):
        self.controlador._tela.log = lambda tipo, msg: self.sinal_log.emit(tipo, msg)
        self.controlador._tela.atualizar_progresso = lambda a, t, m: self.sinal_progresso.emit(a, t, m)

        try:
            scripts, resultados = self.controlador.processar_lote(
                diretorio=self.diretorio,
                clientes=self.clientes,
                modo=self.modo
            )
            stats = self.controlador.obter_estatisticas()
            tem_erros = stats.tem_erros
            msg = f'Concluído com {len(stats.erros)} erro(s).' if tem_erros else 'Concluído com sucesso!'
            self.sinal_finalizado.emit(not tem_erros, msg)
        except Exception as e:
            self.sinal_finalizado.emit(False, str(e))


class InterfaceGrafica(ViewInterface):

    def __init__(self, controlador):
        self.controlador = controlador
        self.clientes_disponiveis = self.controlador.carregar_clientes()
        self.checkboxes = {}
        self.processando = False
        self.worker = None
        self._window = None

    def log(self, tipo: str, mensagem: str):
        if self._window:
            self._window.adicionar_log(tipo, mensagem)

    def atualizar_progresso(self, atual: int, total: int, mensagem: str):
        if self._window:
            self._window.atualizar_progresso_ui(atual, total, mensagem)

    def executar(self):
        app = QApplication.instance() or QApplication(sys.argv)
        app.setStyle('Fusion')
        self._window = MainWindow(self)
        self._window.show()
        app.exec()


class MainWindow(QMainWindow):

    def __init__(self, interface: InterfaceGrafica):
        super().__init__()
        self.interface = interface
        self.setWindowTitle('EXECUTOR DE SCRIPTS SQL')
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        self.setStyleSheet(STYLE)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)

        titulo = QLabel('⬛  EXECUTOR DE SCRIPTS SQL')
        titulo.setObjectName('titulo')
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(titulo)
        root.addSpacing(4)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color: #3a3a3a;')
        root.addWidget(sep)
        root.addSpacing(16)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        root.addWidget(splitter)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        top_layout.addWidget(self._card_diretorio())
        top_layout.addWidget(self._card_clientes())
        top_layout.addWidget(self._card_opcoes_executar())
        top_layout.addStretch()
        splitter.addWidget(top_widget)

        splitter.addWidget(self._card_log())
        splitter.setSizes([520, 260])

    def _label_secao(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName('secao')
        return lbl

    def _card(self):
        frame = QFrame()
        frame.setObjectName('card')
        return frame

    def _card_diretorio(self):
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.addWidget(self._label_secao('📁  DIRETÓRIO DE SCRIPTS'))

        row = QHBoxLayout()
        self.input_diretorio = QLineEdit()
        self.input_diretorio.setPlaceholderText('Nenhum diretório selecionado...')
        self.input_diretorio.setReadOnly(False)
        self.input_diretorio.textChanged.connect(self._atualizar_contagem_manual)

        btn = QPushButton('Selecionar')
        btn.setObjectName('btn_selecionar')
        btn.setFixedWidth(120)
        btn.clicked.connect(self._selecionar_diretorio)

        row.addWidget(self.input_diretorio)
        row.addWidget(btn)
        layout.addLayout(row)

        self.lbl_qtd_arquivos = QLabel('0 arquivo(s) .sql encontrado(s)')
        self.lbl_qtd_arquivos.setStyleSheet('color: #666666; font-size: 11px;')
        layout.addWidget(self.lbl_qtd_arquivos)

        return card

    def _card_clientes(self):
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(self._label_secao('🗄️  CLIENTES'))
        header.addStretch()

        btn_todos = QPushButton('Selecionar Todos')
        btn_todos.clicked.connect(self._selecionar_todos)
        btn_limpar = QPushButton('Limpar Seleção')
        btn_limpar.clicked.connect(self._limpar_selecao)

        header.addWidget(btn_todos)
        header.addSpacing(6)
        header.addWidget(btn_limpar)
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color: #3a3a3a;')
        layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(130)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(4)
        grid.setContentsMargins(4, 4, 4, 4)

        clientes = self.interface.clientes_disponiveis
        if clientes:
            colunas = 4
            for idx, cliente in enumerate(clientes):
                cb = QCheckBox(cliente)
                self.interface.checkboxes[cliente] = cb
                grid.addWidget(cb, idx // colunas, idx % colunas)
        else:
            lbl = QLabel('⚠️  Nenhum cliente configurado no .env')
            lbl.setStyleSheet('color: #cc8800;')
            grid.addWidget(lbl, 0, 0)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        return card

    def _card_opcoes_executar(self):
        card = self._card()
        layout = QHBoxLayout(card)
        layout.setSpacing(24)

        self._grupo_modo = QButtonGroup(self)

        self.rb_atualizar = QRadioButton('Atualizar')
        self.rb_executar_todos = QRadioButton('Executar todos')
        self.rb_apenas_processar = QRadioButton('Apenas processar')
        self.rb_atualizar.setChecked(True)

        self._grupo_modo.addButton(self.rb_atualizar)
        self._grupo_modo.addButton(self.rb_executar_todos)
        self._grupo_modo.addButton(self.rb_apenas_processar)

        layout.addWidget(self.rb_atualizar)
        layout.addWidget(self.rb_executar_todos)
        layout.addWidget(self.rb_apenas_processar)
        layout.addStretch()

        self.btn_executar = QPushButton('▶  EXECUTAR')
        self.btn_executar.setObjectName('btn_executar')
        self.btn_executar.setFixedWidth(150)
        self.btn_executar.clicked.connect(self._executar)
        layout.addWidget(self.btn_executar)

        return card

    def _card_log(self):
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(self._label_secao('📋  LOG DE EXECUÇÃO'))
        header.addStretch()

        self.lbl_status = QLabel('Pronto')
        self.lbl_status.setStyleSheet('color: #666666; font-size: 11px;')
        header.addWidget(self.lbl_status)

        btn_limpar = QPushButton('Limpar')
        btn_limpar.setFixedWidth(90)
        btn_limpar.clicked.connect(lambda: self.log_area.clear())
        header.addWidget(btn_limpar)
        layout.addLayout(header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        return card

    def _obter_modo(self) -> str:
        if self.rb_atualizar.isChecked():
            return 'atualizar'
        if self.rb_executar_todos.isChecked():
            return 'executar_todos'
        return 'apenas_processar'

    def _selecionar_diretorio(self):
        diretorio = QFileDialog.getExistingDirectory(self, 'Selecionar Diretório')
        if diretorio:
            self.input_diretorio.setText(diretorio)
            arquivos = list(Path(diretorio).glob('*.sql'))
            self.lbl_qtd_arquivos.setText(f'{len(arquivos)} arquivo(s) .sql encontrado(s)')

    def _selecionar_todos(self):
        for cb in self.interface.checkboxes.values():
            cb.setChecked(True)

    def _limpar_selecao(self):
        for cb in self.interface.checkboxes.values():
            cb.setChecked(False)

    def _obter_clientes_selecionados(self):
        return [c for c, cb in self.interface.checkboxes.items() if cb.isChecked()]

    def _atualizar_contagem_manual(self, texto):
        caminho = Path(texto)
        if caminho.is_dir():
            arquivos = list(caminho.glob('*.sql'))
            self.lbl_qtd_arquivos.setText(f'{len(arquivos)} arquivo(s) .sql encontrado(s)')
        else:
            self.lbl_qtd_arquivos.setText('Diretório inválido')

    def _executar(self):
        diretorio_str = self.input_diretorio.text()
        diretorio = Path(diretorio_str) if diretorio_str else None
        clientes = self._obter_clientes_selecionados()
        modo = self._obter_modo()

        valido, mensagem = self.interface.controlador.validar_execucao(diretorio, clientes, modo)
        if not valido:
            QMessageBox.warning(self, 'Aviso', mensagem)
            return

        if self.interface.processando:
            QMessageBox.warning(self, 'Aviso', 'Já existe um processamento em andamento.')
            return

        msg = self.interface.controlador.montar_mensagem_confirmacao(diretorio, clientes, modo)
        if QMessageBox.question(self, 'Confirmar Execução', msg) != QMessageBox.StandardButton.Yes:
            return

        self.interface.processando = True
        self.btn_executar.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_status.setText('Processando...')

        self.interface.worker = Worker(
            self.interface.controlador, diretorio, clientes, modo
        )
        self.interface.worker.sinal_log.connect(self.adicionar_log)
        self.interface.worker.sinal_progresso.connect(self.atualizar_progresso_ui)
        self.interface.worker.sinal_finalizado.connect(self._on_finalizado)
        self.interface.worker.start()

    def adicionar_log(self, tipo: str, mensagem: str):
        cores = {
            'info':    '#888888',
            'success': '#5a9a5a',
            'warning': '#cc8800',
            'error':   '#cc4444',
        }
        simbolos = {
            'info':    'ℹ',
            'success': '✓',
            'warning': '⚠',
            'error':   '✗',
        }

        cor = cores.get(tipo, '#888888')
        simbolo = simbolos.get(tipo, '•')

        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(cor))
        cursor.setCharFormat(fmt)
        cursor.insertText(f'{simbolo}  {mensagem}\n')

        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()

    def atualizar_progresso_ui(self, atual: int, total: int, mensagem: str):
        if total > 0:
            self.progress_bar.setValue(int((atual / total) * 100))
            self.lbl_status.setText(f'{atual}/{total}')

    def _on_finalizado(self, sucesso: bool, mensagem: str):
        self.interface.processando = False
        self.btn_executar.setEnabled(True)
        self.lbl_status.setText('Pronto')
        self.progress_bar.setValue(100 if sucesso else self.progress_bar.value())

        if sucesso:
            QMessageBox.information(self, 'Sucesso', mensagem)
        else:
            QMessageBox.warning(self, 'Aviso', mensagem)