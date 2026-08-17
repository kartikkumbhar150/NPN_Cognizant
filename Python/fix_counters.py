import re

with open('generate_database.py','r',encoding='utf-8') as f:
    content = f.read()

patterns = [
    (r'f"CCA\{cca_idx:05d\}"', r'f"CCA{cca_idx[0]:05d}"'),
    (r'cca_idx \+= 1', r'cca_idx[0] += 1'),
    (r'f"LOAN\{loan_idx:05d\}"', r'f"LOAN{loan_idx[0]:05d}"'),
    (r'loan_idx \+= 1', r'loan_idx[0] += 1'),
    (r'f"DEP\{dep_idx:05d\}"', r'f"DEP{dep_idx[0]:05d}"'),
    (r'dep_idx \+= 1', r'dep_idx[0] += 1'),
    (r'f"INV\{inv_idx:05d\}"', r'f"INV{inv_idx[0]:05d}"'),
    (r'inv_idx \+= 1', r'inv_idx[0] += 1'),
    (r'f"INS\{ins_idx:05d\}"', r'f"INS{ins_idx[0]:05d}"'),
    (r'ins_idx \+= 1', r'ins_idx[0] += 1'),
    # Also remove the nested function and just inline the logic
]

for pat, repl in patterns:
    before = content
    content = re.sub(pat, repl, content)

# Also fix nonlocal ins_idx line since it's nested
content = content.replace('        nonlocal ins_idx\n', '')

with open('generate_database.py','w',encoding='utf-8') as f:
    f.write(content)

print('Done - replacements applied')
