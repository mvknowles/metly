import re

class Schema(object):
    FLOAT, STRING = range(2)
    TYPES = {"field1": FLOAT, "field2": FLOAT, "field3": STRING, "field4": STRING}
    FIELDS = TYPES.keys()


class Lexer(object):

    RULES = [
            ('\d+',             'NUMBER'),
            ('\w+',             'TEXT'),
            ('\+',              'PLUS'),
            ('\-',              'MINUS'),
            ('\*',              'MULTIPLY'),
            ('\/',              'DIVIDE'),
            ('\(',              'LP'),
            ('\)',              'RP'),
            ('=',               'EQUALS'),
    ]

    def __init__(self):
        self.tokens = []

    def tokenize(self, statement):
        regex_parts = []
        for regex, name in self.RULES:
            regex_parts.append('(?P<%s>%s)' % (name, regex))

        regex = '|'.join(regex_parts)
        for token in re.split(regex, statement):
            if token != None and len(token) != 0 and token != " ":
                self.tokens.append(token.strip())
        

    def current(self):
        if len(self.tokens) > 0:
            return self.tokens[0]
        else:
            return None

    def next(self):
        self.tokens = self.tokens[1:]
        return self.current()

    def peek(self):
        return self.tokens[1]


class Field(object):

    #ALIASES = {"facility": "deviceCustomString1", \
            #"severity": "deviceCustomString2" }

    def __init__(self, lexer):
        self.name = lexer.current()
        lexer.next()

    def __repr__(self):
        return "Field(%s)" % self.name

class From(object):
    def __init__(self, lexer):
        self.table = lexer.current()
        lexer.next()

    def __repr__(self):
        return "From(%s)" % self.table


"""
expression : ( expression )
expression : expression AND expression
expression : expression OR expression
expression : term = term
expression : term != term
"""

# Fix left associativity http://eli.thegreenplace.net/2009/03/14/some-problems-of-recursive-descent-parsers

class AndExpression(object):
    def __init__(self, lexer):
        print "AndExpression"
        self.lhs = TermExpression(lexer)
        self.operator = lexer.current()
        if self.operator != "AND":
            raise Exception("Expected AND")
        lexer.next()
        self.rhs = Expression(lexer)
        print str(self)

    def __repr__(self):
        return "AndExpression(%s %s %s)" % (self.lhs, self.operator, self.rhs)

    def evaluate(self, row):
        return self.lhs.evaluate(row) and self.rhs.evaluate(row)

class OrExpression(object):
    def __init__(self, lexer):
        print "OrExpression"
        self.lhs = TermExpression(lexer)
        self.operator = lexer.current()
        if self.operator != "OR":
            raise Exception("Expected Or")
        lexer.next()
        self.rhs = Expression(lexer)
        print str(self)

    def __repr__(self):
        return "OrExpression(%s %s %s)" % (self.lhs, self.operator, self.rhs)

    def evaluate(self, row):
        return self.lhs.evaluate(row) or self.rhs.evaluate(row)


class TermExpression(object):
    def __init__(self, lexer):
        print "TermExpression"
        self.lhs = lexer.current()
        lexer.next()
        self.operator = lexer.current()
        if self.operator not in ["!=", "=", ">", ">=", "<", "<="]:
            raise Exception("Expected comparator")
        lexer.next()
        self.rhs = lexer.current()
        lexer.next()

        print str(self)

    def __repr__(self):
        return "TermExpression(%s %s %s)" % (self.lhs, self.operator, self.rhs)

    def parse_val(self, hs, row):
        print "hS= %s" % hs
        if hs in Schema.FIELDS:
            value = row[hs]
            typ = Schema.TYPES[hs]
        else:
            print hs
            value = float(hs)
            typ = Schema.FLOAT
        
        return typ, value

    def evaluate(self, row):
        lhs_type, lhs_value = self.parse_val(self.lhs, row)
        rhs_type, rhs_value = self.parse_val(self.rhs, row)

        if lhs_type != rhs_type:
            raise Exception("Type mismatch, %s, %s" % lhs_type, rhs_type)

        if self.operator == "!=":
            return lhs_value != rhs_value
        elif self.operator == "=":
            return lhs_value == rhs_value
        elif self.operator == ">":
            return lhs_value > rhs_value
        elif self.operator == ">=":
            return lhs_value >= rhs_value
        elif self.operator == "<":
            return lhs_value < rhs_value
        elif self.operator == "<=":
            return lhs_value <= rhs_value
            


class BracketExpression(object):
    def __init__(self, lexer):
        print "bracketexpression"
        if lexer.current() != "(":
            raise Exception("Expected (")
        lexer.next()

        self.expr = Expression(lexer)
        if lexer.current() != ")":
            raise Exception("Expected )")
        lexer.next()

    def __repr__(self):
        return "BracketExpression(%s)" % (self.expr)

    def evaluate(self, row):
        return self.expr.evaluate(row)


#SELECT field1, field2, field3, field4 FROM iinet WHERE (field1 = 10 AND field2 = 100)

#BracketExpression(AndOrExpression(TermExpression(


class Expression(object):
    def __init__(self, lexer):
        self.expr = None

        sub_rules = [AndExpression, OrExpression, BracketExpression, TermExpression]

        for rule in sub_rules:
            tokens = lexer.tokens
            try:
                self.expr = rule(lexer)
            except Exception, ex:
                lexer.tokens = tokens
                print str(ex)
                pass

    def __repr__(self):
        return str(self.expr)

    def evaluate(self, row):
        return self.expr.evaluate(row)
                


class Where(object):
    def __init__(self, lexer):
        self.expression = Expression(lexer)
        lexer.next()

    def __repr__(self):
        return "Where(%s)" % str(self.expression)

    def evaluate(self, row):
        return self.expression.evaluate(row)


class FieldList(object):
    def __init__(self, lexer):
        self.fields = []
        self.fields.append(Field(lexer))

#        if c == "*":
#            pass
#            #TODO
            

        while True:
            c = lexer.current()
            if c != ",":
                break

            lexer.next() 
            self.fields.append(Field(lexer))


    def __repr__(self):
        return "FieldList(%s)" % str(self.fields)

    def to_list(self):
        l = []
        for field in self.fields:
            l.append(field.name)
            
        return l

class Select(object):
    def __init__(self, lexer):
        self.field_list = FieldList(lexer)

    def __repr__(self):
        return "Select(%s)" % str(self.field_list)

class SQLStatement(object):
    def __init__(self, lexer):
        if lexer.current().upper() == "SELECT":
            lexer.next()
            self.select = Select(lexer)
        else:
            raise Exception("Expected SELECT")
        
        if lexer.current().upper() == "FROM":
            lexer.next()
            self.from_table = From(lexer)
        else:
            raise Exception("Expected FROM")

        current = lexer.current()
        if current != None and current.upper() == "WHERE":
            lexer.next()
            self.where = Where(lexer)
        else:
            self.where = None
            

    def __repr__(self):
        return "SQLStatement(%s, %s, %s)" % \
                (str(self.select), str(self.from_table), str(self.where))

    def evaluate(self, row):
        result = None
        if self.where == None or self.where.evaluate(row) == True:
            result = {}
            for field in self.select.field_list.to_list():
                if field in row:
                    result[field] = row[field]
                else:
                    result[field] = ""

        return result

class SQLParser(object):
    def parse(self, statement):
        lexer = Lexer()
        lexer.tokenize(statement)
        return SQLStatement(lexer)
