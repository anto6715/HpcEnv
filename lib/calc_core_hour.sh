#!/bin/bash
isleap() { date -d $1-02-29 &>/dev/null && return 0 || return 1; }
user=${1:-`whoami`}
period=${2:-w}
if [ "$period" != "m" ] && [ "$period" != "w" ]; then
    echo "Usage: $0 <user> <period: m or w>" >&2
    exit 1
fi
today=$(date -u "+%Y%m%d")
isleap ${today:0:4}
leap=$?
lastMond=$(date -u -d "next monday - 14 days" +%Y%m%d)
lastMonth=$(date -u -d "${today} -1 month" "+%Y%m05")
file_in=/users_home/.accounting/last_week_${lastMond}/${user}-acct-${lastMond}.csv
days=7
if [ "$period" == "m" ];then
  file_in=/users_home/.accounting/last_month_${lastMonth}/${user}-acct-${lastMonth}.csv
  days=$(cal $(date +"%m %Y" --date "last month") | awk 'NF {DAYS = $NF}; END {print DAYS}')
fi
echo $file_in
ls $file_in
res=$(awk '{gsub(/\"/,"")};1' ${file_in}| awk -F "," '{ sum += $13 } END { print sum }')
#project=$(awk '{gsub(/\"/,"")};1' ${file_in}|tail -1| awk -F ";" '{ print $6 }')
#project_all=$(/zeus/opt/tools/bin/bprojects | grep $project)
#project_all=$(grep $project /work/opa/${USER}/bprojects.txt)
one_day=`echo ${res}/${days} | bc`
#echo "Project: ${project_all}"
echo "Core seconds = ${one_day}"
core_hour=`echo ${one_day}/3600|bc`
core_hour_feb=`echo ${core_hour}*28|bc`
[ $leap -eq 0 ] && core_hour_feb=`echo ${core_hour}*29|bc`
core_hour_30=`echo ${core_hour}*30|bc`
core_hour_31=`echo ${core_hour}*31|bc`
echo "Core Hour for one day = ${core_hour}"
echo "Estimated monthly usage in the future:"
echo -e "JAN\tFEB\tMAR\tAPR\tMAI\tJUN\tJUL\tAUG\tSEP\tOCT\tNOV\tDEC"
echo -e "${core_hour_31}\t${core_hour_feb}\t${core_hour_31}\t${core_hour_30}\t${core_hour_31}\t${core_hour_30}\t${core_hour_31}\t${core_hour_31}\t${core_hour_30}\t${core_hour_31}\t${core_hour_30}\t${core_hour_31}"
