# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_tagmaker.ipynb.

# %% auto 0
__all__ = ['convert_layout', 'LayoutProc']

# %% ../nbs/02_tagmaker.ipynb 3
from nbdev.config import get_config
from nbdev.process import extract_directives
from nbdev.processors import Processor
from nbdev.export import nb_export
from nbdev.doclinks import nbglob
from nbdev.sync import write_nb

from fastcore.script import call_parse
from fastcore.xtras import Path

from string import Template

# %% ../nbs/02_tagmaker.ipynb 5
_LAYOUT_STR = Template("::: {$layout}\n$content\n")

# %% ../nbs/02_tagmaker.ipynb 6
def convert_layout(cell, layout):
    "Parses cell formatted with ::: {$something}, and potentially :::"
    content = cell.source
    cell.source = _LAYOUT_STR.substitute(
        layout=" ".join(layout),
        content=content
    )

# %% ../nbs/02_tagmaker.ipynb 9
class LayoutProc(Processor):
    """A proc that will automatically change #| layout format
    to ::: {format} ... :::
    """
    has_partial = False
    def cell(self, cell):
        if cell.cell_type == "markdown" and "layout" in cell.directives_:
            directives_ = cell.directives_["layout"]
            if self.has_partial and "end" in directives_:
                    cell.source += "\n:::"
                    directives_.remove("end")
                    self.has_partial = False
            else:
                if "start" in directives_:
                    self.has_partial = True
                    directives_.remove("start")
                    convert_layout(cell, directives_)
                else:
                    convert_layout(cell, directives_)
                    cell.source += ":::"
