#!/bin/sh
#
# Given an URL path, return an HTTP 301 to GitHub or a 404.
# Can also be called as a CGI script, which expects a QUERY_STRING.

PATH_INFO=${QUERY_STRING=$1}
GITHUB="https://raw.githubusercontent.com/IHCC-cohorts/data-harmonization"
ROOT="/opt/data-harmonization"
DICTS="data_dictionaries"
LOCATION=""

# We need to run `git` commands from the repository root.
if [ -d "${ROOT}" ]; then
    cd "${ROOT}"
else
    cd ..
fi

# Determine PURL type: term, latest, or versioned.
TERM=$(expr "${PATH_INFO}" : '^[[:alpha:]]\+_[[:digit:]]\+$')
LATEST=$(expr "${PATH_INFO}" : '^[[:alpha:]]\+.owl$')
VERSIONED=$(expr "${PATH_INFO}" : '^[[:alpha:]]\+/releases/[[:digit:]]\+-[[:digit:]]\+-[[:digit:]]\+/[[:alpha:]]\+.owl$')

# Get the version date for a commit and a file as an integer, e.g. 20210101
date() {
    COMMIT_ID=$1
    FILE=$2
    git show "${COMMIT_ID}:${DICTS}/${FILE}" \
    | grep -m1 "owl:versionIRI rdf:resource=" \
    | sed 's/.*\([0-9][0-9][0-9][0-9]\)-\([0-9][0-9]\)-\([0-9][0-9]\).*/\1\2\3/'
}

if [ ${TERM} -gt 0 ]; then
    ONTOLOGY=$(echo "${PATH_INFO}" | cut -d'_' -f1 | tr '[:upper:]' '[:lower:]')
    FILE="${ONTOLOGY}.owl"
    if [ -f "${DICTS}/${FILE}" ]; then
        LOCATION="https://registry.ihccglobal.app/ontologies/${ONTOLOGY}/terms?iri=https%3A%2F%2Fpurl.ihccglobal.org%2F${PATH_INFO}"
    fi
elif [ ${LATEST} -gt 0 ]; then
    FILE="${PATH_INFO}"
    if [ -f "${DICTS}/${FILE}" ]; then
        LOCATION="${GITHUB}/master/data_dictionaries/${FILE}"
    fi
elif [ ${VERSIONED} -gt 0 ]; then
    DATE=$(echo "${PATH_INFO}" | cut -d'/' -f3 | sed 's/-//g')
    FILE=$(echo "${PATH_INFO}" | cut -d'/' -f4)
    COMMIT_IDS=$(git log --follow -- "${DICTS}/${FILE}" | grep commit | sed 's/^commit //')
    for COMMIT_ID in $COMMIT_IDS
        do
            DATE2="$(date ${COMMIT_ID} ${FILE})"
            if [ "${DATE2}" -eq "${DATE}" ]; then
                LOCATION="${GITHUB}/${COMMIT_ID}/${DICTS}/${FILE}"
                break
            elif [ "${DATE2}" -lt "${DATE}" ]; then
                break
            fi
    done
fi

if [ "${LOCATION}" ]; then
    echo "Status: 301 Moved Permanently"
    echo "Location: ${LOCATION}"
    echo "Content-Type: text/html"
    echo ""
    echo "${LOCATION}"
else
    echo "Status: 404 Not Found"
    echo "Content-Type: text/html"
    echo ""
    echo "Error 404: Not Found"
fi
