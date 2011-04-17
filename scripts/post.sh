#!/bin/bash
str="curl "
id=0
while getopts "t:c:a:l:f:n:" opt;
do
    case $opt in
    t)
    str=$str" -F title=\"$OPTARG\""
    ;;
    c)
    str=$str" -F content=\"$OPTARG\""
    ;;
    a)
    str=$str" -F author=\"$OPTARG\""
    ;;
    l)
    str=$str" -F lang=\"$OPTARG\""
    ;;
    f)
    str=$str" -F file=@$OPTARG"
    ;;
    n)
    echo $OPTARG
    id=$OPTARG
    ;;
    ?)
    echo 'Invalid Parameter!'
    ;;
    esac
done

if [ $id == 0 ]; then
    echo "Error: Code ID must be specified!"
    exit
fi
str=$str" http://localhost:8080/$id/update"
eval $str
