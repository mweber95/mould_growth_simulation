import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QSizePolicy, QPushButton, QLabel
import sys


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.title = 'Mould Growth Simulation'
        self.width = 650
        self.height = 400
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.m = PlotCanvas(self, width=5, height=4)
        self.m.move(150, 0)

        self.label_m_index = QLabel("Mould Index (0-6)", self)
        self.label_m_index.move(12, 10)
        self.label_m_index.resize(130, 20)
        self.field_m_index = QLineEdit(self)
        self.field_m_index.setText("0")
        self.field_m_index.move(10, 40)
        self.field_m_index.resize(130, 20)

        self.label_temperature = QLabel("Temperature in °C", self)
        self.label_temperature.move(12, 70)
        self.label_temperature.resize(130, 20)
        self.field_temperature = QLineEdit(self)
        self.field_temperature.setText("25")
        self.field_temperature.move(10, 100)
        self.field_temperature.resize(130, 20)

        self.label_rel_hum = QLabel("Rel. Humidity in %", self)
        self.label_rel_hum.move(12, 130)
        self.label_rel_hum.resize(130, 20)
        self.field_rel_hum = QLineEdit(self)
        self.field_rel_hum.setText("95")
        self.field_rel_hum.move(10, 160)
        self.field_rel_hum.resize(130, 20)

        self.label_surf_qual = QLabel("Surf. Quality (0-1)", self)
        self.label_surf_qual.move(12, 190)
        self.label_surf_qual.resize(130, 20)
        self.field_surf_qual = QLineEdit(self)
        self.field_surf_qual.setText("0")
        self.field_surf_qual.move(10, 220)
        self.field_surf_qual.resize(130, 20)

        self.label_wood_spec = QLabel("Wood Species (0-1)", self)
        self.label_wood_spec.move(12, 250)
        self.label_wood_spec.resize(130, 20)
        self.field_wood_spec = QLineEdit(self)
        self.field_wood_spec.setText("0")
        self.field_wood_spec.move(10, 280)
        self.field_wood_spec.resize(130, 20)

        self.button = QPushButton('Compute', self)
        self.button.setToolTip('Computing Mould Growth')
        self.button.move(20, 320)
        self.button.resize(110, 60)
        self.button.clicked.connect(self.clicked)

        self.show()

    def clicked(self):
        m_index = int(self.field_m_index.text())
        calc_m_index = [m_index]
        calc_m_index_plot = []
        temp = int(self.field_temperature.text())
        surf_qual = int(self.field_surf_qual.text())
        growth_days = np.arange(101)
        wood_spec = int(self.field_wood_spec.text())
        rel_hum = int(self.field_rel_hum.text())

        growth_days, calc_m_index_plot = calculate_growth(calc_m_index, calc_m_index_plot, growth_days, m_index,
                                                          rel_hum, surf_qual, temp, wood_spec)

        self.m.plot(growth_days, calc_m_index_plot)


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = None

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot(self, x, y):
        if not self.ax:
            self.ax = self.figure.add_subplot(111)
        self.ax.clear()
        self.ax.plot(x, y, 'r-')
        self.ax.set_title('Simulated Mould Growth')
        self.draw()


def tv_function(temp, rel_hum, wood_spec):
    tv_value = np.exp(-0.74 * np.log(temp) - 12.72 * np.log(rel_hum) + 0.06 * wood_spec + 61.5)
    return tv_value


def tm_function(temp, rel_hum, wood_spec, surf_qual):
    tm_value = np.exp(-0.68 * np.log(temp) - 13.9 * np.log(rel_hum) + 0.14 * wood_spec - 0.33 * surf_qual + 66.02)
    return tm_value


def coefficient_one(m_index, tv, tm):
    if m_index < 1:
        k1 = 1
        return k1
    elif m_index >= 1:
        k1 = 2 / ((tv / tm) - 1)
        return k1


def rel_hum_crit_function(temp):
    if temp <= 20:
        rel_hum_crit = ((- 0.00267 * (temp ** 3)) + (0.160 * (temp ** 2)) - (3.13 * temp) + 100)
        return rel_hum_crit
    if temp > 20:
        rel_hum_crit = 80
        return rel_hum_crit


def m_max_function(rel_hum, rel_hum_crit):
    m_max = 1 + (7 * ((rel_hum_crit - rel_hum) / (rel_hum_crit - 100))) - 2 * (((rel_hum_crit - rel_hum) / (rel_hum_crit - 100)) ** 2)
    return m_max


def coefficient_two(m_index, m_max):
    k2 = 1 - (np.exp(2.3 * (m_index - m_max)))
    return k2


def main_function(temp, rel_hum, wood_spec, surf_qual, k1, k2):
    curr_mol_index_update = (1 / (7 * np.exp(-0.68 * np.log(temp) - 13.9 * np.log(rel_hum) + 0.14 * wood_spec - 0.33 * surf_qual + 66.02))) * k1 * k2
    return curr_mol_index_update


def calculate_growth(calc_m_index, calc_m_index_plot, growth_days, m_index, rel_hum, surf_qual, temp, wood_spec):
    for day in growth_days:
        tv = tv_function(temp, rel_hum, wood_spec)
        tm = tm_function(temp, rel_hum, wood_spec, surf_qual)
        k1 = coefficient_one(m_index, tv, tm)

        rel_hum_crit = rel_hum_crit_function(temp)
        m_max = m_max_function(rel_hum, rel_hum_crit)
        k2 = coefficient_two(m_index, m_max)

        curr_mol = main_function(temp, rel_hum, wood_spec, surf_qual, k1, k2)
        calc_m_index.append(curr_mol)

        m_index = np.sum(np.array(calc_m_index))
        calc_m_index_plot.append(m_index)

        print(f"Day = {day} --> Index = {m_index}")

    return growth_days, calc_m_index_plot


def main():
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
