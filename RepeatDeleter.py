import imagehash
from pathlib import Path
from PIL import Image
from enum import Enum


class ImagesTypes(Enum):
    JPG = '*.jpg'
    JPEG = '*.jpeg'
    PNG = '*.png'


class DeleteRepeatImages:
    """
    Удаляет повторяющиеся фотографии в директории.
    Фото сканируются по хэшу
    """

    def __init__(self, path: Path):
        self.path = path
        self.trash_path = Path(path, 'повторы')
        self.create_dir()
        self.hashes_list = []

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
        # photo_hash = imagehash.average_hash(Image.open(img)) - ошибается на некоторых фото
        photo_hash = imagehash.phash(Image.open(img))
        return str(photo_hash)

    def move_to_trash(self, img: Path):
        img.rename(Path(self.trash_path, img.name))

    def detecter(self):
        """main"""
        images = self.get_imgs_path()
        for image in images:
            img_hash = self.get_hash(image)
            if img_hash not in self.hashes_list:
                self.hashes_list.append(img_hash)
            else:
                self.move_to_trash(image)

    def test(self, img: Path):
        main_hash = self.get_hash(img)
        images = self.get_imgs_path()
        for image in images:
            img_hash = self.get_hash(image)
            if img_hash == main_hash:
                image.rename(Path('C:/Users/Астана11б/Pictures/Client/', image.name))

    def test_print_hashes(self):
        images = self.get_imgs_path()
        for image in images:
            img_hash = self.get_hash(image)
            print(img_hash)


if __name__ == '__main__':
    path1 = input('Скопируй адрес к папке и вставь сюда: ')
    path = Path(path1)
    # img_ = Path('C:/Users/Астана11б/Pictures/Client/262/повторы/WhatsApp Image 2022-11-21 at 16.02.39.jpeg')
    DeleteRepeatImages(path).detecter()
