#!/usr/bin/env python

# SPDX-FileCopyrightText: 2021 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0-only

import dataclasses
import hashlib
import re
import shelve
import subprocess

import tqdm

CUTOFF_SIZE = 2**10
SHELVE = '/tmp/progressbar-all-the-things.db'
MIN_CMD_LEN = 12


BPFTRACE_CODE = rb"""
BEGIN { @activity = 0; }
tracepoint:syscalls:sys_enter_write / comm != "bpftrace" / {
    //if (args->fd == 1 || args->fd == 2) {
        @[pid] += args->count;
        @activity = 1;
    //}
}

interval:ms:20 {
    if (@activity == 1) {
        print(@);
        clear(@);
        @activity = 0;
    }
}

tracepoint:syscalls:sys_enter_exec* {
    @[pid] = 0;
    printf("!exec %d %s ", pid, comm);
    join(args->argv);
    print("\n");
}

tracepoint:sched:sched_process_exit {
    if (@activity == 1) {
        print(@);
        clear(@);
        @activity = 0;
    }
    printf("!exit %d\n", pid);
}
"""


def hash(cmdline):
    return hashlib.sha256(cmdline)


def bpftrace():
    proc = subprocess.Popen(['sudo', 'bpftrace', '-'],
                            stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    proc.stdin.write(BPFTRACE_CODE)
    proc.stdin.close()
    for line in proc.stdout:
        yield line


@dataclasses.dataclass
class ProcessRecord:
    pid: int
    comm: bytes
    cmdline: bytes
    hash: bytes
    hashdigest: str
    written: int


class StatsKeeper():
    def __init__(self):
        try:
            with shelve.open(SHELVE) as db:
                self.previously_written = db['previously_written']
        except KeyError:
            self.previously_written = {}
        self.tracked_processes = {}
        self.notable_processes = {}
        self.bars = {}

    def save(self):
        with shelve.open(SHELVE) as db:
            db['previously_written'] = self.previously_written

    def run(self):
        for line in bpftrace():
            if m := re.match(rb'!exec (\d+) (\S*) (.*)\n', line):
                pid, comm, cmdline = int(m[1]), m[2], m[3]
                self.start_tracking(pid, comm, cmdline)
            elif m := re.match(rb'@\[(\d+)\]: (\d+)\n', line):
                pid, current_written = int(m[1]), int(m[2])
                self.account(pid, current_written)
            elif m := re.match(rb'!exit (\d+)\n', line):
                pid = int(m[1])
                self.stop_tracking(pid)
            else:
                pass

    def start_tracking(self, pid, comm, cmdline):
        if len(cmdline) < MIN_CMD_LEN:
            return
        if pid in self.tracked_processes:
            self.stop_tracking(pid)
        self.tracked_processes[pid] = ProcessRecord(pid, comm, cmdline,
                                                    hash(cmdline).digest(),
                                                    hash(cmdline).hexdigest(),
                                                    0)

    def account(self, pid, current_written):
        if pid in self.tracked_processes:
            pr = self.tracked_processes[pid]
            pr.written += current_written
            if pr.written > CUTOFF_SIZE:
                if pid not in self.notable_processes:
                    self.promote_to_notable(pr)
                self.bars[pid].update(current_written)

    def promote_to_notable(self, pr):
        self.notable_processes[pr.pid] = pr
        desc = f'{pr.pid:7d} {pr.comm.decode()[:15]}'
        fmt = '{l_bar}{bar}|{remaining}'
        if pr.hash in self.previously_written:
            prev_written = self.previously_written[pr.hash]
            self.bars[pr.pid] = tqdm.tqdm(total=prev_written,
                                          leave=False,
                                          bar_format=fmt, desc=desc,
                                          mininterval=.05, delay=.05,
                                          maxinterval=.15, miniters=1)
        else:
            self.bars[pr.pid] = tqdm.tqdm(leave=False,
                                          bar_format=fmt, desc=desc,
                                          mininterval=.05, delay=.05,
                                          maxinterval=.15, miniters=1)

    def stop_tracking(self, pid):
        if pid in self.tracked_processes:
            pr = self.tracked_processes[pid]
            del self.tracked_processes[pid]
            if pid in self.notable_processes:
                self.previously_written[pr.hash] = pr.written
                del self.notable_processes[pid]
                self.bars[pid].close()
                del self.bars[pid]
            del pr


def main():
    sk = StatsKeeper()
    try:
        sk.run()
    except KeyboardInterrupt:
        sk.save()


if __name__ == '__main__':
    main()
