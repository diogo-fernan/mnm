#!/usr/bin/env python

import os, sys
from struct import pack, unpack

_DRIVE	 = r'\\.\PHYSICALDRIVE0'
_BSECTOR = 512
_MFTREC	 = 1024

def fixb (b):
	from string import printable
	if chr(b) not in printable[:-5]:
		return '.'
	return chr(b)

def hexdump (b, width=16, sep='.', offset=0x00):
	if width <= 0:
		width = 16
	dmp = ''
	for x in [b[i:i+width] for i in range(len(b)) if (i%width) == 0]:
		dmp += '{0:#010x}  '.format(offset)
		txt = ''
		for i, y in enumerate(x):
			dmp += '{0:02x} '.format(y)
			txt += fixb (y)
			if i == int(width / 2) - 1:
				dmp += ' '
		dmp += ' ' + txt + '\n'
		offset += width
	return dmp

class Partition ():
	def __init__ (self, mbr):
		mask			= 0b0000001111111111

		self.offset 		= 0x00
		self.mbr		= mbr
		self.bBootInd 		= mbr[0x01be]
		self.bType		= mbr[0x1c2]
		# bootable partition and NTFS
		while self.bBootInd is not 0x80 and self.bType is not 0x70:
			self.offset	+= 0x10 # up to four partition entries
			self.bBootInd	= mbr[0x01be+self.offset]
			self.bType	= mbr[0x1c2+self.offset]

		self.bHead		= mbr[0x01bf+self.offset]
		self.bSector		= mbr[0x01c0+self.offset] >> 2
		self.bCylinder		= unpack ('<H', mbr[0x01c0+self.offset:0x01c2+self.offset])[0] & mask
		self.bLastHead		= mbr[0x01c3+self.offset]
		self.bLastSector	= mbr[0x01c4+self.offset] >> 2
		self.dLastCylinderSector= unpack ('<H', mbr[0x01c4+self.offset:0x01c6+self.offset])[0] & mask
		self.dwRelativeSector	= unpack ('<L', mbr[0x01c6+self.offset:0x01ca+self.offset])[0]
		self.dwNumberSectors	= unpack ('<I', mbr[0x01ca+self.offset:0x01ce+self.offset])[0]

		self.bootOffset			= self.dwRelativeSector * _BSECTOR
	def __repr__ (self):
		return hexdump (self.mbr)
class NTFS ():
	def __init__ (self, offset, ntfs):
		self.offset			= offset
		self.ntfs			= ntfs
		self.sJumpInstruction 		= unpack ('<BBB', ntfs[0x00:0x03])[0]
		self.sOemID			= unpack ('<Q', ntfs[0x03:0x0b])[0]

		self.wBytesPerSec		= unpack ('<H', ntfs[0x0b:0x0d])[0]
		self.bSecPerClust		= ntfs[0x0d]
		self.wReservedSec		= unpack ('<H', ntfs[0x0e:0x10])[0]
		self.wReserved			= unpack ('<BBB', ntfs[0x10:0x13])[0]
		self.wUnused1			= unpack ('<H', ntfs[0x13:0x15])[0]
		self.bMediaDescriptor		= ntfs[0x15]
		self.wUnused2			= unpack ('<H', ntfs[0x16:0x18])[0]
		self.wSecPerTrack		= unpack ('<H', ntfs[0x18:0x1a])[0]
		self.wNumberOfHeads		= unpack ('<H', ntfs[0x1a:0x1c])[0]
		self.dwHiddenSec		= unpack ('<I', ntfs[0x1c:0x20])[0]
		self.dwUnused3			= unpack ('<I', ntfs[0x20:0x24])[0]
		self.dwUnused4			= unpack ('<I', ntfs[0x24:0x28])[0]
		self.llTotalSec			= unpack ('<Q', ntfs[0x28:0x30])[0]
		self.llMFTLogicalClustNum	= unpack ('<Q', ntfs[0x30:0x38])[0]
		self.llMFTMirrLogicalClustNum = unpack ('<Q', ntfs[0x38:0x40])[0]
		self.iClustPerMFTRecord		= unpack ('<I', ntfs[0x40:0x44])[0]
		self.iClustPerIndexRecord	= unpack ('<I', ntfs[0x44:0x48])[0]
		self.llVolumeSerialNum		= unpack ('<Q', ntfs[0x48:0x50])[0]
		self.dwChecksum			= unpack ('<I', ntfs[0x50:0x54])[0]

		self.mftOffset = (self.bSecPerClust * self.wBytesPerSec) \
						* self.llMFTLogicalClustNum + self.offset

		# self.sBootstrapCode 0x54 # size 426
		# self.wSecMark 0x1fe
	def __repr__ (self):
		return hexdump (self.ntfs, offset=self.offset)
class MFT ():
	def __init__ (self, offset, mft):
		self.offset = offset
		self.mft    = mft

		# MFT Entry Header
		self.sFileSignature	= unpack ('<I', mft[0x00:0x04])[0]
		self.wFixupOffset 	= unpack ('<H', mft[0x04:0x06])[0]
		self.wFixupSize 	= unpack ('<H', mft[0x06:0x08])[0]
		self.llLogSeqNumber	= unpack ('<Q', mft[0x08:0x10])[0]
		self.wSequence 		= unpack ('<H', mft[0x10:0x12])[0]
		self.wHardLinks 	= unpack ('<H', mft[0x12:0x14])[0]
		self.wAttribOffset 	= unpack ('<H', mft[0x14:0x16])[0]
		self.wFlags 		= unpack ('<H', mft[0x16:0x18])[0]
		self.dwRecLength 	= unpack ('<I', mft[0x18:0x1c])[0]
		self.dwAllLength 	= unpack ('<I', mft[0x1c:0x20])[0]
		self.llBaseMftRec 	= unpack ('<Q', mft[0x20:0x28])[0]
		self.wNextAttrID 	= unpack ('<H', mft[0x28:0x2a])[0]
		self.wFixupPattern 	= unpack ('<H', mft[0x2a:0x2c])[0]

		# Attribute Header
		# Attribute: $FILE_NAME
		# Attribute Header
		# Attribute: $STANDARD_INFORMATION
		# Attribute Header
		# Attribute: $DATA
	def __repr__ (self):
		return hexdump (self.mft, offset=self.offset)

if __name__ == '__main__':
	fd = os.open (_DRIVE, os.O_RDONLY | os.O_BINARY)
	part = Partition (os.read (fd, _BSECTOR))
	print (part)

	os.lseek (fd, part.bootOffset, os.SEEK_SET) 
	ntfs = NTFS (part.bootOffset, os.read (fd, _BSECTOR))
	print (ntfs)

	os.lseek (fd, ntfs.mftOffset, os.SEEK_SET)
	# first 16 MFT entries are for the MFT metadata files
	# 0 $MFT, 1 $MFTMirr, 2 $logFile, 3 $Volume, 4 $AttrDef
	# 5 root dir (\), 6 $Bitmap, 7 $Boot, 8 $BadClus
	# 9 $Secure, 10 $Upcase, 11 $Extend
	# 12-15 Reserved
	offset = ntfs.mftOffset
	for i in range (0, 16):
		mft = MFT (offset, os.read (fd, _MFTREC))
		print (mft)
		offset += _MFTREC
