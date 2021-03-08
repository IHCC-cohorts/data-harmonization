#!/bin/sh

echo "TEST 301"
echo ""
sh resolve_purl.sh VZ_0000001
sh resolve_purl.sh vz.owl
sh resolve_purl.sh vz/releases/2020-12-01/vz.owl
sh resolve_purl.sh vz/releases/2020-10-07/vz.owl
sh resolve_purl.sh ge/releases/2020-09-24/ge.owl

echo ""
echo "TEST 404"
echo ""
sh resolve_purl.sh XXX_123
sh resolve_purl.sh VZ_ABC
sh resolve_purl.sh vz/2020-12-01/vz.owl
sh resolve_purl.sh vz/releases/2020-12-02/vz.owl
