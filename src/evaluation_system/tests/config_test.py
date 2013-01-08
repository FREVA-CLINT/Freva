'''
Created on 07.01.2013

@author: estani
'''
import os
import unittest
from evaluation_system.api import config
import logging
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

class Test(unittest.TestCase):
    
    def setUp(self):
        if config._DEFAULT_ENV_CONFIG_FILE in os.environ:
            del os.environ[config._DEFAULT_ENV_CONFIG_FILE]
        config.reloadConfiguration()


    def testConfigPlugin(self):
        c = config.Configuration()
        conf = c.setupConfiguration()
        self.assertTrue(conf is not None)
        self.assertEquals(conf, c.__config_metadict__)
        self.assertEquals(conf[config.BASE_DIR], 'evaluation_system')
        
    def testGet(self):
        base_dir = config.get(config.BASE_DIR)
        self.assertEquals(base_dir, 'evaluation_system')
        self.failUnlessRaises(config.ConfigurationException, config.get, 'non-existing-key')
        self.assertEquals(config.get('non-existing-key', 'default-answer'), 'default-answer')
    
    def testKeys(self):
        keys = config.keys()
        self.assertTrue(len(keys) >= 2)
        self.assertTrue(config.BASE_DIR in keys)
        
    def testReload(self):
        """Test we can reload the configuration"""
        config._config[config.BASE_DIR_LOCATION] = 'TEST'
        c1 = config.get(config.BASE_DIR_LOCATION)
        self.assertEquals(c1, 'TEST')
        config.reloadConfiguration()
        c2 = config.get(config.BASE_DIR_LOCATION)
        self.assertNotEquals(c1, c2)
        
    def testConfigFile(self):
        """If a config file is provided it should be read"""
        import tempfile
        fd, name = tempfile.mkstemp(__name__, text=True)
        with os.fdopen(fd, 'w') as f:
            f.write('[Configuration]\n%s=nowhere\n' % config.BASE_DIR)
        
        self.assertEquals(config.get(config.BASE_DIR), 'evaluation_system')
        os.environ[config._DEFAULT_ENV_CONFIG_FILE] = name
        config.reloadConfiguration()
        self.assertEquals(config.get(config.BASE_DIR), 'nowhere')
        os.unlink(name)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPlugin']
    unittest.main()