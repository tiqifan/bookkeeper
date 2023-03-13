"""
Виджет для представления категорий.
"""
from PySide6 import QtWidgets, QtCore

from bookkeeper.view.utils import LabeledInput, HistoryTable, \
    LabeledBox, add_del_buttons_widget
from bookkeeper.repository.abstract_repository import AbstractRepository, T
from bookkeeper.models.category import Category
from bookkeeper.models.expense import Expense


def parent_to_pk(repo: AbstractRepository[T], name: str) -> int | None:
    """
    Поиск идентификатора категории name по репозиторию repo
    """
    try:
        return repo.get_all({'name': name.lower()})[0].pk
    except IndexError:
        return None


class CategoriesExists(QtWidgets.QWidget):
    """
    Поджет для отображения существующих категорий
    """
    cellChanged = QtCore.Signal(str)

    def __init__(self, cat_repo: AbstractRepository[Category], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cat_repo = cat_repo
        self.columns = ('Category', 'Parent')
        self.data: list[list[str]] = []
        self.table = HistoryTable(columns=self.columns,
                                  n_rows=len(self.cat_repo.get_all()))
        self.set_data()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(QtWidgets.QLabel('Categories'))
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.table.cellChanged.connect(self.handle_cell_changed)

    def handle_cell_changed(self, row: int, column: int) -> None:
        """
        Обработчик изменения ячейки в таблице по номеру строки и столбцы
        """
        new_value = self.table.item(row, column).text().lower()
        pk = self.cat_repo.get_all()[::-1][row].pk
        changed_row = self.cat_repo.get(pk)
        if column == 0:
            changed_row.name = new_value
        else:
            parent_pk = parent_to_pk(self.cat_repo, new_value)
            if parent_pk is not None:
                changed_row.parent = parent_pk
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'Parant doesn\'t exist')
                return None
        self.cat_repo.update(changed_row)
        return None

    def set_data(self) -> None:
        """
        отображение таблицы с существующими категориями
        """
        self.data = []
        got_all = self.cat_repo.get_all()
        if got_all:
            for cat in got_all[::-1]:
                try:
                    temp = [cat.name,
                            self.cat_repo.get(int(cat.parent)).name]
                except TypeError:
                    temp = [cat.name, '']
                self.data.append(temp)
        self.table.set_data(self.data)


class CategoryManager(QtWidgets.QWidget):
    """
    виджет для добавления и удаления категорий.
    """
    button_clicked = QtCore.Signal(str, str)

    def __init__(self, cat_repo: AbstractRepository[Category],
                 exp_repo: AbstractRepository[Expense],
                 cat_ex: CategoriesExists,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cat_ex = cat_ex
        self.cat_repo = cat_repo
        self.exp_repo = exp_repo
        self.par_list = [cat.name for cat in self.cat_repo.get_all()][::-1]
        self.parent_choice = LabeledBox('Parent (if needed)', self.par_list)
        self.def_cat = 'Другое'
        self.parent_choice.box.setCurrentText(self.def_cat)
        self.name_input = LabeledInput('Category name', '')
        self.set_par_choice()

        self.add_button = QtWidgets.QPushButton('Add')
        self.add_button.clicked.connect(self.add)
        self.delete_button = QtWidgets.QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(QtWidgets.QLabel('Category manager'))
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(self.parent_choice)

        self.layout.addWidget(add_del_buttons_widget(self))
        self.setLayout(self.layout)

    def set_par_choice(self) -> None:
        """
        "Другое" как категория по умолчанию
        """
        self.par_list = [cat.name.capitalize() for
                         cat in self.cat_repo.get_all()][::-1]
        self.parent_choice.box.clear()
        self.parent_choice.box.addItems(self.par_list)
        self.parent_choice.box.setCurrentText(self.def_cat)
        self.button_clicked.emit('', '')

    def submit(self, mode: str) -> None:
        """
        Вызов обработки полученных данных по нажатии кнопки
        """
        try:
            self.button_clicked.emit(str(self.name_input.input.text()),
                                     str(self.parent_choice.box.currentText()))
            self.button_clicked.connect(
                self.edit_category(mode,
                                   str(self.name_input.input.text()),
                                   str(self.parent_choice.box.currentText())))
            self.button_clicked.connect(self.cat_ex.set_data())
            self.button_clicked.connect(self.set_par_choice())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Incorrect input!')

    def edit_category(self, mode: str, name: str, parent: str) -> None:
        """
        Добавляет объект в репозиторий и удаляет объект по названию и родительской категории
        """
        parent_pk = parent_to_pk(self.cat_repo, parent)
        cat = Category(name.lower(), parent_pk)
        if parent != '' and parent_pk is None:
            QtWidgets.QMessageBox.critical(self, 'Error',
                                           'Parent doesn\'t exist!')
            return
        if mode == 'add':
            self.cat_repo.add(cat)
        elif mode == 'delete':
            cat_pk = self.cat_repo.get_all({'name': name.lower(),
                                            'parent': parent_pk})[0].pk
            if cat_pk == 255:
                return
            self.cat_repo.delete(cat_pk)
            for exp in self.exp_repo.get_all({'category': cat_pk}):
                new_exp = Expense(exp.amount, int(parent_pk), exp.expense_date,
                                  exp.added_date, exp.comment, exp.pk)
                self.exp_repo.update(new_exp)
            for cat in self.cat_repo.get_all({'parent': cat_pk}):
                new_cat = Category(cat.name, parent_pk, cat.pk)
                self.cat_repo.update(new_cat)

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


class CategoriesTab(QtWidgets.QWidget):
    """
    Объединение существующих категорий и категории добавления/удаления
    """
    def __init__(self, cat_repo: AbstractRepository[Category],
                 exp_repo: AbstractRepository[Expense], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exp_repo = exp_repo
        self.cat_repo = cat_repo
        self.layout = QtWidgets.QVBoxLayout()
        self.act_cat = CategoriesExists(cat_repo=self.cat_repo)
        self.new_cat = CategoryManager(self.cat_repo, self.exp_repo,
                                       self.act_cat)
        self.layout.addWidget(self.act_cat)
        self.layout.addWidget(self.new_cat)
        self.setLayout(self.layout)