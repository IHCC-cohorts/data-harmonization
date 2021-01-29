#!/bin/sh
#
# Given an URL path, return an HTTP 301 to GitHub or a 404.
# Can also be called as a CGI script, which expects a PATH_INFO.

PATH_INFO=${PATH_INFO=$1}
GITHUB="https://raw.githubusercontent.com/IHCC-cohorts/data-harmonization"
LOCATION=""

# Determine PURL type: latest or versioned.
LATEST=$(expr "${PATH_INFO}" : '^/[[:alpha:]]\+.owl$')
VERSIONED=$(expr "${PATH_INFO}" : '^/[[:alpha:]]\+/releases/[[:digit:]]\+-[[:digit:]]\+-[[:digit:]]\+/[[:alpha:]]\+.owl$')

# echo ${LATEST} ${VERSIONED} ${PATH_INFO}

# Get the version date for a commit and a file as an integer, e.g. 20210101
date() {
   git show $1:data_dictionaries/${2} \
   | grep -m1 "owl:versionIRI rdf:resource=" \
   | sed 's/.*\([0-9][0-9][0-9][0-9]\)-\([0-9][0-9]\)-\([0-9][0-9]\).*/\1\2\3/'
}

if [ ${LATEST} -gt 0 ]; then
    FILE="$(echo ${PATH_INFO} | sed s:/::)"
    if [ -f "data_dictionaries/${FILE}" ]; then
        LOCATION="${GITHUB}/master/data_dictionaries/${FILE}"
    fi
elif [ ${VERSIONED} -gt 0 ]; then
    DATE=$(echo "${PATH_INFO}" | cut -d'/' -f4 | sed 's/-//g')
    FILE=$(echo "${PATH_INFO}" | cut -d'/' -f5)
    COMMIT_IDS=$(git log --follow -- "data_dictionaries/${FILE}" | grep commit | sed 's/^commit //')
    for COMMIT_ID in $COMMIT_IDS
        do
            DATE2="$(date ${COMMIT_ID} ${FILE})"
            if [ "${DATE2}" -eq "${DATE}" ]; then
                LOCATION="${GITHUB}/${COMMIT_ID}/data_dictionaries/${FILE}"
                break
            elif [ "${DATE2}" -lt "${DATE}" ]; then
                break
            fi
    done
fi

if [ "${LOCATION}" ]; then
    echo "Status: 301 Moved Permanently"
    echo "Location: ${LOCATION}"
else
    echo "Status: 404 Not Found"
fi

echo "Content-Type: text/html"
