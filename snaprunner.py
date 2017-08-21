# $Author: norbert $
# $Date: 2014-08-03 20:34:12 +0200 (So, 03 Aug 2014) $
# $Revision: 252 $

import os
import sys
import string
import argparse
import shlex
import platform
import traceback
import subprocess
import email
import smtplib
import itertools
import logging
import tempfile
import locale
from email.mime.text import MIMEText
from datetime import datetime, date, time, timedelta

locale.setlocale(locale.LC_ALL, '') # use system's locale
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',level=logging.DEBUG)

class ProgError(Exception):
    pass

class snapshot:
    def __init__(self, args):
        # Default snapshot arguments, if --argsfile is not used.
        # --CreateDir: Create destination directory if it does not exist.
        self.default_snapshot_args = ['--CreateDir', '--AutoBackupSize:512', '-L0', '-Gx' ]

        # Those arguments can not be used in the snapshot arguments file because they are used by this script.
        self.bad_snapshot_args = ['-W', '--LogFile', '-h' ]

        # Date format used in backup file names. Should not be changed.
        self.dateformat = '%Y%m%d-%H%M%S'

        self.args = args
        self.backup_file = None
        self.backup_commandline = None
        self.backup_nr = None
        self.backup_type = None
        self.machine = None
        self.drive = None

        self.failed = False
        self.exception = None
        self.logfilename = None
        self.logtext = None
        self.returncode = None
        
        self.deletetime_all = None
        self.deletetime_diff = None
        self.deleted_files = []

    def split_args(self, s):
        lex = shlex.shlex(s, posix=True)
        lex.whitespace_split = True
        lex.escape = ''
        lex.commenters = ''
        return list(lex)

    def read_snapshot_args(self, argsfile):
        if not os.path.isfile(argsfile):   
            raise(ProgError('The snapshot arguments file \'{0}\' was not found!'.format(argsfile)))

        with open(argsfile, 'r') as logfile:
            argstr = logfile.read()

        arglist = self.split_args(argstr)

        for arg in arglist:
            for bad_arg in self.bad_snapshot_args:
                if arg.lower().startswith(bad_arg.lower()):
                    raise(ProgError('Argument "{0}" can not be used in snapshot arguments file "{1}", because this argument is used by this script itself!'.format(arg, argsfile)))

        return arglist

    def dismantle(self, file):
        name = os.path.splitext(file)[0] # remove extension
        parts = name.split('_')
        if len(parts) != 5:
            raise(ProgError('{0}: invalid backup file name. It must be composed of five_parts separated by \'_\'.'.format(file)))

        nr = parts[2]
        if not nr.startswith('b'):
            raise(ProgError('{0}: invalid backup number. It must start with \'b\' followed by a number.'.format(file)))
    
        nr = nr[1:]
        if not nr.isdigit():
            raise(ProgError('{0}: invalid backup number. It must start with \'b\' followed by a number.'.format(file)))
        nr = int(nr)

        type = parts[4]
        if type != 'full' and type != 'diff':
            raise(ProgError('{0}: invalid type \'{1}\'.'.format(file, type)))
    
        ds = parts[3];
        if len(ds) != 15:
            raise(ProgError('{0}: invalid date part \'{1}\'.'.format(file, parts[1])))

        dd = datetime.strptime(ds, self.dateformat)

        return (file, nr, type, dd)

    def makemachinefilter(self, machine, drive):
        def findmachine(x) : 
            return x.startswith(machine + '_' + drive + '_')
        return findmachine

    def findhsh(self, x) : return x.endswith('.hsh')

    def findsna(self, x) : return x.endswith('.sna')

    def get_existing_backups(self):
        # get all backup files which belong to this machine and drive
        filesall = filter(self.findsna, os.listdir(self.args.backupdir))
        files = filter(self.makemachinefilter(self.machine, self.drive), filesall)

        # get parts of each file name
        struct = map(self.dismantle, files)
        if not struct:
            struct = []
    
        return struct

    def delete_backupfiles(self, files):
        logging.debug(files)
        retval = [] 
        for filename in files:
            base = os.path.splitext(filename)[0].lower()
            for f in sorted(os.listdir(self.args.backupdir)):
                f = f.lower()
                if not os.path.isfile(f):   
                    dpath = os.path.join(self.args.backupdir, f)
                    [dbase, dext] = os.path.splitext(f)
                
                    if base == dbase:
                        # delete only *.hsh and *.sn* files
                        if dext.startswith('.sn') or dext == '.hsh':
                            logging.info('Deleting {0}'.format(dpath))
                            retval.append(dpath)
                            if not self.args.simulate:
                                os.remove(dpath)

        return retval

    def dobackup(self):
        self.machine = platform.node().lower()
        self.drive = self.args.drive.lower()
        if self.drive.endswith(':'):
            self.drive = self.drive[:-1]

        # check if snapshot command exists
        if not os.path.isfile(self.args.cmd):   
            raise(ProgError('The snapshot executable \'{0}\' was not found!'.format(self.args.cmd)))
        if not os.access(self.args.cmd, os.X_OK):
            raise(ProgError('The snapshot executable \'{0}\' is not executable!'.format(self.args.cmd)))
    
        # check if backup dir is not a file and create it
        if os.path.isfile(self.args.backupdir):
            raise(ProgError('The backup directory \'{0}\' is not a directory !!!'.format(self.args.backupdir)))

        # read snapshot args file
        snapshot_args = self.default_snapshot_args
        if self.args.argsfile:
            snapshot_args = self.read_snapshot_args(self.args.argsfile)

        self.args.backupdir = os.path.abspath(self.args.backupdir)
        if not os.path.isdir(self.args.backupdir):   
            os.makedirs(self.args.backupdir)

        struct = self.get_existing_backups()

        # Sort by backup number and date. The last one in the list is the most recent backup.
        struct = sorted(struct, key=lambda x: (x[1], x[3]))

        # filter out all full backups 
        fullbackups = [ s for s in struct if s[2] == 'full' ]

        # determine last full backup
        lastfull = None
        if len(fullbackups) > 0:
            lastfull = fullbackups[-1]
            hshfile = os.path.join(self.args.backupdir, lastfull[0][:-4] + '.hsh')
            if not os.path.isfile(hshfile):
                raise(ProgError('Hash file of last full backup {0} does not exist!'.format(hshfile)))

        # determine number of differential backups since last full backup
        count_diffs = 0
        if lastfull:
            diffbackups = [ s for s in struct if s[1] == lastfull[1] and s[2] == 'diff' ]
            count_diffs = len(diffbackups)

        # make this a differential backup if full backup exists and the number of differential 
        # backups is below --diffcount
        self.backup_type = 'diff'
        if not lastfull:
            self.backup_type = 'full'
            self.backup_nr = 1            
        else:
            self.backup_nr = lastfull[1]
            if count_diffs >= self.args.diffcount:
                self.backup_type = 'full'
                self.backup_nr = self.backup_nr + 1

        # create file name of backup        
        date = datetime.now()
        self.backup_file = os.path.join(self.args.backupdir, '{0}_{1}_b{2}_{3}_{4}.sna'.format(self.machine, self.drive, self.backup_nr, date.strftime(self.dateformat), self.backup_type))

        # create backup command line
        backup_cmd = [self.args.cmd, self.drive + ':', self.backup_file, '-W'] + snapshot_args

        # if diff backup add reference to hash file of full backup
        if self.backup_type == 'diff':
            logging.info('Performing differential backup based on hash file {0}.'.format(hshfile))
            backup_cmd = backup_cmd + [ '-h' + hshfile ]

        # exclude files 
        if self.args.exclude:
            # merge exclude arguments into a single list
            excludes = [el for elements in self.args.exclude for el in elements]
            exstr = string.join(map(lambda s: '"{0}"'.format(s) if '@' in s else s, excludes), ',')
            backup_cmd = backup_cmd + [ '--exclude:' + exstr ]

        # log to temp logfile
        with tempfile.NamedTemporaryFile(delete=False, suffix = ".log") as logfile:
            self.logfilename = logfile.name

        backup_cmd = backup_cmd + [ '--LogFile:' + self.logfilename ]
        
        self.backup_commandline = string.join(backup_cmd)
        logging.info("Executing: " + self.backup_commandline)

        # do it      
        if (not self.args.simulate):      
            self.returncode = subprocess.call(backup_cmd)
        else:
            self.returncode = 0

        with open(self.logfilename, 'r') as logfile:
            self.logtext = logfile.read()

        if self.returncode != 0:
            raise(ProgError('Snapshot returned with errorcode {0}!'.format(self.returncode)))

    def docleanup(self):
        # clean up old backups
        struct = self.get_existing_backups()

        now = datetime.now()
        delfiles = set()
        # delete differential backups older then x days
        if not self.args.deletediff is None:
            self.deletetime_diff = now - timedelta(days = self.args.deletediff)
            logging.info('Deleting differential backups <= {0}'.format(self.deletetime_diff))

            delfiles.update([ f for f in struct if f[2] == 'diff' and f[3] <= self.deletetime_diff ])

        # delete all backups older then x days
        if not self.args.delete is None:
            self.deletetime_all = now - timedelta(days = self.args.delete)
            logging.info('Deleting all backups <= {0}'.format(self.deletetime_all))

            delfiles.update([ f for f in struct if f[3] <= self.deletetime_all ])

            # do not delete full backups which have diff backups that are kept.
            keep_id = set([ f[1] for f in struct if not f in delfiles ])
            delfiles.difference_update([ f for f in delfiles if f[1] in keep_id and f[2] == 'full' ])

        delfiles = [ f[0] for f in delfiles ]

        # actually delete the files
        self.deleted_files = self.delete_backupfiles(delfiles)

    def mail(self, body):
        # mail the stuff
        if self.args.mail_to:
            msg = MIMEText(body, 'text')
            msg['Subject'] = '{0}Snapshot of {1} drive {2} {3}'.format('SIMULATED ' if self.args.simulate else '', self.machine, self.args.drive, 'FAILED' if self.failed else 'SUCCESSFULL')
            msg['From'] = self.args.mail_from
            msg['To'] = self.args.mail_to
            msg['Date'] = email.utils.formatdate(localtime=True)
            msg.add_header('X-SnapshotBackup', 'Yes')

            # force base64 encoding
            msg._headers = [h for h in msg._headers if h[0] != 'Content-Transfer-Encoding']
            email.encoders.encode_base64(msg)

            if (self.args.mail_ssl):
                server = smtplib.SMTP_SSL(self.args.mail_smtp)
            else:
                server = smtplib.SMTP(self.args.mail_smtp)

            if self.args.mail_debug:
                server.set_debuglevel(1)

            # log in, if credentials are given
            if self.args.mail_user != None or self.args.mail_password != None:
                server.login(self.args.mail_user, self.args.mail_password)

            try:
                server.sendmail(self.args.mail_from, self.args.mail_to, msg.as_string())
            finally:
                server.quit()

    def execute(self):
        # We catch any exceptions during backup and cleanup and 
        # add that to the mail.
        try:
            # execute snapshot backup
            self.dobackup()

            # perform cleanup
            self.docleanup()
        except (KeyboardInterrupt, SystemExit):    
            raise
        except Exception, ex:
            logging.exception(ex.message)
            self.exception = traceback.format_exc()
            self.failed = True

        if self.logfilename:
             os.remove(self.logfilename)

        # gather information into readable form
        body = ''
        if self.args.simulate:
            body = body + 'Simulation:     YES\n'
        if self.machine:
            body = body + 'Machine:        {0}\n'.format(self.machine)
        if self.drive:
            body = body + 'Drive:          {0}\n'.format(self.drive)
        if self.backup_type:
            body = body + 'Backup Type:    {0}\n'.format(self.backup_type)
        if self.backup_nr:
            body = body + 'Backup Number:  {0}\n'.format(self.backup_nr)
        if self.backup_file:
            body = body + 'Backup File:    {0}\n'.format(self.backup_file)
        if self.backup_commandline:
            body = body + 'Backup Command: {0}\n'.format(self.backup_commandline)
        if not self.returncode is None:
            body = body + 'Return Value:   {0}\n'.format(self.returncode)
        if self.exception:
            body = body + '\nException:\n{0}\n'.format(self.exception)
        if self.logtext:
            body = body + '\nOutput of snapshot:{0}\n'.format(self.logtext)

        if self.deletetime_all or self.deletetime_diff:
            body = body + '\nCLEANUP:\n'
            if self.deletetime_all:
                body = body + 'Deleted all backups <= {0}\n'.format(self.deletetime_all.strftime("%x %X"))
            if self.deletetime_diff:
                body = body + 'Deleted differental backups <= {0}\n'.format(self.deletetime_diff.strftime("%x %X"))

            body = body + 'Deleted files:\n'
            for f in self.deleted_files:
                body = body + '    {0}\n'.format(f)

        logging.info('\n' + body)

        self.mail(body)

        logging.info("Finished!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # paths
    parser.add_argument('backupdir', help='directory containing the backup files')
    parser.add_argument('drive', help='drive to back up. e.g. C:')

    # general options
    parser.add_argument('--cmd', default='snapshot.exe', help='Path for snapshot binary snapshot64.exe or snapshot.exe.')
    parser.add_argument('--diffcount', type=int, default=0, metavar='X', help='Create X differential backups after every full backup. 0 = only full backups.')
    parser.add_argument('--exclude', nargs='*', action='append', help='Excludes given file(s) or folder(s)')
    parser.add_argument('--argsfile', '-af', metavar='ARGS_FILE', help='Additional command line arguments for snapshot are read form this file. If not specified, the following arguments are used by default: --CreateDir --AutoBackupSize:512 -L0 -Gx -W.')
    parser.add_argument('--simulate', action='store_true', help='Does not call snapshot nor deletes any files. All messages are printed and mail is sent.')
    parser.add_argument('--delete', '-d', type=int, metavar='DAYS', help='Delete all backups which are older then DAYS days. Full backups are not deleted if there are any differential backups depending on them which are kept.')
    parser.add_argument('--deletediff', '-dd', type=int, metavar='DAYS', help='Delete differential backups which are older then DAYS days.')

    # mail options
    mailgroup = parser.add_argument_group('mail options')
    mailgroup.add_argument('--mail-to', help='Mail address for status mail.')
    mailgroup.add_argument('--mail-from', help='Sender mail address for mail. Required if --mail_to is specified.')
    mailgroup.add_argument('--mail-smtp', help='Smtp server for mailing. Required if --mail_to is specified.')
    mailgroup.add_argument('--mail-ssl', help='Use SSL (port 465) for sending mail.', action='store_true')
    mailgroup.add_argument('--mail-user', help='User for mailing if authentication is needed.')
    mailgroup.add_argument('--mail-password', help='User  for mailing if authentication is needed.')
    mailgroup.add_argument('--mail-debug', help='Outputs  messages for debugging mail issues.', action='store_true')
    args = parser.parse_args()

    if args.mail_to:
        argerr = []
        if not args.mail_from:
            argerr = argerr + ['The argument mail_from is missing.']
        if not args.mail_smtp:
            argerr = argerr + ['The argument mail_smtp is missing.']

        if len(argerr) > 0:
            parser.print_help()
            sys.stderr.write('\n{0}\n'.format(string.join(argerr, '\n')))
            os._exit(1)

    snapshot = snapshot(args)
    snapshot.execute()
