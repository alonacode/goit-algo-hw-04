import argparse
from pathlib import Path
import shutil
import sys


def parse_args():
    p = argparse.ArgumentParser(
        description="Рекурсивно копіює файли з джерела в теку призначення, "
                    "сортуючи їх у підпапки за розширенням."
    )
    p.add_argument("src", type=Path, help="Шлях до вихідної директорії")
    p.add_argument("dest", nargs="?", type=Path, default=Path("dist"),
                   help="Шлях до директорії призначення (за замовчуванням: ./dist)")
    return p.parse_args()


def ext_bucket(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return ext if ext else "no_ext"


def copy_file(src_file: Path, dest_root: Path):
    try:
        bucket = dest_root / ext_bucket(src_file)
        bucket.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, bucket / src_file.name)
    except PermissionError as e:
        print(f"Попередження: немає доступу до файлу {src_file}: {e}", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"Попередження: файл не знайдено {src_file}: {e}", file=sys.stderr)
    except OSError as e:
        print(f"Попередження: помилка копіювання {src_file}: {e}", file=sys.stderr)


def walk_recursive(current_dir: Path, dest_root: Path, dest_root_resolved: Path):
    # читаємо вміст директорії з обробкою помилок
    try:
        entries = list(current_dir.iterdir())
    except PermissionError as e:
        print(f"Попередження: немає доступу до директорії {current_dir}: {e}", file=sys.stderr)
        return
    except FileNotFoundError as e:
        print(f"Попередження: директорію не знайдено {current_dir}: {e}", file=sys.stderr)
        return
    except OSError as e:
        print(f"Попередження: помилка читання {current_dir}: {e}", file=sys.stderr)
        return

    for entry in entries:
        # якщо тека призначення всередині джерела — не заходимо в неї
        try:
            if entry.is_dir() and entry.resolve() == dest_root_resolved:
                continue
        except OSError:
            pass

        if entry.is_dir():
            # уникаємо циклів по симлінкам на директорії
            if entry.is_symlink():
                continue
            walk_recursive(entry, dest_root, dest_root_resolved)
        elif entry.is_file():
            copy_file(entry, dest_root)
        # інші типи (FIFO, сокети) ігноруємо


def main():
    args = parse_args()
    src, dest = args.src, args.dest

    if not src.exists() or not src.is_dir():
        print(f"Помилка: вихідна директорія недоступна або не існує: {src}", file=sys.stderr)
        return 2

    try:
        dest.mkdir(parents=True, exist_ok=True)
        dest_resolved = dest.resolve()
    except OSError as e:
        print(f"Помилка: не вдалося підготувати директорію призначення {dest}: {e}", file=sys.stderr)
        return 2

    walk_recursive(src, dest, dest_resolved)
    print("Готово: файли скопійовано і відсортовано за розширеннями у директорії призначення.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
