# encoding=utf-8
# python3.6
# bear_export_sync.py

'''
# Markdown export from Bear sqlite database 
Version 0.04, 2018-01-11 at 05:59 EST
github/rovest, rorves@twitter

## Syncing external updates:

First checking for Changes in Markdown files (previously exported from Bear)
* Adding updated or new Notes to Bear with x-callback-url command
* Marking updated note with message and link to original note.
* Moving original note to trash (unless a sync conflict)
* Moving changed files to a "Sync Inbox" as a backup. 

Then exporting Markdown from Bear sqlite db.
* Uses rsync for copying, so only markdown files of changed sheets will be updated  
and synced by Dropbox (or other sync services)
'''

import sqlite3
import datetime
import re
import subprocess
import urllib.parse
import os
import time
import shutil
import fnmatch

HOME = os.getenv('HOME', '')

# export_path = os.path.join(HOME, 'Dropbox', 'Bear Notes')
export_path = os.path.join(HOME, 'OneDrive', 'Bear Notes')

sync_inbox = os.path.join(HOME, 'Temp', 'BearSyncInbox')
temp_path = os.path.join(HOME, 'Temp', 'BearExportTemp') # NOTE! Do not change the "BearExportTemp" folder name!!!
# time_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
bear_db = os.path.join(HOME, 'Library/Containers/net.shinyfrog.bear/Data/Documents/Application Data/database.sqlite')

conn = None


def main():
    global conn

    conn = sqlite3.connect(bear_db)
    conn.row_factory = sqlite3.Row
    check_for_md_updates(export_path, sync_inbox)
    time.sleep(2)
    clean_old_files()
    export_markdown()
    conn.close()

    write_time_stamp()
    sync_files()
    print('Export completed to:')
    print(export_path)
    notify('Export completed')


def export_markdown():
    query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0'"
    c = conn.execute(query)
    for row in c:
        title = row['ZTITLE']
        md_text = row['ZTEXT'].strip()
        creation_date = row['ZCREATIONDATE']
        modified = row['ZMODIFICATIONDATE']
        uuid = row['ZUNIQUEIDENTIFIER']
        filename = clean_title(title) + date_time_conv(creation_date) + '.md'
        filepath = os.path.join(temp_path, filename)
        mod_dt = dt_conv(modified)
        md_text += '\n\n{BearID:' + uuid + '}\n'
        write_file(filepath, md_text, mod_dt)


def write_time_stamp():
    # write to time-stamp.txt file (used during sync)
    write_file(os.path.join(temp_path, ".export-time.txt"),
               "Markdown from Bear written at: " +
               datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), 0)
    write_file(os.path.join(temp_path, ".sync-time.txt"),
               "Markdown from Bear written at: " +
               datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), 0)


# def hide_tags(md_text):
#     # Hide tags:
#     # return re.sub(r'\#([a-zA-Z])', r'@\1', md_text)
#     md_text =  re.sub(r'\#([\w]+)(?= )?', r'<!--#\1-->', md_text)
#     md_text = re.sub(r'\<\!--\#(.+?)--\>(.+?)\#(?=\n)', r'<!--#\1\2#-->', md_text)
#     return md_text


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


def read_file(file_name):
    f = open(file_name, "r", encoding='utf-8')
    file_content = f.read()
    f.close()
    return file_content


def get_file_date(filename):
    try:
        t = os.path.getmtime(filename)
        return t
    except:
        return 0


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


def time_stamp_ts(ts):
    dtdate = datetime.datetime.fromtimestamp(ts)
    return dtdate.strftime('%Y-%m-%d at %H:%M') 


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


def check_for_md_updates(md_path, sync_inbox):
    ts_file = os.path.join(md_path, ".sync-time.txt")
    files_found = False
    if not os.path.exists(ts_file):
        return False
    ts_last_export = os.path.getmtime(ts_file)
    for root, dirnames, filenames in os.walk(md_path):
        for filename in fnmatch.filter(filenames, '*.md'):
            md_file = os.path.join(root, filename)
            try:
                ts = os.path.getmtime(md_file)
            except:
                pass
            if ts > ts_last_export:
                files_found = True
                if not os.path.exists(sync_inbox):
                    os.makedirs(sync_inbox)
                synced_file = os.path.join(sync_inbox, filename)
                count = 2
                while os.path.exists(synced_file):
                    # Making sure no previous identical filename to prevent overwrite:
                    file_part = re.sub(r"(( - \d\d)?\.md)", r"", synced_file)
                    synced_file = file_part + " - " + str(count).zfill(2) + ".md"
                    count += 1
                md_text = read_file(md_file)
                ts = get_file_date(md_file)
                write_file(synced_file, md_text, ts)
                os.remove(md_file)
                print("*** File to md_sync_inbox: " + synced_file)
                update_bear_note(md_text, ts_last_export, ts)
                print("*** Bear Note Updated")
                
    # Finally, update synced timestamp file:
    write_file(os.path.join(md_path, ".sync-time.txt"),
               "Checked for Markdown updates to sync at: " +
               datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), 0)
    return files_found


def update_bear_note(md_text, ts_last_export, ts):
    uuid = ''
    match = re.search(r'\{BearID:(.+?)\}', md_text)
    if match:
        uuid = match.group(1)
        # Remove old BearID: from new note
        md_text = re.sub(r'\{BearID\:' + uuid + r'\}', '', md_text).rstrip() + '\n'

        sync_conflict = check_sync_conflict(uuid, ts_last_export)

        link_original = 'bear://x-callback-url/open-note?id=' + uuid
        if sync_conflict:
            message = '::[External update: Sync conflict with original note!!](' + link_original + ')::'
        else:
            message = '::[External update: Original note moved to trash.](' + link_original + ')::'        
        lines = md_text.splitlines()
        lines.insert(1, message)
        md_text = '\n'.join(lines)
    else:
        message = '::New external Note - ' + time_stamp_ts(ts) + '::'
        lines = md_text.splitlines()
        lines.insert(1, message)
        md_text = '\n'.join(lines)

    # Add remote update of note to Bear in any case: (if updated, new or sync conflict)
    x_create = 'bear://x-callback-url/create?show_window=no&text=' + urllib.parse.quote(md_text)
    subprocess.call(["open", x_create])
    time.sleep(.2)

    if match and not sync_conflict:
        # Trash old original note:
        x_trash = 'bear://x-callback-url/trash?show_window=no&id=' + uuid
        print(x_trash)
        subprocess.call(["open", x_trash])
        time.sleep(.2)


def check_sync_conflict(uuid, ts_last_export):
    conflict = False
    # Stub: Check modified date of original note in Bear sqlite db!
    query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0' AND `ZUNIQUEIDENTIFIER` LIKE '" + uuid + "'"
    c = conn.execute(query)
    for row in c:
        title = row['ZTITLE']
        modified = row['ZMODIFICATIONDATE']
        uuid = row['ZUNIQUEIDENTIFIER']
        mod_dt = dt_conv(modified)
        dtdate = datetime.datetime.fromtimestamp(mod_dt)
        print(dtdate.strftime('%Y-%m-%d %H:%M'))
        print(title, ts_last_export, mod_dt)
        conflict = mod_dt > ts_last_export
    return conflict


def notify(message):
    title = "ul_sync_md.py"
    try:
        # Uses "terminal-notifier", download at:
        # https://github.com/julienXX/terminal-notifier/releases/download/2.0.0/terminal-notifier-2.0.0.zip
        # Only works with MacOS 10.11+
        subprocess.call(['/Applications/terminal-notifier.app/Contents/MacOS/terminal-notifier',
                         '-message', message, "-title", title, '-sound', 'default'])
    except:
        print('* "terminal-notifier.app" is missing!')
    # print("* Message:", str(message.encode("utf-8")))
    return


if __name__ == '__main__':
    main()
