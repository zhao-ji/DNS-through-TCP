#! /usr/bin/env python
# -*- coding: utf8 -*-

import argparse
import socket
from SocketServer import ForkingUDPServer, DatagramRequestHandler
import struct


from dnslib import DNSRecord
import logbook


class ProxyHandler(DatagramRequestHandler):
    '''DNS Proxy Server'''
    def handle(self):
        data, client = self.request

        domain = str(DNSRecord.parse(data).q.qname)
        logbook.info("query name: {}".format(domain))

        basic_domain = ".".join(domain.rstrip(".").split(".")[-2:])
        logbook.info(basic_domain)
        if basic_domain in CHINA_DOMAIN_LIST:
            logbook.info("Go dirty DNS")
            sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            sock.sendto(data, DIRTY_DNS)
            ret_data, _ = sock.recvfrom(8192)
        else:
            logbook.info("Go pure DNS")
            send_data = struct.pack("!H", len(data)) + data
            recv_data = send_tcp(send_data)
            ret_data = recv_data[2:]

        ip_list = "\n".join(
            [str(r.rdata) for r in DNSRecord.parse(ret_data).rr]
            )
        logbook.info("record name:\n{}".format(ip_list))
        client.sendto(ret_data, self.client_address)

def send_tcp(data):
    """
        Helper function to send/receive DNS TCP request
        (in/out packets will have prepended TCP length header)
    """
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect(PURE_DNS)
    sock.sendall(data)
    response = sock.recv(8192)
    # try:
    #     assert len(response) >= 2
    # except AssertionError:
    #     sock.close()
    #     logbook.error("ops! empty response")
    # else:
    length = struct.unpack("!H",bytes(response[:2]))[0]
    while len(response) - 2 < length:
        response += sock.recv(8192)
    sock.close()
    return response


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="DNS Proxy")
    p.add_argument(
        "--port","-p", type=int, default=53,
        metavar="<port>",
        help="Local proxy port (default:53)")
    p.add_argument(
        "--address", "-a", default="127.0.0.1",
        metavar="<address>",
        help="Local proxy listen address (default:all)")
    p.add_argument(
        "--pure", "-f", default="8.8.8.8:53",
        metavar="<dns server:port>",
        help="Pure foreign DNS server:port (default:8.8.8.8:53)")
    p.add_argument(
        "--dirty", "-d", default="114.114.114.114:53",
        metavar="<dns server:port>",
        help="Dirty china DNS server:port (default:114.114.114.114:53)")
    args = p.parse_args()

    args.pure_dns, _, args.pure_dns_port = \
        args.pure.partition(':')
    args.pure_dns_port = int(args.pure_dns_port or 53)
    args.dirty_dns, _, args.dirty_dns_port = \
        args.dirty.partition(':')
    args.dirty_dns_port = int(args.dirty_dns_port or 53)

    PURE_DNS = (args.pure_dns, args.pure_dns_port)
    DIRTY_DNS = (args.dirty_dns, args.dirty_dns_port)

    from china_domain import china_domain_list as CHINA_DOMAIN_LIST

    server = ForkingUDPServer((args.address, args.port), ProxyHandler)
    logbook.info(
        "Start proxy server at {}:{}"
        .format(args.address, args.port))

    server.serve_forever()
