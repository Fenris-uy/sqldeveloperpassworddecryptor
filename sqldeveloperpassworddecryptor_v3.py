# -*- coding: utf-8 -*-

# This file is part of sqldeveloperpassworddecrypter.
#
# Copyright (C) 2015, Thomas Debize <tdebize at mail.com>
# All rights reserved.
#
# sqldeveloperpassworddecrypter is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# sqldeveloperpassworddecrypter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with sqldeveloperpassworddecrypter.  If not, see <http://www.gnu.org/licenses/>.

from Crypto.Cipher import DES
import sys
import base64
import array
import hashlib
import codecs

# Script version
VERSION = '1.0'

# OptionParser imports
from optparse import OptionParser
from optparse import OptionGroup

# Options definition
parser = OptionParser(usage="%prog [options]\nVersion: " + VERSION)

main_grp = OptionGroup(parser, 'v3 and v4 parameters')
main_grp.add_option('-p', '--encrypted-password', help = '(mandatory): password that you want to decrypt. Ex. -p 054D4844D8549C0DB78EE1A98FE4E085B8A484D20A81F7DCF8', nargs = 1)
#main_grp.add_option('-c', '--connections-file', help = '(optional): "connections.xml" file containing encrypted passwords.', nargs = 1)

v4_grp = OptionGroup(parser, 'v4 specific parameters')
v4_grp.add_option('-d', '--db-system-id-value', help = '(mandatory for v4): machine-unique value of "db.system.id" attribute in the "product-preferences.xml" file. Ex: -d 6b2f64b2-e83e-49a5-9abf-cb2cd7e3a9ee', nargs = 1)
#v4_grp.add_option('-f', '--db-system-id-file', help = '(optional): "product-preferences.xml" file  containing the "db.system.id" attribute value.', nargs = 1)

parser.option_groups.extend([main_grp, v4_grp])

# Handful functions
def des_cbc_decrypt(encrypted_password, decryption_key, iv):
	unpad = lambda s : s[:-ord(s[len(s)-1:])]
	crypter = DES.new(decryption_key, DES.MODE_CBC, iv)
	decrypted_password = unpad(crypter.decrypt(encrypted_password))

	return decrypted_password

def decrypt_v4(encrypted, db_system_id, parser):
	encrypted_password = base64.b64decode(encrypted)

	salt = bytearray.fromhex("051399429372e8ad")#codecs.decode("051399429372e8ad", "hex")#str(b'051399429372e8ad','hex')
	num_iteration = 42

	# key generation from a machine-unique value with a fixed salt

	sid = bytearray()
	sid.extend(map(ord,db_system_id))
	key = sid + salt

	for i in range(num_iteration):
		m = hashlib.md5(key)
		key = m.digest()

	secret_key = key[:8]
	iv = key[8:]

	decrypted = des_cbc_decrypt(encrypted_password, secret_key, iv)

	return decrypted

def decrypt_v3(encrypted, parser):
	if len(encrypted) % 2 != 0:
		parser.error('v3 encrypted password length is not even (%s), aborting.' % len(encrypted))

	if not(encrypted.startswith("05")):
		parser.error('v3 encrypted password string not beginning with "05", aborting.\nRemember, for a v4 password you need the db.system.id value !')

	encrypted = encrypted.decode('hex')
	secret_key = encrypted[1:9]
	encrypted_password = encrypted[9:]
	iv = "\x00" * 8

	decrypted = des_cbc_decrypt(encrypted_password, secret_key, iv)

	return decrypted

def main(options, arguments):
	"""
		Dat main
	"""
	global parser, VERSION

	if not(options.encrypted_password):
		parser.error("Please specify a password to decrypt")

	print('sqldeveloperpassworddecryptor.py version \n',VERSION)
	print ("[+] encrypted password: " , options.encrypted_password)

	if options.db_system_id_value:
		# v4 decryption
		print("[+] db.system.id value: ", options.db_system_id_value)
		print("\n[+] decrypted password: ", decrypt_v4(options.encrypted_password, options.db_system_id_value, parser))

	else:
		#v3 decryption
		print("\n[+] decrypted password: ", decrypt_v3(options.encrypted_password, parser))

	return None

if __name__ == "__main__" :
	options, arguments = parser.parse_args()
	main(options, arguments)
