#!/usr/bin/env bash

#set -e

VERSION_IRI=$1
DATE=$(echo "$VERSION_IRI" |grep -Eo '[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}' )
DATA_DICT=$(echo $VERSION_IRI | sed 's:.*/::')
DATA_DICT_PATH="data_dictionaries/$DATA_DICT"

if git rev-parse --git-dir > /dev/null 2>&1; then
  git checkout master --quiet
  git pull --quiet
  COMMIT_IDS=$(git log --follow -- "$DATA_DICT_PATH" | grep commit | sed 's/^commit //')
  for COMMIT_ID in $COMMIT_IDS
    do
      if git checkout "$COMMIT_ID" "$DATA_DICT_PATH" --quiet &> /dev/null; then
        # If we can find the version iri in the file, return the corresponding raw gh URL
        if grep -q "$VERSION_IRI" "$DATA_DICT_PATH"; then
          echo "https://raw.githubusercontent.com/IHCC-cohorts/data-harmonization/$COMMIT_ID/data_dictionaries/$DATA_DICT";
          exit 0
        else
          DATE_COMMIT=$(git show -s --format='%ci' "$COMMIT_ID" --quiet)
          # if the date of the commit is newer than the data of the IRI, stop searching - this is highly unlikely to happen
          if [[ "$DATE" > "$DATE_COMMIT" ]] ;
          then
              echo "No version found"
              exit 1
          fi
        fi
      else
          echo "No version found (last commit checked did not have the file)"
          exit 1
      fi
    done
else
  echo "Not a git repo, aborting"
  exit 1
fi
echo "No version found (unknown error)"
exit 1