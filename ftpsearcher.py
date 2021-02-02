import argparse
import os
import asyncio
import aioftp
import threading
import socket
import async_timeout
from os import environ
from socket import gaierror
from ftplib import FTP, error_perm
from colorama import Fore, Style, init

def get_args():
    print("ver. 1.1\n")
    parser = argparse.ArgumentParser(epilog="rest in pantene")
    parser.add_argument("-l", type=str, dest="list", default="ftplist.txt",
            help="Path to txt file with FTP target list in form 'host:port' (ftplist.txt by default).")
    parser.add_argument("-f", type=str, dest="hosts", default=False, nargs="+",
            help="Single or some target FTP with the input data as 'host:port'.")
    parser.add_argument("-ip", dest="range", type=str, default=False,
            help="Target IP range as 'start-end:port'.")
    parser.add_argument("-r", dest="result", type=str, default="results.html",
            help="Path to html-file for saving results (results.html by default). Enter '-r N' to cancel.")
    parser.add_argument("-q", dest="obj", type=str, default="", nargs="+",
            help="Queries to search substrings into filenames.")
    parser.add_argument("-d", "--download", dest="download", action="store_true", default=False,
            help="Automatically downloads all the find files to the /downloads/ folder.")
    parser.add_argument("-nd", "--nodisplay", dest="display", action="store_false", default=True,
            help="Do not display servers that are not responding in the terminal log.")
    parser.add_argument("-A", "--all", dest="obj", action="store_const", const="", default="",
            help="Search all files.")
    parser.add_argument("-img", "--images", dest="extns", action="store_const", const=('.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.tif', '.tiff', '.psd', '.xcf'), default=False,
            help="Search only by images (jpg, jpeg, png, gif, svg, bmp, tif/tiff, psd, xcf).")
    parser.add_argument("-vid", "--videos", dest="extns", action="store_const", const=('.mp4', '.mov', '.avi', '.webm', '.3gp', '.3gpp'), default=False,
            help="Search only by videos (mp4, mov, avi, webm, 3gp/3gpp).")
    parser.add_argument("-aud", "--audios", dest="extns", action="store_const", const=('.mp3', '.ogg', '.wav', '.aif', '.ape', '.flac'), default=False,
            help="Search only by audios (mp3, ogg, wav, aif, ape, flac).")
    parser.add_argument("-doc", "--docs", dest="extns", action="store_const", const=('.doc', '.docx', '.pdf', '.epub', '.fb2'), default=False,
            help="Search only by docs (doc, docx, pdf, epub, fb2).")
    parser.add_argument("-zip", "--archives", dest="extns", action="store_const", const=('.zip', '.rar', '.7z', '.tar', '.tar.gz', '.cab'), default=False,
            help="Search only by archives (zip, rar, 7z, tar, tar.gz, cab).")
    parser.add_argument("-s", "--sync", dest="sync", action="store_true", default=False,
            help="Use only synchronous requests.")
    return parser.parse_args()

# searching for a file by filetype with a param or by a substring of an object with a query.
def searching(name, pathlist, ftp):
    full_path = "/".join(filter(None, pathlist)) + "/" + name
    full_path = full_path.encode('cp1252').decode('cp1251')
    global syncnumber
    syncnumber += 1
    if args.extns != False:
        for extension in args.extns:
            if full_path.endswith(extension):
                results(full_path, syncnumber)
                syncdownload(name, full_path, ftp) if args.download else None
    elif args.obj == '':
        results(full_path, syncnumber)
        syncdownload(name, full_path, ftp) if args.download else None
    else:
        for object in args.obj:
            if object in full_path.split("/")[-1]:
                results(full_path, syncnumber)
                syncdownload(name, full_path, ftp) if args.download else None

def syncdownload(name, full_path, ftp):
    try:
        print(full_path + Fore.GREEN + " downloading...")
        download_folder = os.path.join(r"download", name)
        fsea = open(download_folder, "wb")
        ftp.retrbinary("RETR " + name, fsea.write, 8*1024)
        fsea.close()
        print(Fore.GREEN + "Ok.")
    except KeyboardInterrupt:
        print(Fore.RED + "\nYou have interrupted file downloading.")
        pass
# ----------------------------------SYNCHRONOUS BLOCK-------------------------------------------------------------------
# recursively checking all directories that are not files using the MLSD-method, if it can be used.
def cycle_inner(folder, ftp, pathlist):
    ftp.cwd(folder)
    pathlist.append(folder)
    for data in ftp.mlsd():
        type = data[1].get('type')
        if data[0] != '.' and  data[0] != '..':
            if type != 'dir':
                searching(data[0], pathlist, ftp)
            elif type == 'dir':
                try:
                    cycle_inner(data[0], ftp, pathlist)
                    ftp.sendcmd('cdup')
                    pathlist.pop() if len(pathlist) > 1 else None
                except error_perm:
                    print(Fore.YELLOW + "Cannot open the folder " + Fore.WHITE + data[0])
                    results(data[0], -3)
                    ftp.sendcmd('cdup')
                    pathlist.pop() if len(pathlist) > 1 else None

# recursively checking all files and directories together using the NLST-method, if MLSD is not supported on the server.
def badftp_cycle(maybe_folder, ftp, pathlist):
    ftp.cwd(maybe_folder)
    pathlist.append(maybe_folder)
    if len(ftp.nlst()) >= 1:
        for isitafolder in ftp.nlst():
            try:
                badftp_cycle(isitafolder, ftp, pathlist)
                ftp.sendcmd('cdup')
                pathlist.pop() if len(pathlist) > 1 else None
            except error_perm:
                searching(isitafolder, pathlist, ftp)
                continue
    else:
        ftp.sendcmd('cdup')
        pathlist.pop() if len(pathlist) > 1 else None

# connecting to FTP with ftplib.
def connect(host, cnct_port):
    print(Fore.GREEN + "Now it's " + Fore.WHITE + host + Fore.GREEN + " with synchronous MLSD.")
    host_port = host + ":" + str(cnct_port)
    pathlist = [host_port]
    try:
        ftp = FTP(host, timeout=10)
        ftp.connect(port=cnct_port)
        ftp.login()
        global syncnumber
        syncnumber = 0
        try:
            cycle_inner("", ftp, pathlist)
        except KeyboardInterrupt:
            print(Fore.RED + "\nYou have interrupted folder scanning. Move back to the parent directory.")
            ftp.sendcmd('cdup')
            pathlist.pop()
        except error_perm as msg:
            if msg.args[0][:3] == '500':
                print(Fore.GREEN + "MLSD is not supported on server " + Fore.WHITE + host + Fore.GREEN + ". Trying to use synchronous NLST.")
                badftp_cycle("", ftp, pathlist)
        print(host + Fore.GREEN + " was getted.")
        ftp.quit()
    except OSError as oerr:
        if str(oerr) == "timed out":
            print(host + Fore.RED + " does not keep a stable connection. Try to run this one separately or later?")
            results(host, -2)
    except EOFError:
        print(Fore.RED + "Server sent a reset package.")
    except error_perm as msg:
        if msg.args[0][:3] != '530':
            print(Fore.GREEN + "Login authentication failed onto " + Fore.WHITE + host + ":" + str(cnct_port))
            results(host, -1)
        else:
            print(msg.args[0][:3])
    except KeyboardInterrupt:
        print(Fore.RED + "\nYou have interrupted folder scanning. Move back to the parent directory.")
        ftp.sendcmd('cdup')
        pathlist.pop()

# --------------------------------ASYNCHRONOUS BLOCK--------------------------------------------------------------------
# aioftp connecting and checking.
async def asyncgetting(host, port, command, asyncnumber):
    try:
        client = aioftp.Client()
        async with async_timeout.timeout(7):
            await client.connect(host, port)
            await client.login()
        print(host + Fore.GREEN + " started with asynchronous method: " + Fore.WHITE + command)
        try:
            async for path, info in client.list(recursive=True, raw_command=command):
                if info["type"] == "file":
                    if args.extns != False:         # for extensions.
                        for extension in args.extns:
                            if str(path).endswith(extension):
                                asyncnumber += 1
                                await asyncpreresults(host, port, path, asyncnumber)
                    elif args.obj == '':            # for --all.
                        asyncnumber += 1
                        await asyncpreresults(host, port, path, asyncnumber)
                    elif args.obj != '':
                        for object in args.obj:     # for query.
                            if object in str(path).split("/")[-1]:
                                asyncnumber += 1
                                await asyncpreresults(host, port, path, asyncnumber)
                elif info["type"] == "dir":
                    full_path = str(host) + ":" + str(port) + "/" + str(path)
                    results(full_path, 0)
            print(host + Fore.GREEN + " was getted.")

# exception handling.
        except aioftp.StatusCodeError as inerr:
            if str(inerr.received_codes) == "('500',)":
                if str(inerr.info) == "[' Unknown command.']":
                    print(Fore.GREEN + "MLSD is not supported on server " + Fore.WHITE + host + ":" + str(port) + Fore.GREEN + ". Trying to use asynchronous LIST.")
                    await asyncgetting(host, port, 'LIST', 0)
                elif "not underst" in str(inerr.info):
                    print(Fore.GREEN + "Asynchronous methods is not available on server " + Fore.WHITE + host + ":" + str(port) + Fore.GREEN + ". Trying to use synchronous MLSD.")
                    t = threading.Thread(target=connect, name="Thread " + host + str(port), args=(host, port))
                    thread_list.append(t)
                    t.start()
                else:
                    print(inerr)
            elif str(inerr.received_codes) == "('550',)":
                print(Fore.GREEN + "Error 550 (Can't check for file existence) with server " + Fore.WHITE + host + ":" + str(port) + Fore.GREEN + ". Trying to use synchronous MLSD.")
                t = threading.Thread(target=connect, name="Thread " + host + str(port), args=(host, port))
                thread_list.append(t)
                t.start()
            elif "Waiting for ('1xx',) but got 501" in str(inerr):
                print(Fore.GREEN + "Error 501 (Not a directory) with server " + Fore.WHITE + host + ":" + str(port) + Fore.GREEN + ". Trying to use synchronous MLSD.")
                t = threading.Thread(target=connect, name="Thread " + host + str(port), args=(host, port))
                thread_list.append(t)
                t.start()
            else:
                print(inerr)
    except aioftp.StatusCodeError as exerr:
        if str(exerr.received_codes) == "('530',)":
            print(Fore.GREEN + "Login authentication failed onto " + Fore.WHITE + host + ":" + str(port))
            results(host, -1)
        else:
            print(exerr)
    except ConnectionResetError:
        print(host + ":" + str(port) + Fore.RED + " sent a reset package.")
    except gaierror:
        print(host + ":" + str(port) + Fore.RED + " not responding.") if args.display else None
    except asyncio.TimeoutError:
        print(host + ":" + str(port) + Fore.RED + " not responding.") if args.display else None
    except OSError as oerr:
        if str(oerr) == "timed out":
            print(host + ":" + str(port) + Fore.RED + " not responding.") if args.display else None
        elif "[Errno 111] Connect call failed" in str(oerr):
            print(host + ":" + str(port) + Fore.RED + " not responding (error 111).") if args.display else None
        elif "[Errno 113] Connect call failed" in str(oerr):
            print(host + ":" + str(port) + Fore.RED + " not responding (error 113).") if args.display else None
        elif "[Errno 101] Connect call failed" in str(oerr):
            print(host + ":" + str(port) + Fore.RED + " not responding (error 101).") if args.display else None
        elif str(oerr) == "[Errno 24] Too many open files":
            print("The range is too large. Try to specify less?")
        else:
            print(oerr)
    except KeyboardInterrupt:
        print(Fore.RED + "\nYou have interrupted host scanning. Move to the next one.")

# ----------------------------------------------------------------------------------------------------------------------
# opening FTP from the list.
def unpack_list(list):
    try:
        flist = open(list, "r")
        liststr = flist.read().split('\n')
        if args.sync:
            for string in liststr:
                if string != "":
                    host, *port = string.split(":")
                    port = ([int(port) for port in port]) if port != [] else [21]
                    connect(host, *port)
        else:
            global tasks_list
            tasks_list = [[]]
            for string in liststr: # repetition to decrease O(n).
                if string != "":
                    host, *port = string.split(":")
                    port = ([int(port) for port in port]) if port != [] else [21]
                    tasks_list = [0].append(asyncgetting(host, *port, "MLSD", 0))
        flist.close()
    except FileNotFoundError:
        print(Fore.RED + "File " + Fore.WHITE + list + Fore.RED + " not found.")
    except PermissionError:
        print(Fore.RED + "Unable to open results file, but file " + Fore.WHITE + list + Fore.RED + " was found. Check your privileges.")

# opening FTP from ip-range.
def unpack_range(range_port):
    import ipaddress
    import struct
    global tasks_list
    tasks_list = []
    iprange, *port = range_port.split(':')
    port = ([int(port) for port in port]) if port != [] else [21]
    try:
        start, end = iprange.split('-')
        start = struct.unpack('>I', socket.inet_aton(start))[0]
        end = struct.unpack('>I', socket.inet_aton(end))[0]
        hosts = [socket.inet_ntoa(struct.pack('>I', i)) for i in range(start, end)]

# division a range by blocks with 1000 hosts to bypass aioftp connection error [Errno 24].
        [tasks_list.append([]) for _ in range(int(len(hosts) / 1000) + 1)]
        if args.sync:
            for host in hosts:
                connect(host, *port)
        else:
            for task in range (len(tasks_list)):
                while len(hosts) != 1:
                    if len(tasks_list[task]) <= 999:
                        tasks_list[task].append(asyncgetting(hosts.pop(0), *port, "MLSD", 0))
                    else:
                        break
    except ValueError as verr:
        print(Fore.RED + "IP range must be separeted by '-' character.") if "not enough values to unpack" in str(verr) else None
    except OSError as oerr:
        print(Fore.RED + "Illegal IP address string passed in range.") if "illegal IP address string passed to inet_aton" in str(oerr) else None

# ----------------------------------------------------------------------------------------------------------------------

async def asyncpreresults(host, port, path, asyncnumber):
    full_path = str(host) + ":" + str(port) + "/" + str(path)
    results(full_path, asyncnumber)
    if args.download:
        try:
            client2 = aioftp.Client()
            await client2.connect(host, port)
            await client2.login()
            print(full_path + Fore.GREEN + " downloading...")
            print("download/" + host + "/" + str(path))
            await client2.download(path, "download/" + host + "/" + str(path), write_into=True)
        except aioftp.errors.PathIOError:
            print(Fore.RED + "Unable to download files into \"download\" folder. Check out your privileges.")

# writing results to file and console.
def results(full_path, number):
    print(str(number) + ". " + full_path) if number > 0 else print(full_path) if number == 0 else None
    if args.result != "N":
        try:
            fres = open(args.result, 'a')
            if number > 0:
                fres.write("<a href='ftp://" + full_path + "'>" + str(number) + ". " + full_path + "</a><br>\n")
            elif number == 0:
                fres.write("<a href='ftp://" + full_path + "'>" + full_path + "</a><br>\n")
            elif number == -1:
                fres.write("Login authentication failed onto " + full_path + "<br>\n")
            elif number == -2:
                fres.write(full_path + " does not keep a stable connection. Try to run this separately or later?<br>\n")
            elif number == -3:
                fres.write("Cannot open the folder " + full_path + "<br>\n")
            fres.close
        except FileNotFoundError:
            print(Fore.RED + "File" + Fore.WHITE + args.result + Fore.RED + " not found.")
        except PermissionError:
            print(Fore.RED + "Unable to add string into results file, but file " + Fore.WHITE + args.result + Fore.RED + " was found. Check out your privileges.")

# ----------------------------------------------------------------------------------------------------------------------

def main():
    program_banner = open(os.path.join("banner_android.txt")).read() if 'ANDROID_STORAGE' in environ else open(os.path.join("banner.txt")).read()
    init(autoreset = True)
    print(Fore.YELLOW + Style.BRIGHT + program_banner)
    global args
    args = get_args()
    global thread_list
    thread_list = []
    global port
    global tasks_list
    if args.result != "N":
        try:
            frw = open(args.result, 'w')
            frw.close
        except FileNotFoundError:
            print(Fore.RED + "File " + Fore.WHITE + args.result + Fore.RED + " not found.")
        except PermissionError:
            print(Fore.RED + "Unable to open results file, but file " + Fore.WHITE +  args.result + Fore.RED + " was found. Check your privileges.")
    if args.hosts != False: # for single or some target FTP.
        args.list = False
        print(Style.DIM + str(args)[10:-1] + "\n")
        if args.sync:
            for host_port in args.hosts:
                host, *port = host_port.split(":")
                port = ([int(port) for port in port]) if port != [] else [21]
                connect(host, *port)
        else:
            tasks_list = [[]]
            for host_port in args.hosts: # repetition to decrease O(n).
                host, *port = host_port.split(":")
                port = ([int(port) for port in port]) if port != [] else [21]
                tasks_list[0].append(asyncgetting(host, *port, "MLSD", 0))
    elif args.range != False: # for IP range.
        args.list = False
        print(Style.DIM + str(args)[10:-1] + "\n")
        unpack_range(args.range)
    else: # for the list in file.
        print(Style.DIM + str(args)[10:-1] + "\n")
        unpack_list(args.list)
    if args.sync == False:
        ioloop = asyncio.get_event_loop()

        try:
            for tasks in tasks_list:
                ioloop.run_until_complete(asyncio.gather(*tasks))
                [t.join() for t in thread_list if thread_list != []]

            print(Fore.YELLOW + Style.BRIGHT + "Connections completed.")
        except KeyboardInterrupt:
            print(Fore.RED + "\nYou have interrupted the FTP Searcher.")
        except NameError:
            pass

        ioloop.close()

if __name__ == '__main__':
    main()
