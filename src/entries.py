"""
entries.py: Provides both the helper functions and the main function to process the dictionary and definitions for them.
"""
from jinja2.loaders import FileSystemLoader
from latex.jinja2 import make_env
from parse import so_far_collected
from stanford import tag_sentences
from operator import itemgetter, attrgetter
import natsort
from natsort.ns_enum import ns

def check_data (data, entry):
    fields = data.keys()
    if "\\sro" not in fields:
        err = ValueError(f"An entry is missing the \\sro field.  Likely, an entry got separated by an extra line break, which makes it computationally indistinguishable from two entries. You will likely need to find the line for this.\n\nIf you intend to have entries without \\sro fields, please talk with altlab.")
        err.debug_info = so_far_collected(entry) # type: ignore
        err.last_line="" # type:ignore
        raise err        

def expand_conventions(defn: str)-> str:
    return defn.replace("s.o.","someone").replace("s.t.","something").replace("S/he","she").replace("s/he","she")

class TBEntry:

    def __init__(self, original_data: list[tuple[str, str]]):
        self.original_data = original_data
        self.original_dict = dict()
        for key, value in original_data:
            self.original_dict.setdefault(key,[]).append(value)
        self.populate_fields()
    
    def populate_fields(self):
        check_data(self.original_dict, self.original_data)
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

        self.subsenses_expanded = [
            expand_conventions(sense) for sense in self.subsenses
        ]

        self.parsed_subsenses: list[list[tuple[str,str,str]]] = []
        
        self.processed_subsenses: list[str] = []

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
            if key == "\\gl" and value.strip():
                main_entry=[value.strip()]
            if key == "\\glp" and value.strip():
                if '-' in value:
                    before, _, after = value.partition("-")
                    self.glosses.append([before.strip(),after.strip()])
                else:
                    self.glosses.append([value.strip()])
                    print(f"Warning: \\glp field that does not have a separator: {value} in entry {self.sro}")
            if main_entry:
                self.glosses.append(main_entry)
                main_entry = []
        main, _, rest = (self.pos[0] if len(self.pos)>0 else "").partition("-")
        self.latex_pos = "\\textit{{{}}}\\textsubscript{{\\textit{{{}}}}}" .format(main.lower(), rest.lower()) if rest else "\\textit{{{}}}".format(main.lower())
        self.latex_stem = self.stem[0].strip()
        if not self.latex_stem:
            self.latex_stem = self.sro[0].strip()

def build_basic_tbentries(data : list[list[tuple[str, str]]]) -> list[TBEntry]:
    return [TBEntry(x) for x in data if next(filter(lambda y: y[0] != "line", x), None) is not None]

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

def simplify_defns(remove:str, entry: TBEntry) -> list[tuple[str,str,str]]:
    defns = [defn for defn in entry.processed_subsenses if remove in defn]
   
    return [defn.partition(remove) for defn in defns]

def canonicalize_defn(parts: tuple[str,str,str]) -> str:
    def chunk(parts: list[str]) -> str:
        if parts[1]:
            if parts[0] or parts[2]:
                return "{\\raisebox{-.25em}{\\textasciitilde}} ".join([parts[0],parts[2]])
            return ""
        return parts[0]
    
    return chunk([x.replace("&","\\&").replace("{","\\{").replace("}","\\}").replace("#","\\#").replace("$","\\$").strip()
                  for x in parts])

ESCAPED_KEY = "itwewina_entries"

def sort_main_entries(entries: list[tuple[tuple[str,str,str],TBEntry]]) -> list[tuple[str,TBEntry]]:
    candidates = natsort.natsorted(entries,key=lambda x: x[0][2],alg=ns.NUMAFTER | ns.GROUPLETTERS | ns.LOWERCASEFIRST)
    candidates = natsort.natsorted(candidates,key=lambda x: x[0][0],alg=ns.NUMAFTER | ns.GROUPLETTERS | ns.LOWERCASEFIRST)
    return [(canonicalize_defn(split_defn), entry) for split_defn, entry in candidates]

def sort_subheading_keys(entries: list[str], heading: str) -> list[str]:
    candidates = [entry.partition(heading) for entry in entries]
    candidates = natsort.natsorted(candidates,key=itemgetter(2),alg=ns.NUMAFTER | ns.GROUPLETTERS | ns.LOWERCASEFIRST)
    candidates = natsort.natsorted(candidates,key=itemgetter(0),alg=ns.NUMAFTER | ns.GROUPLETTERS | ns.LOWERCASEFIRST)

    return [''.join(t) for t in candidates]

def sort_subheading_entries(entries: list[tuple[tuple[str,str,str],TBEntry]]) -> list[tuple[str, TBEntry]]:
    # This looks like repeats sort_main_entries but we keep it separate in case we need to change it separately later
    candidates = natsort.natsorted(entries,key=lambda x: x[0][2],alg=ns.NUMAFTER | ns.GROUPLETTERS | ns.LOWERCASEFIRST)
    candidates = natsort.natsorted(candidates,key=lambda x: x[0][0],alg=ns.NUMAFTER | ns.GROUPLETTERS | ns.LOWERCASEFIRST)
    return [(canonicalize_defn(split_defn), entry) for split_defn, entry in candidates]

class DictEntry:
    def __init__(self, heading, parsed_heading, data):
        self.head = heading
        self.main_entries = sort_main_entries([(split_defn,entry) for entry in data.get(ESCAPED_KEY,[]) for split_defn in simplify_defns(parsed_heading, entry)])
        self.subheading_keys = sort_subheading_keys([key for key in data.keys() if key != ESCAPED_KEY], heading)
        # Now you could sort the subheadings
        # But for now, we are keeping them as they come.
        self.subheadings = []
        for key in self.subheading_keys:
            self.subheadings.append((key, sort_subheading_entries([(split_defn,entry) for entry in data[key].get(ESCAPED_KEY,[]) for split_defn in simplify_defns(key, entry)])))


class Dictionary:
    def __init__(self, data: list[list[tuple[str,str]]]):
        self.data = data
        self.crkentries = build_basic_tbentries(data)
        # Group all entries by gloss
        keys = set()
        self.entries = dict()
        for entry in self.crkentries:
            for gloss in entry.glosses:
                current = self.entries
                for index in gloss:
                    current = current.setdefault(index, dict())
                    keys.add(index)
                current.setdefault(ESCAPED_KEY,[]).append(entry)
        keys = list(keys)
        parsed_keys = tag_sentences(keys)
        self.parsed_keys = {unparsed:parsed_keys[key] for key, unparsed in enumerate(keys)}
    
    def latex(self) -> str:
        data = env.get_template("dict.latex").render({"entries":self.context()})
        return data

    def context(self):
        entries = [DictEntry(entry_key, pick_sense(self.parsed_keys[entry_key], entry_key, None), entry_body) for entry_key, entry_body in self.entries.items() if entry_key]        
        return sort_top_dictentries(entries)

def make_dictionary (f : list[list[tuple[str, str]]]) -> Dictionary :
    d = Dictionary(f)
    inflected_senses = list({sense for entry in d.crkentries for sense in entry.subsenses_expanded if sense.strip()})
    parsed_senses = tag_sentences(inflected_senses)
    transfered_senses = {inflected:parsed_senses[key] for key, inflected in enumerate(inflected_senses)}
    # Now that we have the data, we can actually provide the correct definitions to each sense
    for entry in d.crkentries:
        entry.parsed_subsenses = [transfered_senses[sense] for sense in entry.subsenses_expanded if sense.strip()]
        entry.processed_subsenses = [pick_sense(parsed, entry.subsenses[i], entry) for i, parsed in enumerate(entry.parsed_subsenses)]   
    return d

def pick_sense(parsed: list[tuple[str,str,str]], original:str, entry: TBEntry | None)-> str:
    # The entry is there in case we need to so some distinction for vai/vti/etc.
    # TODO: merge entries in a set.
    candidate = parsed.copy()
    if candidate[0][2].strip() in ["she", "my"] and len(candidate)>1:
        del candidate[0]
    try:
        if candidate[-1][2].strip() in ["someone", "something"] and len(candidate)>1:
            del candidate[-1]
    except IndexError:
        print("Indexerror in picksense (checking ending)")
    return ' '.join([x[2] if x[1].startswith("V") else x[0] for x in candidate])

def sort_top_dictentries(entries: list[DictEntry])-> list[DictEntry]:
    return natsort.natsorted(entries, key = attrgetter("head"), alg=ns.NUMAFTER | ns.GROUPLETTERS | ns.LOWERCASEFIRST)
