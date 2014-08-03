# Creates a bunch of empty test files which come in handy for testing the cleanup feature.

from datetime import datetime, timedelta, date
import os 

dir = 'F:\\backup_test'
today = datetime.today()
dateformat = '%Y%m%d-%H%M%S'

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

cnt = 0
nr = 0
for i in reversed(list(xrange(100))):
    day = today - timedelta(days = i)

    type = 'diff'
    if (cnt % 5 == 0):
        type = 'full'
        nr = nr + 1
    cnt = cnt + 1

    base = os.path.join(dir, 'firebird_g_b{0}_{1}_{2}.'.format(nr, day.strftime(dateformat), type))

    touch(base + 'sna')
    touch(base + 'sn1')
    if type == 'full':
        touch(base + 'hsh')
