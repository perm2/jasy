#!/usr/bin/env python3

import sys, os, unittest

# Extend PYTHONPATH with 'lib'
jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir))
sys.path.insert(0, jasyroot)

import jasy.parser.Parser as Parser
import jasy.process.Compressor as Compressor

def parse(code):
    return Parser.parse(code).toXml(False)
    
def compress(code):
    return Compressor.compress(Parser.parse(code))



class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass
        
        
    def test_function(self):
        self.assertEqual(
            parse("function abc() { return 1; }"),
            '<script line="0"><function functionForm="declared_form" line="0" name="abc"><body><script line="0"><return line="0"><value><number line="0" value="1"/></value></return></script></body></function></script>'
        )

        self.assertEqual(
            parse("var abc = function() { return 1; }"),
            '<script line="0"><var line="0"><declaration line="0" name="abc" readOnly="false"><initializer><function functionForm="expressed_form" line="0"><body><script line="0"><return line="0"><value><number line="0" value="1"/></value></return></script></body></function></initializer></declaration></var></script>'
        )
        
        self.assertEqual(
            parse("var abc = function abc() { return 1; }"),
            '<script line="0"><var line="0"><declaration line="0" name="abc" readOnly="false"><initializer><function functionForm="expressed_form" line="0" name="abc"><body><script line="0"><return line="0"><value><number line="0" value="1"/></value></return></script></body></function></initializer></declaration></var></script>'
        )
        
        
    def test_expression(self):
        
        self.assertEqual(
            parse('a + ++i;'),
            '<script line="0"><semicolon line="0"><expression><plus line="0"><identifier line="0" value="a"/><increment line="0"><identifier line="0" value="i"/></increment></plus></expression></semicolon></script>'
        )
        
        
        self.assertEqual(
            parse('a++ + i;'),
            '<script line="0"><semicolon line="0"><expression><plus line="0"><increment line="0" postfix="true"><identifier line="0" value="a"/></increment><identifier line="0" value="i"/></plus></expression></semicolon></script>'
        )
        
        


    


class TestCompressor(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_and(self):
        self.assertEqual(compress('x && y'), 'x&&y;')

    def test_arithm(self):
        self.assertEqual(compress('i++; j-- + 3;'), 'i++;j--+3;')

    def test_array_number(self):
        self.assertEqual(compress('var data1 = [ 1, 2, 3 ];'), 'var data1=[1,2,3];')

    def test_array_string(self):
        self.assertEqual(compress('var data2 = [ "hello" ];'), 'var data2=["hello"];')

    def test_array_sparse(self):
        self.assertEqual(compress('var data3 = [ 1, , , 4, , 6 ];'), 'var data3=[1,,,4,,6];')
        
    def test_array_comprehension(self):
        self.assertEqual(compress('exec([i for (i in obj) if (i > 3)]);'), 'exec([i for(i in obj)if(i>3)]);')

    def test_bitwise_and(self):
        self.assertEqual(compress('z = x & y;'), 'z=x&y;')

    def test_block_separate(self):
        self.assertEqual(compress('{ x = 1; y = 2; }'), '{x=1;y=2}')

    def test_block_empty(self):
        self.assertEqual(compress('if (true) {}'), 'if(true){}')

    def test_call_singlearg(self):
        self.assertEqual(compress('hello("hello world");'), 'hello("hello world");')

    def test_call_multiargs(self):
        self.assertEqual(compress('multi(1, 2, 3);'), 'multi(1,2,3);')

    def test_call_destruct(self):
        self.assertEqual(compress('[a, b] = f();'), '[a,b]=f();')

    def test_const(self):
        self.assertEqual(compress('const foo = 3;'), 'const foo=3;')

    def test_const_multi(self):
        self.assertEqual(compress('const foo = 3, bar = 4;'), 'const foo=3,bar=4;')

    def test_continue(self):
        self.assertEqual(compress('while(x) { continue; }'), 'while(x){continue}')

    def test_continue_label(self):
        self.assertEqual(compress('dist: while(y) { continue dist; }'), 'dist:while(y){continue dist};')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')

    def test_(self):
        self.assertEqual(compress(''), '')


        
        
        
        
        



if __name__ == '__main__':
    unittest.main()
    
    