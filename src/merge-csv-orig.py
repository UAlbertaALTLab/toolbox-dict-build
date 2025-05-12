import csv
import parse
from process import check_data

data = parse.data
# This file is expected to add a particular field from the CSV as replacing from observably most fields that should remain the same.
# Test 81f97d4f057dd1
CSV_FILENAME="../data/Wolvengrey_altlab.csv"
OUTPUT_FILE="../data/Wolvengrey_altlab_output.toolbox"
csv_data = []
with open(CSV_FILENAME,'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_data.append(row)

# Now, at least for now, check how many gaps are there? Maybe they are in order?

in_csv = dict()

KEYTEMPLATE="{}!!!{}!!!{}"

duplicate_keys = [
    'papâmi-piciwin!!!NI-1!!!traveling around, moving around with one\'s camp, trekking about',
    'paskopitêw!!!VTA-4!!!s/he plucks s.o. (e.g. bird), s/he defeathers s.o.',
    'paskopitêw!!!VTA-4!!!s/he plucks s.o. (e.g. bird), s/he defeathers s.o.',
    'pâhko-!!!IPV!!!dry',
    'pîhcâyihk!!!IPC!!!inside, indoors',
    'pîmastêhikan!!!NI-1!!!spinning wheel',
    'sîsipâskwatihkasam!!!VTI-1!!!s/he bakes s.t. with maple sugar as sweetener, s/he sweetens s.t. with maple sugar',
    'pîmisîhêw!!!VTA-1!!!s/he makes s.o. crooked',
    'waskitahiwêw!!!VAI-1!!!s/he puts people on the top'
]

typos = [
    'pihêkwâkamin!!!VII-2n!!!it it hard water, the water is coarse and bitter to taste',
    'pôni-wîcêwêw!!!VTA-2!!!she stops accompanyuing s.o., s/he stops living with s.o., s/he separates from s.o.',
    'tipiskocipaýihcikêw!!!VAI-1!!!s/he makes thinggs even',
    'pêtisahikêw!!!VAI-1!!!s/he drives thngs hither, s/he sends things hither'
]

removed = [
    'toni!!!IPC!!!very, really, intensively, fully, completely, to full degree; quite; much, a lot; well'
]

full_keys = []

for datum in csv_data:
    key = KEYTEMPLATE.format(datum['\\sro'], datum['\\ps'], datum['\\def'])
    if key == KEYTEMPLATE.format('','',''):
        continue
    if key in in_csv:
        if in_csv[key] != datum and key not in duplicate_keys:
            print(f"INSUFFICIENT KEY TO DISTINGUISH: {key}")
        continue
    in_csv[key] = datum
    full_keys.append(key+"!!!"+datum['\\def'])

def find_in_csv(entry):
    try:
        return in_csv[KEYTEMPLATE.format(entry['\\sro'],entry['\\ps'], entry['\\def'])]
    except KeyError:
        return None

def collect_entries_missing():
    # Note that this function is destructive, do not run it with other methods!
    keys = {key.partition('!!!')[0] for key in in_csv.keys()}
    for entry in parse.data:
        check_data(entry)
        key = KEYTEMPLATE.format(entry['\\sro'][0],' ;; '.join(entry['\\ps']),' ;; '.join(entry['\\def']))
        if in_csv and (key in in_csv):
            del in_csv[key]
        elif entry['\\sro'][0] in keys and key not in duplicate_keys:
            print(key)

#collect_entries_missing()
#print(f"Left {in_csv.keys()}")

# Now that we have a data structure that works, collect all the data and replace the fields that we want to replace!


def remove_fields(list, field_names):
    return [x for x in list if not any([x.startswith(f+" ") or x == f+"\n" for f in field_names])]

with open(OUTPUT_FILE,'w') as output:
    with open(parse.TOOLBOX_FILE) as f:
        header = next(f)
        if not header.startswith("\\_sh "):
            raise ValueError(f"first line is not as expected: {header}")
        if next(f).strip():
            raise ValueError(f"More than one line in the toolbox file header.")
        output.write(f"{header}\n")

    #Process entries in order from the data structure:
    for entry,source in parse.sources:
        key = KEYTEMPLATE.format(entry['\\sro'][0],' ;; '.join(entry['\\ps']),' ;; '.join(entry['\\def']))
        fields = remove_fields(source, [
            "\\wn",
            "\\rw",
            "\\rw2"
        ])
        for field in fields[:-1]:
            output.write(field)

        if in_csv and (key in in_csv):
            csv_entry = in_csv[key]
            for wn in csv_entry['\\wn'].split(';;'):
                output.write(f"\\wn {wn.strip()}\n")
            if not csv_entry['\\wn']:
                output.write("\\wn\n")
            for rw in csv_entry['\\rw'].split(';;'):
                output.write(f"\\rw {rw.strip()}\n")
            if not csv_entry['\\rw']:
                output.write("\\rw\n")
            for rw2 in csv_entry['\\rw2'].split(';;'):
                output.write(f"\\rw2 {rw2.strip()}\n")
            if not csv_entry['\\rw2']:
                output.write("\\rw2\n")
        else:
            output.write("\\wn\n\\rw\n\\rw2\n")
        output.write(fields[-1])

        output.write('\n')

