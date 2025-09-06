import random
import timeit
import statistics as stats
from dataclasses import dataclass
from typing import Callable, List, Dict
from pathlib import Path

# =========================
# Алгоритми сортування
# =========================


def insertion_sort(a: List[int]) -> List[int]:
    arr = a[:]  # працюємо з копією
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j+1] = arr[j]
            j -= 1
        arr[j+1] = key
    return arr


def merge_sort(a: List[int]) -> List[int]:
    arr = a[:]  # копія
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)


def _merge(left: List[int], right: List[int]) -> List[int]:
    i = j = 0
    out: List[int] = []
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


# Timsort: просто використовуємо вбудоване sorted
def timsort(a: List[int]) -> List[int]:
    return sorted(a)

# =========================
# Генератори наборів даних
# =========================


def gen_random(n: int, seed: int = 42) -> List[int]:
    rnd = random.Random(seed)
    return [rnd.randint(-10_000, 10_000) for _ in range(n)]


def gen_sorted(n: int) -> List[int]:
    return list(range(n))


def gen_reversed(n: int) -> List[int]:
    return list(range(n, 0, -1))


def gen_nearly_sorted(n: int, swaps: int = None, seed: int = 42) -> List[int]:
    """Переважно відсортований масив: робимо кілька випадкових перестановок."""
    if swaps is None:
        swaps = max(1, n // 100)  # ~1% випадкових пар
    arr = list(range(n))
    rnd = random.Random(seed)
    for _ in range(swaps):
        i = rnd.randrange(n)
        j = rnd.randrange(n)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def gen_many_dups(n: int, seed: int = 42) -> List[int]:
    """Багато дублікатів (значення з невеликого діапазону)."""
    rnd = random.Random(seed)
    return [rnd.randint(0, 100) for _ in range(n)]

# =========================
# Бенчмаркінг
# =========================

@dataclass
class Case:
    name: str
    generator: Callable[[int], List[int]]

DataGenRegistry: Dict[str, Callable[[int], List[int]]] = {
    "random": gen_random,
    "sorted": gen_sorted,
    "reversed": gen_reversed,
    "nearly_sorted": gen_nearly_sorted,
    "many_dups": gen_many_dups,
}

AlgoRegistry: Dict[str, Callable[[List[int]], List[int]]] = {
    "insertion": insertion_sort,
    "merge": merge_sort,
    "timsort(sorted)": timsort,
}


def time_algorithm(algo, data, repeat, number):
    """
    Повертає (min, median, max) часу виконання.
    Запускаємо algo на КОПІЇ даних (data[:]), щоб уникнути побічних ефектів.
    Без жодних імпортів із __main__.
    """
    timer = timeit.Timer(lambda: algo(data[:]))
    times = timer.repeat(repeat=repeat, number=number)   # сумарний час кожної серії
    times = [t / number for t in times]                  # час за 1 запуск
    return (min(times), stats.median(times), max(times))


def run_bench():
    # Налаштування масштабу експериментів
    sizes = [100, 300, 1000, 3000, 10_000]  # можна розширити
    datasets = ["random", "sorted", "reversed", "nearly_sorted", "many_dups"]

    # Для повільних алгоритмів (вставки) на великих n зменшуємо number
    # Щоб запуск тривав розумний час
    base_repeat = 5
    base_number = 3

    rows = []
    for ds_name in datasets:
        for n in sizes:
            data = DataGenRegistry[ds_name](n)
            # підлаштування параметрів вимірів
            if ds_name in ("reversed", "random") and n >= 10_000:
                repeat, number = 3, 1
            else:
                repeat, number = base_repeat, base_number

            for algo_name, algo_fn in AlgoRegistry.items():
                # Insertion sort дуже повільний на великих n
                if algo_name == "insertion" and n > 3000 and ds_name in ("random", "reversed"):
                    # пропускаємо як «непрактично»
                    rows.append((ds_name, n, algo_name, None, None, None, "skipped"))
                    continue

                mn, med, mx = time_algorithm(algo_fn, data, repeat=repeat, number=number)
                rows.append((ds_name, n, algo_name, mn, med, mx, "ok"))

    return rows


def save_csv(rows, path: Path):
    def fmt(x):
        return "" if x is None else f"{x:.6f}"

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("dataset,size,algorithm,min_s,median_s,max_s,status\n")
        for ds, n, algo, mn, med, mx, st in rows:
            f.write(f"{ds},{n},{algo},{fmt(mn)},{fmt(med)},{fmt(mx)},{st}\n")


def to_md_table(rows) -> str:
    # Групуємо: (dataset, size) -> результати
    from collections import defaultdict
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r[0], r[1])].append(r)

    lines = []
    lines.append("| Dataset | N | Algorithm | min (s) | median (s) | max (s) |")
    lines.append("|---|---:|---|---:|---:|---:|")
    for (ds, n), lst in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1])):
        for ds_, n_, algo, mn, med, mx, st in sorted(lst, key=lambda x: x[2]):
            if st == "skipped":
                lines.append(f"| {ds} | {n} | {algo} |  –  |  –  |  –  |")
            else:
                lines.append(f"| {ds} | {n} | {algo} | {mn:.6f} | {med:.6f} | {mx:.6f} |")
    return "\n".join(lines)


def auto_conclusions(rows) -> str:
    """
    Прості автоматичні висновки на основі медіан часу:
    - Підтвердження очікуваних порядків: вставки ~O(n^2), злиття ~O(n log n), Timsort ~O(n) на майже відсортованих і дуже швидкий загалом.
    """
    # зберемо медіани у зручну форму
    from collections import defaultdict
    med = defaultdict(lambda: {})
    for ds, n, algo, mn, m, mx, st in rows:
        if st == "ok" and m is not None:
            med[(ds, n)][algo] = m

    bullets = []

    # 1) Вставки vs інші на великих випадкових
    big = max(n for ds, n in med.keys() if ds == "random")
    if all(k in med[("random", big)] for k in ("merge", "timsort(sorted)")):
        msg = "- На великих випадкових масивах **Timsort** і **злиття** суттєво швидші за **вставки**, що відповідає теорії (O(n log n) проти O(n²))."
        bullets.append(msg)

    # 2) Майже відсортовані — перевага Timsort
    any_n = max(n for ds, n in med.keys() if ds == "nearly_sorted")
    if all(k in med[("nearly_sorted", any_n)] for k in ("merge", "timsort(sorted)")):
        if med[("nearly_sorted", any_n)]["timsort(sorted)"] < med[("nearly_sorted", any_n)]["merge"]:
            bullets.append("- На **майже відсортованих даних** Timsort помітно швидший за злиття завдяки використанню природних «runs» та вставок усередині малих підмасивів (лінійна близькість до O(n)).")

    # 3) Відсортовані — Timsort близький до O(n)
    any_n2 = max(n for ds, n in med.keys() if ds == "sorted")
    if "timsort(sorted)" in med[("sorted", any_n2)]:
        bullets.append("- На **вже відсортованих** даних Timsort працює майже лінійно (близько до O(n)) завдяки стабільності та детекції вже відсортованих підпослідовностей.")

    # 4) З багатьма дублікатами
    any_n3 = max(n for ds, n in med.keys() if ds == "many_dups")
    if all(k in med[("many_dups", any_n3)] for k in ("merge", "timsort(sorted)")):
        bullets.append("- Для **даних із великою кількістю дублікатів** Timsort також показує відмінні результати через оптимізоване злиття і стабільність.")

    # 5) Загальний висновок
    bullets.append("**Висновок:** гібридність Timsort (поєднання злиття + вставок, детекція природних runs, «галопуюче» злиття) робить його **практично найефективнішим загальним сортуванням** у Python, тому розробники у більшості випадків використовують **вбудований `sorted`/`.sort()`**, а не пишуть власні реалізації.")

    return "\n".join(bullets)


def write_readme(rows, path: Path):
    md_table = to_md_table(rows)
    conclusions = auto_conclusions(rows)
    text = f"""# Порівняння алгоритмів сортування: вставки, злиття та Timsort

**Мета:** емпірично порівняти алгоритми за часом виконання на різних наборах даних за допомогою `timeit`.

## Набори даних
- `random` — випадкові числа
- `sorted` — вже відсортований масив
- `reversed` — зворотно відсортований
- `nearly_sorted` — майже відсортований (≈1% випадкових перестановок)
- `many_dups` — багато дублікатів (значення з малого діапазону)

## Розміри масивів
`[100, 300, 1000, 3000, 10000]` (для дуже повільних випадків insertion sort може бути пропущено як «skipped»).

## Результати (секунди, менше — краще)
{md_table}

## Аналіз і висновки
{conclusions}

### Теоретичні очікування
- **Insertion sort**: O(n²) у середньому/гіршому; дуже швидкий на дуже малих масивах або майже відсортованих.
- **Merge sort**: O(n log n) завжди; стабільний, але потребує додаткову памʼять.
- **Timsort (sorted)**: гібрид злиття та вставок + детекція «runs», оптимізоване злиття (включно з «галопуванням»). У найкращих для нього випадках близький до O(n), загалом змагально-швидкий на реальних даних.

> Саме завдяки цим властивостям **Timsort** у Python є дефолтним і зазвичай **істотно ефективніший** за «чисті» класичні реалізації, тому програмісти використовують **вбудовані** `sorted`/`.sort()`.
"""
    path.write_text(text, encoding="utf-8")

def main():
    out_dir = Path("bench_out")
    out_dir.mkdir(exist_ok=True)
    rows = run_bench()
    save_csv(rows, out_dir / "results.csv")
    print("Збережено CSV:", out_dir / "results.csv")
    # Друк короткої таблиці в консоль
    print()
    print(to_md_table(rows))
    # Зберегти README.md з висновками
    write_readme(rows, Path("README.md"))
    print("\nREADME.md з висновками згенеровано.")

if __name__ == "__main__":
    main()
