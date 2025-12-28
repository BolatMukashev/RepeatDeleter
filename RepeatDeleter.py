import imagehash
from pathlib import Path
from PIL import Image
from enum import Enum
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Button, Static, Input, ProgressBar, Log
from textual.binding import Binding


class ImagesTypes(Enum):
    JPG = '*.jpg'
    JPEG = '*.jpeg'
    PNG = '*.png'
    TIFF = '*.tiff'


class DeleteRepeatImages:
    """
    Удаляет повторяющиеся фотографии в директории.
    Фото сканируются по хэшу
    """

    def __init__(self, path: Path, progress_callback=None):
        self.path = path
        self.trash_path = Path(path, 'повторы')
        self.create_dir()
        self.hashes_list = []
        self.progress_callback = progress_callback

    def create_dir(self) -> None:
        """создать папку (корзину) для повторяющихся фото"""
        self.trash_path.mkdir(parents=True, exist_ok=True)

    def get_imgs_path(self):
        images = []
        types = [x.value for x in ImagesTypes]
        for type_ in types:
            imgs = self.path.glob(type_)
            images.extend(imgs)
        return images

    def get_hash(self, img: Path):
        photo_hash = imagehash.phash(Image.open(img))
        return str(photo_hash)

    def move_to_trash(self, img: Path):
        img.rename(Path(self.trash_path, img.name))

    def detecter(self):
        """main"""
        images = self.get_imgs_path()
        total = len(images)
        moved_count = 0
        
        for idx, image in enumerate(images):
            try:
                img_hash = self.get_hash(image)
                if img_hash not in self.hashes_list:
                    self.hashes_list.append(img_hash)
                else:
                    self.move_to_trash(image)
                    moved_count += 1
                
                if self.progress_callback:
                    self.progress_callback(idx + 1, total, image.name, moved_count)
            except Exception as e:
                if self.progress_callback:
                    self.progress_callback(idx + 1, total, f"Ошибка: {image.name} - {str(e)}", moved_count)
        
        return moved_count, total


class ImageDuplicateApp(App):
    """Приложение для удаления дубликатов изображений"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #input-container {
        height: auto;
        margin: 1 2;
        padding: 1;
        border: solid $primary;
    }
    
    #status {
        height: auto;
        margin: 1 2;
        padding: 1;
        background: $panel;
        color: $text;
    }
    
    #log-container {
        height: 1fr;
        margin: 1 2;
        padding: 1;
        border: solid $accent;
    }
    
    Input {
        margin: 1 0;
    }
    
    Button {
        margin: 1 0;
    }
    
    ProgressBar {
        margin: 1 0;
    }
    
    Log {
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Выход"),
        Binding("c", "clear_log", "Очистить лог"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="input-container"):
                yield Static("🖼️  Удаление дубликатов изображений", classes="title")
                yield Input(
                    placeholder="Введите путь к папке с изображениями...",
                    id="path-input"
                )
                yield Button("🔍 Начать поиск дубликатов", id="start-btn", variant="primary")
            
            with Vertical(id="status"):
                yield Static("Готов к работе", id="status-text")
                yield ProgressBar(total=100, show_eta=True, id="progress")
            
            with Vertical(id="log-container"):
                yield Static("📋 Журнал работы:", classes="log-title")
                yield Log(id="log")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Инициализация при запуске"""
        self.query_one("#progress").display = False
        self.title = "Image Duplicate Remover"
        self.sub_title = "Поиск и удаление повторяющихся фото"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Обработка нажатия кнопки"""
        if event.button.id == "start-btn":
            self.start_processing()
    
    def start_processing(self) -> None:
        """Начать обработку изображений"""
        path_input = self.query_one("#path-input", Input)
        path_str = path_input.value.strip()
        
        if not path_str:
            self.update_status("❌ Ошибка: Путь не указан", "error")
            self.log_message("Пожалуйста, введите путь к папке")
            return
        
        path = Path(path_str)
        
        if not path.exists() or not path.is_dir():
            self.update_status("❌ Ошибка: Папка не найдена", "error")
            self.log_message(f"Папка не существует: {path_str}")
            return
        
        # Отключить кнопку во время обработки
        button = self.query_one("#start-btn", Button)
        button.disabled = True
        
        # Показать прогресс-бар
        progress_bar = self.query_one("#progress", ProgressBar)
        progress_bar.display = True
        
        self.update_status("🔄 Обработка изображений...", "processing")
        self.log_message(f"Начинаем сканирование: {path}")
        
        try:
            processor = DeleteRepeatImages(path, progress_callback=self.progress_update)
            moved, total = processor.detecter()
            
            self.update_status(
                f"✅ Готово! Найдено дубликатов: {moved} из {total}",
                "success"
            )
            self.log_message(f"\n{'='*50}")
            self.log_message(f"Результаты:")
            self.log_message(f"  Всего изображений: {total}")
            self.log_message(f"  Дубликатов перемещено: {moved}")
            self.log_message(f"  Папка с дубликатами: {processor.trash_path}")
            self.log_message(f"{'='*50}\n")
            
        except Exception as e:
            self.update_status(f"❌ Ошибка: {str(e)}", "error")
            self.log_message(f"Произошла ошибка: {str(e)}")
        
        finally:
            # Включить кнопку обратно
            button.disabled = False
            progress_bar.display = False
    
    def progress_update(self, current: int, total: int, filename: str, moved: int) -> None:
        """Обновление прогресса"""
        progress_bar = self.query_one("#progress", ProgressBar)
        progress_bar.update(total=total, progress=current)
        
        status_text = f"🔄 Обработано: {current}/{total} | Дубликатов: {moved}"
        self.update_status(status_text, "processing")
        
        if "Ошибка" in filename:
            self.log_message(f"⚠️  {filename}")
        else:
            if current % 10 == 0:  # Логируем каждое 10-е изображение
                self.log_message(f"Проверено: {filename}")
    
    def update_status(self, message: str, status_type: str = "info") -> None:
        """Обновить статус"""
        status_widget = self.query_one("#status-text", Static)
        status_widget.update(message)
    
    def log_message(self, message: str) -> None:
        """Добавить сообщение в лог"""
        log_widget = self.query_one("#log", Log)
        log_widget.write_line(message)
    
    def action_clear_log(self) -> None:
        """Очистить лог"""
        log_widget = self.query_one("#log", Log)
        log_widget.clear()
        self.log_message("Лог очищен")


if __name__ == '__main__':
    app = ImageDuplicateApp()
    app.run()