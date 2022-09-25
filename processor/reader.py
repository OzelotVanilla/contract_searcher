import enum
from types import TracebackType
from typing import Optional, Type
import pdfplumber
import fitz


class ReaderType(enum.Enum):
    type_pdfplumber = 0
    type_pymupdf = 1


class PDFFile:
    pdf_file: pdfplumber.PDF | fitz.Document
    text_cache: dict[int, str]

    def __init__(self, pdf_path: str, reader_type: ReaderType = ReaderType.type_pdfplumber) -> None:
        match reader_type:
            case ReaderType.type_pdfplumber:
                self.pdf_file = pdfplumber.open(pdf_path)
            case ReaderType.type_pymupdf:
                self.pdf_file = fitz.Document(pdf_path)

        self.text_cache = dict()
        # Set -1, and max_page_index, to empty string
        self.text_cache[-1] = ""
        self.text_cache[len(self.pdf_file.pages)] = ""

    def getPageAndNearby(self, at_index: int) -> tuple[str, str, str]:
        self._cacheTextIfNeedAtIndex(at_index - 1)
        self._cacheTextIfNeedAtIndex(at_index)
        self._cacheTextIfNeedAtIndex(at_index + 1)

        return (self.text_cache[at_index - 1], self.text_cache[at_index], self.text_cache[at_index + 1])

    def _cacheTextIfNeedAtIndex(self, index: int) -> None:
        # -1, and max_page_index, will always be "", so it is "in keys"
        if index not in self.text_cache.keys():
            match type(self.pdf_file):
                case pdfplumber.PDF:
                    self.text_cache[index] = self.pdf_file.pages[index].extract_text()
                case fitz.Document:
                    text_blocks: list[tuple[int, int, int, int, str, int, int]] \
                        = self.pdf_file.load_page(index).get_text("block")
                    # Ensure order: left-right, up-down, customized for text in columns
                    text_blocks = sorted(text_blocks, key=lambda t: t[0])
                    texts_list = [block[4].replace("\n", " ") for block in text_blocks]
                    text = " ".join(texts_list)
                    self.text_cache[index] = text

    def __len__(self) -> int:
        match type(self.pdf_file):
            case pdfplumber.PDF:
                return len(self.pdf_file.pages)
            case fitz.Document:
                return len(self.pdf_file)

    def __enter__(self) -> "PDFFile":
        return self

    def __exit__(self,
                 t: Optional[Type[BaseException]],
                 value: Optional[BaseException],
                 traceback: Optional[TracebackType],):
        self.text_cache.clear()
        self.pdf_file.__exit__(t, value, traceback)


def getReadByPagesGenerator(pdf_file_path: str) -> str:
    with pdfplumber.open(pdf_file_path) as pdf_file:
        for page in pdf_file.pages:
            yield page.extract_text()
