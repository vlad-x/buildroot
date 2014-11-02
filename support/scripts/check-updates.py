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
import distutils
import ftplib
import glob
import logging
import logging
import os
import re
import shutil
import subprocess
import sys
import urllib2

TEMPLATE = """
<html>
<head>
  <title>Buildroot packages updates</title>
  <script src="http://code.jquery.com/jquery-2.0.3.min.js"></script>
  </script><script type="text/javascript" src="jquery.tablesorter.min.js">
  </script>
  <script type="text/javascript">
    $(document).ready(function() {
      $("table.tablesorter").tablesorter();});
  </script>
  <style>
h1 {
    text-align: center;
    background-color: #b8e2f4;
    margin-bottom: 10px;
}
table {
    border-collapse:collapse;
}
td {
    padding: 3px;
    text-align: center;
    border: 1px solid black;
}
tr.header td {
    background-color: #d4d4d4;
}
td.ok {
    background-color: #d9ffc5;
}
td.nok {
    background-color: #ffa879;
}
td.other {
    background-color: #ffd870;
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
PKG_DIR = "package"

NB_PKG = 0
NB_PKG_UPTODATE = 0
NB_PKG_TOUPDATE = 0
NB_PKG_UNKNOWN = 0
NB_PKG_INFRA_AUTOTOOLS = 0
NB_PKG_INFRA_GENERIC = 0
NB_PKG_INFRA_CMAKE = 0
NB_PKG_INFRA_OTHER = 0

# TODO: Python packages updates
# TODO : Lua packages updates

class Package(object):

    def __init__(self, package_name):
        global NB_PKG_INFRA_AUTOTOOLS
        global NB_PKG_INFRA_GENERIC
        global NB_PKG_INFRA_CMAKE
        global NB_PKG_INFRA_OTHER

        self.name = package_name
        self.mk_name = self.name.upper().replace('-','_')
        self.fname = os.path.join('package', package_name, package_name + '.mk')

        self.infra = 'unknown'
        self.last_version = None
        self.license = False
        self.license_files = False
        self.provider = None
        self.source = None
        self.url = None
        self.version = None

        content = None
        with open(self.fname) as f:
            content = f.readlines()

        # Find everything we need in the content of the mk file
        for line in content:
            if line.startswith("%s_SITE" % self.mk_name):
                site_url = line.split('=')[1][:-1].split(' ')[0]
                self.url = site_url.replace('"', '')
            if line.startswith("%s_SOURCE" % self.mk_name):
                self.source = line.split('=')[1][:-1].split(' ')[0]
            if line.startswith("%s_VERSION" % self.mk_name):
                self.version = line.split('=')[1][:-1].split(' ')[0]
            if line.startswith("%s_LICENSE" % self.mk_name):
                self.license = True
            if line.startswith("%s_LICENSE_FILES" % self.mk_name):
                self.license_files = True

            if 'autotools-package' in line:
                self.infra = 'autotools'
                NB_PKG_INFRA_AUTOTOOLS += 1

            if 'generic-package' in line:
                self.infra = 'generic'
                NB_PKG_INFRA_GENERIC += 1

            if 'cmake-package' in line:
                self.infra = 'cmake'
                NB_PKG_INFRA_CMAKE += 1

        if self.infra == 'unknown':
            NB_PKG_INFRA_OTHER += 1

        self.patch_count = self.count_patches()
        # logging.info('site :' + self.url)
        # logging.info('version :' + self.version)
        # logging.debug('package name : ' + package_name)

    def retrieve(self):
        logging.info('retrieving : ' + self.package_name)
        result = self.retrieve_specific()
        return result;

    def retrieve_specific(self):
        logging.error('should not be called')
        return None

    def get_last_version(self):
        try:
            logging.debug('1')
            self.result = self.retrieve()
            logging.debug('2')
            logging.debug(self.result)
        except:
            logging.error('website error')
            return 'website error'
        self.last_version = self.get_last_version_specific()
        return self.last_version

    def get_last_version_specific(self):
        logging.error('should not be called')
        return None

    def clean_version(self):
        return last_version

    def count_patches(self):
        pkg_dir = os.path.join(PKG_DIR, self.name)
        return len(glob.glob1(pkg_dir,"*.patch"))

    def __str__(self):
        print self.name
        print self.mk_name
        print self.fname
        return ""

class Package_www(Package):
    """ Specific www website
        Try to find last version by looking for available downloads on the page
    """
    def __init__(self, package_name):
        super(Package_www, self).__init__(package_name)
        self.provider = 'www'

        logging.debug('www website')

    def retrieve_specific(self):
        logging.debug('retrieve www')
        return urllib2.urlopen(self.url).read()

    def get_last_version_specific(self):
        logging.debug('get_last_version_www')
        package_name_tmp = self.package_name.replace('+', '\+')
        logging.debug('package_name : %s' % package_name_tmp)
        logging.debug(self.result)
        regex = re.compile(r'%s(?:-|.)(.*?)(?:.zip|.tar.gz|.tar.xz|.tgz|.tar.bz2|.js|.bin)' % package_name_tmp, re.IGNORECASE)
        versions = regex.findall(self.result)
        logging.debug(versions)
        versions = [i for i in versions if re.match(r'\D+-', i) == None]
        logging.debug(versions)
        versions = helper_clean_versions(versions)
        logging.debug(versions)
        #versions = [i for i in versions if re.match(r'\D*-*', i) == None]
        #logging.debug(versions)
        if (versions == None) or (len(versions) == 0):
            logging.error('can\'t determine site version')
            return None

        try:
            last_version = helper_get_last_version(versions)
            logging.debug(last_version)
        except:
            logging.error('can\'t determine site version')
            return None

        return last_version

class Package_ftp(Package):
    """ Specific http website
        Try to find last version by listing FTP dir
    """
    def __init__(self, package_name):
        super(Package_ftp, self).__init__(package_name)
        self.provider = 'ftp'

    def retrieve_specific(self):
        logging.debug('retrieve ftp')
        result = None
        logging.debug('1' + self.url);
        base_url = self.url.split('/')[2]
        logging.debug('2' + base_url + '--' + self.url)
        directory = self.url.split(base_url)[1]
        logging.debug('3')
        logging.debug('caching :' + base_url + ' ' + directory)
        ftp = ftplib.FTP(base_url)
        logging.debug('4');
        ftp.login()
        logging.debug('5');
        ftp.cwd(directory)
        logging.debug('6');
        result = []
        ftp.retrlines('LIST', result.append)
        logging.debug('7');
        ftp.quit()
        return result

    def get_last_version_specific(self):
        versions = [i.split(' ')[-1] for i in self.result]
        logging.debug(versions)
        package_name = self.package_name.replace('+', '\+')
        versions = [re.findall(r'%s(?:-|.|)(.*?)(?:.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2|.js|.bin)' % package_name, i) for i in versions]
        logging.debug(versions)
        versions = [i[0] for i in versions if i != []]
        logging.debug(versions)
        versions = helper_clean_versions(versions)
        logging.debug(versions)
        versions = [i for i in versions if re.match(r'\D+-', i) == None]
        logging.debug(versions)

        try:
            last_version = helper_get_last_version(versions)
        except:
            logging.error('can\'t determine last ftp version')
            return None

        return last_version

class Package_svn(Package):
    """ SVN
        We are using svn log to list commits
    """
    def __init__(self, package_name):
        super(Package_svn, self).__init__(package_name)
        self.provider = 'svn'

    def retrieve_specific(self):
        logging.debug('retrieve svn')
        return subprocess.check_output(["svn log --xml %s | grep \"revision\" | head -1" % self.url], shell=True)

    def get_last_version_specific(self):
        logging.debug('get_last_version_specific svn')
        try:
            last_version = self.result.split('revision="')[1].split('"')[0]
            logging.debug(last_version)
        except:
            logging.error('can\'t determine svn version')
            return None

        return last_version

class Package_launchpad(Package_www):
    """ Launchpad
        The following url list the versions available
        https://launchpad.net/PROJECT/+download
    """
    def __init__(self, package_name):
        super(Package_launchpad, self).__init__(package_name)
        self.provider = 'launchpad'
        self.package_name = self.url.split('launchpad.net/')[1].split('/')[0]
        self.url = 'https://launchpad.net/%s/+download' % package_name

    def get_last_version_specific(self):
        versions = re.findall(r'%s(?:-|.)(.*?)(?:.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2|.bin)' % self.package_name, self.result)
        logging.debug(versions)
        versions = helper_clean_versions(versions)
        logging.debug(versions)
        versions = [i for i in versions if re.match(r'\D*-', i) == None]
        logging.debug(versions)
        versions = [i for i in versions if re.search(r'-(.*)', i) == None]
        logging.debug(versions)

        try:
            last_version = helper_get_last_version(versions)
            last_version = last_version.split('/')[-1]
        except:
            logging.error('can\'t determine launchpad version')
            return None

        return last_version

class Package_git(Package):
    """ Git
        We are using git ls-remotes --tags|--heads GIT_REPOSITORY to list tags
    """
    def __init__(self, package_name):
        super(Package_git, self).__init__(package_name)
        self.provider = 'git'

        # get real git url from cgit
        if 'cgit' in self.url and not self.url.endswith('.git'):
            url_tmp = self.url.replace('snapshot', '')
            logging.debug(url_tmp)
            request = urllib2.urlopen(url_tmp).read()
            logging.debug(request)
            res = re.findall(r'\'(git://.*)\'', request)
            if len(res) == 1:
                self.url = res[0]
            else :
                res = re.findall(r'<tr><td colspan=\'\d\'><a href=\'([http.?].*?)\'>', request)
                logging.debug(res)
                self.url = res[0]
            logging.debug(self.url)


    def retrieve_specific(self):
        logging.debug('retrieve git')

        if len(self.version) == 40:
            if 'github.com' in self.url:
                git_url = self.url.split('github.com/')[1]
                git_url = git_url.split('/tarball/')[0]
                git_url = 'https://github.com/' + git_url + '.git'

            if 'git://' in self.url:
                git_url = self.url

            result = subprocess.check_output(["git ls-remote --heads %s" % git_url], shell=True)
            logging.debug(result)
        else:
            # if version is a real version number
            if ('github.com' in self.url):
                git_url = self.url.split('github.com/')[1]
                logging.debug(git_url)
                if ('downloads' in git_url):
                    git_url = git_url.replace('downloads/', '')
                    if git_url[-1] == '/':
                        git_url = git_url[:-1]
                    git_url = 'https://github.com/' + git_url + '.git'
                elif ('tarball' in git_url):
                    git_url = git_url.split('/tarball/')[0]
                    git_url = 'https://github.com/' + git_url + '.git'
                elif ('archive' in git_url):
                   git_url = git_url.split('/archive')[0]
                   git_url = 'https://github.com/' + git_url + '.git'
                else:
                    git_url = 'https://github.com/' + git_url
                logging.debug(git_url)
            else:
                git_url = self.url

            result = subprocess.check_output(["git ls-remote --tags %s" % git_url], shell=True)
        return result

    def get_last_version_specific(self):
        # if version refers to a commit id
        if len(self.version) == 40:
            last_version = re.search(r'(.*)\trefs/heads/master', self.result).group(1)
            logging.debug(last_version)
        else:
            versions = [i.split('\t') for i in self.result.split('\n')]
            versions = [i for i in versions if i[0] != '']
            logging.debug(versions)
            versions = [i[1].replace('refs/tags/', '') for i in versions]
            logging.debug(versions)
            versions = [i.replace('_', '.') for i in versions]
            logging.debug(versions)
            versions = [i for i in versions if '^{}' not in i]
            logging.debug(versions)
            #versions = [i for i in versions if re.match(r'\D*-', i) == None]
            #logging.debug(versions)
            versions = helper_clean_versions(versions)
            logging.debug(versions)
            try:
                last_version = helper_get_last_version(versions)
                logging.debug(last_version)
            except:
                logging.error('can\'t determine git version')
                return None

            # when version starts with v, this should be uniformized (does this word exist?)
            if last_version[0] == 'v' and self.version[0] != 'v':
                last_version = last_version[1:]
            # when version starts with v.
            if last_version[0] == '.' and self.version[0] != '.':
                last_version = last_version[1:]

        return last_version

class Package_sourceforge(Package):
    """ Sourceforge.net
        The following url give you the url of the last version available
        http://sourceforge.net/projects/PROJECT_NAME/files/latest/download
    """
    def __init__(self, package_name):
        super(Package_sourceforge, self).__init__(package_name)
        self.provider = 'sourceforge'
        if '/project/' in self.url:
            self.package_name = self.url.split('project/')[1].split('/')[0]
        elif '/sourceforge/' in self.url:
            self.package_name = self.url.split('/sourceforge/')[1].split('/')[0]
        elif '.cvs.' in self.url:
            self.package_name = self.url.split('http://')[1].split('.')[0]
        elif '.sourceforge.net' in self.url:
            self.package_name = self.url.split('.sourceforge.net')[0].split('//')[1]
        elif '/p/' in self.url:
            self.package_name = self.url.split('/p/')[1].split('/')[0]
        else:
            logging.error('Can\'t find sf package name')
            return None
        self.url = 'http://sourceforge.net/projects/%s/files/latest/download' % self.package_name


    def retrieve_specific(self):
        logging.debug('retrieve sourceforge')
        result = getUrlRedirection(self.url)
        #result = urllib2.urlopen(self.url).geturl()
        logging.debug('retrieve_sf' + self.url)

    def get_last_version_specific(self):
        logging.debug('get_last_version_specific')
        result = urllib2.unquote(self.result) # replace all hexa caracters like %20
        logging.debug(result)

        last_version = result.split('/')[-1]
        logging.debug(last_version)
        filename = self.package_name.replace('+', '\+')
        regex = re.compile(r'%s(-|_|)(.*)(.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2|.bin)' % filename, re.IGNORECASE)
        last_version = regex.search(last_version)
        if last_version == None:
            return None
        last_version = last_version.group(2)
        logging.debug(last_version)
        last_version = helper_clean_last_version(last_version)
        logging.debug(last_version)

        return last_version

class Package_googlecode(Package_www):
    """ googlecode
        The following url give you the url of the last version available
        https://code.google.com/p/PROJECT_NAME/downloads/list
    """
    def __init__(self, package_name):
        super(Package_googlecode, self).__init__(package_name)
        self.package_name = self.url.split('.googlecode.com')[0].split('//')[1]
        self.url = 'https://code.google.com/p/%s/downloads/list' % self.package_name
        self.provider = 'googlecode'

    def retrieve_specific(self):
        logging.debug('retrieve googlecode')
        versions = re.findall(r'%s(?:-|.)(.*?)(?:.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2|.bin)' % filename, self.result)
        logging.debug(versions)
        versions = helper_clean_versions(versions)
        logging.debug(versions)
        versions = [i for i in versions if re.match(r'\D*-', i) == None]
        loggingdebug(versions)
        versions = [i for i in versions if re.search(r'-(.*)', i) == None]
        logging.debug(versions)

        try:
            last_version = helper_get_last_version(versions)
            last_version = last_version.split('/')[-1]
        except:
            logging.error('can\'t determine version from googlecode')
            return None

        return last_version

class Package_pecl_php(Package):
    """ pecl.php.net
        The following url give you the url of the last version available
        pecl.php.net/get/PROJECT_NAME
    """
    def __init__(self, package_name):
        super(Package_pecl_php, self).__init__(package_name)
        self.url = 'http://pecl.php.net/get/%s' % self.package_name
        self.provider = 'pecl.php.net'

    def retrieve_specific(self):
        logging.debug('retrieve pecl.php.net')
        response = urllib2.urlopen(self.url)
        logging.debug(response.info().getheader('Content-Disposition'))
        return response.info().getheader('Content-Disposition')

    def get_last_version_specific(self):
        logging.debug('retrieve pecl_php')
        logging.debug(self.result)
        versions = re.findall(r'%s(?:-|.)(.*?)(?:.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2)' % self.package_name, self.result)
        logging.debug(versions)
        versions = helper_clean_versions(versions)
        logging.debug(versions)

        try:
            last_version = helper_get_last_version(versions)
            last_version = last_version.split('/')[-1]
        except:
            logging.error('can\'t determine version from pecl.php.net')
            return None

        return last_version

class Package_alioth_debian(Package):
    """ alioth.debian.org
        TODO
    """
    def __init__(self, package_name):
        super(Package_alioth_debian, self).__init__(package_name)
        self.provider = 'alioth.debian.org'

def package_factory(package_name):
    pkg = Package(package_name)

    url = package.url
    if 'svn' in url:
        package = Package_svn(package_name)
    elif 'git://' in url or 'github.com' in url or 'cgit' in url:
        package = Package_git(package_name)
    elif ('sf.net' in url or 'sourceforge.net' in url):
        package = Package_sourceforge(package_name)
    elif 'googlecode.com' in url:
        package = Package_googlecode(package_name)
    elif 'launchpad.net' in url:
        package = Package_launchpad(package_name)
    elif 'ftp://' in url or 'ftp.' in url:
        package = Package_ftp(package_name)
    elif 'alioth.debian.org' in url:
        package = Package_alioth_debian(package_name)
    elif 'cvs://' in url:
        package = Package(package_name)
    elif 'bitbucket.org' in url:
        package = Package(package_name)
    elif 'pecl.php.net' in url:
        package = Package_pecl_php(package_name)
    else:
        package = Package_www(package_name)

    return package

def version_clean_output(string):
    """ Clean version before writing :
          - replace None by 'None'
          - return the first 8 characters if it's a 40 characters hash
    """
    if string == None:
        return 'None'
    if len(string) == 40:
        return string[:8]
    else:
        return string

def helper_get_last_version(search_str):
    last_version = '0'

    if len(search_str) == 0:
        return 'unknown'

    for version in search_str:
        if (distutils.version.LooseVersion(version)) > last_version:
            last_version = version

    return helper_clean_last_version(last_version)

def helper_clean_versions(versions):
    logging.debug('avant : ')
    logging.debug(versions)
    # TODO remove 0, and use a variable for versions[idx] ?, use xrange ?
    for idx in range(0, len(versions)):
        if '/' in versions[idx]:
            versions[idx] = versions[idx].split('/')[-1]
        #if 'latest' in versions[idx]:
        #    versions[idx] = ''
        if re.search(r'\d', versions[idx]) == None:
            versions[idx] = ''
    logging.debug('apres : ')
    logging.debug(versions)

    versions = [i for i in versions if ('<' not in i) and ('>' not in i)]
    #versions = [i for i in versions if re.match('\D*-', i) == None]
    versions = [i for i in versions if i!= '' and i!='xxx']
    versions = [i for i in versions if i!='cgi' and i != 'win32']
    versions = [i for i in versions if ' ' not in i]

    return versions

def helper_clean_last_version(last_version):
    last_version = last_version.replace('.orig', '')
    last_version = last_version.replace('.src', '')
    last_version = last_version.replace('.rpm', '')
    last_version = last_version.replace('-src', '')
    last_version = last_version.replace('-source', '')
    last_version = last_version.replace('-doc', '')
   # last_version = last_version.replace('release-', '')
    last_version = last_version.replace('-avr32', '')
    last_version = last_version.replace('-win32', '')
    last_version = last_version.replace('-win', '')
    last_version = last_version.replace('-win64', '')
    last_version = last_version.replace('.OSX', '')
    last_version = last_version.replace('-cygwin64', '')
    last_version = last_version.replace('-Linux-i386', '')
    last_version = last_version.replace('-android', '')
    last_version = last_version.replace('-sunos', '')
    last_version = last_version.replace('-x86', '')
    last_version = last_version.replace('-x64', '')
    last_version = last_version.replace('-xdoc', '')
    last_version = last_version.replace('-gpl', '')

    #if last_version != None and last_version != '' and last_version[0] == '.':
    #    last_version = last_version[1:]

    return last_version

def check(package_name):
    logging.info('Checking package: ' + package_name)

    package = package_factory(package_name)
    last_version = package.get_last_version()
    return package

if __name__ == '__main__':

    if (len(sys.argv) < 2):
        logging.error("You must give a file to write output to.")
        sys.exit(1)

    f = open(sys.argv[1], 'w')
    f.write(TEMPLATE)

    list_dir_sorted = os.listdir(PKG_DIR)
    list_dir_sorted.sort()
    for pkg_name in list_dir_sorted:
        if os.path.isfile(os.path.join(PKG_DIR, pkg_name)):
            continue
        NB_PKG += 1
        print pkg_name
        pkg = check(pkg_name)

        print pkg
        continue

        if package.version is None or package.provider in ERR_PROVIDER:
            status = 'DONTCHECK'
            version_class = 'other'
        elif package.last_version is None:
            NB_PACKAGE_UNKNOWN += 1
            status = 'UNKNOWN'
            version_class = 'other'
        elif package.version == package.last_version:
            status = 'OK'
            version_class = 'ok'
            NB_PACKAGE_UPTODATE += 1
        else:
            status = 'NOK'
            version_class = 'nok'
            NB_PACKAGE_TOUPDATE += 1

        if package.patch_count == 0:
            patch_count_class = 'ok'
        elif package.patch_count < 5:
            patch_count_class = 'other'
        else:
            patch_count_class = 'nok'

        # write package name, patch count and infrastructure
        f.write('<tr><td>%s</td><td class="%s">%s</td>' % (package_name, patch_count_class, package.patch_count))
        f.write('<td>%s</td>'% package.infra)

        if package.have_licence:
            f.write('<td class="ok">%s</td>' % have_licence)
        else:
            f.write('<td class="nok">%s</td>' % have_licence)

        if have_licence_files:
            f.write('<td class="ok">%s</td>' % have_licence_files)
        else:
            f.write('<td class="nok">%s</td>' % have_licence_files)

        f.write('<td class="%s">%s</td><td class="%s">%s</td>' % (version_class, version_clean_output(package.version), version_class, version_clean_output(package.last_version)))

        #for logging.debug only, will be removed later
        f.write('<td>%s</td><td>%s</td></tr>' % (package.provider, status))

    f.write('</tbody></table>')
    f.write('Stats: %d packages (%d up to date, %d old and %d unknown)<br/>' % (nb_package, nb_package_uptodate, nb_package_toupdate, nb_package_unknown))

    f.write('packages using <i>autotools</i> infrastructure : %d<br/>' % nb_package_infra_autotools)
    f.write('packages using <i>generic</i> infrastructure : %d<br/>' % nb_package_infra_generic)
    f.write('packages using <i>cmake</i> infrastructure : %d<br/>' % nb_package_infra_cmake)
    f.write('packages using <i>other</i> infrastructure : %d<br/>' % nb_package_infra_other)

    f.write('</body></html>')

    logging.info('Stats: %d packages (%d up to date, %d old and %d unknown)<br/>' % (nb_package, nb_package_uptodate, nb_package_toupdate, nb_package_unknown))
