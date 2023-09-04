import sys
import re
import tkinter as tk
from tkinter import scrolledtext

WORD = set('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщыэюя')
NUM = set('0123456789')
OPS = "\+|\-|\*|/|\(|\)|\[|\|\^]"
BR_START = ["("]
BR_END = [")"]

LABEL_REQUIREMENT = False  # Если поставить False, то метка перед выражением будет не обязательна


def start_check(text):
    text = text.strip()

    if not text.startswith('Начало') or not text.endswith('Конец'):
        return 'Ошибка вводных слов Начало/Конец. Правильно: Начало <текст> Конец', {}

    text = text.replace('Начало', '', 1).replace('Конец', '', 1).strip()

    return text, {}


def bracks_check(input):
    if not BR_START or not BR_END:
        return True

    stack = []
    for i in input:
        if i in BR_START:
            stack.append(i)
        elif i in BR_END:
            pos = BR_END.index(i)
            if stack and (BR_START[pos] == stack[-1]):
                stack.pop()
            else:
                return False
    return len(stack) == 0


def var_check(word):
    if word and word[0] not in WORD:
        return False
    for char in word:
        if char not in WORD and char not in NUM:
            return False
    return True


def num_check(word):
    for char in word:
        if char not in NUM:
            return False
    return True


def expression_check(word):
    # Проверка сбалансированности скобок
    stack = []
    for i, char in enumerate(word):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if not stack:
                return "Ошибка скобочной последовательности. Найдены лишние закрывающие скобки.", word[max(0, i - 1):i + 1]
            stack.pop()

    if stack:
        idx = stack[0]
        return "Ошибка скобочной последовательности. Найдены лишние открывающие скобки.", word[idx:min(len(word), idx + 2)]

    # Проверка на подряд идущие арифметические знаки с исключением **
    consecutive_ops = []
    prev_char = ''
    for char in word:
        if char in '+-*/^':
            if prev_char in '+-*/^' and not (prev_char == '*' and char == '*'):
                consecutive_ops.append(prev_char + char)
        prev_char = char

    if consecutive_ops:
        return (
            "Ошибка: подряд идут два или более знака операции без чисел между ними (исключение: **).",
            consecutive_ops[-1]
        )

    # Проверка, что после знака операции не стоит закрывающая скобка
    op_before_closing_bracket = re.search(r'[\+\-\*/\^]\s*\)', word)
    if op_before_closing_bracket:
        return "Ошибка: после знака операции не может стоять закрывающая скобка.", op_before_closing_bracket.group()

    # Проверка, что выражение не заканчивается знаком операции
    end_with_op = [m for m in re.finditer(r'[\+\-\*/\^]\s*$', word)]
    if end_with_op:
        last_match = end_with_op[-1]
        return "Ошибка: выражение не должно заканчиваться знаком операции.", word[max(0, last_match.start() - 1):]

    expr_list = re.split(r'[\+\-\*/\^]', word)
    for val in expr_list:
        val = val.strip()
        if not var_check(val) and not num_check(val) and not val.startswith('(') and not val.endswith(')'):
            return f'Ошибка правой части в {val}. Правильно: переменные и числа, используя только русский алфавит и десятичную арифметику.', val
    return None, None


def calculate_expression(expression, variables):
    try:
        for var_name, var_value in variables.items():
            expression = expression.replace(var_name, str(var_value))
        return eval(expression)
    except:
        return "Ошибка вычисления"


def main_check(raw_text):
    text, variables = start_check(raw_text)
    if isinstance(text, str) and 'Ошибка' in text:
        return text, {}, raw_text[:6]

    if not '\n' in text:
        return 'Ошибка - Отсутствует разделитель Множеств и Операторов. Правильно: используйте перевод строки для разделения.', {}, raw_text[
                                                                                                                                    -6:]

    set_list = text.split('\n')

    for elem in set_list:
        elem = elem.strip()
        if not elem:
            continue

        if elem.startswith('Анализ') or elem.startswith('анализ'):
            elem = elem.replace('Анализ', '').strip()
            sub_elem_list = elem.split()
            for sub_elem in sub_elem_list:
                if not var_check(sub_elem):
                    return f"Ошибка элемента множества Анализ - {sub_elem}. Переменная = набор букв и цифр с первой буквой, используя только русский алфавит и десятичную арифметику.", {}, sub_elem

        elif elem.startswith('Синтез') or elem.startswith('синтез'):
            if elem.startswith('Синтез'):
                elem = elem.replace('Синтез', '').strip()
            elif elem.startswith('синтез'):
                elem = elem.replace('синтез', '').strip()
            sub_elem_list = elem.split()
            for sub_elem in sub_elem_list:
                if not num_check(sub_elem):
                    return f"Ошибка элемента множества Синтез - {sub_elem}. Правильно: только целые числа.", {}, sub_elem

        elif LABEL_REQUIREMENT and ':' in elem or not LABEL_REQUIREMENT:
            if ':' in elem:
                main_list = elem.split(':')

                if not main_list[0]:
                    return f'Ошибка - Отсутствует метка - {elem}. Правильно: <метка>: <выражение>', {}, elem

                if not num_check(main_list[0]):
                    return f"Ошибка в Метке - {main_list[0]}. Правильно: метка должна быть целым числом.", {}, \
                           main_list[0]

                if len(main_list) != 2:
                    return f"Ошибка - Отсутствует либо лишнее выражение в {main_list}. Правильно: <метка>: <выражение>", {}, main_list

                equation = main_list[1]
            else:
                equation = elem.strip()
            #
            # if not '=' in equation:
            #     error, error_fragment = "Ошибка: отсутствует знак равенства.", equation
            #     return error, {}, error_fragment

            eq_list = equation.strip().split('=')

            if len(eq_list) < 2:
                # Разбиваем строку по пробелам
                parts = eq_list[0].split()
                if parts:
                    # Возвращаем только первые три символа имени переменной как фрагмент с ошибкой
                    error_fragment = parts[0][:3]
                else:
                    # Возвращаем всю строку, если в ней нет пробелов
                    error_fragment = eq_list[0]
                return "Ошибка: отсутствует знак равенства.", {}, error_fragment

            if len(eq_list) != 2:
                return f"Ошибка - Отсутствует либо лишняя правая часть в {equation}. Правильно: <переменная> = <выражение>", {}, equation

            if not var_check(eq_list[0]):
                return f"Ошибка в левой части - {eq_list[0]}. Метка должна быть со знаком ':', а переменная = набор букв и цифр с первой буквой, используя только русский алфавит и десятичную арифметику.", {}, \
                       eq_list[0]

            error, error_fragment = expression_check(eq_list[1])

            if error:
                return error, {}, error_fragment or eq_list[1]

            var_name = eq_list[0].strip()
            expr = eq_list[1].strip()

            if var_name in variables:
                var_value = variables[var_name]
            else:
                var_value = calculate_expression(expr, variables)

            if isinstance(var_value, str) and 'Ошибка' in var_value:
                return var_value, {}

            variables[var_name] = var_value
        else:
            return f"Ошибка, строка ни Множество ни Оператор - {elem}. Правильно: Анализ <элементы> или Синтез <элементы> или <метка>: <выражение>", {}, elem

    return 'Синтаксис верный! Все выражения были вычислены!', variables, ''


def on_check_button_click():
    text = text_area.get("1.0", tk.END)
    result, variables, error = main_check(text)
    result_label.config(text=result)
    variables_label.config(text=str(variables))

    if error:
        text_area.delete(1.0, tk.END)
        error_index = text.find(error)

        text_area.insert(tk.END, text[:error_index], 'start')

        text_area.insert(tk.END, error, 'error')
        text_area.tag_config('error', foreground='red')

        text_area.insert(tk.END, text[error_index + len(error):], 'end')
    # мои попытки
    else:
        text_area.insert(tk.END, error, 'error')
        text_area.tag_config('error', foreground='black')


def paste_from_clipboard():
    clipboard_text = root.clipboard_get()
    text_area.insert(tk.INSERT, clipboard_text)


# Создание графического интерфейса
root = tk.Tk()
root.title("Проверка синтаксиса")
root.geometry("700x700")  # Увеличил размер окна чтобы уместить картинку

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=15)
text_area.pack(padx=20, pady=20)
text_area.insert("1.0", """Язык = "Начало" Множество...Множество Оператор...Оператор "Конец"
Множество = "Анализ" Переменная...Переменная ! "Синтез" Целое...Целое
Оператор = </Метка ":"/> Переменная "=" Правая_часть
Правая_часть = </ "-" /> Блок ["+" ! "-"]... Блок
Блок = Часть ["*" ! "/"]... Часть
Часть = Кусок ["**"]... Кусок
Кусок = Переменная ! Целое ! "(" Правая_часть ")"
Переменная = Буква {"Буква" ! Цифра}
Метка = Целое
Буква = "А" ! "Б" ! ... ! "Я"
Цифра = "0" ! "1" ! ... ! "9"
Целое = Цифра ... Цифра""")

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10)
text_area.pack(padx=20, pady=20)
text_area.insert("1.0", """Начало
    Анализ ф1 ф2 ф3
    Синтез 2343 456456
    1: ф1= 321+23-2**(-4/30)
    2: ф2= ф1+500-3*2*3*(6/30)
    3: ф3= ф2+230-2**(3/10)
Конец""")

check_button = tk.Button(root, text="Проверить", command=on_check_button_click)
check_button.pack()

result_label = tk.Label(root, text="", wraplength=400)
result_label.pack(pady=20)

variables_label = tk.Label(root, text="", wraplength=400)
variables_label.pack(pady=20)

root.mainloop()
