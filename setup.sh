#!/usr/bin/sh

cat ./dnsmasq-china-list/accelerated-domains.china.conf \
| awk 'BEGIN {print "china_domain_list = ["} 
    {
        # match($0, /\/(.*)\//);
        # print "    ", substr($0, RSTART+1, RLENGTH-2), ","
        split($0, array, "/");
        printf "    \"%s\"%s\n", array[2], ",";
    }
    END {print "]"}' \
> china_domain.py
