import sys
import parse
import classes
import csv

if __name__ == '__main__':
    args = sys.argv
    file = args[1]
    output = file.split('.')[0] + '-results.txt'
    model, order = parse.parse_file(file)
    graph = classes.graph(model)
    graph.create_graph()
    belief = classes.belief(graph)
    belief.run()
    with open(output, 'w') as f:
        writer = csv.writer(f, delimiter=' ')
        lines_to_p = {}
        for node in belief.graph.graph_nodes:
            vals = [node.potential.table[(key,)] for key in node.values]
            lines_to_p[node.name] = vals
        for node in order:
            writer.writerow([node] + lines_to_p[node])
