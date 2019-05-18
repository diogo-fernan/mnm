# MNM

*MNM* is a Python research tool for reading raw Master Boot Record (MBR), NT File System (NTFS) and Master File Table (MFT) binary data in a Windows NT system. The tool reads a disk sector (512 bytes) at a time, finds the first bootable NTFS partition and computes the offsets of the NTFS and MFT clusters. It further prints hexadecimal dumps of the MBR and NTFS structures, as well as of the first 16 MFT records. 

# Usage

*MNM* implements three classes that accordingly unpack the binary data of the MBR, NTFS and MFT records. The raw disk reads are sourced from the first physical drive available, usually named `\\.\PHYSICALDRIVE0` in the Windows NT namespace nomenclature. The drive is specified in the `_DRIVE` variable.

# Author

[@dfernan__](https://twitter.com/dfernan__)