#!/usr/bin/env bash

set -e

# VERSION_IRI = $1
VERSION_IRI="https://purl.ihccglobal.org/vz/releases/2020-12-01/vz.owl"
DATE=$(echo "$VERSION_IRI" |grep -Eo '[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}' )
DATE=$DATE" 23:59:59"
DATA_DICT=$(echo $VERSION_IRI | sed 's:.*/::')

echo $DATE

echo $DATA_DICT


if git rev-parse --git-dir > /dev/null 2>&1; then
  git checkout master --quiet
  git pull --quiet
  #git checkout 'master@{'"$DATE"'}' --quiet
  #COMMIT_ID=$(git rev-parse --verify HEAD@{"$DATE"})
  #echo "https://raw.githubusercontent.com/IHCC-cohorts/data-harmonization/$COMMIT_ID/data_dictionaries/$DATA_DICT"
  
  #git checkout 'master@{'"$DATE"'}' --quiet
  COMMIT_ID2=$(git log -n1 --before "$DATE" --pretty=format:"%h")
  echo "https://raw.githubusercontent.com/IHCC-cohorts/data-harmonization/$COMMIT_ID2/data_dictionaries/$DATA_DICT"

  
else
  echo "Not a git repo, aborting"
fi