import requests
from urllib.parse import quote
from urllib.request import urlopen
import sys
from bs4 import BeautifulSoup
import json
from fastapi import FastAPI
import re
#from pymarc import * #doesn't work



#paraula_clau="El quadern gris"
#paraula_clau="El món d'Horaci"
paraula_clau="La punyalada"
#paraula_clau="Naruto"
#paraula_clau="El castell ambulant"
#paraula_clau="Guilleries"
#paraula_clau="Mirall trencat"

main_url='cataleg.atena.biblioteques.cat'
search_url = main_url+'/iii/encore/search'
book_url=main_url+"/iii/encore/record"
language="cat"
mediatype="4 | a" #llibre i còmic
"""
LEADER:00000nam a2200193za 4500
008:161118s2016 spc |||| f cat||
020:9788416367740
035:b18413171
084:833.4"19"
090:N Pag
100:1 Pagès, Vicenç,|d1963-2022
245:13 El Món d'Horaci /|cVicenç Pagès Jordà ; epíleg de l'autor
i:colofó d'Enric Sullà
250:2a ed.
260:Barcelona :|bEmpúries,|c2016
300:410 p. ;|c22 cm
336:text|btxt|2rdacontent
337:sense mediació|bn|2rdamedia
338:volum|bnc|2rdacarrier
830:0 Narrativa (Empúries) ;|v509
989:7
el_mu00f3n_d_horaci_______________________________________:
_______2016410_2__ema_______________________________:
"""





author_registers={ "indicators":[
                                {"0":"forename","1":"surname","3":"family name"}
                                ],
                   "d":"author dates"
                   }

title_registers={  "indicators":[
                                {"0":"noadded","1":"added"},
                                {"0":"nofilling"} #extra numbers will be filled with the number indicator
                                ],
                    "c":"description",
                   }

original_registers={  
                    "indicators":[
                                {"0":"noadded","1":"added"},
                                {"0":"nofilling"} #extra numbers will be filled with the number indicator
                                ],
                    "c":"description",
                   }
publication_registers={
                   "a":"place", 
                   "b":"publisher",
                   "c":"publishing date" 
                }

phisical_description_registers={
                   "a":"extends", 
                   "c":"dimensions" 
                }
series_registers={
                "indicators":[
                                 {"0":"nofilling"} #extra numbers will be filled with the number indicator
                                ],
                "v":"volume"
}

marc_registers={"100":[author_registers,"author"],
                "020":"isbn",
                "240":[original_registers,"original_title"],
                "245":[title_registers,"title"],
                "260":[publication_registers,"publication"],
                "250":"edition",
                "300":[phisical_description_registers,"physical description"],
                ""
                "830":[series_registers,"series"]}

excluded_registers_keys=["LEADER","008","035","040","041","084","090","336","337","338",]


def lookup_book_atena(paraula_clau):
    #now we have all these books. Then extrait the extra information for all of them
    global main_url
    book={}
    reference=book_url+"/C__"+paraula_clau+"?lang=cat&marcData=Y"
    print(quote(reference))
    result=requests.get("http://"+quote(reference))
    
    decoded_html = result.text.lstrip().rstrip()


    print(decoded_html.splitlines())
    print("-----")
    last_register_used=None
    for line in decoded_html.splitlines():
        #print(line)
        splittedline=line.lstrip().rstrip().split()
        register=splittedline[0]
        data=' '.join(splittedline[1:])
        #print(register+":"+data)

        #print(marc_registers.keys())
        if register in marc_registers.keys():
            if type(marc_registers[register]) is list:
                
                these_registers=marc_registers[register][0]
                default_register=marc_registers[register][1]
                if "indicators" in these_registers.keys():
                    skipped=len(these_registers['indicators'])
                    data=data[skipped+1:]
                info=data.split('|')
                if len(info)>1:            
                    for indx,a in enumerate(info):
                        if a[0] in these_registers:
                            reg=these_registers[a[0]]
                            book[reg]=a[1:].lstrip().rstrip()
                            last_register_used=reg
                        elif indx==0:
                            #the first element does not contain any key information, then using for this the default
                            book[default_register]=a.lstrip().rstrip()
                            last_register_used=default_register
                elif info[0] in these_registers.keys():
                    reg==these_registers[info[0]]
                    book[reg]=a[1:].lstrip().rstrip()
                    last_register_used=reg

                else:
                    book[default_register]=info[0].lstrip().rstrip()
                    last_register_used=default_register

            else:
                default_register=marc_registers[register]
                book[default_register]=data.rstrip().lstrip()
                last_register_used=default_register

        elif re.search("^[0-9]{3}",register) is None:
            print(re.search("^[0-9]{3}",register))
            #print("this line is not taken into account:"+register)
            print(register)
            print(line)
            if last_register_used is not None:
                print(last_register_used)
                print(line)
                book[last_register_used]=book[last_register_used].replace('\n\r','').lstrip().rstrip()+" "+line.lstrip().rstrip()
        else:
            print("this register is not taken into account:"+register+" data:"+data)
            last_register_used=None
    book["key"]=paraula_clau
    print(book)
    return book



def lookup_atena(paraula_clau):

    global main_url
    global search_url

    global language
    global mediatype

    final_url=quote(search_url+"/C__S("+paraula_clau+") f:("+mediatype+") l:"+language+"__Orightresult__U?lang="+language+"&suit=def")

    with urlopen("http://"+final_url) as response:
        html_response = response.read()
        encoding = response.headers.get_content_charset('utf-8')
        decoded_html = html_response.decode(encoding)
    
    fullhtml=decoded_html




    startItem="<!--  start item -->"
    endItem='<!-- end item -->'

    if startItem not in  fullhtml:
        #print(fullhtml)
        print("nothing found in web:"+"http://"+final_url)
        return ""


    findBooks=fullhtml.split(startItem)

    if len(findBooks)>1:
        books=list()
    else:
        print("Not found")
        sys.exit(1)

    for b in findBooks:
        element=b.split('<!-- end item -->')
        if len(element)>1:
            #exists!
            toParseBook=element[0]
            #parse here.
            title=toParseBook.split('<div class="dpBibTitle">')[1].split('</a>')[0]
            reference=title.split('href="')[1].split('"')[0]
            title=title.split('>')[-1].lstrip() #last element
            title=title.rstrip() #last element
            title=title.rstrip() #last element
            try:
                autor=title.split('/')[1].rstrip().lstrip()
            except:
                autor=""

            try:
                description=autor.split(';')[1].rstrip().lstrip()
                autor=autor.split(';')[0].rstrip().lstrip()
            except:
                description=""

            ##year
            try:
                year=toParseBook.split('<div class="recordDetailValue">')[1].split('</div>')[0]
                year=year.split('<span class="itemMediaYear"')[1].split('</span>')[0]
                year=year.split('">')[1]
            except:
                print(toParseBook.split('<div class="recordDetailValue">'))
                year=""
            

            reference=reference.split('/iii/encore/record/')[1]
            reference=reference.split('__')
            key=reference[1]

            title=title.split('/')[0].rstrip().lstrip()
            book={"title":title,"author":autor,"key":key,"description":description,"year":year}
            books.append(book)

    #print(books)
    return books

##to obtain all data from an author

def author_lookup_atena(paraula_clau):
    booksout=dict()
    booksout["author"]=paraula_clau
    books=lookup_atena(paraula_clau)
    booksout["works"]=[b for b in books if paraula_clau in b["author"]]

    #print(json.dumps(booksout,ensure_ascii=False))
    return booksout

def nicelookup_atena(paraula_clau):
    books=lookup_atena(paraula_clau)

    booksout=books
    for b in booksout:
        del b['reference']

    #print(json.dumps(booksout,ensure_ascii=False))
    return booksout

#####api rest

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Atena, Biblioteques de Catalunya Parser"}


@app.get("/book")
async def books(k=None):
    if k is None or len(k)!=9:
        return{"Error":"key word not present or too small"}
    books= lookup_book_atena(k)
    return books

@app.get("/books")
async def books(q=None):
    print(q)
    if q is None or len(q)<3:
        return{"Error":"key word not present or too small"}
    books= nicelookup_atena(q)
    return books


@app.get("/author")
async def books(q=None):
    print(q)
    if q is None or len(q)<3:
        return{"Error":"key word not present or too small"}
    books= author_lookup_atena(q)
    return books

@app.get("/search")
async def search(q=None):
    print(q)
    if q is None or len(q)<3:
        return{"Error":"key word not present or too small"}
    books= lookup_atena(q)
    return books