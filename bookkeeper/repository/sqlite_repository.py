import sqlite3

from inspect import get_annotations
from bookkeeper.repository.abstract_repository import AbstractRepository, T

from datetime import datetime
from typing import Any


class SQLiteRepository(AbstractRepository[T]):
    def __init__(self, db_file: str, cls: type) -> None:
        self.db_file = db_file
        self.table_name = cls.__name__.lower()
        self.fields = get_annotations(cls, eval_str=True)
        self.fields.pop('pk')

    def add(self, obj: T) -> int:
        if getattr(obj, 'pk', None) != 0:
            raise ValueError(f'object {obj} has filled `pk` attribute')
        names = ', '.join(self.fields.keys())
        p = ', '.join("?" * len(self.fields))
        values = [getattr(obj, x) for x in self.fields]
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys = ON')
            cur.execute(f'INSERT INTO {self.table_name} ({names}) '
                        f'VALUES ({placeholders})', values)
            con.commit()
            obj.pk = cur.lastrowid
        con.close()
        return obj.pk

    def conv_dt(self, temp: list[T] | tuple[T]) -> tuple[T]:
        """
        datetime конвертер.

        temp - 'элементы объекта в виде списка'

        возращает конвертированный список элементов
        """

        obj = self.cls(*temp)
        conv_temp: tuple = tuple()
        for i, elem in enumerate(temp):
            try:
                conv_temp += (list(obj.__annotations__.values())[i](elem),)
            except TypeError:
                if temp[i] is None:
                    conv_temp += (temp[i],)
                elif isinstance(temp[i], datetime):
                    conv_temp += (list(obj.__annotations__.values(
                    ))[i].strptime(elem, '%Y-%m-%d %H:%M:%S'),)
                else:
                    conv_temp += (type(temp[i])(temp[i]),)
        return conv_temp

    def get(self, pk: int) -> T | None:
        """ Получить объект по id """

        with sqlite3.connect(self.db_file) as con:
            curs = con.cursor()
            res = curs.execute(f'SELECT * FROM {self.table_name} WHERE pk = {pk}')
            temp = res.fetchone()
        con.close()
        if temp is None:
            return None
        return self.cls(*self.conv_dt(temp))

    def get_all(self, where: dict[str, Any] | None = None) -> list[T]:
        """
        Получить все записи по некоторому условию
        where - условие в виде словаря {'название_поля': значение}
        если условие не задано (по умолчанию), вернуть все записи

        возвращает список объектов из базы данных
        """
        with sqlite3.connect(self.db_file) as con:
            curs = con.cursor()
            res = curs.execute(f'SELECT * FROM {self.table_name}')
        if where is None:
            return [self.cls(*self.conv_dt(temp))
                    for temp in res.fetchall()]
        objs = []
        for temp in res.fetchall():
            obj = self.cls(*self.conv_dt(temp))
            if all([getattr(obj, attr) == value for attr, value in where.items()]):
                objs.append(obj)
        con.close()
        return objs

    def update(self, obj: T) -> None:
        """ Обновить данные об объекте. Объект должен содержать поле pk.
        перезаписывает элемент в базе данных, не меняя его идентификатор.
        ничего не возвращает
        """
        if obj.pk == 0:
            raise ValueError('unknown primary key of the object')
        names = list(self.fields.keys())
        values = [getattr(obj, i) for i in self.fields]
        pk = obj.pk
        with sqlite3.connect(self.db_file) as con:
            curs = con.cursor()
            for i, elemen in enumerate(names):
                try:
                    curs.execute(f'UPDATE {self.table_name} SET {elemen}'
                                f' = {repr(values[i])} WHERE pk = {pk}')
                except sqlite3.OperationalError:
                    curs.execute(f'UPDATE {self.table_name} SET {elemen}'
                                f' = {repr(str(values[i]))} WHERE pk = {pk}')
            con.commit()
        con.close()

    def delete(self, pk: int) -> None:
        """ Удалить запись """
        with sqlite3.connect(self.db_file) as con:
            curs = con.cursor()
            curs.execute(f'DELETE FROM {self.table_name} WHERE pk = {pk}')
            rows = curs.rowcount
            if rows == 0:
                raise KeyError
            con.commit()
        con.close()
