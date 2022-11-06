#!/bin/bash
sed -i -E 's/$/\r/' e2e_tests/Many_email.in
function slowcat(){ while read; do sleep .05; echo "$REPLY" ; done; }
cat e2e_tests/Many_email.in | slowcat | nc localhost 1025