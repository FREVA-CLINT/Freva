#!/bin/env python
# encoding: utf-8
'''
find_files -- find files from the miklip baselines

@copyright:  2012 FU Berlin. All rights reserved.
        
@license:    BSD

@contact:    estanislao.gonzalez@met.fu-berlin.de
'''

import sys
import os
import getopt

import model.file as mf

__all__ = []
__version__ = 0.1
__date__ = '2012-10-18'
__updated__ = '2012-10-18'


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg, show_help=True):
        super(CLIError).__init__(type(self))
        auto_doc()
        self.msg = " %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def auto_doc(message=None):
    import re, sys, os
    file = sys.argv[0]
    script_name = os.path.basename(file)
    #check if in unit tests
    if script_name == 'runfiles.py':
        print "No auto doc for unit test."
        return
    
    re_start = re.compile('.*\*!!!\*$')
    re_end = re.compile('^[ \t]*$')
    re_entries= re.compile("^[^']*'([^']*)'[^']*(?:'([^']*)')?[^#]*#(.*)$")
    parsing=False
    results = []
    for line in open(file, 'r'):
        if parsing:
            items = re_entries.match(line)
            if items:
                flag, flag_opt, mesg = items.groups()
                if flag_opt: flag = '%s, %s' % (flag, flag_opt)
                results.append('  %-20s : %s' % (flag, mesg))
            if re_end.match(line): break
        elif re_start.match(line): parsing = True

    if message: message = ': ' + message
    else: message = ''
    if results: print '%s [opt] query %s\nopt:\n%s' % (script_name, message, '\n'.join(results))
    else: print '%s %s' % (script_name, message)

    print """
The query is of the form key=value.

For Example:
    %s model=MPI-ESM-LR experiment=decadal2000 time_frequency=mon variable=tas
""" % script_name

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv[1:]

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    
    program_license = '''
find_files -- find files from the miklip baselines

Copyright (c) 2012, FU Berlin
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
 are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this 
    list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, 
    this list of conditions and the following disclaimer in the documentation 
    and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY 
OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE 
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
OF THE POSSIBILITY OF SUCH DAMAGE.
'''

    try:
        # Setup argument parser
        args, lastargs = getopt.getopt(argv, "hd", ['baseline', 'help', 'debug', 'multiversion'])
        
        #defaults
        DEBUG = False
        baseline = 0
        latest=True
        
        #parse arguments *!!!*
        for flag, arg in args:
            if flag=='-h' or flag=='--help':        #This help
                auto_doc()
                return 0
            elif flag == '--baseline':              #define which baseline to use [0.1.2]. default := 0
                baseline = int(arg)
            elif flag == '--multiversion':          #select not only the latest version but all of them
                latest=False
            elif flag == '-d' or flag == '--debug': #turn on debuging info
                DEBUG = True
        
        #The search is done by the last args
        if len(lastargs) == 0:
                auto_doc()
                return 1
            
        search_dict = {}
        for arg in lastargs:
            if '=' not in arg:
                raise CLIError("Invalid format for query: %s" % arg)
            
            items = arg.split('=')
            search_dict[items[0]] = ''.join(items[1:])
            
        if DEBUG:
            print "Searching string: ", search_dict
       
        #find the files 
        files = mf.BaselineFile.search(baseline, latest_version=latest, **search_dict)

        #display them
        for f in files:
            sys.stdout.write(str(f))
            sys.stdout.write('\n')
            sys.stdout.flush()
        
    except getopt.error:
        print sys.exc_info()[:3]
        return 1
    

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or __name__ != "__main__":
            raise(e)
        return 2

if __name__ == "__main__":
    sys.exit(main())
