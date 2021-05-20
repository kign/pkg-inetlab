def IF (cond,if_clause,else_clause=None) :
    if cond :
        return if_clause
    else :
        return else_clause

def rematch (re_exp, str, q=None, flags=0) :
    import re
    r = re.match ( re_exp, str, flags )
    if r and q != None:
        q += [r]
    return r

def research (re_exp, str, q=None, flags=0) :
    import re
    r = re.search ( re_exp, str, flags )
    if r and q != None:
        q += [r]
    return r

# http://www.python.org/doc/2.3.5/ref/sequence-types.html
# http://www.python.org/doc/2.3.5/ref/customization.html
# http://www.python.org/doc/2.3.5/tut/node11.html
class Enum :
    def __init__ ( self, *args ) :
        if len(args) == 1:
            if type(args[0]) == type([]) :
                self.values = args[0][:]
            else :
                self.values = [args[0]]
        else :
            self.values = [x for x in args]
        if len(self.values) > 0 :
            self.val = self.values[0]
        else :
            self.val = None

    def __str__ ( self ) :
        return  \
    "Enum(" + ",".join ( [IF(x==self.val,"*"+str(x)+"*",str(x)) for x in self] ) + ")"

    def __repr__ ( self ) :
        return  \
    "Enum(" + ",".join ( [IF(x==self.val,"*"+repr(x)+"*",repr(x)) for x in self] ) + ")"

    def set (self, val) :
        if val not in self.values :
            raise Exception ( "Value '" + repr(val) + "' is not a member in " + repr(self) )
        self.val = val
        
    def seta (self, val) :
        if val not in self.values :
            self.values.append ( val )
        self.val = val

    def append ( self, val ) :
        self.values.append ( val )
        
    def __len__ (self) :
        return len(self.values)
    
    def __iter__ (self) :
        for x in self.values :
            yield x
    
if __name__ == "__main__" :
    # Testing Enum class

    x = Enum ( "appl", "orange", "banana" )
    y = Enum ( [ 2, 3, 5, 7, 11, 13, 17 ] )

    print("x.len = ", len(x))
    print("x = ", x)
    print("y = ", y)

    x.set ( "orange" );
    y.set ( 13 );

    print("x = ", x)
    print("y = ", y)

    x.set ( 10 )
