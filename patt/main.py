#!/usr/bin/env python

# SPDX-FileCopyrightText: 2021 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0-only

import dataclasses
import hashlib
import re
import shelve
import subprocess

import tqdm

CUTOFF_SIZE = 2 * 2**10
SHELVE = '/tmp/progressbar-it-all.db'


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
        print("!!!!\n");
        @activity = 0;
    }
}

tracepoint:syscalls:sys_enter_exec* {
    printf("!exec %d %s ", pid, comm);
    join(args->argv);
    print("\n");
    @[pid] += 0;
}

tracepoint:sched:sched_process_exit {
    print(@);
    clear(@);
    print("!!!!\n");
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
                self.previous_processes = db['previous_processes']
        except KeyError:
            self.previous_processes = {}
        self.tracked_processes = {}
        self.notable_processes = {}
        self.bars = {}

    def save(self):
            with shelve.open(SHELVE) as db:
                db['previous_processes'] = self.previous_processes

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
            elif line == b'!!!!\n':
                self.sync()
            else:
                pass

    def start_tracking(self, pid, comm, cmdline):
        self.tracked_processes[pid] = ProcessRecord(pid, comm, cmdline,
                hash(cmdline).digest(), hash(cmdline).hexdigest(), 0)

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
        if pr.hash in self.previous_processes:
            prev = self.previous_processes[pr.hash]
            self.bars[pr.pid] = tqdm.tqdm(total=prev.written, desc=desc,
                                          leave=False, unit='B',
                                          unit_scale=True, unit_divisor=1024,
                                          mininterval=.05, delay=.05,
                                          maxinterval=.15, miniters=1,
                                          )
        else:
            self.bars[pr.pid] = tqdm.tqdm(desc=desc,
                                          leave=False, unit='B',
                                          unit_scale=True, unit_divisor=1024,
                                          mininterval=.05, delay=.05,
                                          maxinterval=.15, miniters=1)

    def sync(self):
        pass
        #for pid, pr in self.notable_processes.items():
        #    self.bars[pid].update(pr.written)
        #print(self.notable_processes)

    def stop_tracking(self, pid):
        if pid in self.tracked_processes:
            pr = self.tracked_processes[pid]
            del self.tracked_processes[pid]
            if pid in self.notable_processes:
                self.previous_processes[pr.hash] = pr
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
