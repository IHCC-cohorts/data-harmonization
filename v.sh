#!/usr/bin/env bash

#set -e

VERSION_IRI=$1
DATE=$(echo "$VERSION_IRI" |grep -Eo '[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}' )
DATA_DICT=$(echo $VERSION_IRI | sed 's:.*/::')

if git rev-parse --git-dir > /dev/null 2>&1; then
  git checkout master --quiet
  git pull --quiet
  COMMIT_IDS=$(git log --follow -- data_dictionaries/vz.owl | grep commit | sed 's/^commit //')
  for COMMIT_ID in $COMMIT_IDS
    do
        ONT="https://raw.githubusercontent.com/IHCC-cohorts/data-harmonization/$COMMIT_ID/data_dictionaries/$DATA_DICT"
        RES="v_$COMMIT_ID.txt"
        if robot query -I $ONT --query sparql/version_iri.sparql "$RES" >/dev/null; then
          V_IRI=$(cat $RES | grep http)
          rm -f $RES
          DATE_V_IRI=$(echo "$V_IRI" |grep -Eo '[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}' )
          if [ "$DATE" == "$DATE_V_IRI" ]; then
            echo $ONT;
            exit 0
          else
            if [[ "$DATE" > "$DATE_V_IRI" ]] ;
            then
                echo "No version found"
                exit 1
            fi  
          fi
        fi
    done
else
  echo "Not a git repo, aborting"
  exit 1
fi
echo "No version found"
exit 1