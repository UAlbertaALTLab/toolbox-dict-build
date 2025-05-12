from io import StringIO
def build_toolbox_data_structure( iterator : StringIO ) -> list[list[tuple[str, str]]]:
    entries = []
    entry = []
    linenum = 3
    for line in iterator:
        if not line.strip():
            entries.append(entry)
            entry = [("line", str(linenum))]
        else:
            candidate = line.strip().partition(" ")
            if len(candidate) != 3:
                raise ValueError(f"Line does not have a mapping: {line}")
            if not candidate[0].startswith("\\"):
                raise ValueError(f"Line missing toolbox key: {line}")
            entry.append((candidate[0], candidate[2]))
        linenum += 1
    # Now add last entry
    if len(entry) > 1:
        entries.append(entry)

    # Finished first attempt at parsing.
    return entries

def load_toolbox( data : str) -> list[list[tuple[str, str]]]:
    f = StringIO(data)
    header = next(f)
    if not header.startswith("\\_sh "):
        raise ValueError(f"first line is not as expected: {header}")
    if next(f).strip():
        raise ValueError(f"More than one line in the toolbox file header.")
    return build_toolbox_data_structure (f)

