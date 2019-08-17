import os
from pathlib import Path
import subprocess as sp
import re
import datetime as dt
import pickle
from collections import defaultdict
import hashlib

import matplotlib
import matplotlib.pyplot as plt


def run(cmd):
    return sp.run(cmd, check=True, shell=True, stdout=sp.PIPE, stderr=sp.DEVNULL, encoding='utf8')


def _texcount(fn_globs):
    return run('texcount -sum -brief {}'.format(' '.join(fn_globs))).stdout


def _git_check_on_master():
    return re.search('\* master', run('git branch').stdout.strip())


def _git_ordered_tags():
    return run('git tag --sort=committerdate').stdout.split('\n')


def _git_revisions():
    return run('git rev-list master').stdout.split('\n')[::-1]


def _git_checkout(rev):
    # Don't care about output.
    sp.run('git checkout {}'.format(rev), check=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL, shell=True)


def _git_status():
    # Want to show output.
    sp.run('git status', shell=True)


def _git_rev_date():
    return parse_git_datetime(run('git show -s --format=%ci').stdout.strip())


def get_tex_summary_info(*fn_globs):
    texcount_output = _texcount(fn_globs)
    if re.search('!!!', texcount_output):
        raise TexCountError(texcount_output)
    counts_for_fns = {}

    for line in texcount_output.split('\n'):
        if not line:
            continue
        split_line = line.split(':')
        if len(split_line) == 3:
            word_count = int(split_line[0])
            # Hack to make ch01_introduction appear the same as ch01 (deals with renames).
            filename = split_line[2].strip()[:4]
        elif len(split_line) == 2:
            word_count = int(split_line[0])
            filename = 'totl'
        else:
            raise Exception(split_line)
        counts_for_fns[filename] = word_count

    return counts_for_fns


def parse_git_datetime(s):
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S %z')


class TexCountError(Exception):
    pass


class TexGitInfo:
    def __init__(self, tex_dir, fn_globs, use_tags=False):
        self.tex_dir = tex_dir
        self.fn_globs = fn_globs
        self.use_tags = use_tags
        fn_globs_hash = hashlib.sha1(' '.join(self.fn_globs).encode()).hexdigest()
        print(fn_globs_hash[:10])
        self.cache_dir = tex_dir / '.tex_git_info' / fn_globs_hash[:10]
        if not self.cache_dir.exists():
            self.cache_dir.mkdir()

    def run(self):
        orig_dir = Path.cwd()
        os.chdir(self.tex_dir)
        self.error = False
        if not _git_check_on_master():
            raise Exception('Not on master')

        try:
            if self.use_tags:
                rev_list = _git_ordered_tags()
            else:
                rev_list = _git_revisions()

            self.dates_for_fn = defaultdict(list)
            self.counts_for_fn = defaultdict(list)
            self.commits_for_fn = defaultdict(list)
            self.all_dates = {}
            counter = 0

            for rev in rev_list:
                if not rev:
                    continue
                rev_cache = self.cache_dir / rev
                if rev_cache.exists():
                    with rev_cache.open('rb') as rc:
                        date, fn_counts = pickle.load(rc)
                else:
                    _git_checkout(rev)
                    date = _git_rev_date()
                    try:
                        fn_counts = get_tex_summary_info(*self.fn_globs)
                    except TexCountError as tce:
                        print(f'ERROR: {rev}')
                        print(f'ERROR: {tce}')
                        continue

                print(f'{rev}: {date}')

                with rev_cache.open('wb') as rc:
                    pickle.dump((date, fn_counts), rc)

                for fn, count in fn_counts.items():
                    self.counts_for_fn[fn].append(count)
                    self.dates_for_fn[fn].append(date)
                    self.commits_for_fn[fn].append(rev)
                    if date not in self.all_dates:
                        self.all_dates[date] = counter
                        counter += 1
        except Exception as e:
            print(e)
            _git_status()
            self.error = True
        finally:
            _git_checkout('master')
            os.chdir(orig_dir)

    def plot(self, use_date=True, show=True, display_tex_dir=False):
        if not self.error:
            plt.figure('word_counts')
            plt.title('word counts')
            for fn, counts in self.counts_for_fn.items():
                dates = self.dates_for_fn[fn]
                commits = self.commits_for_fn[fn]
                label = self.tex_dir.parts[-1] + ' / ' + fn if display_tex_dir else fn
                if not self.use_tags:
                    commits = range(len(commits))
                if use_date:
                    plt.plot(dates, counts, label=label)
                else:
                    plt.plot(commits, counts, label=label)
            plt.legend()
            if use_date or self.use_tags:
                plt.xticks(rotation=90)
            plt.tight_layout()

            if show:
                plt.show()


def main(tex_dir, fn_globs, use_tags, use_date):
    tex_git_info = TexGitInfo(tex_dir, fn_globs, use_tags)
    tex_git_info.run()
    tex_git_info.plot(use_date=use_date)
    return tex_git_info
