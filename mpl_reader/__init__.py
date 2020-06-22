from .__main__ import main as _reader_funcfunc

from .mpl_fmt import import_dic
from .mpl_fmt import size2eind_func, size2sind_func
mpl_reader = _reader_funcfunc(import_dic, size2eind_func, size2sind_func)

from .smmpl_fmt import import_dic
from .smmpl_fmt import size2eind_func, size2sind_func
smmpl_reader = _reader_funcfunc(import_dic, size2eind_func, size2sind_func)
