#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check-updates script
"""
import sys
import urllib2
import httplib2
from ftplib import FTP
import ftplib
import re
from os import listdir, walk
from os.path import exists, isfile, join
import shutil
from distutils.version import LooseVersion
import logging
from logging import info, debug, error 
from subprocess import check_output
import pickle

template = """
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
	<th>current version</th>
	<th>last version</th>
	<th>provider</th>
    <th>status</th>
    </thead>
    <tbody>"""

# TODO: Python packages updates
# TODO : Lua packages updates
# sf fix way to check updates
# audiofile > use git instead
# gd > bitbucket 

# mysql_client takes too long (why?ftp pb?)
# snmppp doesn't list downloads in same page
# whetsstone, ttcp is a .c file
# pcmanfm version very old
# cegui06 needs to be updated
# vim uses hg
# latencytop site is down
# ipset, cups, noip, fconfig > impossible to list
# libsvgtiny moved to git
# sstrip and libnfc-llcp > website error ?
# jpeg is only use to select other packages
# lftp need to be checked
# libmodplug : sourceforge package with different projects
# cjson is a svn sourceforge project
# net-tools is a git sourceforge project

exception_list = ('fan-ctrl', 'mysql_client', 'snmppp', 'jquery',
				  'jquery-ui-themes', 'jquery-keyboard', 'jquery-sparkline',
				  'libjpeg', 'musepack', 'whetstone', 'crosstool-ng', 'pcmanfm',
				  'tcllib', 'imlib2', 'vde2', 'ebtables', 'procps', 'cegui06',
				  'libsysfs', 'vim', 'latencytop', 'doom-wad', 'ipset',
				  'libsvgtiny', 'cups', 'noip', 'sstrip','libnfc-llcp', 'ttcp',
				  'lftp', 'jpeg', 'libmodplug', 'cjson', 'net-tools', 'joe')

website_error_list = ('python-setuptools', 'googlefontdirectory',
					  'python-distutilscross', 'libatomic_ops', 'xinetd',
					  'udpcast', 'luajit', 'fconfig', 'libvpx', 'openvpn',
					  'iostat', 'libdvbsi', 'jq', 'portmap', 'rsyslog', 'ipkg',
					  'vsftpd', 'ntfs-3g', 'owl-linux', 'libmodbus', 'bzip2',
					  'libftdi', 'aiccu', 'lrzsz', 'jquery-ui', 'sdl_sound',
					  'luabitop', 'libnss', 'python-serial', 'python-bottle',
					  'python-tornado', 'python-pysnmp', 'python-pysnmp-mibs',
					  'python-pysnmp-apps', 'python-configobj',
					  'python-m2crypto', 'python-pycrypto', 'python-setuptools',
					  'python-pyzmq', 'fconfig')

USE_CACHE = True

def getUrlRedirection(url):
    h = httplib2.Http(".cache_httplib")
    h.follow_all_redirects = True
    resp = h.request(url, "GET")[0]
    contentLocation = resp['content-location']
    return contentLocation
	
class Package(object):

	def __init__(self, package_name):
		self.package_name = package_name
		(url, source, version) = self.get_url_and_version(package_name)
		self.url = url
		self.version = version
		#count patch before eventually changing package_name
		self.patch_count = self.count_patches()
		if source != None and source != '':
			self.package_name = source
		self.last_version = None
		self.provider = None	
		info('site :' + self.url)
		info('version :' + self.version)

	def get_url_and_version(self, package_name):
		site_url = ''
		source = ''
		version = ''
		package_name_tmp = self.package_name.upper().replace('-','_')

		debug('package name : ' + package_name)

		for line in open('vars.list'):
			if line.startswith(package_name_tmp + '_SITE'):
				site_url = line.split('=')[1][:-1].split(' ')[0]
				site_url = site_url.replace('"', '')
			if line.startswith(package_name_tmp + '_SOURCE'):
				source = line.split('=')[1][:-1].split(' ')[0]
			if line.startswith(package_name_tmp + '_VERSION'):
				version = line.split('=')[1][:-1].split(' ')[0]
				break

		if source != '':
			source = source.replace('-'+version, '')
			source = source.replace(version, '')
			source = source.replace('-src', '')
			source = source.replace('-gpl', '')
			source = source.split('.')[0]
			if '_' in source:
				info('source under:' + source)
				if re.search(r'_\D', source) == None:
					source = source.split('_')[0]

			debug('source :' + source)

		return (site_url, source, version)

	def retrieve(self):
		debug('function cache')
		debug(self.package_name)
		
		if USE_CACHE and isfile('site/' + self.package_name):
			debug('cache found !')
			f = open('site/' + self.package_name, 'r')
			result = pickle.load(f)
			f.close()
		else:
			info('retrieving : ' + self.package_name)
			result = self.retrieve_specific()
			if USE_CACHE:
				debug('writing cache for ' + self.package_name)
				f = open('site/' + self.package_name, 'w')
				pickle.dump(result, f)
				f.close()

		return result;

	def retrieve_specific(self):
		error('should not be called')
		return None

	def get_last_version(self):
		try:
			debug('1')
			self.result = self.retrieve()
			debug('2')
			debug(self.result)
		except:
			error('website error')
			return 'website error'
		self.last_version = self.get_last_version_specific()
		return self.last_version
	
	def get_last_version_specific(self):
		error('should not be called')
		return None
		
	def clean_version(self):
		return last_version
		
	def count_patches(self):
		package_dir = join('../../package', self.package_name)
		return len([f for root, dirs, files in walk(package_dir) for f in files if f.endswith('.patch')])
		

class Package_www(Package):
	""" Specific www website
		Try to find last version by looking for available downloads on the page
	"""
	def __init__(self, package_name):
		super(Package_www, self).__init__(package_name)
		self.provider = 'www'
		
		debug('www website')

	def retrieve_specific(self):
		debug('retrieve www')
		return urllib2.urlopen(self.url).read()

	def get_last_version_specific(self):
		debug('get_last_version_www')
		package_name_tmp = self.package_name.replace('+', '\+')
		debug('package_name : %s' % package_name_tmp)
		debug(self.result)
		regex = re.compile(r'%s(?:-|.)(.*?)(?:.zip|.tar.gz|.tar.xz|.tgz|.tar.bz2|.js|.bin)' % package_name_tmp, re.IGNORECASE)
		versions = regex.findall(self.result)
		debug(versions)
		versions = [i for i in versions if re.match(r'\D+-', i) == None]
		debug(versions)
		versions = helper_clean_versions(versions)
		debug(versions)
		#versions = [i for i in versions if re.match(r'\D*-*', i) == None]
		#debug(versions)
		if (versions == None) or (len(versions) == 0):
			error('can\'t determine site version')
			return None

		try:    
			last_version = helper_get_last_version(versions)
			debug(last_version)
		except:
			error('can\'t determine site version')
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
		debug('retrieve ftp')
		result = None
		debug('1' + self.url);
		base_url = self.url.split('/')[2]
		debug('2' + base_url + '--' + self.url)
		directory = self.url.split(base_url)[1]
		debug('3')
		debug('caching :' + base_url + ' ' + directory)
		ftp = FTP(base_url)
		debug('4');
		ftp.login()
		debug('5');
		ftp.cwd(directory)
		debug('6');
		result = []
		ftp.retrlines('LIST', result.append)
		debug('7');
		ftp.quit()
		return result

	def get_last_version_specific(self):
		versions = [i.split(' ')[-1] for i in self.result]
		debug(versions)
		package_name = self.package_name.replace('+', '\+')
		versions = [re.findall(r'%s(?:-|.|)(.*?)(?:.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2|.js|.bin)' % package_name, i) for i in versions]
		debug(versions)
		versions = [i[0] for i in versions if i != []]
		debug(versions)
		versions = helper_clean_versions(versions)
		debug(versions)
		versions = [i for i in versions if re.match(r'\D+-', i) == None]
		debug(versions)

		try:
			last_version = helper_get_last_version(versions)
		except:
			error('can\'t determine last ftp version')
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
		debug('retrieve svn')
		return check_output(["svn log --xml %s | grep \"revision\" | head -1" % self.url], shell=True)
		
	def get_last_version_specific(self):
		debug('get_last_version_specific svn')
		try:
			last_version = self.result.split('revision="')[1].split('"')[0]
			debug(last_version)
		except:
			error('can\'t determine svn version')
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
		debug(versions)
		versions = helper_clean_versions(versions)
		debug(versions)
		versions = [i for i in versions if re.match(r'\D*-', i) == None]
		debug(versions)
		versions = [i for i in versions if re.search(r'-(.*)', i) == None]
		debug(versions)

		try:
			last_version = helper_get_last_version(versions)
			last_version = last_version.split('/')[-1]
		except:
			error('can\'t determine launchpad version')
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
			debug(url_tmp)
			request = urllib2.urlopen(url_tmp).read()
			debug(request)
			res = re.findall(r'\'(git://.*)\'', request)
			if len(res) == 1:
				self.url = res[0]
			else :
				res = re.findall(r'<tr><td colspan=\'\d\'><a href=\'([http.?].*?)\'>', request)
				debug(res)
				self.url = res[0]
			debug(self.url)
	

	def retrieve_specific(self):
		debug('retrieve git')
			
		if len(self.version) == 40:
			if 'github.com' in self.url:
				git_url = self.url.split('github.com/')[1]
				git_url = git_url.split('/tarball/')[0]
				git_url = 'https://github.com/' + git_url + '.git'

			if 'git://' in self.url:
				git_url = self.url
			
			result = check_output(["git ls-remote --heads %s" % git_url], shell=True)
			debug(result)
		else:   
			# if version is a real version number
			if ('github.com' in self.url):
				git_url = self.url.split('github.com/')[1]
				debug(git_url)
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
				debug(git_url)
			else:
				git_url = self.url

			result = check_output(["git ls-remote --tags %s" % git_url], shell=True)
		return result

	def get_last_version_specific(self):
		# if version refers to a commit id
		if len(self.version) == 40:
			last_version = re.search(r'(.*)\trefs/heads/master', self.result).group(1)
			debug(last_version)
		else:
			versions = [i.split('\t') for i in self.result.split('\n')]
			versions = [i for i in versions if i[0] != '']
			debug(versions)
			versions = [i[1].replace('refs/tags/', '') for i in versions]
			debug(versions)
			versions = [i.replace('_', '.') for i in versions]
			debug(versions)
			versions = [i for i in versions if '^{}' not in i]
			debug(versions)
			#versions = [i for i in versions if re.match(r'\D*-', i) == None]
			#debug(versions)
			versions = helper_clean_versions(versions)
			debug(versions)
			try:
				last_version = helper_get_last_version(versions)
				debug(last_version)
			except:
				error('can\'t determine git version')
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
			error('Can\'t find sf package name')
			return None
		self.url = 'http://sourceforge.net/projects/%s/files/latest/download' % self.package_name


	def retrieve_specific(self):
		debug('retrieve sourceforge')
		result = getUrlRedirection(self.url)
		#result = urllib2.urlopen(self.url).geturl()
		debug('retrieve_sf' + self.url)

	def get_last_version_specific(self):
		debug('get_last_version_specific')
		result = urllib2.unquote(self.result) # replace all hexa caracters like %20
		debug(result)

		last_version = result.split('/')[-1]
		debug(last_version)
		filename = self.package_name.replace('+', '\+')
		regex = re.compile(r'%s(-|_|)(.*)(.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2|.bin)' % filename, re.IGNORECASE)
		last_version = regex.search(last_version)
		if last_version == None:
			return None
		last_version = last_version.group(2)
		debug(last_version)
		last_version = helper_clean_last_version(last_version)
		debug(last_version)

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
		debug('retrieve googlecode')
		versions = re.findall(r'%s(?:-|.)(.*?)(?:.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2|.bin)' % filename, self.result)
		debug(versions)
		versions = helper_clean_versions(versions)
		debug(versions)
		versions = [i for i in versions if re.match(r'\D*-', i) == None]
		debug(versions)
		versions = [i for i in versions if re.search(r'-(.*)', i) == None]
		debug(versions)

		try:
			last_version = helper_get_last_version(versions)
			last_version = last_version.split('/')[-1]
		except:
			error('can\'t determine version from googlecode')
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
		debug('retrieve pecl.php.net')
		response = urllib2.urlopen(self.url)
		debug(response.info().getheader('Content-Disposition'))
		return response.info().getheader('Content-Disposition')
		
	def get_last_version_specific(self):
		debug('retrieve pecl_php')
		debug(self.result)
		versions = re.findall(r'%s(?:-|.)(.*?)(?:.zip|.tar.gz|.tgz|.tar.xz|.tar.bz2)' % self.package_name, self.result)
		debug(versions)
		versions = helper_clean_versions(versions)
		debug(versions)

		try:
			last_version = helper_get_last_version(versions)
			last_version = last_version.split('/')[-1]
		except:
			error('can\'t determine version from pecl.php.net')
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
	package = Package(package_name)

	if package_name in exception_list:
		error('Package in exception list! TODO later')
		package.provider = 'exception list'
	elif package_name in website_error_list:
		package.provider = 'website not reachable'
		error('site not reachable!')
	elif ('sf.net' in package.url or 'sourceforge.net' in package.url):
		package.provider = 'skip sf'
		error('skip sf')
	else:
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
        if (LooseVersion(version)) > last_version:
            last_version = version

    return helper_clean_last_version(last_version)

def helper_clean_versions(versions):
    debug('avant : ')
    debug(versions)
    # TODO remove 0, and use a variable for versions[idx] ?, use xrange ?
    for idx in range(0, len(versions)):
        if '/' in versions[idx]:
            versions[idx] = versions[idx].split('/')[-1]
        #if 'latest' in versions[idx]:
        #    versions[idx] = ''
        if re.search(r'\d', versions[idx]) == None:
            versions[idx] = ''
    debug('apres : ')
    debug(versions)

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
	info('Checking package: ' + package_name)

	package = package_factory(package_name)
	last_version = package.get_last_version()
#	if last_version == 'website error':
#		last_version = 'unknown'
#		provider = 'website not found'
#
#	if last_version != None:
#		info('last version :' + last_version)

	return package

if __name__ == '__main__':
	nb_package = 0
	nb_package_uptodate = 0
	nb_package_toupdate = 0
	nb_package_unknown = 0
	nb_package_infra_autotools = 0
	nb_package_infra_generic = 0
	nb_package_infra_cmake = 0
	nb_package_infra_other = 0

	logger = logging.getLogger()
	list_var = check_output(["make -C ../.. printvars | grep '_SOURCE=\|_VERSION=\|_SITE=' > vars.list"], shell=True)

	if len(sys.argv) == 2:
		logger.setLevel(logging.DEBUG)
		package = check(sys.argv[1])
		debug(package.package_name + ' ' + package.version + ' ' + str(package.last_version) + ' ' + package.provider)
		debug('patch count : ' + str(package.patch_count))
	else:
		fh = logging.FileHandler('res.log', 'w')
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		fh.setFormatter(formatter)
		logger.addHandler(fh) 
		logger.setLevel(logging.INFO)

		f = open('out.html', 'w')
		f.write(template)

		for package_name in listdir('../../package'):
			if isfile(join('../../package', package_name)):
				continue
			nb_package += 1

			patch_count = 0
			infra = 'unknown'
			have_licence = True
			have_licence_files = True
			package = check(package_name)

			if package.version == None or package.provider == 'exception list' or package.provider == 'website not reachable' or package.provider == 'alioth.debian.org' or package.version == 'undefined':
				status = 'DONTCHECK'
				version_class = 'other'
			elif package.last_version == None:
				nb_package_unknown += 1
				status = 'UNKNOWN'
				version_class = 'other'
			elif package.version == package.last_version:
				status = 'OK'
				version_class = 'ok'
				nb_package_uptodate += 1
			else:
				status = 'NOK'
				version_class = 'nok'
				nb_package_toupdate += 1
				
			if package.patch_count == 0:
				patch_count_class = 'ok'
			elif package.patch_count < 5:
				patch_count_class = 'other'
			else:
				patch_count_class = 'nok'

			# write package name, patch count and infrastructure
			f.write('<tr><td>%s</td><td class="%s">%s</td>' % (package_name, patch_count_class, package.patch_count))
			
			#write infra
			
			if (package_name != 'celt051'):
				for line in open(join('../../package/', package_name, package_name + '.mk')):
					if 'autotools-package' in line:
						infra = 'autotools'
						nb_package_infra_autotools += 1
						break
					elif 'generic-package' in line:
						infra = 'generic'
						nb_package_infra_generic += 1
						break
					elif 'cmake-package' in line:
						infra = 'cmake'
						nb_package_infra_cmake += 1
						break

			if infra == 'unknown':
				nb_package_infra_other += 1
	
			f.write('<td>%s</td>'% infra)

			if have_licence:
				f.write('<td class="ok">%s</td>' % have_licence)
			else:
				f.write('<td class="nok">%s</td>' % have_licence)

			if have_licence_files:
				f.write('<td class="ok">%s</td>' % have_licence_files)
			else:
				f.write('<td class="nok">%s</td>' % have_licence_files)

			f.write('<td class="%s">%s</td><td class="%s">%s</td>' % (version_class, version_clean_output(package.version), version_class, version_clean_output(package.last_version)))

			#for debug only, will be removed later
			f.write('<td>%s</td><td>%s</td></tr>' % (package.provider, status))

		f.write('</tbody></table>')
		f.write('Stats: %d packages (%d up to date, %d old and %d unknown)<br/>' % (nb_package, nb_package_uptodate, nb_package_toupdate, nb_package_unknown))
		
		f.write('packages using <i>autotools</i> infrastructure : %d<br/>' % nb_package_infra_autotools)
		f.write('packages using <i>generic</i> infrastructure : %d<br/>' % nb_package_infra_generic)
		f.write('packages using <i>cmake</i> infrastructure : %d<br/>' % nb_package_infra_cmake)
		f.write('packages using <i>other</i> infrastructure : %d<br/>' % nb_package_infra_other)
		
		f.write('</body></html>')
		
		info('Stats: %d packages (%d up to date, %d old and %d unknown)<br/>' % (nb_package, nb_package_uptodate, nb_package_toupdate, nb_package_unknown))
	print 'done!'
