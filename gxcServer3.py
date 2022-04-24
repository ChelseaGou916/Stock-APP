from socket import *
import _thread
import pycurl
from io import BytesIO
import base64
import json
from bs4 import BeautifulSoup
import sys

APItoken = 'pk_dbd72ad292fa4c13be7abb8b5814c962'
gxc_user = "19029705"
gxc_password = "19029705"

serverSocket = socket(AF_INET, SOCK_STREAM)

serverPort = int(sys.argv[1])
# serverPort = 8080
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(("", serverPort))

serverSocket.listen(5)

print('The server is running')



# basic access authentication
def authentication(message):
    if('Authorization' in message):
        ms = message.split()
        bmessage = ms[ms.index("Authorization:") + 2]
        bbytes = bmessage.encode('ascii')
        message_bytes = base64.b64decode(bbytes)

        tu=tuple(message_bytes.decode('ascii').split(":"))
        username=tu[0]
        password=tu[1]

        # Authentication success
        if(username==gxc_user and password==gxc_password):
            return True
    else:
        return False


def updateResponse():
    responseHeader = ''
    responseBody = ''
    return responseHeader,responseBody


# def getIcon(message):
#     try:
#         f = open('icon.png', 'rb')
#         responseBody = f.read()
#         f.close()
#         responseHeader = "HTTP/1.1 200 OK\r\n\r\n".encode()
#
#     except IOError:
#         responseHeader = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
#         responseBody = "404 icon Not Found".encode()
#
#     return responseHeader, responseBody


def getPor(notification=''):
    responseHeader,responseBody=updateResponse()
    portfolio = []

    try:
    	with open('portfolio.json', 'r') as j1:
            lines = j1.readlines()
            leng=len(lines)

            if(leng!=0):
                for line in lines:
                    js = json.loads(line.strip())
                    stockname = js['stock']
                    quantity = js['quantity']
                    price = js['price']

                    # https://cloud.iexapis.com/stable/stock/symbol/quote?token=YourAPIToken
                    response_buffer = BytesIO()
                    curl = pycurl.Curl()
                    curl.setopt(curl.SSL_VERIFYPEER, False)
                    curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/stock/' + stockname + '/quote?token='+APItoken)
                    curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
                    curl.perform()
                    curl.close()

                    response = response_buffer.getvalue().decode('UTF-8')
                    latest_quote = json.loads(response)['latestPrice']

                    # Gain or loss = (latest quote – price) / price * 100
                    gainorloss = round(((latest_quote - price) / price * 100), 2)

                    portfolio.append({'stock':stockname, 'quantity':quantity, 'price':price, 'gain':gainorloss})
            else: # leng==0
                responseHeader = "HTTP/1.1 200 OK\r\n\r\n".encode()
                responseBody = open('portfolio.html').read().encode()
    except:
        # print('Processing portfolio data: unexpected error occured! ')
        responseHeader = "HTTP/1.1 500 Internal Server Error\r\n\r\n".encode()
        responseBody = 'Processing portfolio data: unexpected error occured! '.encode()


    try:
        with open("portfolio.html", 'r') as h:
            bsoup = BeautifulSoup(h, "html.parser")
            tabl = bsoup.select_one("#table")

            for row in portfolio:
                cont = '<tr>' + '<td>' + str(row['stock']) + '</td>' + '<td>' + \
                          str(row['quantity']) + '</td>' + '<td>' + str(round(row['price'], 4)) \
                          + '</td>' + '<td>' + str(row['gain']) + '%</td>' + '</tr>'
                tabl.append(BeautifulSoup(cont,'html.parser'))

            noti = bsoup.select_one("#notification")
            noti.append(BeautifulSoup(notification,'html.parser'))

            cslist = bsoup.select_one("#candidates")

            with open('symbols4cs.json', 'r') as j2:
                symbols = json.loads(j2.read())
                for n in range(len(symbols)):
                    cslist.append(BeautifulSoup("<option value=\"{}\" />".format(symbols[n]),'html.parser'))
            responseHeader = "HTTP/1.1 200 OK\r\n\r\n".encode()
            responseBody = bsoup.encode()

    except:
        # print("HTML file not found")
        responseHeader = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
        responseBody = 'portfolio.html not found.'.encode()

    return responseHeader, responseBody


def getSymbols():
    j = open('symbols4cs.json', 'r')
    symbols = json.loads(j.read())
    j.close()
    return symbols


def readFile(loc):
    cache=[]
    with open(loc, 'r') as f:
        lines = f.readlines()
        for line in lines:
            jstring = json.loads(line.strip())
            cache.append(jstring)
    return cache


def setPor(message):
    responseHeader = "HTTP/1.1 302 See Other\r\nLocation:http://localhost:8080/portfolio\r\n\r\n".encode()
    responseBody = "Info updated. Redirecting to your portfolio.".encode()

    # stores info for four entries in the table
    para = {}
    symbols=getSymbols()
    content = message.split()[-1]
    print(content)
    pairs = content.split('&')[:3]


    for index in range(len(pairs)):
        if(index==0):# symbol
            stockname = pairs[0].split('=')[-1].upper()
            # print(stockname)
            if (stockname in symbols):
                para['stock'] = stockname
            else:
                responseHeader = "HTTP/1.1 400 Bad Request\r\n\r\n".encode()
                # print(stockname,type(stockname))
                # print("---------------------------")
                return responseHeader, getPor('Note: The stock symbol is incorrect')[1]
        elif(index==1):# quantity
            try:
                para['quantity'] = int(pairs[index].split('=')[-1])
            except ValueError:
                # print("Note: The number entered is not an integer")
                responseHeader = "HTTP/1.1 400 Bad Request\r\n\r\n".encode()
                return responseHeader, getPor('Note: The number entered is not an integer')[1]
        else:# price
            try:
                price = float(pairs[index].split('=')[-1].strip())
                if (price > 0):
                    para['price'] = price

                elif(price <= 0):
                    responseHeader = "HTTP/1.1 400 Bad Request\r\n\r\n".encode()
                    return responseHeader, getPor('Note: The input price needs to be greater than zero')[1]

            except ValueError:
                print("Note: The price entered is not a number")
                responseHeader = "HTTP/1.1 400 Bad Request\r\n\r\n".encode()
                return responseHeader, getPor('Note: The price entered is not a number')[1]
    print(para)

    cache = readFile('portfolio.json')
    leng=len(cache)

    judge_append = True # judge append/ rewritten

    for index in range(leng):

        if (cache[index]['stock'] == para['stock']):
            judge_append = False

            oriQuantity = cache[index]['quantity']
            addQuantity = para['quantity']
            oriPrice = cache[index]['price']
            curPrice = para['price']
            cache[index]['quantity'] = int(oriQuantity + addQuantity)
            sta=cache[index]['quantity']

            if(sta > 0):
                sump = oriQuantity*oriPrice + addQuantity*curPrice
                cache[index]['price'] = sump/cache[index]['quantity']
            elif(sta < 0):
                responseHeader = "HTTP/1.1 400 Bad Request\r\n\r\n".encode()
                return responseHeader, getPor('Note: You intend to sell more shares than you own!')[1]
            elif(sta == 0):
                del cache[index]

            break

    # rewrite
    if judge_append==False:
        with open('portfolio.json', 'w') as f:
            for line in cache:
                f.write(json.dumps(line)+'\n')

    # append
    if judge_append==True:
        if (para['quantity'] > 0):
            # print('----------------------appended-------------------')
            with open('portfolio.json', 'a') as f:
                f.write(json.dumps(para)+'\n')
        elif(para['quantity'] <= 0):
            responseHeader = "HTTP/1.1 400 Bad Request\r\n\r\n".encode()
            return responseHeader, getPor('Note: You intend to sell more shares than you own!')[1]

    return responseHeader, responseBody


def getStock(notification=''):
    resetInfo()
    try:
        with open("graph.html", 'r') as h:
            bsoup = BeautifulSoup(h, "html.parser")

            noti = bsoup.select_one("#notification")
            noti.append(BeautifulSoup(notification,'html.parser'))
            data = bsoup.select_one("#candidates")

            with open('symbols4cs.json', 'r') as j:
                symbols = json.loads(j.read())

                for n in range(len(symbols)):
                    data.append(BeautifulSoup("<option value=\"{}\" />".format(symbols[n]),'html.parser'))

            responseHeader = "HTTP/1.1 200 OK\r\n\r\n".encode()
            responseBody = bsoup.encode()

    except:
        responseHeader = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
        responseBody = 'graph.html not found.'.encode()

    return responseHeader, responseBody

# get data about the stock
def getDetail(stockname):
    response_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, False)
    curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/stock/' + stockname + '/stats?token=' + APItoken)
    curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
    curl.perform()
    curl.close()

    body = response_buffer.getvalue().decode('UTF-8')
    linebreak = "\n"
    dic_j=json.loads(body)

    Symbol = "Symbol: " + stockname + linebreak
    companyName ="Company Name: "+ str(dic_j["companyName"])+ linebreak
    peRatio ="PE ratio: "  + str(dic_j["peRatio"])+ linebreak
    marketcap ="Market capitalization: "  + str(dic_j["marketcap"]) + linebreak
    high ="52 week high: "  + str(dic_j["week52high"])+ linebreak
    low ="52 week low: " + str(dic_j["week52low"]) + linebreak

    print(Symbol + companyName + peRatio + marketcap + high + low)

    info = "<textarea rows='10' cols='100'>"+ Symbol + companyName + peRatio + marketcap + high + low + "</textarea>"

    return info


def getGraph(stockname):
    responseHeader = "HTTP/1.1 200 OK\r\n\r\n".encode()
    symbols=getSymbols()
    detail = []

    if (stockname not in symbols):
        return "HTTP/1.1 400 Bad Request\r\n\r\n".encode(), 'Note: The stock symbol is incorrect'.encode()
    response_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, False)

    # https://cloud.iexapis.com/stable/stock/symbol/chart/5y?chartCloseOnly=true&token=yourAPIToken
    curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/stock/' + stockname + '/chart/5y?chartCloseOnly=true&token='+APItoken)

    curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
    curl.perform()
    curl.close()

    response = json.loads(response_buffer.getvalue().decode('UTF-8'))
    jstring = json.loads(json.dumps(response))

    for line in jstring:
        detail.append({'date':line['date'], 'closePrice':line['close']})
    responseBody = json.dumps(detail).encode()


    return responseHeader, responseBody

# Display stock information at the bottom of the chart
def addInfo(table):
    f1 = 'graph.html'
    f2= open("test.html")
    lines = f2.readlines()
    f2.close()

    with open(f1, 'w') as f:
        for i in lines:
            f.write(i)
        f.write(table)
    f.close()

# Reset to original HTML
def resetInfo():
    f1 = 'graph.html'
    f2= open("test.html")
    lines = f2.readlines()
    f2.close()

    with open(f1, 'w') as f:
        for i in lines:
            f.write(i)
    f.close()


def process(connectionSocket):
    responseHeader,responseBody=updateResponse()
    message = connectionSocket.recv(1024).decode()
    # print(message)

    if(authentication(message)):
        if len(message) > 1:
            resource = message.split()[1][1:]

            if resource == "":
                responseHeader = "HTTP/1.1 200 OK\r\nSet-Cookie: code=19029705\r\n\r\n".encode()
                responseBody = "Authentication Succeed!".encode()

            elif resource == "portfolio":
                body = message.split('\r\n\r\n')[-1]
                if(body==''):
                    # print(123456)
                    responseHeader, responseBody = getPor()
                else:
                    responseHeader, responseBody = setPor(body)
            elif resource == "research":
                body = message.split('\r\n\r\n')[-1].strip().upper()
                if(body==''):
                    responseHeader, responseBody = getStock()
                else:
                    responseHeader, responseBody = getGraph(body)
                    info=getDetail(body)
                    addInfo(info)

            # elif resource == "favicon.ico":
            #     responseHeader, responseBody = getIcon(message)
            else:
                responseHeader = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
                responseBody = "404 Not Found".encode()
    else:
        responseHeader = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=User Visible Realm\r\n\r\n".encode()
        responseBody = "Note: basic access authentication is required.".encode()

    connectionSocket.send(responseHeader)
    connectionSocket.send(responseBody)
    connectionSocket.close()


while True:
    # Set up a new connection from the client
	connectionSocket, addr = serverSocket.accept()
	#Clients timeout after 60 seconds of inactivity and must reconnect.
	connectionSocket.settimeout(60)
	# start new thread to handle incoming request
	_thread.start_new_thread(process,(connectionSocket,))
