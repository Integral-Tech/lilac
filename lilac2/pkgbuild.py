# PKGBUILD related stuff that lilac uses (excluding APIs)

import os
import subprocess
from typing import List, Set

import pyalpm

_official_repos = ['core', 'extra', 'community', 'multilib']
_official_packages: Set[str] = set()
_official_groups: Set[str] = set()

class ConflictWithOfficialError(Exception):
  def __init__(self, groups, packages):
    self.groups = groups
    self.packages = packages

def init_data(dbpath: os.PathLike) -> None:
  for _ in range(3):
    p = subprocess.run(
      ['fakeroot', 'pacman', '-Sy', '--dbpath', dbpath],
    )
    if p.returncode == 0:
      break
  else:
    p.check_returncode()

  H = pyalpm.Handle('/', dbpath)
  for repo in _official_repos:
    db = H.register_syncdb(repo, 0)
    _official_packages.update(p.name for p in db.pkgcache)
    _official_groups.update(g[0] for g in db.grpcache)

def check_srcinfo() -> None:
  srcinfo = get_srcinfo()
  bad_groups = []
  bad_packages = []

  for line in srcinfo:
    line = line.strip()
    if line.startswith('group = '):
      g = line.split()[-1]
      if g in _official_groups:
        bad_groups.append(g)
    elif line.startswith('replaces = '):
      pkg = line.split()[-1]
      if pkg in _official_packages:
        bad_packages.append(pkg)

  if bad_groups or bad_packages:
    raise ConflictWithOfficialError(bad_groups, bad_packages)

def get_srcinfo() -> List[str]:
  out = subprocess.check_output(
    ['makepkg', '--printsrcinfo'],
    universal_newlines = True,
  )
  return out.splitlines()
