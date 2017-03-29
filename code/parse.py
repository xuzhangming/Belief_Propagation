import re
import sys
import classes


def isNum(val):
    try:
        test = float(val)
        return True
    except:
        return False

def parse_file(file):
    with open(file, 'r') as f:
        bayes = classes.bayes_model()
        found = 0
        found_var = 0
        order = []
        for line in f:
            if found == 1:
                if '}' in line:
                    found = 0
                else:
                    row = re.sub(r'[;]\n','',line)
                    row = re.sub(r'\(', ' ', row)
                    row = re.sub(r'\)', ' ', row)
                    row = re.sub(',', ' ', row)
                    row = row.split()
                    curr_states = []
                    curr_vals = []
                    for val in row:
                        if isNum(val):
                            curr_vals.append(float(val))
                        else:
                            curr_states.append(val)
                    bayes.nodes[query].cpt_row_states.append(curr_states)
                    bayes.nodes[query].cpt_row_vals.append(curr_vals)
            elif found_var == 1:
                row = re.sub(r'[;]\n', '', line)
                row = re.sub(r'\(', ' ', row)
                row = re.sub(r'\)', ' ', row)
                row = re.sub(',', ' ', row)
                row = re.sub('\{', ' ', row)
                row = re.sub('\}', ' ', row)
                row = re.sub('\[', ' ', row)
                row = re.sub('\]', ' ', row)
                row = row.split()
                row = row[2:]
                new_node.card = int(row[0])
                new_node.values = row[1:]
                found_var = 0
            elif 'probability' in line:
                val = re.sub(r'[(){}\n]','', line)
                val = re.sub(r',', ' ', val)
                val = val.split()
                val = val[1:]
                query = val[0]
                evidence = val[2:]
                bayes.nodes[query].parents = [bayes.nodes[ev] for ev in evidence]
                bayes.nodes[query].num_parents += len(evidence)
                for ev in evidence:
                    bayes.nodes[ev].children.append(bayes.nodes[query])
                    bayes.nodes[ev].num_children += 1
                found = 1
            elif 'variable' in line:
                curr_var = line.split()[1]
                order.append(curr_var)
                new_node = classes.bayes_node(curr_var)
                bayes.nodes[curr_var] = new_node
                found_var = 1
    return bayes, order




