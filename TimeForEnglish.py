import csv
import os
import random
import sqlite3
import tkinter
from collections import namedtuple

import pyttsx3
from PIL import ImageTk, Image

RowDb = namedtuple(typename='RowDb',
                   field_names='id_ key translate form_2 form_3 example_text example_question description',
                   defaults=(None, '', '', '', '', '', '', ''))


class TimeValue:
    """
    Класс, состоящий из изменяемых объектов, необходимо для передачи параметров по ссылке
    """
    SECOND = MINUTE = HOUR = 0

    @classmethod
    def get_time_values(cls) -> tuple:
        return cls.SECOND, cls.MINUTE, cls.HOUR

    @classmethod
    def add_second(cls) -> int:
        cls.SECOND += 1
        return cls.SECOND

    @classmethod
    def add_minute(cls) -> int:
        cls.MINUTE += 1
        return cls.MINUTE

    @classmethod
    def add_hour(cls) -> int:
        cls.HOUR += 1
        return cls.HOUR

    @classmethod
    def zeroing_second(cls) -> int:
        cls.SECOND = 0
        return cls.SECOND

    @classmethod
    def zeroing_minute(cls) -> int:
        cls.MINUTE = 0
        return cls.MINUTE

    @classmethod
    def zeroing_hour(cls) -> int:
        cls.HOUR = 0
        return cls.HOUR


class SampleApp(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)
        self._frame = None
        self.mistake = False
        self.background_color = '#669999'
        self.default_entry_color = 'black'

        self.audio_image = Image.open(fp='audio_image.png')
        self.audio_image = ImageTk.PhotoImage(self.audio_image)

        self.key = ''
        self.answer = ''
        self.words_dict = {}
        self.irregular_verbs_dict = {}

        self.set_root_config()

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 100)

        # TODO после реализации добавления/редактирования/удаления слов с помощью интерфейса,
        # TODO удалить метод convert_csv_to_sqlite
        # Подготавливаем массив слов для изучения из файла English_dictionary.csv

        # соединяемся с базой данных, если базы данных нет, то создается новая
        self.db_con = sqlite3.connect('TimeForEnglish.db')
        self.db_cur = self.db_con.cursor()

        self.convert_csv_to_sqlite()
        self.create_or_read_db()

        menu_frame = tkinter.Frame(self, background=self.background_color)
        menu_frame.grid(column=0, row=0, columnspan=7)
        last_ten_words_button = tkinter.Button(menu_frame, text="Testing Page", font="Arial 12",
                                               command=lambda: self.switch_frame(MainPage))

        last_ten_words_button.grid(column=0, row=0, padx=10, pady=10)

        last_ten_words_button = tkinter.Button(menu_frame, text="Last 10 Words Added", font="Arial 12",
                                               command=lambda: self.switch_frame(TenWordsPage))

        last_ten_words_button.grid(column=1, row=0, padx=10, pady=10)

        irregular_words_button = tkinter.Button(menu_frame, text="Irregular Verbs", font="Arial 12",
                                                command=lambda: self.switch_frame(IrregularVerbsPage))

        irregular_words_button.grid(column=2, row=0, padx=10, pady=10)

        irregular_words_button = tkinter.Button(menu_frame, text="Add New Word", font="Arial 12",
                                                command=lambda: self.switch_frame(AddNewWord))

        irregular_words_button.grid(column=3, row=0, padx=10, pady=10)

        self.random_word = random.choice(list(self.words_dict.keys()))
        self.random_word = self.random_word.capitalize()

        self.random_irregular_verb = random.choice(list(self.irregular_verbs_dict.keys()))
        self.random_irregular_verb = self.random_irregular_verb.capitalize()

        close_button = tkinter.Button(self, text="Close", font="Arial 12")
        close_button.config(command=self.close_button_func)
        close_button.grid(column=6, row=4, padx=10, pady=10)

        self.switch_frame(PhotoImage)

    def create_or_read_db(self):
        # создаем таблицу, если ее не существует
        self.db_cur.executescript("""
            CREATE TABLE IF NOT EXISTS Words(
                id_ INTEGER PRIMARY KEY ASC,
                key TEXT,
                translate TEXT,
                example_text TEXT,
                example_question TEXT,
                description TEXT
                );
                
            CREATE TABLE IF NOT EXISTS IrregularVerbs(
                id_ INTEGER PRIMARY KEY ASC,
                key TEXT,
                translate TEXT,
                form_2 TEXT,
                form_3 TEXT,
                example_text TEXT,
                example_question TEXT,
                description TEXT
                );
        """)

        rows_words = self.db_cur.execute("""
            SELECT 
                id_,
                key,
                translate,
                example_text,
                example_question,
                description
            FROM Words
        """)
        for row in rows_words:
            word = RowDb(*row)
            self.words_dict[word.key] = word

        rows_irregular_verbs = self.db_cur.execute("""
            SELECT 
                id_,
                key,
                translate,
                example_text,
                example_question,
                description,
                form_2,
                form_3
            FROM IrregularVerbs
        """)
        for row in rows_irregular_verbs:
            word = RowDb(*row)
            self.irregular_verbs_dict[word.key] = word
        self.db_con.commit()

        if self.words_dict:
            print(f'Общее количество записей в базе - {len(self.words_dict) + len(self.irregular_verbs_dict)}\n')
        else:
            raise Exception('Нет данных для изучения')

    def new_word(self) -> str:
        """ Выбирает новое слово """
        self.random_word = random.choice(list(self.words_dict.keys()))
        return self.random_word.capitalize()

    def new_verb(self) -> str:
        """ Выбирает новый неправильный глагол """
        self.random_irregular_verb = random.choice(list(self.irregular_verbs_dict.keys()))
        return self.random_irregular_verb

    @staticmethod
    def put_placeholder(entry_, text_):
        entry_.insert(0, text_)
        entry_['fg'] = 'grey'

    @staticmethod
    def focus_in(event=None, entry_=None, color=None):
        if entry_ and entry_['fg'] == 'grey':
            entry_.delete('0', 'end')
            entry_['fg'] = color

    @staticmethod
    def focus_out(event=None, entry_=None, text=None):
        if not entry_.get():
            SampleApp.put_placeholder(entry_, text)

    def switch_frame(self, frame_class):
        """ Destroys current frame and replaces it with a new one. """

        # проверка на повторное нажатие кнопки возврата к окну, в котором находишься,
        # при этом не нужно создавать окно заново
        if self._frame and self._frame.__class__.__name__ == frame_class.__name__:
            return

        # создаем новый виджет
        new_frame = frame_class(self)

        # удаляем старый
        if self._frame is not None:
            self._frame.destroy()

        self._frame = new_frame
        self._frame.grid(column=1, row=1, columnspan=6, rowspan=3, sticky=tkinter.N)

    def set_root_config(self):
        """
        Заполнение конфигурации для корневого окна (ROOT)
        """
        self.title('Time For English')

        # Запрещаем пользователю менять размеры окна!
        self.resizable(False, False)

        # для особенных
        self.protocol('WM_DELETE_WINDOW', self._window_deleted)  # обработчик закрытия окна

        # Установка цвета фона окна
        self.configure(background=self.background_color)

        # Размеры экрана
        screen_width = self.winfo_screenwidth()  # ширина экрана
        screen_height = self.winfo_screenheight()  # высота экрана

        # создаем сетку (разметку) для виджетов - колонки и строки,
        # общие параметры которых равны размерам окна приложения (self.geometry)
        self.columnconfigure(0, weight=50)
        self.columnconfigure(1, weight=160)
        self.columnconfigure(2, weight=160)
        self.columnconfigure(3, weight=160)
        self.columnconfigure(4, weight=160)
        self.columnconfigure(5, weight=160)
        self.columnconfigure(6, weight=50)

        self.rowconfigure(0, weight=20)
        self.rowconfigure(1, weight=217)
        self.rowconfigure(2, weight=217)
        self.rowconfigure(3, weight=217)
        self.rowconfigure(4, weight=29)

        width = screen_width // 2  # середина экрана
        height = screen_height // 2
        width -= 450  # смещение от середины
        height -= 350
        self.geometry(f'900x700+{width}+{height}')

    def _window_deleted(self):
        from tkinter import messagebox
        messagebox.showwarning("Warning", 'We have buttom "Close"!!!')
        self.db_cur.close()
        self.db_con.close()
        ROOT.quit()

    def close_button_func(self):
        """
        Реализация кнопки "Close"
        """
        self.db_cur.close()
        self.db_con.close()
        self.quit()

    def convert_csv_to_sqlite(self):
        """
        Получения списка всех слов
        """
        csv_path = "English_dictionary.csv"

        # отчищаем базу
        self.db_cur.executescript("""
            DROP TABLE IF EXISTS Words; 
            DROP TABLE IF EXISTS IrregularVerbs;
        """)
        self.db_con.commit()

        # создаем таблицу, если ее не существует
        self.db_cur.executescript("""
            CREATE TABLE IF NOT EXISTS Words(
                id_ INTEGER PRIMARY KEY ASC,
                key TEXT,
                translate TEXT,
                example_text TEXT,
                example_question TEXT,
                description TEXT
                );
                
            CREATE TABLE IF NOT EXISTS IrregularVerbs(
                id_ INTEGER PRIMARY KEY ASC,
                key TEXT,
                translate TEXT,
                form_2 TEXT,
                form_3 TEXT,
                example_text TEXT,
                example_question TEXT,
                description TEXT
                );
        """)

        with open(csv_path, "r") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=';')
            for row in reader:
                if row['irregular_verbs']:
                    self.db_cur.execute("""
                        INSERT INTO IrregularVerbs(
                            key,
                            translate,
                            form_2,
                            form_3,
                            example_text,
                            example_question,
                            description) VALUES (?,?,?,?,?,?,?)
                           """, (row['key'].lower(), row['translate'].lower(),
                                 row['form_2'], row['form_3'],
                                 row['example_text'], row['example_question'],
                                 row['description']))
                else:
                    self.db_cur.execute("""
                        INSERT INTO Words(
                            key,
                            translate,
                            example_text,
                            example_question,
                            description) VALUES (?, ?, ?, ?, ?)
                           """, (row['key'].lower(), row['translate'].lower(),
                                 row['example_text'], row['example_question'],
                                 row['description']))
        self.db_con.commit()


class PhotoImage(tkinter.Frame):
    """
    Загрузка картинки
    """

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)

        self.viewed_pictures_file = "./PhotoImage/viewed_pictures.txt"
        self.picture_choice = ''

        self._get_picture_choice()
        image = Image.open(f'./PhotoImage/{self.picture_choice}')

        # находим максимальную длину сторон
        max_size = max(image.size)
        # вычисляем пропорцию для уменьшения или увеличения изображения в окно
        ratio = (550 / float(max_size))
        width = int((float(image.size[0]) * float(ratio)))
        height = int((float(image.size[1]) * float(ratio)))

        # изменяем размер изображения
        resized_img = image.resize((width, height), Image.ANTIALIAS)

        self.img = ImageTk.PhotoImage(resized_img)
        self.panel = tkinter.Label(self, image=self.img)
        self.panel.grid(column=1, row=1, columnspan=6, rowspan=3, sticky=tkinter.N)

    def _get_picture_choice(self):
        """
        выбираем рандомную картинку, которую пользователь еще не видел
        """

        # если файл существует, но он пустой
        if os.path.exists(self.viewed_pictures_file) and os.stat(self.viewed_pictures_file).st_size == 0:
            # получаем список файлов из папки
            file_names = os.listdir("./PhotoImage")
            # исключаем viewed_pictures.txt из списка файлов, полученных в предыдущем шаге
            file_names.remove("viewed_pictures.txt")
        elif not os.path.exists(self.viewed_pictures_file):
            # получаем список файлов из папки
            file_names = os.listdir("./PhotoImage")
        else:
            file_names = open(self.viewed_pictures_file, 'r').read().splitlines()

        # выбираем рандомное изображение
        self.picture_choice = random.choice(file_names)

        self.write_file(file_names)

    def write_file(self, file_names: list):
        """
        запись скписка изображений в файл
        """
        # удаляем выбранное изображение из списка
        file_names.remove(self.picture_choice)

        with open(self.viewed_pictures_file, "w") as viewed_pictures:
            for name in file_names:
                viewed_pictures.write(name + '\n')

class MainPage(tkinter.Frame):
    """
    Стартовая страница для ввода слова
    """

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.configure(background=master.background_color)

        self.info_label = tkinter.Label(self)
        self.info_label.config(fg='white',
                               font="Arial 16",
                               background=master.background_color,
                               text='You need to study more!')

        # Виджет Frame (рамка) предназначен для организации виджетов внутри окна.
        self.top_frame = tkinter.Frame(self)
        self.example_frame = tkinter.Frame(self, background=master.background_color)
        self.answer_frame = tkinter.Frame(self.top_frame)

        self.word = tkinter.Label(self.top_frame)
        self.word.config(fg='black', font="Arial 14", width=30)
        self.word['text'] = master.random_word

        self.answer_text = tkinter.Label(self.answer_frame)
        self.answer_text.config(fg='black', font="Arial 14", width=15)
        self.answer_text['text'] = ''

        # Пример предложения с пройденным словом
        self.example_text = tkinter.Label(self.example_frame)
        self.example_text.config(font="Purisa 18", background=master.background_color, fg='white')

        # Аудио с пройденным словом
        self.answer_text_button = tkinter.Button(self.answer_frame, text="Audio", font="Arial 12")
        self.answer_text_button.config(command=self.answer_text_audio, image=master.audio_image)

        # Аудио предложения с пройденным словом
        self.example_text_button = tkinter.Button(self.example_frame, text="Audio", font="Arial 12")
        self.example_text_button.config(command=self.example_text_audio, image=master.audio_image)

        # Пример вопросительного предложения с пройденным словом
        self.example_question = tkinter.Label(self.example_frame)
        self.example_question.config(font="Purisa 18", background=master.background_color, fg='white')

        # Аудио вопросительного предложения с пройденным словом
        self.example_question_button = tkinter.Button(self.example_frame, text="Audio", font="Arial 12")
        self.example_question_button.config(command=self.example_question_audio, image=master.audio_image)

        # Entry - это виджет, позволяющий пользователю ввести одну строку текста.
        self.entry = tkinter.Entry(self.answer_frame, width=25, font="Arial 12", fg='black')
        # Метод bind привязывает событие к какому-либо действию
        # (нажатие кнопки мыши, нажатие клавиши на клавиатуре)
        self.entry.bind("<Return>", self.change)
        self.entry.focus()
        self.entry.grid(column=0, row=0, padx=10, pady=10)

        self.check_button = tkinter.Button(self.top_frame, text="Проверить", font="Arial 12", width=15)
        self.check_button.config(command=self.change)

        self.timer = tkinter.Label(self,
                                   text="%02i:%02i:%02i" % (TimeValue.get_time_values()),
                                   font=("Consolas", 14),
                                   fg='white',
                                   background=master.background_color)
        self.timer.after_idle(self.tick)

        # Блок для ввода слова (top_frame)
        tkinter.Label(self.top_frame).grid(column=0, row=0, padx=10, pady=10)
        self.word.grid(column=0, row=1, padx=10, pady=20)
        self.answer_frame.grid(column=1, row=1, padx=10, pady=10)
        self.check_button.grid(row=1, column=3, padx=10, pady=10)
        tkinter.Label(self.top_frame).grid(column=0, row=2, padx=10, pady=10)

        # Блок информационный (self)
        tkinter.Label(self, background=master.background_color).grid(column=0, row=0, padx=10, pady=10)
        self.info_label.grid(column=0, row=1, padx=10, pady=10)
        tkinter.Label(self, background=master.background_color).grid(column=0, row=2, padx=10, pady=10)
        self.timer.grid(column=0, row=3, padx=10, pady=10)
        tkinter.Label(self, background=master.background_color).grid(column=0, row=4, padx=10, pady=10)
        self.top_frame.grid(column=0, row=5, padx=10, pady=10)
        self.example_frame.grid(column=0, row=6, columnspan=2, padx=10, pady=10)

        # Блок примеров пройденного слова формируется только после правильно введенного значения

    def tick(self):
        """
        Реализация подсчета времени нахождения в программе
        """
        _, minute, hour = TimeValue.get_time_values()
        # Через каждую секунду происходит рекурсивый вызов функции
        self.timer.after(1000, self.tick)
        second = TimeValue.add_second()
        if second == 60:
            minute = TimeValue.add_minute()
            second = TimeValue.zeroing_second()
        elif minute == 60:
            hour = TimeValue.add_hour()
            minute = TimeValue.zeroing_minute()
        elif hour == 24:
            hour = TimeValue.zeroing_hour()
        self.timer['text'] = f"{hour:02}:{minute:02}:{second:02}"

    def example_text_audio(self):
        """
        Аудио предложения с пройденным словом
        """
        self.master.engine.say(self.example_text['text'])
        self.master.engine.runAndWait()

    def answer_text_audio(self, event=None):
        """
        Аудио с пройденным словом
        """
        self.master.engine.say(self.master.answer)
        self.master.engine.runAndWait()

    def example_question_audio(self):
        """
        Аудио вопросительного предложения с пройденным словом
        """
        self.master.engine.say(self.example_question['text'])
        self.master.engine.runAndWait()

    def remove_example_frame(self):
        """
        Скрываем блок примеров пройденного слова
        """
        self.answer_text.grid_remove()
        self.answer_text_button.grid_remove()
        self.example_text.grid_remove()
        self.example_text_button.grid_remove()
        self.example_question.grid_remove()
        self.example_question_button.grid_remove()

    def add_example_frame(self, key_result: RowDb, answer: str):
        """
        Показываем блок примеров пройденного слова (при наличие примеров)
        """
        self.entry.grid_remove()
        self.entry.unbind("<Return>")

        self.example_text['text'] = key_result.example_text
        self.answer_text['text'] = answer

        self.answer_text_button.grid(column=0, row=0, padx=10)
        self.answer_text.grid(column=1, row=0, padx=10, pady=10)
        self.example_question['text'] = key_result.example_question

        if key_result.example_text and key_result.example_question:
            self.example_text.grid(column=1, row=0, padx=10, pady=10)
            self.example_text_button.grid(column=0, row=0, padx=10, pady=10)
            self.example_question.grid(column=1, row=1, padx=10, pady=10)
            self.example_question_button.grid(column=0, row=1, padx=10, pady=10)

        elif not key_result.example_text and key_result.example_question:
            self.example_question.grid(column=1, row=0, padx=10, pady=10)
            self.example_question_button.grid(column=0, row=0, padx=10, pady=10)

        elif key_result.example_text and not key_result.example_question:
            self.example_text.grid(column=1, row=0, padx=10, pady=10)
            self.example_text_button.grid(column=0, row=0, padx=10, pady=10)

    def next_task(self, event=None):
        self.remove_example_frame()
        self.check_button.config(command=self.change, text='Проверить')
        self.entry.grid(column=1, row=1, padx=10, pady=10)
        self.entry.bind("<Return>", self.change)
        self.master.unbind("<Return>")
        self.master.unbind("<space>")

        # Если пользователь не совершил ошибку, слово считается пройденным
        if not self.master.mistake:
            del self.master.words_dict[self.master.key]
        self.master.mistake = False

        if not self.master.words_dict:
            self.word['text'] = ''
            ROOT.after(5000, ROOT.quit())
        else:
            self.new_text_message()
            self.entry.delete(0, tkinter.END)
        self.entry.config(fg='black')

    def change(self, event=None):
        """
        Проверка введенного пользователем значения перевода
        """
        self.master.key = self.word['text']
        key_result = self.master.words_dict.get(self.master.key.lower())
        translate = key_result.translate.lower()
        answer = self.entry.get().lower().strip()
        self.master.answer = answer

        if answer == translate:
            self.add_example_frame(key_result, answer)
            self.check_button.config(command=self.next_task, text='Далее')
            self.master.bind("<Return>", self.next_task)
            self.master.bind("<space>", self.answer_text_audio)

            self.info_label['text'] = 'I knew you could do it!'
            self.info_label.config(fg='white')

        else:
            print(f'\n"{answer}" (answer) -> "{translate}" (translate)')
            self.master.mistake = True
            self.entry.config(fg='#CC3366')
            self.info_label['text'] = 'Turn on your brain!'
            self.info_label.config(fg='#993333')

    def new_text_message(self):
        self.word['text'] = self.master.new_word()


class TenWordsPage(tkinter.Frame):
    """
    Страница для вывода последних 10 слов
    """

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.configure(background=master.background_color)

        self.last_ten_words_frame = tkinter.LabelFrame(self, background=master.background_color)

        last_ten_words = self.get_last_ten_words()
        self.ten_words = tkinter.Label(self.last_ten_words_frame)
        self.ten_words.config(fg='white',
                              font="Arial 21",
                              background=master.background_color,
                              text=last_ten_words)

        tkinter.Label(self, background=master.background_color).grid(column=0, row=0, padx=10, pady=10)
        self.last_ten_words_frame.grid(column=0, row=1, padx=10, pady=10, ipadx=40, ipady=10)
        self.ten_words.pack()

    def get_last_ten_words(self) -> list:
        """
        Получение списка последних 10 добавленных слов
        """
        last_ten_words = ''

        rows_words = self.master.db_cur.execute("""
            SELECT 
                key,
                translate
            FROM Words
            ORDER BY id_ DESC 
            LIMIT 10
        """)
        for row in rows_words:
            last_ten_words += f'{row[0]} -> {row[1]}\n'
        return last_ten_words[:-1]


class AddNewWord(tkinter.Frame):
    """
    Страница добавления новых слов для изучения
    """

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.configure(background=master.background_color)

        self.add_frame = tkinter.Frame(self)
        self.label_word = self.new_label(text='Введите слово или фразу')
        self.label_translate = self.new_label(text='Введите русский перевод')
        self.label_example_text = self.new_label(text='Введите пример утвердительного предложения')
        self.label_example_question = self.new_label(text='Введите пример вопросительного предложения')

        self.entry_word = tkinter.Entry(self.add_frame, width=25, font="Arial 12", fg='black')
        self.entry_translate = tkinter.Entry(self.add_frame, width=25, font="Arial 12", fg='black')
        self.entry_example_text = tkinter.Entry(self.add_frame, width=25, font="Arial 12", fg='black')
        self.entry_example_question = tkinter.Entry(self.add_frame, width=25, font="Arial 12", fg='black')

        self.entry_word.focus()

        self.check_button = tkinter.Button(self.add_frame, text="Добавить", font="Arial 12", width=15)
        self.check_button.config(command=self.add_new_word)

        self.label_word.grid(row=0, column=0, padx=10, sticky=tkinter.S)
        self.entry_word.grid(row=1, column=0, padx=10, pady=10)

        self.label_translate.grid(row=2, column=0, padx=10, sticky=tkinter.S)
        self.entry_translate.grid(row=3, column=0, padx=10, pady=10)

        self.label_example_text.grid(row=4, column=0, padx=10, sticky=tkinter.S)
        self.entry_example_text.grid(row=5, column=0, padx=10, pady=10)

        self.label_example_question.grid(row=6, column=0, padx=10, sticky=tkinter.S)
        self.entry_example_question.grid(row=7, column=0, padx=10, pady=10)

        self.check_button.grid(row=3, column=2, padx=10, pady=10)

        self.add_frame.grid(row=0, column=0, padx=10, pady=10)

    def new_label(self, text: str):
        label_ = tkinter.Label(self.add_frame)
        label_.config(fg='black', font="Arial 10", text=text)
        return label_

    def add_new_word(self):
        """
        Добавление нового слова в базу
        """
        word = self.entry_word.get().strip()
        translate = self.entry_translate.get().lower().strip()
        example_text = self.entry_example_text.get().lower().strip()
        example_question = self.entry_example_question.get().lower().strip()
        params = [word, translate, example_text, example_question, word]
        prev_id_ = self.master.db_cur.lastrowid
        self.master.db_cur.execute("""
            INSERT INTO Words(
                key,
                translate,
                example_text,
                example_question
                ) 
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM Words WHERE key = ?)
            """, params)
        new_id_ = self.master.db_cur.lastrowid
        self.master.db_con.commit()
        if prev_id_ != new_id_:
            self.master.words_dict[word] = RowDb(new_id_, word, translate, example_text, example_question)


class IrregularVerbsPage(tkinter.Frame):
    """
    Страница для ввода неправильных глаголов
    """

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.configure(background=master.background_color)

        # Виджет Frame (рамка) предназначен для организации виджетов внутри окна.
        self.info_label = tkinter.Label(self)
        self.info_label.config(fg='white',
                               font="Arial 16",
                               background=master.background_color,
                               text='You need to study more!')

        self.timer = tkinter.Label(self,
                                   text="%02i:%02i:%02i" % (TimeValue.get_time_values()),
                                   font=("Consolas", 14),
                                   fg='white',
                                   background=master.background_color)
        self.timer.after_idle(self.tick)

        # Блок информационный (self)
        tkinter.Label(self, background=master.background_color).grid(column=0, row=0, padx=10, pady=10)
        self.info_label.grid(column=0, row=1, padx=10, pady=10)
        tkinter.Label(self, background=master.background_color).grid(column=0, row=2, padx=10, pady=10)
        self.timer.grid(column=0, row=3, padx=10, pady=10)
        tkinter.Label(self, background=master.background_color).grid(column=0, row=4, padx=10, pady=10)

        # Блок для ввода неправильных глаголов (top_frame)
        top_frame = tkinter.Frame(self)
        top_frame.grid(column=0, row=5, padx=10, pady=10)

        self.irregular_verb = tkinter.Label(top_frame)
        self.irregular_verb.config(fg='black', font="Arial 14", width=30)
        self.irregular_verb['text'] = master.random_irregular_verb
        self.irregular_verb.grid(column=0, row=1, padx=10, pady=10)

        self.example_text = tkinter.Label(self)
        self.example_text.config(font="Purisa 18",
                                 background=master.background_color,
                                 fg='white')
        self.example_text.grid(column=0, row=6, padx=10, pady=10)

        self.example_question = tkinter.Label(self)
        self.example_question.config(font="Purisa 18",
                                     background=master.background_color,
                                     fg='white')
        self.example_question.grid(column=0, row=7, padx=10, pady=10)

        # Entry - это виджет, позволяющий пользователю ввести одну строку текста.
        self.entry_form_1 = tkinter.Entry(top_frame, width=25, font="Arial 12")
        self.entry_form_2 = tkinter.Entry(top_frame, width=25, font="Arial 12")
        self.entry_form_3 = tkinter.Entry(top_frame, width=25, font="Arial 12")

        # Метод bind привязывает событие к какому-либо действию
        # (нажатие кнопки мыши, нажатие клавиши на клавиатуре)
        # при нажатие кнопки "Enter" в любом поле ввода, будет запущена проверка введенных значений
        self.entry_form_1.bind("<Return>", self.change)
        self.entry_form_2.bind("<Return>", self.change)
        self.entry_form_3.bind("<Return>", self.change)

        self.entry_form_1.focus()

        self.master.put_placeholder(self.entry_form_2, 'second form')
        self.master.put_placeholder(self.entry_form_3, 'third form')

        # если курсор не установлен в поле ввода (<FocusOut>), то появляется плейсхолдер
        self.entry_form_1.bind("<FocusIn>",
                               lambda event: self.master.focus_in(event=event,
                                                                  entry_=self.entry_form_1,
                                                                  color='black'))
        self.entry_form_1.bind("<FocusOut>",
                               lambda event: self.master.focus_out(event=event,
                                                                   entry_=self.entry_form_1,
                                                                   text='first form'))

        self.entry_form_2.bind("<FocusIn>",
                               lambda event: self.master.focus_in(event=event,
                                                                  entry_=self.entry_form_2,
                                                                  color='black'))
        self.entry_form_2.bind("<FocusOut>",
                               lambda event: self.master.focus_out(event=event,
                                                                   entry_=self.entry_form_2,
                                                                   text='second form'))

        self.entry_form_3.bind("<FocusIn>",
                               lambda event: self.master.focus_in(event=event,
                                                                  entry_=self.entry_form_3,
                                                                  color='black'))
        self.entry_form_3.bind("<FocusOut>",
                               lambda event: self.master.focus_out(event=event,
                                                                   entry_=self.entry_form_3,
                                                                   text='third form'))

        self.entry_form_1.grid(column=1, row=0, padx=10, pady=10)
        self.entry_form_2.grid(column=1, row=1, padx=10, pady=10)
        self.entry_form_3.grid(column=1, row=2, padx=10, pady=10)

        self.check_button = tkinter.Button(top_frame, text="Проверить", font="Arial 12", width=15)
        self.check_button.config(command=self.change)
        self.check_button.grid(column=3, row=1, padx=10, pady=10)

    def change(self, event=None):
        """
        Проверка введенного пользователем значения перевода
        """

        self.master.key = self.irregular_verb['text'].lower()
        key_result = self.master.irregular_verbs_dict.get(self.master.key)
        translate_form_1 = key_result.translate.lower()
        translate_form_2 = key_result.form_2.lower()
        translate_form_3 = key_result.form_3.lower()
        answer_form_1 = self.entry_form_1.get().lower().strip()
        answer_form_2 = self.entry_form_2.get().lower().strip()
        answer_form_3 = self.entry_form_3.get().lower().strip()

        if answer_form_1 == translate_form_1 \
                and answer_form_2 == translate_form_2 \
                and answer_form_3 == translate_form_3:
            self.example_text['text'] = key_result.example_text

            # если примера текста нет, то в верхний блок примеров встанет вопрос
            if not self.example_text['text']:
                self.example_text['text'] = key_result.example_question
            else:
                self.example_question['text'] = key_result.example_question

            self.info_label['text'] = 'I knew you could do it!'
            self.info_label.config(fg='white')
            self.entry_form_1.config(fg='black')
            self.entry_form_2.config(fg='black')
            self.entry_form_3.config(fg='black')

            # Если пользователь не совершил ошибку, слово считается пройденным
            if not self.master.mistake:
                del self.master.irregular_verbs_dict[self.master.key]
            self.master.mistake = False

            if not self.master.irregular_verbs_dict:
                self.irregular_verb['text'] = ''
                ROOT.after(5000, ROOT.quit())

            self.new_text_message()
            self.entry_form_1.delete(0, tkinter.END)
            self.entry_form_2.delete(0, tkinter.END)
            self.entry_form_3.delete(0, tkinter.END)
            self.entry_form_1.focus()
        else:
            print(f'{answer_form_1} -> {translate_form_1}\n'
                  f'{answer_form_2} -> {translate_form_2}\n'
                  f'{answer_form_3} -> {translate_form_3}\n')
            self.master.mistake = True
            self.entry_form_1.config(fg='#CC3366')
            self.entry_form_2.config(fg='#CC3366')
            self.entry_form_3.config(fg='#CC3366')
            self.info_label['text'] = 'Turn on your brain!'
            self.info_label.config(fg='#993333')

    def new_text_message(self):
        """
        Выбор Нового неправильного глагола
        """
        self.irregular_verb['text'] = self.master.new_verb()

    def tick(self):
        """
        Реализация подсчета времени нахождения в программе
        """
        _, minute, hour = TimeValue.get_time_values()
        # Через каждую секунду происходит рекурсивый вызов функции
        self.timer.after(1000, self.tick)
        second = TimeValue.add_second()
        if second == 60:
            minute = TimeValue.add_minute()
            second = TimeValue.zeroing_second()
        elif minute == 60:
            hour = TimeValue.add_hour()
            minute = TimeValue.zeroing_minute()
        elif hour == 24:
            hour = TimeValue.zeroing_hour()
        self.timer['text'] = f"{hour:02}:{minute:02}:{second:02}"


if __name__ == '__main__':
    ROOT = SampleApp()
    ROOT.mainloop()
