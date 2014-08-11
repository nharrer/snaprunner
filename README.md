snaprunner
==========

A python wrapper for [Drive Snapshot](http://www.drivesnapshot.de/en/).

Drive Snapshot is simple but effective backup tool for creating image backups. 

`snaprunner` is a command line utility which itself calls the Drive Snapshot executable. It adds certain features which Drive Snapshot is missing and which are especially usefull for scheduled backup scenarios.


Features
--------
- Alternately creates full and differential backups in certain intervals.
- Clean up of either differential and or full backups which are older then a given amount of days.
- Status mail upon successful/failed backup runs.
- Automatically creates meaningfull backup file names by including machine, drive, date/time and backup generation count.

Issues
------
- Does not support backing up multiple drives in a single snapshot (e.g. C:+D:).
- So far no installer/standalone version. Script only, so python has to be installed.

Requirements
------------

Python 2.x has to be installed.

Example
-------

NOTE: If python.exe is not set in PATH, use full path of python.exe (e.g. C:\python27\python.exe).


    python.exe snaprunner.py "\\10.0.0.200\Public\backups\" C: --diffcount 10 --cmd C:\devtools\Snapshot\snapshot.exe --exclude \Sandbox --mail_to nobody@fakemail.com --mail_from "snapshot <root@fakemail.com>" --mail_smtp mail.com

- Creates a backup of drive C: to directory `\\10.0.0.200\Public\backups\` 
- Creates a full backup after every 10th differential backup
- Expects snapshot.exe in `C:\devtools\Snapshot\snapshot.exe`
- Excludes the Directory `C:\Sandbox`
- Success/Fail-Mail is sent to `nobody@fakemail.com` via SMTP Server `mail.com`


    python.exe snaprunner.py "\\10.0.0.200\Public\backups\" C: --diffcount 10 --cmd C:\devtools\Snapshot\snapshot.exe -dd 60 -d 90 --exclude \Sandbox --mail_to nobody@fakemail.com --mail_from "snapshot <root@fakemail.com>" --mail_smtp mail.com

- Same as above but with clean up:
- `-dd 60` Deletes differential backups after 60 days.
- `-d 90` Deletes all backups after 90 days

Usage
-----

    usage: snaprunner.py [-h] [--cmd CMD] [--diffcount X]
                         [--exclude [EXCLUDE [EXCLUDE ...]]]
                         [--argsfile ARGS_FILE] [--simulate] [--delete DAYS]
                         [--deletediff DAYS] [--mail_to MAIL_TO]
                         [--mail_from MAIL_FROM] [--mail_smtp MAIL_SMTP]
                         backupdir drive
    
    positional arguments:
      backupdir             directory containing the backup files
      drive                 drive to back up. e.g. C:
    
    optional arguments:
      -h, --help            show this help message and exit
      --cmd CMD             Path for snapshot binary snapshot64.exe or
                            snapshot.exe. (default: snapshot.exe)
      --diffcount X         Create X differential backups after every full backup.
                            0 = only full backups. (default: 0)
      --exclude [EXCLUDE [EXCLUDE ...]]
                            Excludes given file(s) or folder(s) (default: None)
      --argsfile ARGS_FILE, -af ARGS_FILE
                            Additional command line arguments for snapshot are
                            read form this file. If not specified, the following
                            arguments are used by default: --CreateDir
                            --AutoBackupSize:512 -L0 -Gx -W. (default: None)
      --simulate            Does not call snapshot nor deletes any files. All
                            messages are printed and mail is sent. (default:
                            False)
      --delete DAYS, -d DAYS
                            Delete all backups which are older then DAYS days.
                            Full backups are not deleted if there are any
                            differential backups depending on them which are kept.
                            (default: None)
      --deletediff DAYS, -dd DAYS
                            Delete differential backups which are older then DAYS
                            days. (default: None)
    
    mail options:
      --mail_to MAIL_TO     Mail address for status mail. (default: None)
      --mail_from MAIL_FROM
                            Sender mail address for mail. Required if --mail_to is
                            specified. (default: None)
      --mail_smtp MAIL_SMTP
                            Smtp server for mailing. Required if --mail_to is
                            specified. (default: None)

