#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

This script generates an HTML file that contains a report about all
Buildroot packages, their usage of the different package
infrastructure and possible cleanup actions

Run the script from the Buildroot toplevel directory:

 ./support/scripts/pkg-stats /tmp/pkg.html

"""
import fnmatch
import distutils
import time
import ftplib
import glob
import logging
import os
import re
import subprocess
import sys
import urllib2
import sysconfig

TEMPLATE = """
<html>
<head>
  <title>Buildroot packages updates</title>
  <style>
    table {
      width: 100%;
    }
    td {
      border: 1px solid black;
    }
    td.centered {
      text-align: center;
      }
    td.nok {
      background: #ff9a69;
      text-align: center;
    }
    td.ok {
      background: #d2ffc4;
      text-align: center;
    }
    td.other {
      background: #ffd870;
      text-align: center;
    }
    td.lotsofpatches {
      background: #ff9a69;
      text-align: center;
    }
</style>
</head>
<body>
 <h1>Buildroot packages updates</h1>
<table id="header" class="tablesorter">
    <thead>
    <th>Package</th>
    <th>Patch count</th>
    <th>Infrastructure</th>
    <th>Licence</th>
    <th>Licence files</th>
    <th>Hash file</th>
    <th>Current version</th>
    <th>Last version</th>
    <th>Provider</th>
    <th>Status</th>
    </thead>
    <tbody>"""

ERR_PROVIDER = ['exception list', 'website not reachable', 'alioth.debian.org']

EXCLUDED_PKGS = [
        "boot/common.mk",
        "linux/linux-ext-fbtft.mk",
        "linux/linux-ext-xenomai.mk",
        "linux/linux-ext-rtai.mk",
        "package/efl/efl.mk",
        "package/freescale-imx/freescale-imx.mk",
        "package/gcc/gcc.mk",
        "package/gstreamer/gstreamer.mk",
        "package/gstreamer1/gstreamer1.mk",
        "package/gtk2-themes/gtk2-themes.mk",
        "package/matchbox/matchbox.mk",
        "package/opengl/opengl.mk",
        "package/qt5/qt5.mk",
        "package/x11r7/x11r7.mk"
]

class Package(object):

    def __init__(self, package_mk_path):
        self.mk_path = package_mk_path
        self.name = os.path.basename(os.path.splitext(package_mk_path)[0])
        self.mk_name = self.name.upper().replace('-', '_')
        self.infra = 'unknown'
        self.infra_host = False
        self.last_version = None
        self.hash = False
        self.license = False
        self.license_files = False
        self.provider = None
        self.source = None
        self.site = None
        self.version = None

        data = sysconfig._parse_makefile(package_mk_path)
        for k in ["SITE", "SOURCE", "VERSION", "LICENSE_FILES", "LICENSE"]:
            k_name = "%s_%s" % (self.mk_name, k)
            if k_name in data.keys():
                value = None if data[k_name] == "" else data[k_name]
                setattr(self, k.lower(), value)

        if "package/qt5/" in self.mk_path:
                data = sysconfig._parse_makefile("package/qt5/qt5.mk")
                self.version = data["QT5_VERSION"]

        if "package/efl/" in self.mk_path:
                data = sysconfig._parse_makefile("package/efl/efl.mk")
                self.version = data["EFL_VERSION"]

        with open(package_mk_path) as f:
            # Everything we could not obtain through the parsing of the mk
            # files will get obtained here.
            for line in f.readlines():
                if "%s_VERSION" % self.mk_name in line and\
                   self.version is None:
                        if "$" in line:
                                continue
                        self.version = line[line.rindex('=')+1:].strip()

                if "-package)" not in line:
                    continue
                self.infra = line[line.rindex('(')+1:-2]
                if "host" in self.infra:
                    self.infra_host = True
                self.infra = self.infra[:self.infra.rindex('-')]

        self.patch_count = self.count_patches()

        if "$" in str(self.version):
                self.version = None

        hash_file = "%s.hash" % os.path.splitext(package_mk_path)[0]
        if os.path.exists(hash_file):
            self.hash = True

        self.provider = self.get_provider()

    def count_patches(self):
        pkg_dir = os.path.join("package", self.name)
        return len(glob.glob1(pkg_dir, "*.patch"))

    def get_provider(self):
        if self.site is None:
            return None

        if "github" in self.site:
            return "github"
        elif "sourceforge" in self.site:
            return "sourceforge"

    def __str__(self):
        # write package name, patch count and infrastructure
        if pkg.patch_count == 0:
            patch_count_class = 'ok'
        elif pkg.patch_count < 5:
            patch_count_class = 'other'
        else:
            patch_count_class = 'lotsofpatches'

        output = '<tr>'
        output += '<td>%s</td>' % pkg.mk_path
        output += '<td class="%s">%s</td>' % (patch_count_class, pkg.patch_count)

        infra_type = None
        if "host" not in pkg.infra:
            infra_type = "target"
        if pkg.infra_host:
            if infra_type is not None:
                infra_type = "%s + host" % infra_type
            else:
                infra_type = "host"
        pkg.infra = pkg.infra.replace('host-', '')
        output += '<td class="ok"><b>%s</b><br/>%s</td>'% (pkg.infra, infra_type)

        for l in ['license', 'license_files', 'hash']:
            td_class = "nok"
            td_text = "No"
            if getattr(pkg, l):
                td_class = "ok"
                td_text = "Yes"
            output += '<td class="%s">%s</td>' % (td_class, td_text)

        output += '<td class="centered">%s</td>' % self.version

        # Last version
        output += '<td class="centered">NA</td>'
        # package provider
        output += '<td class="centered">%s</td>' % self.provider
        # status
        output += '<td class="centered">NA</td>'

        output += '</tr>'
        return output

def sourceforge_find_newer(pkg):
    return "NA"

def github_find_newer(pkg):
    if "raw" in pkg.site:
        return "NA"
    data = pkg.site.split(',')
    try:
        username = data[1]
        reponame = data[2]
        # print "https://github.com/%s/releases" % username
    except IndexError:
        print pkg.mk_path
        print pkg.site

    return "NA"

    # Grab "https://github.com/%s/releases")
    # Do a list of the releases and then look for a new one.
    # print(("DEBUG: %s: github: %s"):format(self.pkg.pkgname, self.project))
    # local data, status = assert(https.request(releasesurl))
    # local latest = self.pkg.pkgver
    # for v in string.gmatch(data, ('a href="/%s/archive/v?([0-9a-z._-]+)%%.tar.gz"'):format(self.project)) do
        #         for _,s in pairs{
        #                         {search="-rc", replace="_rc"},
        #                         {search="-beta", replace="_beta"},
        #                         {search="-alpha", replace="_alpha"},
        #                 } do
        #                 v = string.gsub(v, s.search, s.replace)
        #         end
        #         if apk.version_compare(v, latest) == ">" then
        #                 latest = v
        #         end
        # end
        # if latest == self.pkg.pkgver then
        #         latest = nil
        # end
        # return latest

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        logging.error("You must give a file to write output to.")
        sys.exit(1)

    f = open(sys.argv[1], 'w')
    f.write(TEMPLATE)

    now = time.strftime("%a %b %d %H:%M:%S %Z %Y")
    git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"])

    matches = []
    for dir in ["boot", "linux", "package"]:
        for root, _, filenames in os.walk(dir):
            for filename in fnmatch.filter(filenames, '*.mk'):
                path = os.path.join(root, filename)
                if os.path.dirname(path) in dir:
                    continue
                matches.append(path)

    matches.sort()
    packages = []
    for mk_path in matches:

        if mk_path in EXCLUDED_PKGS:
            continue

        pkg = Package(mk_path)

        if pkg is None:
            continue

        # Find a newer packages if that exists, use the specified function.
        if pkg.provider is not None:
            pkg.last_version = locals()["%s_find_newer" % pkg.provider](pkg)

        packages.append(pkg)
        f.write(str(pkg))

    f.write('</tbody></table>')

    nb_pkgs = len(packages)
    nb_pkgs_infra = {}
    nb_patches = 0
    nb_hashes = 0
    nb_license = 0
    nb_license_files = 0
    for p in packages:
        if p.infra not in nb_pkgs_infra:
            nb_pkgs_infra[p.infra] = 0
            continue
        nb_pkgs_infra[p.infra] += 1
        nb_patches += p.patch_count
        if p.license:
                nb_license += 1
        if p.license_files:
                nb_license_files += 1
        if p.hash:
                nb_hashes += 1
        nb_patches += p.patch_count

    f.write('<table>')
    f.write('<tbody>')

    def add_tr_line(col1, col2):
        f.write('<tr>')
        f.write('<td>%s</td>' % col1)
        f.write('<td>%d</td>' % col2)
        f.write('</tr>')

    for k, v in nb_pkgs_infra.iteritems():
        add_tr_line('Packages using <i>%s</i> infrastructure' % k, v)

    add_tr_line('Packages *NOT* having license information', nb_pkgs - nb_license)

    add_tr_line('Packages having license files information', nb_license_files)
    add_tr_line('Packages *NOT* having license files information', nb_pkgs - nb_license_files)

    add_tr_line('Packages having hash file', nb_hashes)
    add_tr_line('Packages *NOT* having hash file', nb_pkgs - nb_hashes)

    add_tr_line('Number of patches in all packages', nb_patches)

    add_tr_line('TOTAL:', nb_pkgs)

    f.write('</tbody>')
    f.write('</table>')

    f.write('Updated on %s, Git commit %s' % (now, git_hash))

    f.write('</body></html>')

