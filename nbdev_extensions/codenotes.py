# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_codenotes.ipynb.

# %% auto 0
__all__ = ['make_panel_tabset', 'convert_explanation', 'extract_code', 'parse_code', 'NoteExportProc', 'parse_notes']

# %% ../nbs/01_codenotes.ipynb 3
from nbdev.config import get_config
from nbdev.process import NBProcessor, extract_directives
from nbdev.processors import Processor, mk_cell
from nbdev.export import nb_export
from nbdev.doclinks import nbglob
from nbdev.sync import write_nb

from fastcore.script import call_parse
from fastcore.xtras import Path

import shlex
import re

# %% ../nbs/01_codenotes.ipynb 4
def make_panel_tabset():
    "Creates a templated panel tabset for Quarto"
    cells = [
        mk_cell("::: {.panel-tabset}\n\n## Code", cell_type="markdown"),
        # Original goes here
        mk_cell("## Code + Explanation", cell_type="markdown"),
        # All explainations go here
        mk_cell(":::", cell_type="markdown")
    ]
    return cells

# %% ../nbs/01_codenotes.ipynb 5
def convert_explanation(explanation_cell, source):
    "Takes an explanation and source code and linkes them together in a new cell"
    _py, newline = "{.python}", "\n"
    explanation = re.sub(r'\*#|.*[\n]', "", explanation_cell.source)
    content = f"{newline}***{newline}```{_py}{newline}{source}{newline}```"
    content += f"{newline}::: "
    content += "{style='padding-top: 0px;'}"
    content += f"{newline}{explanation}{newline}:::"
    return mk_cell(content, cell_type="markdown")

# %% ../nbs/01_codenotes.ipynb 6
def extract_code(start_code, end_code, source, instance_num, end_instance_num=0):
    "Finds code between start and finish potentially with instances to check"
    start_match = list(re.finditer(f'[ \t]*{start_code}', source))[int(instance_num)]
    start_char = start_match.span()[0]
    end_match = list(re.finditer(f'[ \t]*{end_code}', source))[int(end_instance_num)]
    end_char = end_match.span()[1]
    return source[start_char:end_char]

# %% ../nbs/01_codenotes.ipynb 7
def parse_code(code_cell, markdown_cell):
    "Parses directives to extract the code needed to be highlighted"
    directives = markdown_cell.directives_["explain"]
    directives = shlex.split(" ".join(directives))
    multiline = "multiline" in directives
    if multiline:
        directives = directives[1:]
        if len(directives) == 4:
            start_code, start_instance_num, end_code, end_instance_num = directives
        else:
            (start_code, start_instance_num, end_code), (end_instance_num) = directives, 0
        start_code, end_code = re.escape(start_code), re.escape(end_code)
        return extract_code(start_code, end_code, code_cell.source, start_instance_num, end_instance_num)
    else:
        return directives[0]

# %% ../nbs/01_codenotes.ipynb 8
class NoteExportProc(Processor):
    "A proc that checks and reorganizes cells for documentation for proper explainations"
    offset = 0
    steps = []
    _i = 0
    def begin(self):
        self.reset()
        self.has_reset = False
        self.iter = 0
        self.offset = 0
    
    def reset(self):
        self.results = make_panel_tabset()     
        self.code = []
        self._code = None
        self.found_explanation = False
        self.end_link = False
        self.explanations = []
        self.start_idx = None
        self.end_idx = None
    
    def cell(self, cell):
        if cell.cell_type == "code":
            if not self.found_explanation:
                self._code = cell
                self.start_idx = cell.idx_
                
        if cell.cell_type == "markdown" and "explain" in cell.directives_:
            self.found_explanation = True
            self.explanations.append(cell)
            
        if self.found_explanation:
            idx = cell.idx_ + 1
            if (len(self.nb.cells) <= idx+1) or ("explain" not in self.nb.cells[idx].directives_):
                self.end_link = True
                self.end_idx = cell.idx_ + 1
        
        if self.found_explanation and self.end_link:
            # Assume we have all code + explainations
            tabset_code_idx = 1
            tabset_explain_idx = 3
            self.results.insert(tabset_code_idx, self._code)
            explanations = [self._code]
            for i,explanation in enumerate(self.explanations):
                source = parse_code(self._code, explanation)
                converted_explanation = convert_explanation(explanation, source)
                explanations.append(converted_explanation)
                self.nb.cells.remove(explanation)
            self.results = self.results[:3] + explanations + [self.results[3]]
            self.nb.cells.remove(self._code)
            self.offset = 0
            for result in self.results:
                result.idx_ = self.nb.cells[self.start_idx - 1].idx_ + 1
                self.nb.cells.insert(self.start_idx + self.offset, result)
                self.offset += 1
            self.iter += 1
            self.reset()
            self.has_reset = True
            
            self.offset = 0
            for i,c in enumerate(self.nb.cells): c.idx_ = i

# %% ../nbs/01_codenotes.ipynb 9
@call_parse
def parse_notes():
    "Exports notebooks to parsed notes for documentation. Should be called in the workflow, not yourself!"
    for nb in nbglob(get_config().nbs_path):
        processor = NBProcessor(nb, [NoteExportProc], rm_directives=False)
        processor.process()
        write_nb(processor.nb, nb)
