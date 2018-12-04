
source bin/activate

python  nounous.py 1> NOUNOUS_$(date +%Y%m%d).csv 2> NOUNOUS_$(date +%Y%m%d).log

deactivate

soffice NOUNOUS.ods
