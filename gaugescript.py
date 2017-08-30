#!/usr/bin/env python

# This program interprets Microsoft ESP gauge script.
# Gauge script is a postfix language so this program
# uses a stack to interpret the script.

# A really nice feature would allow this interpreter to connect
# to ESP via simconnect and access live variables from the
# simulator (ie either read or write). This may be possible
# using ctypes to acess the simconnect dll functions

#
# Commands
# - pstack : prints the stack
# - pvars : prints the var dictionary
# - quit : quit the interpreter
#

#
# Status
# This is still in a very primordial state
#
# TODO
# - Full support of all gaugescript elements
# - help command
# - default units for vars
# - unit translation
# - debugging
# - connect to FSX etc using simconnect
#

import sys
import re
import math

lexTable = [
    ( 'STRING', re.compile( r'\'(.*)\'' ) ),
    ( 'FLOAT', re.compile( r'\d+\.\d+' ) ),
    ( 'INT', re.compile( r'\d+' ) ),
    ( 'OP', re.compile( r'\&|\||\^|\~|\>\>|\<\<' ) ),
    ( 'OP', re.compile( r'(\=\=)|(\!\=)|\!|\&\&|\|\|' ) ),
    ( 'OP', re.compile( r'\<|\>|\>\=|\<\=' ) ),
    ( 'OP', re.compile( r'(\+\+)|(\-\-)' ) ),
    ( 'OP', re.compile( r'\/\-\/|\?' ) ),
    ( 'OP', re.compile( r'[\+\-\*\/\%]' ) ),
    ( 'ID', re.compile( r'[a-zA-Z_]+' ) ),
    ( 'SPACE', re.compile( r'\s+') ),
    ( 'VAREXPR', re.compile( r'\(([a-zA-Z_: ]+)(,\s*([a-zA-Z]+))?\)' ) ),
    ( 'VARASSIGN', re.compile( r'\(\>([a-zA-Z_: ]+)(,\s*([a-zA-Z]+))?\)' ) ),
]

varDict = {}

def pop( stack ):
    stack.pop()

def add( stack ):
    stack.append( stack.pop() + stack.pop() )

def sub( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A - B )

def mul( stack ):
    stack.append( stack.pop() * stack.pop() )

def div( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A / B )

def mod( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( math.fmod( A, B ) )

def incr( stack ):
    X = stack.pop()
    stack.append( X + 1 )

def decr( stack ):
    X = stack.pop()
    stack.append( X - 1 )

def neg( stack ):
    X = stack.pop()
    stack.append( X * -1 )

def eq( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A == B )

def ne( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A != B )

def gt( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A > B )

def lt( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A < B )

def ge( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A >= B )

def le( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A <= B )

def choose( stack ):
    C = stack.pop()
    B = stack.pop()
    A = stack.pop()
    stack.append( A if C else B )

def bitAnd( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A & B )

def bitOr( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A | B )

def bitXor( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A ^ B )

def bitNot( stack ):
    A = stack.pop()
    stack.append( ~A )

def bitRShift( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A >> B )

def bitLShift( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A << B )

def logicalNot( stack ):
    A = stack.pop()
    stack.append( not A ) 

def logicalAnd( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A and B )

def logicalOr( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A or B )

opTable = {
    '+' : add,
    '-' : sub,
    '*' : mul,
    '/' : div,
    '%' : mod,
    'p' : pop,
    '++' : incr,
    '--' : decr,
    '/-/' : neg,
    '==' : eq,
    '!=' : ne,
    '>' : gt,
    '<' : lt,
    '>=' : ge,
    '<=' : le,
    '?' : choose,
    '&' : bitAnd,
    '|' : bitOr,
    '^' : bitXor,
    '~' : bitNot,
    '>>' : bitRShift,
    '<<' : bitLShift,
    'not' : logicalNot,
    '!' : logicalNot,
    'or' : logicalOr,
    '||' : logicalOr,
    'and' : logicalAnd,
    '&&' : logicalAnd,
}

def abs_( stack ):
    A = stack.pop()
    stack.append( abs( A ) )

def int_( stack ):
    A = stack.pop()
    stack.append( int( A ) )

def rng_( stack ):
    C = stack.pop()
    B = stack.pop()
    A = stack.pop()
    stack.append( A <= C and C <= B )

def pi_( stack ):
    stack.append( math.pi )

def cos_( stack ):
    A = stack.pop()
    stack.append( math.cos( A ) )

def log10_( stack ):
    A = stack.pop()
    stack.append( math.log10( A ) )

def min_( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A if ( A <= B ) else B )

def sin_( stack ):
    A = stack.pop()
    stack.append( math.sin( A ) )

def acos_( stack ):
    A = stack.pop()
    stack.append( math.acos( A ) )

def cot_( stack ):
    A = stack.pop()
    stack.append( 1.0 / math.tan( A ) )

def log_( stack ):
    A = stack.pop()
    stack.append( math.log( A ) )

def square_( stack ):
    A = stack.pop()
    stack.append( A * A )

def asin_( stack ):
    A = stack.pop()
    stack.append( math.asin( A ) )

# Note that this returns a fixed epsilon which might
# not be right. Gaugescript eps takes an argument implying
# that eps depends on the value given.
def eps_( stack ):
    stack.pop()
    stack.append( sys.float_info.epsilon )

def logN_( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( math.log( A, B ) )

def sqrt_( stack ):
    A = stack.pop()
    stack.append( math.sqrt( A ) )

def atan2_( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( math.atan2( A, B ) )

def exp_( stack ):
    A = stack.pop()
    stack.append( math.exp( A ) )

def max_( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( A if A >= B else B )

def pow_( stack ):
    B = stack.pop()
    A = stack.pop()
    stack.append( math.pow( A, B ) )

def tan_( stack ):
    A = stack.pop()
    stack.append( math.tan( A ) )

def atan_( stack ):
    A = stack.pop()
    stack.append( math.atan( A ) )

funcTable = {
    'abs' : abs_,
    'int' : int_,
    'flr' : int_,
    'rng' : rng_,
    'pi' : pi_,
    'cos' : cos_,
    'lg' : log10_,
    'min' : min_,
    'sin' : sin_,
    'acos' : acos_,
    'ctg' : cot_,
    'ln' : log_,
    'sqr' : square_,
    'asin' : asin_,
    'eps' : eps_,
    'log' : logN_,
    'sqrt' : sqrt_,
    'atg2' : atan2_,
    'exp' : exp_,
    'max' : max_,
    'pow' : pow_,
    'tg' : tan_,
    'atg' : atan_,
}

def printHelp():
    print "Commands:"
    print "pstack\tPrint the stack"
    print "pvars\tPrint the variables"
    print "quit\tQuit the program (shortcut q)"

def main():
    repl = True
    stack = []
    while repl:
        try:
            s = raw_input( '> ' )
        except:
            print
            repl = False
            continue
        if s == 'quit' or s == 'q':
            repl = False
            continue
        if s == 'help':
            printHelp()
            continue
        if s == 'pstack':
            print stack
            continue
        if s == 'pvars':
            print varDict
            continue
        i = 0
        while i < len( s ):
            match = False
            for tokType, regex in lexTable:
                result = regex.match(s, i)
                if result:
                    i = result.end()
                    match = True
                    #print "match", tokType, result.group(0)
                    if tokType == 'INT':
                        stack.append( int( result.group( 0 ) ) )
                    elif tokType == 'FLOAT':
                        stack.append( float( result.group( 0 ) ) )
                    elif tokType == 'STRING':
                        stack.append( str( result.group( 1 ) ) )
                    elif tokType == 'OP' or tokType == 'ID':
                        id = result.group( 0 ).lower()
                        if id in opTable:
                            func = opTable[ id ]
                            func( stack )
                        if id in funcTable:
                            func = funcTable[ id ]
                            func( stack )
                    elif tokType == 'VAREXPR':
                        id = result.group( 1 )
                        if result.group( 3 ) is not None:
                            units = result.group( 3 )
                            #print 'units:', units
                        if id in varDict:
                            stack.append( varDict[ id ] )
                        else:
                            print 'Undefined:', id
                    elif tokType == 'VARASSIGN':
                        id = result.group( 1 )
                        if result.group( 3 ) is not None:
                            units = result.group( 3 )
                            #print 'units:', units
                        varDict[ id ] = stack.pop()
                    break

            if not match:
                raise Exception('lexical error at {0}'.format(i))

if __name__ == '__main__':
    main()
