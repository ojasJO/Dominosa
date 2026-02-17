def __init__(self):
    super().__init__()
    self.setWindowTitle("Dominosa")
    self.resize(1000, 800)
    self.setStyleSheet(STYLES)

    self.mode = "SOLO"
    self.human_turn = True

    self.central = QWidget()
    self.setCentralWidget(self.central)

    self.layout = QStackedWidget(self.central)

    self.init_menu()
    self.init_game()

    self.overlay = Overlay(self.central)
    self.overlay.btn.clicked.connect(self.reset_to_menu)

    container = QVBoxLayout(self.central)
    container.setContentsMargins(0, 0, 0, 0)
    container.addWidget(self.layout)
