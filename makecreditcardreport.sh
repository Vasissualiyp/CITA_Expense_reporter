#!/usr/bin/env bash

page=3

year="2024"
month="05"
day="31"
date="$month-$day"

estatement_date="06-07"

pdftk eStatement_"$year"-"$estatement_date".pdf cat "$page" output "$date"/creditcard.pdf
pdftoppm -jpeg $date/creditcard.pdf $date/creditcard
rm $date/creditcard.pdf
mv $date/creditcard-1.jpg $date/creditcard.jpg
