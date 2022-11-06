#!/bin/bash

# Creator: Michael Mai

diff_out=diff.txt
err_log=err.txt
command="coverage run --append server.py config.txt"

rm -f .coverage $diff_out $err_log

for in in $(find e2e_tests -mindepth 1 -wholename '*.in' 2> /dev/null)
do
    out=$(echo $in | sed -e "s/\.in$/\.out/g")
    echo $in | nc localhost 1025 | $command 2>> $err_log | diff - $out >> $diff_out
done

coverage report