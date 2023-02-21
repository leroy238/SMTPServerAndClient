#Justin Smith, COMP 431
#I pledge the honor code.

import string
import sys
from socket import *

curr_message = ""
full_message = ""
addresses = []
finish_flag = False

socket_name = ""

def openSocket():
    try:
        serverSocket = socket(AF_INET, SOCK_STREAM)
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(('', int(sys.argv[1])))
        serverSocket.listen(1)
    except Exception:
        print("ERROR: Could not open socket. Terminating...")
        return None
    return serverSocket

def sendOnSocket(serverSocket, message):
    try:
        serverSocket.send(message.encode())
    except Exception:
        print("ERROR: Could not send message on socket; closing connection now...")
        serverSocket.close()
        return False
    return True

def printError500(serverSocket):
    global finish_flag
    finish_flag = True
    return sendOnSocket(serverSocket, "500 Syntax error: command unrecognized\n")

def printError501(serverSocket):
    global finish_flag
    finish_flag = True
    return sendOnSocket(serverSocket, "501 Syntax error in parameters or arguments\n")

def printError503(serverSocket):
    global finish_flag
    finish_flag = True
    return sendOnSocket(serverSocket, "503 Bad sequence of commands\n")

def print250(serverSocket):
    return sendOnSocket(serverSocket, "250 OK\n")

def print354(serverSocket):
    return sendOnSocket(serverSocket, "354 Start mail input; end with <CRLF>.<CRLF>\n")

def print221(serverSocket):
    return sendOnSocket(serverSocket, f"221 {gethostname()} closing connection\n")

def print220(serverSocket):
    return sendOnSocket(serverSocket, f"220 {gethostname()}\n")

def messageToFile(mailAddress):
    file = None
    try:
        file = open("forward/" + mailAddress, "a")
    except Exception:
        file = open("forward/" + mailAddress, "x")
    finally:
        file.write(full_message)
        file.close()

def isSpace(index):
    if curr_message[index] == '\t' or curr_message[index] == ' ':
        return True
    return False

def isLetter(index):
    if string.ascii_letters.find(curr_message[index]) != -1:
        return True
    return False

def isDigit(index):
    if string.digits.find(curr_message[index]) != -1:
        return True
    return False

def isNull(index):
    return True

def isSpecial(index):
    special_chars = r'<>()[]\.,:@"';
    if special_chars.find(curr_message[index]) != -1:
        return True
    return False

def isCRLF(index):
    if curr_message[index] == '\n':
        return True
    return False

def isChar(index):
    if string.printable.find(curr_message[index]) != -1 and not(isSpecial(index) or isSpace(index)):
        return True
    return False

def isLetterDigit(index):
    if isLetter(index) or isDigit(index):
        return True
    return False

def whitespace(index):
    if index >= len(curr_message):
        return -1
    if isSpace(index):
        index += 1
        return whitespace(index)
    return index

def isNullspace(index):
    if index >= len(curr_message):
        return index
    if isSpace(index):
        index += 1
        return whitespace(index)
    if isNull(index):
        return index
    return -1

def letDigStr(index):
    if index >= len(curr_message):
        return -1
    if isLetterDigit(index):
        index += 1
        return letDigStr(index)
    return index

def name(index):
    if isLetter(index):
        index += 1
        letDigIndex = letDigStr(index)
        if letDigIndex > index:
            return letDigIndex
    return -1

def element(index):
    letterIndex = index
    if isLetter(index):
        letterIndex += 1

    if letterIndex == index:
        return -1

    nameIndex = name(index)
    
    if nameIndex > letterIndex:
        return nameIndex
    else:
        return letterIndex

def domain(index):
    elementIndex = element(index);
    if elementIndex > index:
        if elementIndex < len(curr_message) and curr_message[elementIndex] == '.':
            domainIndex = domain(elementIndex + 1)
            if domainIndex > elementIndex + 1:
                return domainIndex
            else:
                return -1
        return elementIndex
    return -1

def indexString(index):
    if index >= len(curr_message):
        return -1
    if isChar(index):
        index += 1
        return indexString(index)
    return index

def localPart(index):
    stringIndex = indexString(index)
    if stringIndex > index:
        return stringIndex
    return -1

def mailbox(index, forward):
    global addresses
    localIndex = localPart(index)
    if localIndex > index:
        if localIndex < len(curr_message) and curr_message[localIndex] == '@':
            domainIndex = domain(localIndex + 1)
            if domainIndex > localIndex + 1:
                if forward:
                    address = curr_message[localIndex + 1:domainIndex] 
                    if address not in addresses:
                        addresses.append(address)
                return domainIndex
            else:
                return -1
    return -1

def path(index, forward):
    if curr_message[index] == '<':
        index += 1
        mailIndex = mailbox(index, forward)
        if mailIndex > index:
            if curr_message[mailIndex] == '>':
                return mailIndex + 1
        else:
            return -1
    return -1

def reversePath(index):
    pathIndex = path(index, False)
    if pathIndex > index:
        return pathIndex
    else:
        return index

def forwardPath(index):
    global addresses
    pathIndex = path(index, True)
    if pathIndex > index:
        return pathIndex
    else:
        return index

def is2PartMessage(array1, array2):
    index = 0

    for character in array1:
        if index >= len(curr_message):
            return -2
        if curr_message[index] == character:
            index += 1

    if index == len(array1):
        if index >= len(curr_message):
            return -2

        whitespaceIndex = whitespace(index)

        if whitespaceIndex > index:
            index = whitespaceIndex
        else:
            return -2


        for character in array2:
            if index >= len(curr_message):
                return -2
            if curr_message[index] == character:
                index += 1

        if index - whitespaceIndex != len(array2):
            return -1
    else:
        return -1

    return index

def isData():
    data = ['D', 'A', 'T', 'A'];
    index = 0

    for character in data:
        if index >= len(curr_message):
            return False
        if curr_message[index] == character:
            index += 1
        else:
            return False
    return True

def isHELO():
    global curr_message, socket_name
    if len(curr_message) <= 4:
        return (False, 500)

    indexMail = is2PartMessage(['M','A','I','L'], ['F','R','O','M',':'])
    indexRcpt = is2PartMessage(['R','C','P','T'], ['T','O',':'])
    indexData = -1
    if isData():
        indexData = 5

    if indexMail >= 9 or indexRcpt >=  6 or indexData >= 0:
        return (False,503)

    if curr_message[0:4] == "HELO":
        index = 4
        whitespaceIndex = whitespace(index)
        if whitespaceIndex > index:
            index = whitespaceIndex
            domainIndex = domain(index)
            if domainIndex > index:
                socket_name = curr_message[index:domainIndex]
                index = domainIndex
                nullIndex = isNullspace(index)
                if nullIndex >= index:
                    if isCRLF(nullIndex):
                        return (True, 250)
        return (False, 501)
    return (False, 500)

def isMailFromCMD():
    global full_message
    index = is2PartMessage(['M','A','I','L'], ['F','R','O','M',':'])

    index503Rcpt = is2PartMessage(['R','C','P','T'], ['T','O',':'])

    index503Data = -1
    if isData():
        index503Data = 5

    index503HELO = -1
    if isHELO()[0]:
        index503HELO = 5

    if index503Rcpt >=  6 or index503Data >= 0 or index503HELO >= 0:
        return (False,503)

    if index < 9:
        return (False, 500)
    
    nullIndex = isNullspace(index)
    if nullIndex >= index:
        index = nullIndex
        reverseIndex = reversePath(index)
        if reverseIndex > index:
            index = reverseIndex
        else:
            return (False, 501)
    else:
        return (False, 501)

    nullIndex = isNullspace(index)
    if nullIndex >= index:
        index = nullIndex
    else:
        return (False,501)
    
    if isCRLF(index):
        return (True, 250)
    else:
        return (False, 501)

def isRcptToCMD():
    global full_message
    index = is2PartMessage(['R','C','P','T'], ['T','O',':'])

    index503Mail = is2PartMessage(['M','A','I','L'], ['F','R','O','M',':'])

    index503Data = -1
    if isData() or isHELO()[0]:
        index503Data = 5

    index503HELO = -1
    if isHELO()[0]:
        index503HELO = 5

    if index503Mail >= 9 or index503Data >= 0 or index503HELO >= 0:
        return (False, 503)

    if index < 7:
        return (False, 500)

    nullIndex = isNullspace(index)
    if nullIndex >= index:
        index = nullIndex
    else:
        return (False, 501)

    forwardIndex = forwardPath(index)
    if forwardIndex > index:
        index = forwardIndex
    else:
        return (False, 501)
    
    if isCRLF(index):
        return (True, 250)
    else:
        return (False, 501)

def isQuit():
    if len(curr_message) >= 4:
        quitMessage = "QUIT\n"
        if curr_message == quitMessage:
            return True
    return False

def errorProcessing(serverSocket, errorCode):
    global curr_message
    sent = True
    badCode = False
    if errorCode == 500 and curr_message != "\n":
        sent = printError500(serverSocket)
        badCode = True
    elif errorCode == 503:
        sent = printError503(serverSocket)
        badCode = True
    elif errorCode == 501:
        sent = printError501(serverSocket)
        badCode = True
    elif errorCode == 250:
        sent = print250(serverSocket)
    elif errorCode == 354:
        sent = print354(serverSocket)
    return badCode, sent

def receiveLine(serverSocket):
    try:
        serverSocket.settimeout(30)
        line = serverSocket.recv(1024).decode()
        return line
    except Exception:
        print("ERROR: Read failed.")
        return None

def process(serverSocket):
    global curr_message, full_message, addresses, finish_flag
    state = "Mail" # Valid states are "Mail", "Rcpt/Data", "Message"

    curr_message = receiveLine(serverSocket)
    if curr_message == None:
        return

    errorCode = 0
    while True:
        if isQuit():
            print221(serverSocket)
            serverSocket.close()
            break

        if state == "Mail":
            mailValue = isMailFromCMD()
            errorCode = mailValue[1]
            if mailValue[0]:
                finish_flag = False
                state = "Rcpt/Data"
        elif state == "Rcpt/Data":
            rcptValue = isRcptToCMD()
            errorCode = rcptValue[1]
            if isData():
                if len(addresses) != 0:
                    state = "Message"
                    errorCode = 354
                else:
                    errorCode = 503
        elif state == "Message":
            bound = len(curr_message)-3
            if curr_message[bound:] == "\n.\n":
                full_message += curr_message[:bound]
                finish_flag = True
                state = "Mail"
                errorCode = 250
                for address in addresses:
                    messageToFile(address)
            else:
                full_message += curr_message
                curr_message = receiveLine(serverSocket)
                continue

        badCode, sent = errorProcessing(serverSocket, errorCode)
        if badCode:
            state = "MAIL"
        if not(sent):
            return

        curr_message = receiveLine(serverSocket)
        if curr_message == None:
            return
    #end while

    if not(finish_flag):
        sent = printError501(serverSocket)
        if not(sent):
            return
    full_message = ""
    curr_message = ""

def main():
    global curr_message
    serverSocket = openSocket()
    if serverSocket == None:
        return

    while True:
        connection = None
        addr = ""
        try:
            connection, addr = serverSocket.accept()
        except Exception:
            print("ERROR: Could not accept connection. Retrying...")
            continue

        if not(print220(connection)):
           continue 

        sentence = receiveLine(connection)
        if sentence == None:
            continue

        curr_message = sentence
        valid, error = isHELO()
        if valid:
            if not(sendOnSocket(connection, f"250 Hello {socket_name} pleased to meet you\n")):
                continue
            process(connection)
        else:
            errorProcessing(connection, error)
    #end while

main()
