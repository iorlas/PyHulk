# coding: dsl-mammy

class Test(object):

    def abc(self, a=1):
        print a, self
        print self, a
        def b(s):
            print 123 + s
        b(1)
    
    def bbb(self):
        pass

before:
    >>> print "ima hulk"

after:
    >>> print "hulked"
