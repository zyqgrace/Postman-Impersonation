#!/bin/bash
sed -i -E 's/$/\r/' e2e_tests/Syntax_err.in
function slowcat(){ while read; do sleep .05; echo "$REPLY" ; done; }
cat e2e_tests/Syntax_err.in | slowcat | nc localhost 1025