#!/bin/bash
str="curl"
str=$str" http://foleo.appspot.com/n-$@/raw"
eval $str
