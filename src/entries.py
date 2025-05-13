"""
entries.py: Provides both the helper functions and the main function to process the dictionary and definitions for them.
"""
from jinja2.loaders import FileSystemLoader
from latex.jinja2 import make_env
import re

def check_data (data):
    fields = data.keys()
    if "\\sro" not in fields:        
        raise ValueError(f"Missing SRO: {data}")

class TBEntry:

    def __init__(self, original_data: list[tuple[str, str]]):
        self.original_data = original_data
        self.original_dict = dict()
        for key, value in original_data:
            self.original_dict.setdefault(key,[]).append(value)
        self.populate_fields()
    
    def populate_fields(self):
        check_data(self.original_dict)
        self.sro = self.original_dict["\\sro"]
        self.syllabics = self.original_dict["\\syl"]
        self.pos = self.original_dict["\\ps"]
        self.stem = self.original_dict.get("\\stm", [])
        self.date = self.original_dict.get("\\dt",[])
        self.level_annotated_defns = [
            annotate_nesting_levels(defn)
            for defn in self.original_dict["\\def"]
        ]

        self.level_annotated_senses = [
            x 
            for defn in self.level_annotated_defns
            for x in nested_split(defn, ";")
        ]
        self.level_annotated_subsenses = [
            x
            for sense in self.level_annotated_senses
            for x in nested_split(sense, ",")
        ]
        self.definitions = [
            ''.join([x[1] for x in lad])
            for lad in self.level_annotated_defns
        ]
        self.senses = [
            ''.join([x[1] for x in las])
            for las in self.level_annotated_senses
        ]

        self.subsenses = [
            ''.join([x[1] for x in lass])
            for lass in self.level_annotated_subsenses
        ]
        
        self.canonicalized_definitions = [
            drop_nested(x).strip()
            for x in self.level_annotated_defns
        ]

        self.canonicalized_senses = [
            drop_nested(x).strip()
            for x in self.level_annotated_senses
        ]

        self.canonicalized_subsenses = [
            drop_nested(x).strip()
            for x in self.level_annotated_subsenses
        ]

        gloss_data = filter(lambda x: x[0].startswith("\\gl"), self.original_data)
        self.glosses = []
        main_entry = []
        for key, value in gloss_data:
            if key == "\\gl":
                if main_entry:
                    self.glosses.append(main_entry)
                    main_entry = []
            if key in ["\\gl", "\\glp"]:
                main_entry.append(value.strip())
        main, _, rest = (self.pos[0] if len(self.pos)>0 else "").partition("-")
        self.latex_pos = "\\textit{{{}}}\\textsubscript{{\\textit{{{}}}}}" .format(main.lower(), rest.lower()) if rest else "\\textit{{{}}}".format(main.lower())
        self.latex_stem = self.stem[0].strip()
        if not self.latex_stem:
            self.latex_stem = self.sro[0].strip()

def build_basic_tbentries(data : list[list[tuple[str, str]]]) -> list[TBEntry]:
    return [TBEntry(x) for x in data]

def annotate_nesting_levels( data: str, nest_increase=["(","["], nest_decrease=[")","]"]) -> list[tuple[int,str]]:
    # Note that this method does not check that parenthesis are properly balanced,
    # as this is only going to be used to keep the main level anyways.
    level = 0
    def calc_level(char):
        nonlocal level
        if char in nest_increase:
            level += 1
        elif char in nest_decrease:
            level -= 1
        return level
    return [ (calc_level(char), char) for char in data ]

def nested_split ( nested_data: list[tuple[int,str]], char: str, level=0 ) -> list[list[tuple[int,str]]]:
    split = []
    current = []
    for data in nested_data:
        if data == (level, char):
            split.append(current)
            current=[]
        else:
            current.append(data)
    split.append(current)
    return split

def drop_nested( original_annotated_nesting: list[tuple[int,str]]) -> str:
    return ''.join([
        x[1]
        for x in original_annotated_nesting
        if x[0] == 0
    ])

env = make_env(loader=FileSystemLoader("./templates"))

def simplify_defn(remove:str, entry: TBEntry) -> tuple[str, TBEntry]:
    defn = ", ".join([defn for defn in entry.subsenses if remove in defn]).replace("&","\\&").replace("{","\\{").replace("}","\\}").strip()
    if defn == remove:
        return ("", entry)
    else:
        defn = defn.replace(remove, "{\\raisebox{-.25em}{\\textasciitilde}}")
        return (defn, entry) #"\\char`\\~"), entry)

ESCAPED_KEY = "itwewina_entries"

class DictEntry:
    def __init__(self, heading, data):
        self.head = heading
        self.main_entries = [simplify_defn(heading, entry) for entry in data.get(ESCAPED_KEY,[])]
        self.subheading_keys = [key for key in data.keys() if key != ESCAPED_KEY]
        # Now you could sort the subheadings
        # But for now, we are keeping them as they come.
        self.subheadings = []
        for key in self.subheading_keys:
            self.subheadings.append((key, [simplify_defn(key, entry) for entry in data[key].get(ESCAPED_KEY,[])]))        


class Dictionary:
    def __init__(self, data: list[list[tuple[str,str]]]):
        self.data = data
        self.crkentries = build_basic_tbentries(data)
        # Group all entries by gloss
        self.entries = dict()
        for entry in self.crkentries:
            for gloss in entry.glosses:
                current = self.entries
                for index in gloss:
                    current = current.setdefault(index, dict())
                current.setdefault(ESCAPED_KEY,[]).append(entry)
        

    def latex(self) -> str:
        data = env.get_template("dict.latex").render({"entries":self.context()})
        return data

    def context(self):
        entries = [DictEntry(entry_key, entry_body) for entry_key, entry_body in self.entries.items() if entry_key]
        entries.sort(key=lambda x : str.casefold(x.head))
        return entries

def make_dictionary (f : list[list[tuple[str, str]]]) -> Dictionary :
    return Dictionary(f)