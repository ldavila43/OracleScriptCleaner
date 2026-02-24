STYLE = """
    QMainWindow, QWidget {
        background-color: #1e1e1e;
        color: #e0e0e0;
        font-family: 'Consolas', 'Courier New', monospace;
    }

    QFrame#card {
        background-color: #2a2a2a;
        border: 1px solid #3a3a3a;
        border-radius: 6px;
        padding: 8px;
    }

    QLabel#titulo {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 2px;
    }

    QLabel#secao {
        font-size: 12px;
        font-weight: 700;
        color: #aaaaaa;
        letter-spacing: 1px;
    }

    QLabel {
        font-size: 12px;
        font-weight: 600;
        color: #e0e0e0;
    }

    QLineEdit {
        background-color: #1e1e1e;
        border: 1px solid #3a3a3a;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 12px;
        font-weight: 600;
        color: #e0e0e0;
    }

    QLineEdit:focus {
        border: 1px solid #666666;
    }

    QPushButton {
        background-color: #333333;
        border: 1px solid #444444;
        border-radius: 4px;
        padding: 7px 16px;
        font-size: 12px;
        font-weight: 700;
        color: #e0e0e0;
        letter-spacing: 0.5px;
    }

    QPushButton:hover {
        background-color: #3d3d3d;
        border: 1px solid #555555;
    }

    QPushButton:pressed {
        background-color: #2a2a2a;
    }

    QPushButton:disabled {
        background-color: #252525;
        color: #555555;
        border: 1px solid #333333;
    }

    QPushButton#btn_executar {
        background-color: #2d4a2d;
        border: 1px solid #3d6b3d;
        color: #7dbb7d;
        font-size: 13px;
        font-weight: 800;
        padding: 9px 24px;
        letter-spacing: 1px;
    }

    QPushButton#btn_executar:hover {
        background-color: #335233;
        border: 1px solid #4a7a4a;
    }

    QPushButton#btn_executar:disabled {
        background-color: #252525;
        color: #444444;
        border: 1px solid #333333;
    }

    QPushButton#btn_selecionar {
        background-color: #1e3a4a;
        border: 1px solid #2a5266;
        color: #7ab8d4;
        font-weight: 700;
    }

    QPushButton#btn_selecionar:hover {
        background-color: #224455;
    }

    QCheckBox {
        font-size: 12px;
        font-weight: 600;
        color: #cccccc;
        spacing: 6px;
    }

    QCheckBox::indicator {
        width: 14px;
        height: 14px;
        border: 1px solid #555555;
        border-radius: 3px;
        background-color: #1e1e1e;
    }

    QCheckBox::indicator:checked {
        background-color: #4a7a4a;
        border: 1px solid #5a9a5a;
    }

    QProgressBar {
        background-color: #1e1e1e;
        border: 1px solid #3a3a3a;
        border-radius: 3px;
        height: 8px;
        text-align: center;
        font-size: 10px;
        color: transparent;
    }

    QProgressBar::chunk {
        background-color: #4a7a4a;
        border-radius: 3px;
    }

    QTextEdit {
        background-color: #161616;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 11px;
        font-weight: 600;
        color: #cccccc;
        padding: 8px;
    }

    QScrollArea {
        border: none;
        background-color: transparent;
    }

    QScrollBar:vertical {
        background-color: #1e1e1e;
        width: 8px;
        border-radius: 4px;
    }

    QScrollBar::handle:vertical {
        background-color: #444444;
        border-radius: 4px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #555555;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QSplitter::handle {
        background-color: #3a3a3a;
        height: 4px;
    }

    QSplitter::handle:hover {
        background-color: #555555;
    }
"""