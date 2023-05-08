import matplotlib.pyplot as plt
import networkx as nx
from pylab import rcParams
from networkx.drawing.nx_pydot import graphviz_layout

rcParams['figure.figsize'] = 30, 10


def remove_parenteses(s):
    s = s.strip()
    if len(s) > 1 and s[0] == "(" and s[-1] == ")":
        return s[1:-1]
    else:
        return s


def plot_graph(g):
    # print(g.nodes(data=True))
    pos = graphviz_layout(g, prog="dot")
    nx.draw(g, pos=pos,
            node_color='lightgreen',
            node_size=1500,
            with_labels=True)
    plt.show()


def gera_arvore(algebra: str):
    g = nx.Graph()
    strAlgebra = algebra

    if "|X|" in strAlgebra:
        i = strAlgebra.count("|X|")
        arrayOperacoes = list()
        arrayOperacoes.append(strAlgebra[:strAlgebra.index("(") - 1].strip())
        strAlgebra = remove_parenteses(strAlgebra[strAlgebra.index("("):]).strip()
        for n in range(i):

            if not "|X|" in strAlgebra: break
            # Pega o Join
            joinSection = strAlgebra[strAlgebra.index("|X|"):]

            # Pega o que tá a esquerda do join
            esquerdaJoin = strAlgebra[:strAlgebra.index("|X|")]

            # Pega o que tá a direita do join
            if "(" in joinSection:
                strAlgebra = remove_parenteses(joinSection[joinSection.index("("):]).strip()
                joinSection = joinSection[:joinSection.index("(") - 1]
            else:
                strAlgebra = strAlgebra[strAlgebra.rindex(" ") + 1:].strip()
                joinSection = joinSection[joinSection.index("|X|"):joinSection.rindex(" ")]

            esquerdaJoin = remove_parenteses(esquerdaJoin.strip())
            arrayOperacoes.append(joinSection.strip())
            if "(" in esquerdaJoin:
                arrayOperacoes.append(esquerdaJoin[:esquerdaJoin.index("(") - 1].strip())
                while True:
                    esquerdaJoin = remove_parenteses(esquerdaJoin[esquerdaJoin.index("("):])
                    if "(" in esquerdaJoin:
                        arrayOperacoes.append(esquerdaJoin[:esquerdaJoin.index("(") - 1])
                    else:
                        arrayOperacoes.append(esquerdaJoin.strip())
                        break
            else:
                arrayOperacoes.append(esquerdaJoin.strip())
            nx.add_path(g, arrayOperacoes)
            arrayOperacoes.clear()
            arrayOperacoes.append(joinSection.strip())
        if "(" in strAlgebra:
            arrayOperacoes.append(strAlgebra[:strAlgebra.index("(") - 1].strip())
            while True:
                strAlgebra = remove_parenteses(strAlgebra[strAlgebra.index("("):].strip())
                if "(" in strAlgebra:
                    arrayOperacoes.append(strAlgebra[:strAlgebra.index("(") - 1])
                else:
                    arrayOperacoes.append(strAlgebra.strip())
                    break
        else:
            arrayOperacoes.append(strAlgebra.strip())
        nx.add_path(g, arrayOperacoes)
        plot_graph(g)
    # Quando não tem join
    else:
        arrayOperacoes = list()
        arrayOperacoes.append(strAlgebra[:strAlgebra.index("(") - 1].strip())
        while True:
            strAlgebra = remove_parenteses(strAlgebra[strAlgebra.index("("):].strip())
            if "(" in strAlgebra:
                arrayOperacoes.append(strAlgebra[:strAlgebra.index("(") - 1])
            else:
                arrayOperacoes.append(strAlgebra.strip())
                break
        nx.add_path(g, arrayOperacoes)
        plot_graph(g)
