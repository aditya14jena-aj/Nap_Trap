#!/usr/bin/env python3
"""
Pillow Fight Arena - lobby + relay server.

  pip install aiohttp
  python server.py              # serves on 0.0.0.0:8000
  python server.py --port 9000

The host's browser runs the game simulation. This server only handles rooms:
create / join / lobby list / start, and relays inputs (player -> host) and
state snapshots (host -> players).
"""
import argparse
import asyncio
import json
import os
import random
import socket
import traceback

from aiohttp import web, WSMsgType

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_NAMES = ['Pip', 'Bean', 'Mochi', 'Waffle']
MAX_PLAYERS = 4
CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
DIFFS = ('easy', 'normal', 'hard')

rooms = {}


class Member:
    __slots__ = ('ws', 'name', 'slot')

    def __init__(self, ws, name, slot):
        self.ws = ws
        self.name = name
        self.slot = slot


class Room:
    def __init__(self, code):
        self.code = code
        self.members = []          # members[0] is always the host
        self.started = False
        self.plist = []

    @property
    def host(self):
        return self.members[0]

    def free_slot(self):
        used = {m.slot for m in self.members}
        for i in range(MAX_PLAYERS):
            if i not in used:
                return i
        return None

    def lobby_msg(self):
        return {
            't': 'lobby',
            'code': self.code,
            'players': [
                {'slot': m.slot, 'name': m.name, 'host': m is self.members[0]}
                for m in sorted(self.members, key=lambda x: x.slot)
            ],
        }


def clean_name(raw):
    s = ''.join(ch for ch in str(raw or '') if ch.isprintable()).strip()[:10]
    return s or 'Player'


def new_code():
    while True:
        code = ''.join(random.choice(CODE_CHARS) for _ in range(4))
        if code not in rooms:
            return code


def num(v):
    try:
        return max(-1.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


def public_url(request):
    try:
        return _public_url(request)
    except Exception:
        return '%s://%s' % (request.scheme, request.host)


def _public_url(request):
    host = request.host
    hostname = host.rsplit(':', 1)[0] if not host.startswith('[') else host
    if hostname in ('localhost', '127.0.0.1', '[::1]'):
        return 'http://%s:%s' % (lan_ip(), request.app['port'])
    return '%s://%s' % (request.scheme, host)


async def send(ws, obj):
    try:
        if isinstance(obj, str):
            await ws.send_str(obj)
        else:
            await ws.send_str(json.dumps(obj, separators=(',', ':')))
    except Exception as e:
        print('[ws] send failed: %r' % (e,), flush=True)


async def broadcast(room, obj, skip=None):
    targets = [m for m in list(room.members) if m is not skip]
    if targets:
        await asyncio.gather(*(send(m.ws, obj) for m in targets))


async def leave(room, me):
    if rooms.get(room.code) is not room or me not in room.members:
        return
    if me is room.host:
        rooms.pop(room.code, None)
        others = [x for x in room.members if x is not me]
        room.members.clear()
        for x in others:
            await send(x.ws, {'t': 'closed'})
        for x in others:
            try:
                await x.ws.close()
            except Exception:
                pass
    else:
        room.members.remove(me)
        if room.started:
            await send(room.host.ws, {'t': 'left', 'slot': me.slot})
        else:
            await broadcast(room, room.lobby_msg())


async def ws_handler(request):
    ws = web.WebSocketResponse(heartbeat=20, max_msg_size=1 << 20)
    await ws.prepare(request)
    print('[ws] connected from %s' % request.remote, flush=True)
    me = None
    room = None
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                m = json.loads(msg.data)
            except ValueError:
                continue
            if not isinstance(m, dict):
                continue
            t = m.get('t')
            if t not in ('snap', 'in'):
                print('[ws] %s from %s' % (t, request.remote), flush=True)

            # ---- not in a room yet ----
            if room is None:
                if t == 'create':
                    code = new_code()
                    room = Room(code)
                    rooms[code] = room
                    me = Member(ws, clean_name(m.get('name')), 0)
                    room.members.append(me)
                    await send(ws, {'t': 'joined', 'code': code, 'slot': 0,
                                    'host': True, 'url': public_url(request)})
                    print('[ws] room %s created' % code, flush=True)
                    await broadcast(room, room.lobby_msg())
                elif t == 'join':
                    code = str(m.get('code', '')).strip().upper()
                    r = rooms.get(code)
                    if r is None:
                        await send(ws, {'t': 'err', 'msg': 'No room with that code.'})
                    elif r.started:
                        await send(ws, {'t': 'err', 'msg': 'That game already started.'})
                    else:
                        slot = r.free_slot()
                        if slot is None:
                            await send(ws, {'t': 'err', 'msg': 'That room is full.'})
                        else:
                            room = r
                            me = Member(ws, clean_name(m.get('name')), slot)
                            room.members.append(me)
                            await send(ws, {'t': 'joined', 'code': code, 'slot': slot,
                                            'host': False, 'url': public_url(request)})
                            await broadcast(room, room.lobby_msg())
                continue

            # ---- player (not host) ----
            if me is not room.host:
                if t == 'in' and room.started:
                    await send(room.host.ws, {
                        't': 'in', 'slot': me.slot,
                        'mx': num(m.get('mx')), 'my': num(m.get('my')),
                        'down': bool(m.get('down')),
                    })
                continue

            # ---- host ----
            if t == 'snap':
                if room.started:
                    await broadcast(room, msg.data, skip=me)
            elif t == 'start' and not room.started:
                bots = bool(m.get('bots'))
                diff = m.get('diff') if m.get('diff') in DIFFS else 'normal'
                humans = {x.slot: x for x in room.members}
                if len(humans) < 2 and not bots:
                    await send(ws, {'t': 'err', 'msg': 'Need at least 2 players (or enable bots).'})
                    continue
                plist = []
                for i in range(MAX_PLAYERS):
                    if i in humans:
                        plist.append({'slot': i, 'name': humans[i].name, 'bot': False})
                    elif bots:
                        plist.append({'slot': i, 'name': DEFAULT_NAMES[i], 'bot': True})
                room.started = True
                room.plist = plist
                room.diff = diff
                await broadcast(room, {'t': 'start', 'players': plist, 'diff': diff})
            elif t == 'rematch' and room.started:
                present = {x.slot for x in room.members}
                for e in room.plist:
                    if not e['bot'] and e['slot'] not in present:
                        e['bot'] = True       # someone left: a bot takes the slot
                await broadcast(room, {'t': 'start', 'players': room.plist, 'diff': room.diff})
            elif t == 'tolobby' and room.started:
                room.started = False
                await broadcast(room, {'t': 'tolobby'})
                await broadcast(room, room.lobby_msg())
    except Exception:
        traceback.print_exc()
    finally:
        print('[ws] disconnected %s' % request.remote, flush=True)
        if room is not None and me is not None:
            await leave(room, me)
    return ws


async def index(request):
    return web.FileResponse(os.path.join(HERE, 'index.html'),
                            headers={'Cache-Control': 'no-cache'})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default=None, help='bind address (default: all interfaces, IPv4+IPv6)')
    ap.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8000)))
    args = ap.parse_args()

    app = web.Application()
    app['port'] = args.port
    app.router.add_get('/', index)
    app.router.add_get('/ws', ws_handler)

    print('Pillow Fight Arena server')
    print('  This machine : http://localhost:%d' % args.port)
    print('  Same network : https://naptrap.vercel.app/%s:%d   <- share this with friends' % (lan_ip(), args.port))
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == '__main__':
    main()