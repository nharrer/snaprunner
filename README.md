snaprunner
==========

A python wrapper for [Drive Snapshot](http://www.drivesnapshot.de/en/).

Drive Snapshot is a simple but effective backup tool for creating image backups.

`snaprunner` is a command line utility which itself calls the Drive Snapshot executable. It adds certain features which Drive Snapshot is missing and which are especially useful for scheduled backup scenarios.


Project Home
------------

[Project snaprunner](http://www.netzgewitter.com/projects/snaprunner/).


Features
--------
- Alternately creates full and differential backups in certain intervals.
- Clean-up of either differential and or full backups which are older than a given amount of days.
- Status mail upon successful/failed backup runs.
- Automatically creates meaningful backup file names by including machine, drive, date/time and backup generation count.
- Provides simulation of backup and clean-up.

Issues
------
- Does not support backing up multiple drives in a single snapshot (e.g. C:+D:).
- So far no installer/standalone version. Script only, so python has to be installed.

Requirements
------------

Python 2.x has to be installed.

Example 1
---------

    python.exe snaprunner.py "\\10.0.0.200\Public\backups\" C: --diffcount 10 --cmd C:\devtools\Snapshot\snapshot.exe --exclude \Sandbox --mail_to nobody@fakemail.com --mail_from "snapshot <root@fakemail.com>" --mail_smtp mail.com

- Creates backups of drive C: in directory `\\10.0.0.200\Public\backups\` 
- Creates a full backup after every 10th differential backup
- Expects snapshot.exe in `C:\devtools\Snapshot\snapshot.exe`
- Excludes the Directory `C:\Sandbox`
- Success/Fail-Mail is sent to `nobody@fakemail.com` via SMTP Server `mail.com`

NOTE: If python.exe is not set in PATH, use the full path (e.g. C:\python27\python.exe).

NOTE: command lines like this are indented to be used in task scheduler to run hourly, daily, weekly etc.

Example 2
---------

    python.exe snaprunner.py "\\10.0.0.200\Public\backups\" C: --diffcount 10 --cmd C:\devtools\Snapshot\snapshot.exe -dd 60 -d 90 --exclude \Sandbox --mail_to nobody@fakemail.com --mail_from "snapshot <root@fakemail.com>" --mail_smtp mail.com

- Same as example 1 but with clean up:
 - `-dd 60` Deletes differential backups older then 60 days.
 - `-d 90` Deletes all backups older then 90 days.


NOTE: -d does never delete full backups if there are any differential backups which are not deleted and which depend on the full backup.

NOTE: Use option `--simulate` if you are unsure about the delete options. `--simulate` does neither create a backup nor deletes any files. A status mail is created however.

Usage
-----

    usage: snaprunner.py [-h] [--cmd CMD] [--diffcount X]
                         [--exclude [EXCLUDE [EXCLUDE ...]]]
                         [--argsfile ARGS_FILE] [--simulate] [--delete DAYS]
                         [--deletediff DAYS] [--mail-to MAIL_TO]
                         [--mail-from MAIL_FROM] [--mail-smtp MAIL_SMTP]
                         [--mail-ssl] [--mail-user MAIL_USER]
                         [--mail-password MAIL_PASSWORD] [--mail-debug]
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
      --mail-to MAIL_TO     Mail address for status mail. (default: None)
      --mail-from MAIL_FROM
                            Sender mail address for mail. Required if --mail_to is
                            specified. (default: None)
      --mail-smtp MAIL_SMTP
                            Smtp server for mailing. Required if --mail_to is
                            specified. (default: None)
      --mail-ssl            Use SSL (port 465) for sending mail. (default: False)
      --mail-user MAIL_USER
                            User for mailing if authentication is needed.
                            (default: None)
      --mail-password MAIL_PASSWORD
                            User for mailing if authentication is needed.
                            (default: None)
      --mail-debug          Outputs messages for debugging mail issues. (default:
                            False)
