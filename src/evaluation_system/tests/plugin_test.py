'''
Created on 03.12.2012

@author: estani
'''
import unittest
from evaluation_system.api.plugin import metadict, PluginAbstract, ConfigurationError

class DummyPlugin(PluginAbstract):
    """Stub class for implementing the abstrac one"""
    __short_description__ = None
    __version__ = (0,0,0)
    __config_metadict__ =  metadict(compact_creation=True, a=(None, dict(type=int)), b='test', other=1.4)
    _template = "${number} - $something - $other"
    def runTool(self, config_dict=None):
        PluginAbstract.runTool(self, config_dict=config_dict)
class Test(unittest.TestCase):


    def testMetadictCreation(self):
        m1 = metadict(dict(a=1,b=2,c=[1,2,3]))
        m2 = metadict(a=1,b=2,c=[1,2,3])
        self.assertTrue(m1 == m2)
        
        m3 = metadict(a=1,b=2,c=[1,2,3])
        m3.setMetadata('a',test=1)
        #metadata is just a parallel storage and should not affect the data.
        self.assertTrue(m1 == m3)
        
        #the  'compact_creation' is a special key!
        m4 = metadict(compact_creation=False, a=1,b=2,c=[1,2,3])
        self.assertTrue(m1 == m4)
        self.assertFalse('compact_creation' in m4)
        #but after creation you should be able to use it
        m4['compact_creation'] = True
        self.assertFalse(m1 == m4)
        self.assertTrue('compact_creation' in m4)
        
        #setting compact creation to True should only affect tuples! Not lists.
        m5 = metadict(compact_creation=True, a=1,b=2,c=[1,2,3])
        self.assertTrue(m1 == m5)
        #Should fail if compact_creation is set and values are bad formed (i.e. iff tuple then (value, dict)
        self.failUnlessRaises(AttributeError, metadict, compact_creation=True, a=(1, 2),b=2,c=[1,2,3])
        self.failUnlessRaises(AttributeError, metadict, compact_creation=True, a=(1, [2, 3]),b=2,c=[1,2,3])
        
        #Compact creation should produce the same outcome as the normal one
        m6 = metadict(compact_creation=True, a=(1, dict(test=1)),b=2, c=[1,2,3])
        self.assertTrue(m1 == m6)
        self.assertTrue(m3.getMetadata('a') == m6.getMetadata('a'))

    def testMetadictCopy(self):
        m = metadict(dict(a=1,b=2,c=[1,2,3]))
        n = m.copy()
        n['c'][0] = 0
        #check we have a deepcopy of the items
        self.assertTrue(n['c'][0] != m['c'][0])
        
    def testIncompleteAbstract(self):
        #this is an incomplete class not implementing all required fields
        class Incomplete(PluginAbstract):
            pass
        self.failUnlessRaises(TypeError, Incomplete)
        
    def testCompleteAbstract(self):
        """Tests the creation of a complete implementation of the Plugin Abstract class"""
        #even though it's just a stub, it should be complete.
        DummyPlugin()
        
    def testSetupConfiguration(self):
        dummy = DummyPlugin()
        dummy.__config_metadict__ = metadict(compact_creation=True, a=(None, dict(mandatory=1)))
        #the default behavior is to check for None values and fail if found
        self.failUnlessRaises(ConfigurationError, dummy.setupConfiguration)
        
        #it can be turned off
        res = dummy.setupConfiguration(check_cfg=False)
        self.assertTrue(isinstance(res,metadict))

        #check template
        res = dummy.setupConfiguration(dict(num=1),template="$num", check_cfg=False)
        self.assertTrue(isinstance(res,str))
        self.assertEquals("1", res)
        
        #check indirect resolution
        res = dummy.setupConfiguration(dict(num='${a}x', a=1),template="$num", check_cfg=False)
        self.assertEquals("1x", res)
        
    def testParseArguments(self):
        dummy = DummyPlugin()
        dummy.__config_metadict__ = dict(a='', b='')
        res = dummy.parseArguments("a=1 b=2".split())
        self.assertEqual(res, dict(a='1', b='2'))
        
        dummy.__config_metadict__ = dict(a=0,b=0)
        res = dummy.parseArguments("a=1 b=2".split())
        self.assertEqual(res, dict(a=1, b=2))
        
        #even if the default value is different, the metadata can define the type
        dummy.__config_metadict__ = metadict(compact_creation=True, a=('1', dict(type=int)),b=2)
        res = dummy.parseArguments("a=1 b=2".split())
        self.assertEqual(res, dict(a=1, b=2))
        #more arguments than those expected
        dummy.__config_metadict__ = dict(a=0)
        self.failUnlessRaises(ConfigurationError, dummy.parseArguments, "a=1 b=2".split())
        #argument with undefined type
        dummy.__config_metadict__ = dict(a=None, b=1)
        self.failUnlessRaises(ConfigurationError, dummy.parseArguments, "a=1 b=2".split())
        
    def test_parseMetadict(self):
        dummy = DummyPlugin()
        for d, res_d in [(dict(a=0), 1),
                         (metadict(a=0), 1),
                         (metadict(compact_creation=True, a=(None,dict(type=int))), 1),
                         (metadict(compact_creation=True, a=('0',dict(type=int))), 1),
                         (metadict(compact_creation=True, a=2), 1),
                         (dict(a='1'), '1'),
                         (metadict(compact_creation=True, a='2'), '1'),
                         (metadict(compact_creation=True, a=(None,dict(type=str))), '1'),
                         (metadict(compact_creation=True, a=(1,dict(type=str))), '1'),
                         (metadict(compact_creation=True, a=(None,dict(type=bool))), True),
                         (metadict(compact_creation=True, a=(None,dict(type=float))), float('1')),]:
            dummy.__config_metadict__= d
            res = dummy._parseConfigStrValue('a','1')
            self.assertEqual(res, res_d)
            
        
        ##check errors
        #None type
        dummy.__config_metadict__=dict(a=None)
        self.failUnlessRaises(ConfigurationError,dummy._parseConfigStrValue,'a', '1')
        #missing key
        dummy.__config_metadict__=dict(b=1)
        self.failUnlessRaises(ConfigurationError,dummy._parseConfigStrValue,'a', '1')
        
    def testReadConfigParser(self):
        from ConfigParser import SafeConfigParser
        from io import StringIO
        conf = SafeConfigParser()
        conf_str = "[DummyPlugin]\na=42\nb=text"
        conf.readfp(StringIO(conf_str))
        dummy = DummyPlugin()
        
        #check parsing
        for d, res_d in [(dict(a=1), dict(a=42)),
                         (metadict(a=1), dict(a=42)),
                         (metadict(compact_creation=True, a=(1,dict(type=str))), dict(a='42')),
                         (dict(a='1'), dict(a='42')),
                         (dict(a=1,b='1'), dict(a=42,b='text'))]:
            dummy.__config_metadict__= d
            res = dummy.readFromConfigParser(conf)
            self.assertEqual(res, res_d)
        
        ###check errors
        #None type
        dummy.__config_metadict__ = dict(a=None)
        self.failUnlessRaises(ConfigurationError, dummy.readFromConfigParser, conf)
        #wrong type
        dummy.__config_metadict__ = dict(b=1)
        self.failUnlessRaises(ConfigurationError, dummy.readFromConfigParser, conf)
        
    def testSaveConfig(self):
        from StringIO import StringIO
        res_str = StringIO()
        dummy = DummyPlugin()
        
        tests= [(dict(a=1), '[DummyPlugin]\na=1'),
                (dict(a='1'), '[DummyPlugin]\na=1'),
                (metadict(b=2), '[DummyPlugin]\nb=2'),
                (metadict(compact_creation=True,
                          b=(2,dict(help='Example')),
                          a=('1',dict(help='Example 2'))), '[DummyPlugin]\n#Example 2\na=1\n#Example\nb=2')]
        for t, res in tests:
            res_str.truncate(0)
            dummy.saveConfiguration(res_str, t)
            self.assertEqual(res_str.getvalue().strip(), res)
        
    def testReadConfig(self):
        from StringIO import StringIO
        res_str = StringIO()
        dummy = DummyPlugin()
        dummy.__config_metadict__ = metadict(compact_creation=True, a=(None, dict(type=int)), b='test', other=1.4)
        
        for t, res in [(dict(a=1,b='test',other=1.4), '[DummyPlugin]\na=1'),
                       (dict(a=1,b='test',other=1.4), '[DummyPlugin]\na=  1   \n'),
                (dict(a=1,b="2",other=1.4), '[DummyPlugin]\na=1\nb=2')]:
            res_str.write(res)
            res_str.seek(0)
            
            conf_dict = dummy.readConfiguration(res_str)
            self.assertEqual(conf_dict, t)
            
    def _verifyComfingParser(self, config_parser, section, dict_opt):
        #clean up by dumping to string and reloading
        from StringIO import StringIO
        res_str = StringIO()
        config_parser.write(res_str)
        from ConfigParser import SafeConfigParser
        conf = SafeConfigParser()
        res_str.seek(0)
        conf.readfp(res_str)
        
        #first compare options in section
        self.assertEqual(set(conf.options(section)), set(dict_opt))
        #now all values
        for key in conf.options(section):
            self.assertEqual(conf.get(section, key).strip("'"), '%s' %(dict_opt[key]))
        
    def _testWriteConfigParser(self):
        from StringIO import StringIO
        res_str = StringIO()
        dummy = DummyPlugin()
        section = 'DummyPlugin'
        for d in [dict(a=1), metadict(b=1),dict(a=1,b="text"),
                  metadict(compact_creation=True,a=(1,dict(help='Value a'))),
                  metadict(compact_creation=True,a=(1,dict(help='Value a')), 
                        b=(2,dict(help='Value b')),
                        c=(3,dict(help='Value c')))]:
            res = dummy.writeToConfigParser(d)
            res_str.truncate(0)
            res.write(res_str)
            print '%s\n%s' % (d, res_str.getvalue())
            self._verifyComfingParser(res, section, d)
    
    def testHelp(self):
        dummy = DummyPlugin()
        dummy.__version__ = (1,2,3)
        dummy.__short_description__ = 'A short Description.'
        dummy.__config_metadict__ = metadict(compact_creation=True,
                                             a=(1,dict(help='This is the value of a')),
                                             b=(None, dict(help='This is not the value of b')),
                                             example=('test',dict(help="let's hope people write some useful help...")))
        print dummy.getHelp()
        self.assertTrue(len(dummy.getHelp()) > 100)
        
    def testUsage(self):
        dummy = DummyPlugin()
        dummy.__config_metadict__ = metadict(compact_creation=True,
                                             a=(None,dict(type=int,help='This is very important')),
                                             b=2,
                                             c=('x',dict(help='Well this is just an x...')))
        def_config = dummy.setupConfiguration(check_cfg=False)
        def_template = dummy.setupConfiguration(template='a=$a\nb=$b\nc=$c', check_cfg=False)
        from StringIO import StringIO
        res = StringIO() 
        dummy.saveConfiguration(res, def_config)
        res_str1 = res.getvalue()
        res.truncate(0)
        dummy.saveConfiguration(res)
        res_str2 = res.getvalue()
        print def_config
        print def_template
        print res_str1
        self.assertEquals(res_str1, res_str2)
                
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()