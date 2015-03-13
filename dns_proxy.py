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
        logbook.info(
            "query name: {}"
            .format(DNSRecord.parse(data).q.qname))
        send_data = struct.pack("!H", len(data)) + data
        recv_data = send_tcp(send_data)[2:]
        logbook.info(
            "record name: {}"
            .format(DNSRecord.parse(recv_data).a.rname))
        client.sendto(recv_data, self.client_address)

def send_tcp(data):
    """
        Helper function to send/receive DNS TCP request
        (in/out packets will have prepended TCP length header)
    """
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect((args.dns, args.dns_port))
    sock.sendall(data)
    response = sock.recv(8192)
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
        "--upstream", "-u", default="8.8.8.8:53",
        metavar="<dns server:port>",
        help="Upstream DNS server:port (default:8.8.8.8:53)")
    args = p.parse_args()

    args.dns, _, args.dns_port = args.upstream.partition(':')
    args.dns_port = int(args.dns_port or 53)

    server = ForkingUDPServer((args.address, args.port), ProxyHandler)
    logbook.info(
        "Start proxy server at {}:{}"
        .format(args.address, args.port))
    logbook.info(
        "Connect DNS server at {}:{}"
        .format(args.dns, args.dns_port))

    server.serve_forever()
