#Justin Smith, COMP 431
#I pledge the honor code.
import sys
import string
from socket import *

sendArray = []
stateArray = []

def isSpace(character):
    if character == " " or character == "\t":
        return True
    return False

def whitespace(line):
    index = 0
    while True:
        if index >= len(line):
            return index
        if not(isSpace(line[index])):
            return index
        index += 1
    #end while

def isLetter(character):
    if string.ascii_letters.find(character) != -1:
        return True
    return False

def isDigit(character):
    if string.digits.find(character) != -1:
        return True
    return False

def isCRLF(character):
    if character == '\n':
        return True
    return False

def isSpecial(character):
    special_chars = r'<>()[]\.,:@"';
    if special_chars.find(character) != -1:
        return True
    return False

def isLetterDigit(string, index):
    if isLetter(string[index]) or isDigit(string[index]):
        return True
    return False

def isChar(character):
    if string.printable.find(character) != -1 and not(isSpecial(character) or isSpace(character)):
        return True
    return False

def letDigStr(string, index):
    if index >= len(string):
        return -1
    if isLetterDigit(string, index):
        index += 1
        return letDigStr(string, index)
    return index

def name(string, index):
    if isLetter(string[index]):
        index += 1
        letDigIndex = letDigStr(string, index)
        if letDigIndex > index:
            return letDigIndex
    return -1

def element(string, index):
    letterIndex = index
    if isLetter(string[index]):
        letterIndex += 1

    if letterIndex == index:
        return -1

    nameIndex = name(string, index)
    
    if nameIndex > letterIndex:
        return nameIndex
    else:
        return letterIndex

def domain(string, index):
    elementIndex = element(string, index);
    if elementIndex > index:
        if elementIndex < len(string) and string[elementIndex] == '.':
            domainIndex = domain(string, elementIndex + 1)
            if domainIndex > elementIndex + 1:
                return domainIndex
            else:
                return -1
        return elementIndex
    return -1

def indexString(string, index):
    if index >= len(string):
        return -1
    if isChar(string[index]):
        index += 1
        return indexString(string, index)
    return index

def localPart(string, index):
    stringIndex = indexString(string, index)
    if stringIndex > index:
        return stringIndex
    return -1

def mailbox(string, index):
    localIndex = localPart(string, index)
    if localIndex > index:
        if localIndex < len(string) and string[localIndex] == '@':
            domainIndex = domain(string, localIndex + 1)
            if domainIndex > localIndex + 1:
                return domainIndex
            else:
                return -1
    return -1

def path(string):
    index = 0
    mailIndex = mailbox(string, index)
    if mailIndex > index:
        return mailIndex
    return -1

def isPath(string):
    return path(string) >= 0

def readCodeResponse(line, state):
    if len(line) > 3:
        code = line[:3]
        if code == "220" and state == "NONE":
            numWhitespace = whitespace(line[3:])
            return numWhitespace > 0
        if code == "221":
            numWhitespace = whitespace(line[3:])
            return numWhitespace > 0
        if code == "250" and state != "DATA":
            numWhitespace = whitespace(line[3:])
            return numWhitespace > 0
        elif code == "354" and state == "DATA":
            numWhitespace = whitespace(line[3:])
            return numWhitespace > 0
        return False
    return False

def isValid(clientSocket, state):
    codeAccept = False
    try:
        line = clientSocket.recv(1024).decode()
        codeAccept = readCodeResponse(line, state)
    except Exception:
        print("ERROR: Could not receive message. Terminating...")
    return codeAccept

def sendMessage(clientSocket, message, state):
    try:
        clientSocket.send(message.encode())
    except Exception:
        print("ERROR: Could not send message via socket.")
        return (False, False)

    if (message == ".\n" or not(state == "MESSAGE")):
        if isValid(clientSocket, state) and not(message == ".\n"):
            return (True, True)
        try:
            clientSocket.send("QUIT\n".encode())
        except Exception:
            print("ERROR: Could not send message via socket.")
            return (False, False)
        isValid(clientSocket, state)
        if not(message == ".\n"):
            print("ERROR: Error response from server.")
            return(False, True)
    return (True, True)

def readLine(state):
    lineRead = ""
    if state == "MAIL":
        lineRead = input("FROM:\n")
    elif state == "RCPT":
        lineRead = input("RCPT:\n")
    elif state == "DATA":
        lineRead = input("SUBJECT:\n") + '\n'
    elif state == "MESSAGE":
        newLine = input("MESSAGE:\n") + '\n'
        lineRead += newLine
    return lineRead

def openSocket():
    try:
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((sys.argv[1], int(sys.argv[2])))
    except Exception:
        print("ERROR: Could not open socket. Terminating...")
        return None
    return clientSocket

def HELO(clientSocket):
    if isValid(clientSocket, "NONE"):
        #Hostname!!!! {gethostname()}
        clientSocket.send(f"HELO alshdf\n".encode())
        if isValid(clientSocket, "MAIL"):
            return True
    return False

def sendAll(clientSocket):
    string = ""
    for line in sendArray:
        string += line

    try:
        clientSocket.send(string.encode())
    except Exception:
        print("ERROR: Server did not receive message.\n")
        return False

    #How many responses would a (correct) server send?
    responses = 0
    for state in stateArray:
        if state != "MESSAGE":
            responses += 1
    
    #Load all responses from the server
    index = 0
    count = 0
    serverResponses = []
    errorLine = clientSocket.recv(1024).decode()
    while count < responses:
        for char in errorLine:
            index += 1
            if char == '\n':
                serverResponses.append(errorLine[:index])
                errorLine = errorLine[index:]
                index = 0
                count += 1
        if count < responses:
            errorLine += clientSocket.recv(1024).decode()

    #Now with all of the errors loaded, check if there were any errors.
    index = 0
    relatedMessage = 0
    for state in stateArray:
        if sendArray[relatedMessage] == '.\n' or state != "MESSAGE":
            errorValid = readCodeResponse(serverResponses[index], state)
            if not(errorValid):
                print("ERROR: Server sent invalid code.\n")
                return False
            index += 1
        relatedMessage += 1

    return True

def main():
    global sendArray, stateArray
    state = "MAIL" # Legal states are "MAIL", "DATA" ,"RCPT", "MESSAGE"

    userLine = readLine(state)
    reversePath = ""
    forwardPaths = []
    while True:
        if state == "MAIL":
            if not(isPath(userLine)):
                print("ERROR: Not a valid email address, please try again.")
                userLine = readLine(state)
                continue
            reversePath = "<" + userLine + ">\n"
            sendArray.append("MAIL FROM: " + reversePath)
            stateArray.append(state)
            state = "RCPT"
        #End MAIL
        elif state == "RCPT":
            if not(isPath(userLine)):
                print("ERROR: Not a valid email address, please try again.")
                userLine = readLine(state)
                continue
            sendLine = "RCPT TO: <"
            forwardPaths.append('<')
            count = 0
            for char in userLine:
                if char == ' ' or char == '\t':
                    continue
                if char == ',':
                    forwardPaths[count] += '>'

                    count += 1
                    forwardPaths.append('<')
                    
                    sendLine += ">\n"
                    sendArray.append(sendLine)
                    stateArray.append(state)
                    sendLine = "RCPT TO: <"
                else:
                    forwardPaths[count] += char
                    sendLine += char
            sendLine += ">\n"
            sendArray.append(sendLine)
            stateArray.append(state)
            state = "DATA"
        #End RCPT
        elif state == "DATA":
            sendArray.append("DATA\n")
            stateArray.append(state)

            state = "MESSAGE"

            sendArray.append("From: " + reversePath)
            stateArray.append(state)

            toMessage = "To: " + forwardPaths[0]
            for path in forwardPaths[1:]:
               toMessage += ", " + path 
            toMessage += '>\n'

            sendArray.append(toMessage)
            stateArray.append(state)

            #Extra newline seperates headers. Different placement for different header structures.
            sendArray.append("Subject: " + userLine + '\n')
            stateArray.append(state)
        #End DATA
        else:
            while userLine != ".\n":
                sendArray.append(userLine)
                stateArray.append(state)
                userLine = input() + '\n'
            sendArray.append(userLine)
            stateArray.append(state)
            state = "MAIL"
            break
        #End MESSAGE

        userLine = readLine(state)
    #End while

    clientSocket = openSocket()
    if clientSocket == None:
        return

    valid = HELO(clientSocket)
    if not(valid):
        sendMessage(clientSocket, "QUIT\n", "MAIL")
        clientSocket.close()
        return

    sendAll(clientSocket)
    sendMessage(clientSocket, "QUIT\n", "MAIL")
    clientSocket.close()
                    
main()
