#!/usr/bin/env bash

page=1

year="2024"
month="04"
day="26"
date="$month-$day"

estatement_date="05-21"

pdftk eStatement_"$year"-"$estatement_date".pdf cat 1 output "$date"/CreditCard.pdf
pdftoppm -jpeg $date/CreditCard.pdf $date/Creditcard
rm $date/CreditCard.pdf
mv $date/CreditCard-1.jpg $date/CreditCard.jpg
