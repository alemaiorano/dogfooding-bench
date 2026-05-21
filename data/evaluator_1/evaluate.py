import csv

input_file = r'C:\Users\Usuario\Downloads\evaluator_1\human_eval_sample.csv'
output_file = r'C:\Users\Usuario\Downloads\evaluator_1\human_eval_sample_labeled.csv'

# Predefined labels based on human evaluation protocol
labels = {
    'E001': '1',
    'E002': '1',
    'E003': '0', # Cut off at 'If your simul'
    'E004': '1',
    'E005': '1',
    'E006': '1',
    'E007': '1',
    'E008': '1',
    'E009': '1',
    'E010': '1',
    'E011': '1',
    'E012': '0', # Cut off at 'Podemos analisar mais'
    'E013': '1',
    'E014': '0', # Cut off at 'sorted binary'
    'E015': '1',
    'E016': '1',
    'E017': '1',
    'E018': '1',
    'E019': '0', # Cut off at 'saber'
    'E020': '1',
    'E021': '1',
    'E022': '1',
    'E023': '0', # Cut off at 'effectiv'
    'E024': '1',
    'E025': '1',
    'E026': '1',
    'E027': '0', # Cut off at 'sé,'
    'E028': '1',
    'E029': '0', # Cut off at 'doesn\'t'
    'E030': '0', # Cut off at 'domíni'
    'E031': '1',
    'E032': '0', # Cut off at 'content,'
    'E033': '0', # Cut off at 'única'
    'E034': '1',
    'E035': '1',
    'E036': '1',
    'E037': '0', # Generic FAQ paste
    'E038': '1',
    'E039': '0', # Cut off at 'lemona'
    'E040': '1',
    'E041': '1',
    'E042': '0', # Cut off at 'tipo de'
    'E043': '0', # Cut off at 'Quando a'
    'E044': '1',
    'E045': '1',
    'E046': '0', # Cut off at 'sobre'
    'E047': '1',
    'E048': '1',
    'E049': '1',
    'E050': '1',
    'E051': '0', # Cut off at 'Satisf'
    'E052': '1',
    'E053': '0', # Hallucination FA fail (em breve)
    'E054': '1',
    'E055': '1',
    'E056': '0', # Generic FAQ paste diff subject
    'E057': '1',
    'E058': '0', # Cut off at 'conversão'
    'E059': '0', # Generic FAQ paste
    'E060': '1'
}

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

for row in rows:
    eval_id = row['eval_id']
    if eval_id in labels:
        row['evaluator_1'] = labels[eval_id]

with open(input_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Labeled effectively.")
