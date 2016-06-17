#!/bin/bash

printf -v west "%.0f" "$1"
printf -v north "%.0f" "$2"
printf -v east "%.0f" "$3"
printf -v south "%.0f" "$4"

echo $west $north $east $south
