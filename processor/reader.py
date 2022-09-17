from types import TracebackType
from typing import Optional, Type
import pdfplumber


class PDFFile:
    plumber_file: pdfplumber.PDF
    text_cache: dict[int, str]

    def __init__(self, pdf_path: str) -> None:
        self.plumber_file = pdfplumber.open(pdf_path)
        self.text_cache = dict()
        # Set -1, and max_page_index, to empty string
        self.text_cache[-1] = ""
        self.text_cache[len(self.plumber_file.pages)] = ""

    def getPageAndNearby(self, at_index: int) -> tuple[str, str, str]:
        self._cacheTextIfNeedAtIndex(at_index - 1)
        self._cacheTextIfNeedAtIndex(at_index)
        self._cacheTextIfNeedAtIndex(at_index + 1)

        return (self.text_cache[at_index - 1], self.text_cache[at_index], self.text_cache[at_index + 1])

    def _cacheTextIfNeedAtIndex(self, index: int) -> None:
        # -1, and max_page_index, will always be "", so it is "in keys"
        if index not in self.text_cache.keys():
            self.text_cache[index] = self.plumber_file.pages[index].extract_text()

    def __len__(self) -> int:
        return len(self.plumber_file.pages)

    def __enter__(self) -> "PDFFile":
        return self

    def __exit__(self,
                 t: Optional[Type[BaseException]],
                 value: Optional[BaseException],
                 traceback: Optional[TracebackType],):
        self.plumber_file.__exit__(t, value, traceback)


def getReadByPagesGenerator(pdf_file_path: str) -> str:
    with pdfplumber.open(pdf_file_path) as pdf_file:
        for page in pdf_file.pages:
            yield page.extract_text()
