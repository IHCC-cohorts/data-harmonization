#!/bin/sh

echo "TEST 301"
echo ""
sh resolve_purl.sh vz.owl
sh resolve_purl.sh vz/releases/2020-12-01/vz.owl
sh resolve_purl.sh vz/releases/2020-10-07/vz.owl
sh resolve_purl.sh ge/releases/2020-09-24/ge.owl

echo "TEST 404"
echo ""
sh resolve_purl.sh vz/2020-12-01/vz.owl
sh resolve_purl.sh vz/releases/2020-12-02/vz.owl
#sh resolve_purl.sh vz/releases/2020-10-08/vz.owl
#sh resolve_purl.sh vz/releases/2028-12-02/vz.owl
#sh resolve_purl.sh vz/releases/2020-10-03/ge.owl
#sh resolve_purl.sh ge/releases/2020-09-27/ge.owl
