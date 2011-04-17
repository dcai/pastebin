#!/bin/bash
str="curl"
str=$str" http://foleo.appspot.com/$@/raw"
eval $str
