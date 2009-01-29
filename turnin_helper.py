#!/usr/bin/env python
import os, re, sys
from optparse import OptionParser, OptionGroup

VERSION = '0.1'
DISPLAY_WARNINGS = True
FORCE = False
YES = ['yes', 'y', '1']
QUIT = ['quit', 'q']


"""Grading Script for automatically unpacking the newest turnins
   Written By: Bryce Boe (bboe at cs)
   Date: 2009/01/27

   Last Update: 2009/01/28
"""

#==== Custom Test Function
def calci_test():
    """Custom test function for CS160 Proj0 Grading
    
    When turnin_helper is invoked with the argument --test-function=calci_test
    this function is called once for each submission. Prior to the call to this
    function python changes directories to the base of the extracted files
    for the submission.
    """
    print "Testing: %s" % os.path.basename(os.getcwd())

    tests_dir = '/home/bryce/src/TURNIN/TESTS/'
    for test in os.listdir(tests_dir):
        input = os.path.join(tests_dir, test)
        stdout = 'stdout-%s' % test
        stderr = 'stderr-%s' % test
        os.system('calci/calci < %s > %s 2> %s' % (input, stdout, stderr))
        if 'valid' in test:
            os.system('dot -Tps %s | ps2pdf - > %s' % (stdout, '%s.pdf' % test))
#=====

def exit_error(msg):
    print msg
    sys.exit(1)

def warning(msg):
    if DISPLAY_WARNINGS:
        sys.stderr.write('Warning: %s\n' % msg)

def verify(msg):
    input = raw_input('%s ' % msg).lower()
    if input in YES:
        return True
    if input in QUIT:
        exit_error('Aborted')

def get_latest_turnin_list(proj_dir, extension):
    """Builds a list of all the most recent submissions"""
    submit_re = re.compile('(\w+)(-(\d)+)?.%s' % extension)
    submissions = [x for x in os.listdir(proj_dir) if extension in x]
    if not submissions:
        exit_error('No files in %s with extension %s' % (proj_dir, extension))

    # Build unique user submission list, with most recent count
    unique_users = {}
    for submission in submissions:
        user, _, submit_count = submit_re.match(submission).groups()
        submit_count = int(submit_count) if submit_count else 0
        if user in unique_users:
            unique_users[user] = max(unique_users[user], submit_count)
        else:
            unique_users[user] = submit_count

    latest_submissions = []
    for user, submit_count in unique_users.items():
        extra = '-%d' % submit_count if submit_count > 0 else ''
        latest_submissions.append('%s%s' % (user, extra))
    return latest_submissions

def extract_submissions(proj_dir, work_dir, extension, submit_list):
    """Unpacks all files passed in as a list here"""
    if not os.path.isdir(work_dir):
        if not FORCE:
            if not verify('Are you sure you want to create %s?' % work_dir):
                exit_error('Aborted')
        os.mkdir(work_dir)

    for submit in submit_list:
        print 'Unpacking: %s' % submit
        extract_dir = os.path.join(work_dir, submit)
        compressed = os.path.join(proj_dir, '%s.%s' % (submit, extension))
        if os.path.isdir(extract_dir):
            if not FORCE:
                if not verify('Are you sure you want to overwrite %s?' % 
                              extract_dir):
                    continue
        else:
            os.mkdir(extract_dir)
        extract_log = os.path.join(extract_dir, 'extract_log')
        os.system('tar -xvzf %s -C %s > %s' % (compressed, extract_dir,
                                               extract_log))

def make(work_dir, make_dir, makefile, target, submit_list):
    if not os.path.isdir(work_dir):
        exit_error('work_dir does not exist. Extract first')

    """Runs make for each submission"""
    makefile = '-f %s' % makefile if makefile else ''
    target = '' if not target else target
    make_cmd = 'make %s -C %%s %s > %%s' % (makefile, target)

    for submit in submit_list:
        print 'Making: %s' % submit
        submit_dir = os.path.join(work_dir, submit, make_dir)
        make_log = os.path.join(work_dir, submit, 'make_log')

        if not os.path.isdir(submit_dir):
            print 'Cannot build: submit_dir does not exist'
        else:
            os.system(make_cmd % (submit_dir, make_log))

def purge_files(work_dir, submit_list):
    """Deletes directories with submit name in work_dir"""
    if not os.path.isdir(work_dir):
        exit_error('work_dir does not exist')
        return

    if not FORCE:
        if not verify('Are you sure you want to delete user folders?'):
            return  

    for user in submit_list:
        user_dir = os.path.join(work_dir, user)
        if os.path.isdir(user_dir):
            print 'Deleting: %s' % user
            os.system('rm -rf %s' % os.path.join(work_dir, user))
        else:
            warning('%s does not exist' % user_dir)

    if not os.listdir(work_dir):
        if not FORCE:
            if not verify('%s is empty. Do you want to delete?' % work_dir):
                return
        os.rmdir(work_dir)

def run_test_function(work_dir, test_function, submit_list):
    if not os.path.isdir(work_dir):
        exit_error('work_dir does not exist. Extract first')

    if not test_function in globals():
        exit_error('Aborting: No function named %s' % test_function)

    for submit in submit_list:
        os.chdir(os.path.join(work_dir, submit))
        globals()[test_function]()


if __name__ == '__main__':
    # Setup and configure options parser
    usage = 'Usage: %prog [options] proj_dir'
    description = """\
In attempt to save himself time (or so he thought) Bryce Boe embarked on a
journey of semi-great proportions. It started with a simple python file to
extract the newest submission of each student after a project deadline. Soon
later the journey was extended to run make in each of these extracted
directories. Pushing through fatigue, Bryce's journey continued with the
auto execution of certain commands. Upon realizing that more time was probably
spent on this journey rather than the actual grading of the programs Bryce
decided to make it all worthwhile. The journey again was extended to allow for
confirmation of actions and of course making the script as portable as possible.

"""
    parser = OptionParser(usage=usage, description=description,
                          version='%%prog %s' % VERSION)
    parser.add_option('-x', '--extract', action='store_true', default=False,
                      help=' '.join(['extract students\' most recent',
                                     'submission (default: %default)']))
    parser.add_option('-m', '--make', action='store_true', default=False,
                      help='run make for each user (default: %default)')
    parser.add_option('--test-function', metavar='FUNC',
                      help=' '.join(['if specified this is a python function',
                                     'to call from the directory created for',
                                     'each submission']))
    parser.add_option('--purge', action='store_true', default=False,
                      help=' '.join(['delete extracted user folders and their',
                                     'contents (default: %default)']))

    group = OptionGroup(parser, 'Configuration Options')
    group.add_option('--work-dir', metavar='DIR', default='.',
                     help='directory to perform work in (default: %default)')
    group.add_option('--make-dir', metavar='DIR', default='.',
                     help=' '.join(['directory within submission to run make',
                                    '(default: %default)']))
    group.add_option('--makefile', metavar='FILE',
                     help=' '.join(['relative or absolute path to the makefile',
                                    'to use with make (default: student\'s',
                                    'submitted makefile)']))
    group.add_option('--target', metavar='TARGET',
                     help='make target to call')
    group.add_option('--extension', metavar='EXT', default='tar.Z',
                     help='extension of submitted files (default: %default)')
    group.add_option('-W', '--no-warn', action='store_true', default=False,
                      help='suppress warning messages')
    group.add_option('-f', '--force', action='store_true', default=False,
                     help='answer yes to all verification questions')
    parser.add_option_group(group)


    # Run options parser and verify required command line arguments
    options, args = parser.parse_args()
    if len(args) == 0:
        parser.error('Must provide turnin_directory')
    elif len(args) > 1:
        parser.error('Too many arguments')

    if options.no_warn:
        DISPLAY_WARNINGS = False
    if options.force:
        FORCE = True

    # Verify supplied paths
    proj_dir = os.path.join(os.getcwd(), args[0])
    if not os.path.isdir(proj_dir):
        exit_error('proj_dir does not exist' % proj_dir)
    elif not os.path.isfile(os.path.join(proj_dir, 'LOGFILE')):
        warning('proj_dir does not appear to be valid. Reason: No LOGFILE')

    work_dir = os.path.join(os.getcwd(), options.work_dir)
    submit_list = get_latest_turnin_list(proj_dir, options.extension)

    if options.extract:
        extract_submissions(proj_dir, work_dir, options.extension, submit_list)
    if options.make:
        if options.makefile:
            makefile = os.path.join(os.getcwd(), options.makefile)
            if not os.path.isfile(makefile):
                exit_error('Makefile (%s) does not exist' % makefile)
        else:
            warning('Using student supplied makefiles')
            makefile = None
        make(work_dir, options.make_dir, makefile, options.target, submit_list)
    if options.purge:
        purge_files(work_dir, submit_list)
    if options.test_function:
        run_test_function(work_dir, options.test_function, submit_list)