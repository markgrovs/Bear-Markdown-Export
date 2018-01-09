# bear_export.py
'''
Markdown export from Bear sqlite database 
github/rovest, rorves@twitter: 2018-01-08 at 21:01 EST
'''

import sqlite3
import datetime
import re
import subprocess
import os
import shutil

HOME = os.getenv('HOME', '')

export_path = os.path.join(HOME, 'Dropbox', 'Bear Export')
# export_path = os.path.join(HOME, 'OneDrive', 'Bear Export')

temp_path = os.path.join(HOME, 'Temp', 'BearExportTemp') # NOTE! Do not change the "BearExportTemp" folder name!!!

# time_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")

bear_db = os.path.join(HOME, 'Library/Containers/net.shinyfrog.bear/Data/Documents/Application Data/database.sqlite')

conn = None


def main():
    global conn
    clean_old_files()
    conn = sqlite3.connect(bear_db)
    conn.row_factory = sqlite3.Row
    get_markdown()
    conn.close()
    sync_files()


def get_markdown():
    query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0'"
    c = conn.execute(query)
    for row in c:
        title = row['ZTITLE']
        md_text = row['ZTEXT']
        creation_date = row['ZCREATIONDATE']
        modified = row['ZMODIFICATIONDATE']
        filename = clean_title(title) + date_time_conv(creation_date) + '.md'
        filepath = os.path.join(temp_path, filename)
        mod_dt = dt_conv(modified)
        write_file(filepath, md_text, mod_dt)
        #print(date_time_conv(creation_date))


def clean_title(title):
    title = title[:56]
    title = re.sub(r'[/\\*?$@!^&\|~:]', r'-', title)
    title = re.sub(r'-$', r'', title)    
    return title.strip()


def write_file(filename, file_content, modified):
    f = open(filename, "w", encoding='utf-8')
    f.write(file_content)
    f.close()
    if modified > 0:
        os.utime(filename, (-1, modified))


def dt_conv(dtnum):
    # Formula for date offset based on trial and error:
    hour = 3600 # seconds
    year = 365.25 * 24 * hour
    offset = year * 31 + hour * 6
    return dtnum + offset


def date_time_conv(dtnum):
    newnum = dt_conv(dtnum) 
    dtdate = datetime.datetime.fromtimestamp(newnum)
    #print(newnum, dtdate)
    return dtdate.strftime(' - %Y-%m-%d_%H%M') 


def date_conv(dtnum):
    dtdate = datetime.datetime.fromtimestamp(dtnum)
    return dtdate.strftime('%Y-%m-%d')


def clean_old_files():
    # Move all markdown files to temp folder using rsync:
    if os.path.exists(temp_path) and "BearExportTemp" in temp_path:
        # *** NOTE! Double checking that temp_path folder contains "BearExportTemp"
        # *** Otherwise if accidentally empty or root,
        # *** shutil.rmtree() will delete all files on your complete Hard Drive!!
        shutil.rmtree(temp_path)
        # *** NOTE: USE rmtree() WITH EXTREME CAUTION!
    os.makedirs(temp_path)


def sync_files():
    # Move all markdown files to new folder using rsync:
    if not os.path.exists(export_path):
        os.makedirs(export_path)
    subprocess.call(['rsync', '-r', '-t', '--delete',
                     temp_path + "/", export_path])


if __name__ == '__main__':
    main()
