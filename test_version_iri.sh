#!/usr/bin/env bash

echo "testing successfull ones:"
sh version_iri.sh https://purl.ihccglobal.org/vz/releases/2020-12-01/vz.owl
sh version_iri.sh https://purl.ihccglobal.org/vz/releases/2020-10-07/vz.owl
sh version_iri.sh https://purl.ihccglobal.org/ge/releases/2020-09-24/ge.owl

echo "testing bad ones"
sh version_iri.sh https://purl.ihccglobal.org/vz/releases/2010-12-02/vz.owl
sh version_iri.sh https://purl.ihccglobal.org/vz/releases/2020-12-02/vz.owl
sh version_iri.sh https://purl.ihccglobal.org/vz/releases/2020-10-08/vz.owl
sh version_iri.sh https://purl.ihccglobal.org/vz/releases/2028-12-02/vz.owl
sh version_iri.sh https://purl.ihccglobal.org/vz/releases/2020-10-03/ge.owl
sh version_iri.sh https://purl.ihccglobal.org/ge/releases/2020-09-27/ge.owl