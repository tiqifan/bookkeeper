"""
предстваление виджета расходов.
"""
from datetime import datetime
from PySide6 import QtWidgets, QtCore

from bookkeeper.view.utils import LabeledInput, HistoryTable, \
    LabeledBox, add_del_buttons_widget
from bookkeeper.repository.abstract_repository import AbstractRepository
from bookkeeper.models.expense import Expense
from bookkeeper.models.category import Category


class ExpenseHistory(QtWidgets.QWidget):
    """
    история расходов
    """
    def __init__(self, exp_repo: AbstractRepository[Expense],
                 cat_repo: AbstractRepository[Category], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exp_repo = exp_repo
        self.cat_repo = cat_repo
        self.columns = ('Date', 'Paid', 'Category', 'Comment')
        self.table = HistoryTable(columns=self.columns,
                                  n_rows=len(self.exp_repo.get_all()))
        self.data: list[list[str]] = []
        self.set_data()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(QtWidgets.QLabel('History'))
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.table.cellChanged.connect(self.handle_cell_changed)

    def handle_cell_changed(self, row: int, column: int) -> None:
        """
        Обработчик изменения ячейки таблицы
        """
        new_value = self.table.item(row, column).text()
        pk = self.exp_repo.get_all()[::-1][row].pk
        changed_row = self.exp_repo.get(pk)
        try:
            if column == 0:
                changed_row.added_date = datetime.strptime(new_value, '%Y-%m-%d %H:%M:%S')
            elif column == 1:
                changed_row.amount = int(new_value)
            elif column == 2:
                changed_row.category = self.cat_repo.get_all(
                    {'name': new_value.lower()})[0].pk
            else:
                changed_row.comment = new_value
            self.exp_repo.update(changed_row)
        except (TypeError, ValueError):
            QtWidgets.QMessageBox.critical(self, 'Error', 'Wrong input!')

    def set_data(self) -> None:
        """
        представление таблицы истории расходов
        """
        self.data = []
        got_all = self.exp_repo.get_all()
        if got_all:
            for exp in got_all[::-1]:
                temp = [exp.expense_date, exp.amount,
                        self.cat_repo.get(int(exp.category)).name, exp.comment]
                self.data.append(temp)
        self.table.set_data(self.data)


class ExpenseManager(QtWidgets.QWidget):
    """
    виджет добавления и удаления расходов
    """
    button_clicked = QtCore.Signal(int, str, str, datetime)

    def __init__(self, exp_repo: AbstractRepository[Expense],
                 cat_repo: AbstractRepository[Category],
                 exp_hist: ExpenseHistory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exp_hist = exp_hist
        self.exp_repo = exp_repo
        self.cat_repo = cat_repo
        self.cat_list: list[str] = []
        self.comm_input = LabeledInput('Comment:', '')
        self.paid_input = LabeledInput('Paid:', '0')
        self.cat_choice = LabeledBox('Category', self.cat_list)
        self.set_cat_list()

        self.add_button = QtWidgets.QPushButton('Add')
        self.add_button.clicked.connect(self.add)
        self.delete_button = QtWidgets.QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete)

        self.date_input = QtWidgets.QDateTimeEdit()
        self.date_input.setDateTime(QtCore.QDateTime.currentDateTime())

        self.main_layout = QtWidgets.QVBoxLayout()

        self.main_layout.addWidget(QtWidgets.QLabel('New expense'))

        self.inputs_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.cat_choice, 0, 0)
        self.layout.addWidget(self.paid_input, 0, 1)
        self.layout.addWidget(self.date_input, 1, 1)
        self.layout.addWidget(self.comm_input, 1, 0)
        self.inputs_widget.setLayout(self.layout)
        self.main_layout.addWidget(self.inputs_widget)

        self.main_layout.addWidget(add_del_buttons_widget(self))

        self.setLayout(self.main_layout)

    @QtCore.Slot()
    def set_cat_list(self) -> None:
        """
        обновление выпадающего списка категорий
        """
        self.cat_list = [cat.name.capitalize() for
                         cat in self.cat_repo.get_all()]
        self.cat_choice.box.clear()
        self.cat_choice.box.addItems(self.cat_list)
        self.exp_hist.set_data()

    def submit(self, mode: str) -> None:
        """
        обработка полученных данных
        """
        try:
            self.button_clicked.emit(int(self.paid_input.input.text()),
                                     str(self.cat_choice.box.currentText()),
                                     str(self.comm_input.input.text()),
                                     str(datetime.strptime(self.date_input.text(),
                                                           '%d.%m.%Y %H:%M')))
            self.button_clicked.connect(self.edit_expense(
                mode, int(self.paid_input.input.text()),
                self.cat_choice.box.currentText(), self.comm_input.input.text(),
                datetime.strptime(self.date_input.text(), '%d.%m.%Y %H:%M')))
            self.button_clicked.connect(self.exp_hist.set_data())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Incorrect input!')

    def edit_expense(self, mode: str, amount: int,
                     cat: str, comm: str, date: datetime) -> None:
        """
        добавление и удаление объектов в зависимости от значения режима mod: 'add' или 'delete'
        по категории cat на сумму amount
        """
        cat_pk = self.cat_to_pk(cat)
        exp = Expense(amount, int(cat_pk), expense_date=date, comment=comm)
        if mode == 'add':
            self.exp_repo.add(exp)
        elif mode == 'delete':
            exp_pk = self.exp_repo.get_all({'amount': amount,
                                            'category': cat_pk,
                                            'expense_date': str(date)})[0].pk
            self.exp_repo.delete(exp_pk)

    def cat_to_pk(self, cat: str) -> int:
        """
        поиск идентификатора категории по названию
        """
        return self.cat_repo.get_all({'name': cat.lower()})[0].pk

    def add(self) -> None:
        """
        submit в режиме добавления.
        """
        self.submit('add')

    def delete(self) -> None:
        """
        submit в режиме удаления.
        """
        self.submit('delete')


class ExpenseTab(QtWidgets.QWidget):
    """
    объединение истории и добавления/удаления
    """
    def __init__(self, exp_repo: AbstractRepository[Expense],
                 cat_repo: AbstractRepository[Category],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exp_repo = exp_repo
        self.cat_repo = cat_repo
        self.layout = QtWidgets.QVBoxLayout()
        self.exp_hist = ExpenseHistory(self.exp_repo, self.cat_repo)
        self.new_exp = ExpenseManager(self.exp_repo, self.cat_repo, self.exp_hist)
        self.layout.addWidget(self.exp_hist)
        self.layout.addWidget(self.new_exp)
        self.setLayout(self.layout)