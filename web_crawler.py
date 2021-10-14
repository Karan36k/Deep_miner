import urllib.request
import re
import threading
import sys
from multiprocessing import Queue
from threading import Lock

tally = 1
iterate = 0
Anchor = False
mutex = Lock()


# The function that is there for the crawling purpose
def findkeywordlvl(strwebsiteinp, strmatch, queueget):
    global tally  # this variable is kept to kee record of how many positive results the crawler has sniffed so far
    global Anchor  # This variable is ketp as a flag that would raise the interrupt signal to terminate all the threads at once as soon as the total number of positive results is reached
    if Anchor == False:
        mutex.acquire()  # Mutex locking is acquired before the critical section
        if strmatch.startswith("src="):
            # The function is saving those strings that start with src or hrefs as in to save any links that are in the webpage
            strmatch = strmatch[5 : len(strmatch)]
        elif strmatch.startswith("href="):
            strmatch = strmatch[6 : len(strmatch)]
        mutex.release()  # Mutex locking is acquired before the critical section

        # This check exists to make sure that the link sniffed out isn't of any picture of a gif
        if (
            not (strmatch.endswith(".png"))
            or (strmatch.endswith(".bmp"))
            or (strmatch.endswith(".jpg"))
            or (strmatch.endswith(".gif"))
        ):
            mutex.acquire()  # Mutex locking is acquired before the critical section
            # this exists to check if the link sniffed is an independant url
            #  of its own or whether its a subsection of the current website it is sniffing
            if strmatch.startswith("//"):
                strwebsite2 = "http:" + strmatch
            # if the url sniffed is a subsection, the breadcrumb of the website before it is attached before it to make it a proper url to be put back into the web crawler
            elif strmatch.startswith("/"):
                strwebsite2 = strwebsiteinp + strmatch
            else:
                strwebsite2 = strmatch
            mutex.release()
            if "\\" not in strwebsite2:
                try:
                    # print(strwebsite2)
                    strcontent = urllib.request.urlopen(strwebsite2).read()
                    match2 = re.findall(re.escape(strKeyword), str(strcontent))
                    match3 = re.findall(
                        "href=['\"]http\://[A-z0-9_\-\./]+|href=['\"]\/[A-z0-9_\-\./]+|href=['\"]www[A-z0-9_\-\./]+",
                        str(strcontent),
                    )
                    match3 = match3 + re.findall(
                        "src=['\"]http\://[A-z0-9_\-\./]+|src=['\"]\/[A-z0-9_\-\./]+|src=['\"]www[A-z0-9_\-\./]+",
                        str(strcontent),
                    )
                    if match2:
                        if tally < iterate:
                            mutex.acquire()
                            tally += 1
                            mutex.release()
                            strPrint = (
                                strwebsite2
                                + " has "
                                + str(len(match2))
                                + " matches with keyword: "
                                + strKeyword
                                + "\n"
                            )
                            print(strPrint)
                            strFile.write(strPrint)
                        else:

                            Anchor = True
                    else:
                        print("No matches for:", strwebsite2)
                    strFile3.write(strwebsite2 + "\n")
                    queueget.put([strwebsite2, match3])
                    return [strwebsite2, match3]
                except Exception as ex:
                    errormsg = "Exception {0} occurred!! We've hit a dud!"
                    message = errormsg.format(type(ex).__name__, ex.args)
                    print(message)
                    strFile2.write(message)
    else:
        sys.exit()


def linkOptimizer(webString):

    if webString.find("https://") != -1:  # if https in the string
        webString = webString.replace("https://", "http://")
    if webString.find("http://") == -1:  # if http not in string
        if webString.find("www") != -1:  # if www in string
            webString = webString.replace("www.", "http://")
        else:
            webString = "http://" + webString
    elif webString.find("www") != -1:  # if www in string
        webString = webString.replace("www.", "")
    return webString


# standard input prompting user to first enter the url then the keyword and
#  then choose between the 3 levels of searching he wishes the web crawler to
# perform the search operation from
strWebsite = input("Enter website (Format http://domain.com):\n")
strKeyword = input("Enter keyword to search for:\n")
intLevel = int(
    input(
        "Select levels to scan. Choose 1st level or 2nd level or 3 level\
         although 3rd level be prone to errors:\n"
    )
)
if intLevel == 3:
    iterate = int(input("Enter The Number Of Positive Results you wish to acquire:\n"))
# creation of 2 files to log for the positive results and errors
filename = strWebsite[7 : len(strWebsite)] + " positives.log"
filename2 = strWebsite[7 : len(strWebsite)] + " errors.log"
filename3 = strWebsite[7 : len(strWebsite)] + " queue.log"
strFile = open(filename, "w")
strFile2 = open(filename2, "w")
strFile3 = open(filename3, "w")

# the mentioned prefixes are removed with the http:/ because thats what
# the program only accepts standard input prompting user to
#  first enter the url then the keyword and then choose between the 3 levels
# of searching he wishes the web crawler to perform the search operation from
strWebsite = linkOptimizer(strWebsite)

# url is opened using the urllib library
strContent = urllib.request.urlopen(strWebsite).read()
# this line of code is comparing the strings
# of the returned with the keyword using the re library
match2 = re.findall(re.escape(strKeyword), str(strContent))
match3 = []

if match2:

    """
    # this one just searches the webpage once and returns the result and
    # accounts for the 1st level of search of the web crawler
    """

    strPrint = (
        strWebsite
        + " has "
        + str(len(match2))
        + " matches with keyword: "
        + strKeyword
        + "\n"
    )
    print(strPrint)
    strFile.write(strPrint)
else:
    print("No matches for:", strWebsite)

if intLevel == 1:
    print("Finished scanning website for keywords")
elif intLevel in range(2, 4):
    regex1 = r"src=[\'\"]http\://[A-z0-9_\-\./]+|src=[\'\"]\/[A-z0-9_\-\./]+\
    |src=[\'\"]www[A-z0-9_\-\./]+"
    regex2 = r"href=[\'\"]http\://[A-z0-9_\-\./]+|href=[\'\"]\/[A-z0-9_\-\./]+\
    |href=[\'\"]www[A-z0-9_\-\./]+"

    results = []

    match = re.findall(re.compile(regex2), str(strContent))
    matchsrc = re.findall(re.compile(regex1), str(strContent))
    match = match + matchsrc

    q = Queue()
    threads = []

    i = 0
    while i < len(match):
        if threading.active_count() < 10:
            t = threading.Thread(target=findkeywordlvl, args=(strWebsite, match[i], q))
            t.start()
            threads.append(t)
            i += 1

    for p in threads:
        p.join()
    while not q.empty():
        results.append(q.get_nowait())
    # print(results)

    threads = []
    j = 0
    if intLevel == 3:
        for i in range(0, len(results)):
            while j < len(results[i][1]):
                if threading.active_count() < 10:
                    threads.append(
                        threading.Thread(
                            target=findkeywordlvl,
                            args=(results[i][0], results[i][1][j], q),
                        )
                    )
                    threads[j].start()
                    j += 1
        for p in threads:
            p.join()
    print("it has ended here!!!!!!!\n")
else:
    print("Wrong level. Try again.")

strFile.close()
strFile2.close()
strFile3.close()
