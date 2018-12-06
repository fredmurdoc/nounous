from bs4 import BeautifulSoup as bs
import requests
import re
import sqlite3
import os
import argparse
import gettext
import logging
import logging.handlers
from datetime import datetime


logger = logging.getLogger("default")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s | %(levelname)8s | %(message)s")

stStdout = logging.StreamHandler()
stStdout.setFormatter(formatter)
logger.addHandler(stStdout)

appDir= os.environ['HOME']+"/.nounous"
logsDir = appDir + "/logs"
if not os.path.isdir(logsDir):
    if not os.path.isdir(appDir):
        os.mkdir(appDir)
    os.mkdir(logsDir)

stLogfile = logging.handlers.RotatingFileHandler(logsDir+'/log', maxBytes=256*1024, backupCount=10)
stLogfile.setFormatter(formatter)
#stLogfile.doRollover()
logger.addHandler(stLogfile)


# DB Preparation
db = sqlite3.connect(appDir+"/db")
db.execute("""
CREATE TABLE IF NOT EXISTS nounous (
  nom_prenom TEXT,
  url TEXT ,
  url_email TEXT,
  date_maj DATE,
  date_created DATE,
  date_update DATE,
  date_analyzed DATE,
  adresse TEXT,
  precisions TEXT,
  dispo_matin BOOL DEFAULT 0,
  dispo_mercredi_matin BOOL DEFAULT 0,
  PRIMARY KEY(url)
);
""")


def findAllNounous():
    ##li class pgNext > a
    # lien fiche
    ##div class lienEnsavoirPlus > a
    mustPaginate = True
    links = []
    haveToContinue = True
    url = "https://assmat.loire-atlantique.fr/jcms/descriptive-urlstextportal-format-fr-cra_66992?idCommune=rp1_62646&codeInsee=44109&cities=44036&longitude=-1.583453&latitude=47.226386&cityName=Nantes&adresse=1+Boulevard+Pierre+de+Coubertin+44100+Nantes&distance=-10&quartier=4410907&quartier=4410901&quartier=4410903&quartier=4410904&month=1543400000000&age=1%7C17%7C2%7C3%7C10%7C19&branchesId=cra_67000&branchesId=cra_67001&branchesId=&nomassmat=&isSearch=Ok&hashKey=713&withDispo=true&withDispoFuture=true&withNonDispo=false&withDispoNonRenseigne=false"
    while haveToContinue:
        logger.debug("connect")
        pageSoup = bs(requests.get(url).content)
        # We search all the link
        for i, aDiv in enumerate(pageSoup.findAll('div', attrs={'class': 'lienEnsavoirPlus'})):
            aLink = aDiv.find('a') 
            href = aLink.get('href')
            if href:
                logger.debug("searchLinksInUrl : analyze url "+href)
                # And perform a link target matching
                link = "https://assmat.loire-atlantique.fr/%s" % (href)
                links.append(link)
        if mustPaginate :
            aNext = pageSoup.find('li', attrs={'class' : 'pgNext'})
            
            haveToContinue = aNext != None
            if  haveToContinue :
                haveToContinue = aNext.find("a") != None
            if  haveToContinue :
                aNext.find("a") != None
                url = "https://assmat.loire-atlantique.fr/%s"  % (aNext.find("a").get("href"))
                logger.debug("NEXT URL  : "+url )
        else : 
            haveToContinue = False   
    return links

def analyzePageNounou(link) :
    pageSoup = bs(requests.get(link).content)
    nom = pageSoup.find("div", attrs = {'class':"colGauche"}).find("h2").text
    byMail = pageSoup.find("div", attrs = {'class':"colGauche"}).find("a", attrs = {'class':"courrielFull"}).get("href") if pageSoup.find("div", attrs = {'class':"colGauche"}).find("a", attrs = {'class':"courrielFull"}) != None else None
    aDateMaj = pageSoup.find("div", attrs = {'class':"colGauche"}).find("p", attrs = {'class':"exergue"}).text
    p = re.compile(".+(\d{2}/\d{2}/\d{4}).*")
    m = p.search(aDateMaj)
    dateMaj = ""
    if m :
        dateMaj = m.group(1)
    logger.debug("##############")
    logger.debug(nom)
    logger.debug(dateMaj)
    logger.debug(link)
    adresse = pageSoup.find("div", attrs = {'class':"blocAdresse"}).text.replace("\r", "").replace("\n", "").replace("\t", " ").replace("        ", " ").strip()
    
    aPrecisions = pageSoup.find("div", attrs = {'class':"precisionDispo"})
    precisions = ""
    if aPrecisions !=  None :
        precisions = aPrecisions.text.replace("\r", "").replace("\n", "").replace("\t", " ").replace("        ", " ").strip() 
    tabDispos = pageSoup.findAll("table", attrs = {'class':"tabDispos"})
    isDispoMatin = False
    isDispoMercredi = False
    if  tabDispos != None :
        logger.debug(len(tabDispos))
        #logger.debug(tabDispos)
        # Avant ecole LMJV
        isDispoMatin = True
        tabDispo = None
        if len(tabDispos) > 0:
            tabDispo = tabDispos[0]
        if tabDispo != None : 
            for aTd in tabDispo.findAll("tr")[1].findAll("td")[0:5]:
                #logger.debug(aTd)
                isDispoMatin &= aTd.find("img", attrs = {'class':"creneauDispo"}) != None
                logger.debug("dispoMatin : %s " % (isDispoMatin))
            # Mercrddi matin
            isDispoMercredi = True
            for aTr in tabDispo.findAll("tr")[1:3]:
                #logger.debug(aTr)
            
                for i, aTd in enumerate(aTr.findAll("td")):
                    #logger.debug(i)
                    if i == 2 : 
                        #logger.debug("TD3")
                        #logger.debug(aTd)
                        #logger.debug("TD3>IMG")
                        #logger.debug(aTd.find("img", attrs = {'class': "creneauDispo" }))
                        isDispoMercredi &= aTd.find("img", attrs = {'class':"creneauDispo"}) != None
                        logger.debug("isDispoMercredi : %s " % (isDispoMercredi))
    print "%s;%s;%s;%s;%s;%s;%s;%s" % (nom.encode('utf-8'), dateMaj.encode('utf-8'), adresse.encode('utf-8'), precisions.encode('utf-8'), isDispoMatin, isDispoMercredi, link.encode('utf-8'),  ("https://assmat.loire-atlantique.fr/%s" % (byMail) if byMail != None else "").encode('utf-8'))
    db.execute("insert or ignore into nounous ('nom_prenom', 'url','date_created') values (?,?,?);", (nom, link, datetime.now().date()))
    db.commit()    
    date_maj_stored = db.execute("select date_maj from nounous where url = ?;", (link, )).fetchone()[0]
    db.execute("update nounous set date_analyzed  = ? where url = ?", (datetime.now().date(), link))
    
    if date_maj_stored and datetime.strptime(date_maj_stored, "%Y-%m-%d").date() != datetime.strptime(dateMaj, '%d/%m/%Y').date():
        print("MAJ %s != %s" % (date_maj_stored, dateMaj))
        db.execute("update nounous SET 'date_maj' = ?, 'date_update' = ?, 'adresse' = ?, 'precisions' = ?, 'dispo_matin' = ?, 'dispo_mercredi_matin' = ?, 'url_email' = ? where url = ?;", (datetime.strptime(dateMaj, '%d/%m/%Y').date(), datetime.now().date(), adresse, precisions, isDispoMatin, isDispoMercredi, "https://assmat.loire-atlantique.fr/%s" % (byMail) if byMail != None else "", link))
    db.commit()
#analyzePageNounou("https://assmat.loire-atlantique.fr/jcms/fatiha-bregeon-nantes-514169-fr-72337_ProfilASSMAT?portal=cra_66992")
#analyzePageNounou("https://assmat.loire-atlantique.fr/jcms/sophie-russeil-nantes-517140-fr-111056_ProfilASSMAT?portal=cra_66992")
#exit()

nounousLinks = findAllNounous()

print "nom;date MAJ; adresse; precisions; isDispoMatin; isDispoMercredi; lien; lien Mail"
for link in nounousLinks:
    analyzePageNounou(link)


