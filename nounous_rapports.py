import os
import sqlite3
from datetime import datetime
import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)

appDir= os.environ['HOME']+"/.nounous"

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


print "nouvelles nounous"
for nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email in db.execute("select nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email from nounous where date_created = ?;", (datetime.now().date(),)):
    print "%s;%s;%s;%s;%s;%s;%s;%s" % (nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email)
print ";;;;;;"
print "nounous maj;;;;;;"
for nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email in db.execute("select nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email from nounous where date_update = ?;", (datetime.now().date(),)):
    print "%s;%s;%s;%s;%s;%s;%s;%s" % (nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email)
print ";;;;;;"
print "nounous supprimees;;;;;;"
for nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email in db.execute("select nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email from nounous where date_analyzed <> ?;", (datetime.now().date(),)):
    print "%s;%s;%s;%s;%s;%s;%s;%s" % (nom_prenom, date_maj, adresse, precisions, dispo_matin, dispo_mercredi_matin, url, url_email)
