import os
from typing import Iterable


def getPDFFilePathGenerator(dir_path: str) -> Iterable[str]:
    for file in os.listdir(dir_path):
        if file.endswith(".pdf"):
            yield os.path.join(dir_path, file)
