FTP Searcher
=========
![GitHub](https://img.shields.io/github/license/Sunlight-Rim/FTPSearcher?color=green)

**FTP Searcher** is an asynchronous file scanner on FTP servers list/IP range by queries or filetypes with recording the results to a file as a set of links.

![Terminal record](terminal.png)

Features
--------
Unlike other existing FTP crawlers and scanners that use threading, it uses asyncio as concurrency implementation because it's better suited for tasks that can implies slow I/O bound and multiple/unlimited quantity of connections. Also, there used a four types of requests: MLSD/LIST (asynchronous aioftp) in the main and MLSD/NLST (ftplib with multithreading) as a reserve method for some servers.

Installation
--------

```
git clone https://github.com/Sunlight-Rim/FTPSearcher.git
cd FTPSearcher
pip3 install -r requirements.txt
```

Usage
--------

```
ftpsearcher.py [-h] [-l LIST] [-f HOSTS [HOSTS ...]] [-ip RANGE] [-r RESULT] [-q OBJ [OBJ ...]] [-A] [-i] [-v] [-a] [-d] [-z] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -l LIST               Path to txt file with FTP target list in form 'host:port' (ftplist.txt by default). [as default target]
  -f HOSTS [HOSTS ...]  Single or some target FTP with the input data as 'host:port'.
  -ip RANGE             Target IP range as 'start-end:port'.
  -r RESULT             Path to html-file for saving results (results.html by default). To canceling writing to the file, enter '-r N'.
  -q OBJ [OBJ ...]      Queries to search substrings into filenames.
  -A, --all             Search all files. [as default query]
  -i, --images          Search only by images (jpg, jpeg, png, gif, svg, bmp, tif/tiff, psd, xcf).
  -v, --videos          Search only by videos (mp4, mov, avi, webm, 3gp/3gpp).
  -a, --audios          Search only by audios (mp3, ogg, wav, aif, ape, flac).
  -d, --docs            Search only by docs (doc, docx, pdf, epub, fb2).
  -z, --zip             Search only by zip or other archive formats (zip, rar, 7z, tar, tar.gz, cab).
  -s, --sync            Use only synchronous requests.

rest in pantene
```

If you don't explicitly specify the port, port 21 will be used by default.\
The result file is overwritten each time you start the search, unless you specify a file different from the previous one or use '-r N' flag.\
Attention: some poorly configured FTP can't be used with concurrency methods; therefore, in such situations you can prefer to use only synchronous mode (flag '-s').

Examples
--------
Search by query on single FTP with port 20 and don't write results into a file.
```
python3 ftpsearcher.py -f exampleftp.org:20 -r N -q ozone_smell.epub
```

Search images on FTP list in /home/rim/target_place.txt and record results to results_place.html located in the program folder.
```
python3 ftpsearcher.py -l /home/rim/target_place.txt -r results_place.html -i
```

Search on range of 254 addresses eith 21 port by two queries and don't write results.
```
python3 ftpsearcher.py -ip 127.0.0.0-127.0.0.255 -q fairytales.pdf electric_transmission.json -r N
```

Scan all files on FTP from ftplist.txt and write results to results.html.
```
python3 ftpsearcher.py
```

![speed](seconds.png)

--------

Current Release: ver. 1.0 (2020.12.03)
