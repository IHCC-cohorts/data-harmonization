#!/usr/bin/env bash
#
# This simple CGI script helps create a tree browser for ONTIE

cd ..

URL="http://example.com?${QUERY_STRING}"
DB=$(urlp --query --query_field=db "${URL}")
ID=$(urlp --query --query_field=id "${URL}")
TEXT=$(urlp --query --query_field=text "${URL}")
PROJECT=$(urlp --query --query_field=project-name "${URL}")
BRANCH=$(urlp --query --query_field=branch-name "${URL}")

# Check that the sqlite database exists
if ! [[ -s build/${DB}.db ]]; then
	rm build/${DB}.db > /dev/null 2>&1
	make build/${DB}.db > /dev/null 2>&1
fi

if [[ ${TEXT} ]]; then
	echo "Content-Type: application/json"
	echo ""
	python3 -m gizmos.search build/${DB}.db "${TEXT}"
else
	echo "Content-Type: text/html"
	echo ""

	if [[ ${ID} ]]; then
		python3 -m gizmos.tree build/${DB}.db ${ID} -H "?db=${DB}&id={curie}" -s
	else
		python3 -m gizmos.tree build/${DB}.db -H "?db=${DB}&id={curie}" -s
	fi

	echo "<a href=\"/${PROJECT}/branches/${BRANCH}\"><b>Return Home</b></a>"
fi
