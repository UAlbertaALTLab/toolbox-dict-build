DIFF_SRC="../data/Wolvengrey_altlab_diff.toolbox"
DIFF_OUTPUT="../data/Wolvengrey_altlab_output.toolbox"
LEFT="HEAD"
RIGHT="master"
# The key of this file is to process automagically all the changes we already made and which should have been auto merged but for which it seems that git is very dumb (or should have been done with dates?)  I can't really trust merges now it seems

chunks = []
lines = []

# split diffs into chunks

with open(DIFF_SRC,'r+') as f:
    for line in f:
        if line != f"<<<<<<< {LEFT}\n":
            lines.append(line)
        else:
            chunks.append({"diff": False, "lines": lines})
            lines = []
            left = []
            next_line = next(f)
            while (next_line != "=======\n"):
                left.append(next_line)
                next_line = next(f)
            next_line = next(f)
            right = []
            while (next_line != f">>>>>>> {RIGHT}\n"):
                right.append(next_line)
                next_line = next(f)
            chunks.append({"diff": True, "left": left, "right": right})
    if lines:
        chunks.append({"diff": False, "lines": lines})

diffs = [x for x in chunks if x['diff']]

starts = [
    "\\rw",
    "\\rw2",
    "\\wn"
]

def drop_rw(lines):
    return [l for l in lines if not any([l.startswith(s+" ") or l == s+"\n" for s in starts])]

def keep_rw(lines):
    return [l for l in lines if any([l.startswith(s+" ") or l == s+"\n" for s in starts])]

keys = set()

def collect(x : list[str]):
    keys.update([l.partition(" ")[0] for l in x])
    return True

def was_rw(chunk):
    return chunk["diff"] and not chunk["right"] and collect(chunk["left"])

def new_ending(chunk):
    return chunk["diff"] and all([x.startswith("\\dt ") for x in drop_rw(chunk["left"])]) and all([x.startswith("\\dt ") for x in drop_rw(chunk["left"])])


print(f"Chunks: {len(diffs)}")
print(f"Was_rw:{len([d for d in diffs if was_rw(d)])}")
print(f"New_end:{len([d for d in diffs if new_ending(d)])}")
print(f"KEYS: {keys}")
print("\n\n")

with open(DIFF_OUTPUT,'w') as f:
    for chunk in chunks:
        if not chunk["diff"]:
            for line in chunk["lines"]:
                f.write(line)
        elif new_ending(chunk):
            if chunk["right"]:
                for line in keep_rw(chunk["left"]):
                    f.write(line)
                for line in drop_rw(chunk["right"]):
                    f.write(line)
            else:
                for line in chunk["left"]:
                    f.write(line)
        else:
            f.write(f"<<<<<<< {LEFT}\n")
            for line in chunk["left"]:
                f.write(line)
            f.write("=======\n")
            for line in chunk["right"]:
                f.write(line)
            f.write(f">>>>>>> {RIGHT}\n")
