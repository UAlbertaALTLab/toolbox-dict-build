from typing import Iterator


def so_far_collected(data) -> str:
    return '\n'.join([" ".join(x) for x in data])

def build_toolbox_data_structure( iterator : Iterator[str] ) -> list[list[tuple[str, str]]]:
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
                err = ValueError(f"Line {linenum} does not have a mapping.  This mean a line does not have a space after the toolbox key.  You might want to ask altlab for help with this.")
                err.debug_info = so_far_collected(entry)
                err.last_line = line
                raise err
            if not candidate[0].startswith("\\"):
                err = ValueError(f"Line {linenum} missing toolbox key.  This likely means an incorrect line break was added in the previous line.")
                err.debug_info = so_far_collected(entry)
                err.last_line = line
                raise err
            entry.append((candidate[0], candidate[2]))
        linenum += 1
    # Now add last entry
    if len(entry) > 1:
        entries.append(entry)

    # Finished first attempt at parsing.
    return entries

def load_toolbox( data : str) -> list[list[tuple[str, str]]]:
    f = iter(data.splitlines())
    header = next(f)
    if not header.startswith("\\_sh "):
        raise ValueError(f"first line is not as expected: {header}. Ask altlab about this.")
    if next(f).strip():
        raise ValueError(f"More than one line in the toolbox file header. Ask altlab about this.")
    return build_toolbox_data_structure (f)

