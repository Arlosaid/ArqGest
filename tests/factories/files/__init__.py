"""
Factories para modelos de Files

Importación facilitada:
    from tests.factories.files import ProjectFileFactory
"""

from .file_factories import (
    ProjectFileFactory,
    PDFFileFactory,
    ImageFileFactory,
    JPGFileFactory,
    PNGFileFactory,
    WordFileFactory,
    ExcelFileFactory,
    DWGFileFactory,
    RVTFileFactory,
    ZIPFileFactory,
    LargeFileFactory,
    MaliciousFileFactory,
    PathTraversalFileFactory,
    ExecutableFileFactory,
    NoExtensionFileFactory,
)

__all__ = [
    'ProjectFileFactory',
    'PDFFileFactory',
    'ImageFileFactory',
    'JPGFileFactory',
    'PNGFileFactory',
    'WordFileFactory',
    'ExcelFileFactory',
    'DWGFileFactory',
    'RVTFileFactory',
    'ZIPFileFactory',
    'LargeFileFactory',
    'MaliciousFileFactory',
    'PathTraversalFileFactory',
    'ExecutableFileFactory',
    'NoExtensionFileFactory',
]

