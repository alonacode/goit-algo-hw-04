import argparse
import turtle
import sys
from math import sqrt


def koch_segment(t: turtle.Turtle, length: float, level: int) -> None:
    """Рекурсивно малює один відрізок кривої Коха."""
    if level == 0:
        t.forward(length)
    else:
        length /= 3.0
        koch_segment(t, length, level - 1)
        t.left(60)
        koch_segment(t, length, level - 1)
        t.right(120)
        koch_segment(t, length, level - 1)
        t.left(60)
        koch_segment(t, length, level - 1)


def koch_snowflake(t: turtle.Turtle, side: float, level: int) -> None:
    """Малює сніжинку Коха як три з'єднані криві Коха (трикутник)."""
    for _ in range(3):
        koch_segment(t, side, level)
        t.right(120)


def parse_args():
    p = argparse.ArgumentParser(
        description="Візуалізація фракталу «сніжинка Коха» з вказаним рівнем рекурсії."
    )
    p.add_argument(
        "-l", "--level",
        type=int, default=3,
        help="рівень рекурсії (ціле число ≥ 0), за замовчуванням 3"
    )
    p.add_argument(
        "--size",
        type=int, default=700,
        help="розмір вікна в пікселях (ширина=висота), за замовчуванням 700"
    )
    return p.parse_args()


def main():
    args = parse_args()
    level = args.level
    if level < 0:
        print("Помилка: рівень рекурсії має бути цілим числом ≥ 0.", file=sys.stderr)
        return 2

    # Параметри вікна
    size = max(300, args.size)  # мінімум 300
    margin = 40                 # відступ від країв
    side = size - 2 * margin    # довжина сторони базового трикутника

    # Налаштування turtle
    turtle.setup(width=size, height=size)
    screen = turtle.Screen()
    screen.title(f"Сніжинка Коха (level={level})")
    screen.tracer(False)  # пришвидшує отрисовку

    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.pensize(1)

    # Розташування так, щоб сніжинка була по центру
    # Висота рівностороннього трикутника:
    h = sqrt(3) / 2 * side
    start_x = -side / 2
    start_y = -h / 3

    t.penup()
    t.goto(start_x, start_y)
    t.setheading(0)  # дивимося вправо
    t.pendown()

    # Малюємо
    koch_snowflake(t, side, level)

    screen.tracer(True)
    # Залишаємо вікно відкритим до кліку
    turtle.done()
    return 0


if __name__ == "__main__":
    sys.exit(main())
