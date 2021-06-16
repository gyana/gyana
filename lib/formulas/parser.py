from lark import Lark

parser = Lark.open("formula.lark", rel_to=__file__, start="formula")
