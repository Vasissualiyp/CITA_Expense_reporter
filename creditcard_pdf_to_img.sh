#!/usr/bin/env bash

month="05"
day="31"
date="$month-$day"

pdftoppm -jpeg $date/CreditCard.pdf $date/Creditcard
