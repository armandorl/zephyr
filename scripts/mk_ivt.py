#!/usr/bin/python

"""
 Copyright 2021 NXP

 SPDX-License-Identifier:  BSD-3-Clause
"""

import sys
import os
import binascii
import struct

# define a const class
class _const:
    class ConstError(TypeError):pass
    def __setattr__(self,name,value):
        if name in self.__dict__:
            raise self.ConstError("Can't rebind const (%s)" %name)
        self.__dict__[name]=value
const = _const()

# IVT image structure offset
const.DCD_OFFSET                = 0x10
const.DCD_BAK_OFFSET            = 0x14
const.APP_OFFSET                = 0x20
const.APP_BAK_OFFSET            = 0x24
const.BOOT_CONFIG_WORD_OFFSET   = 0x28
const.LOADER_AREA_START         = 0x200000
const.LOADER_AREA_END           = 0x400000
# On QSPI offset is 0, on others it is 0x1000
const.IVT_OFFSET                = 0x0
const.IVT_SIZE                  = 0x100
const.FW_IMG_OFFSET             = 0x18
const.SYS_IMG_OFFSET            = 0x34

# IVT header
const.MAGIC_NUMBER              = 0x600001D1
# Config No secure boot, no swt and boot from m7
const.BOOT_CONFIG_M7            = 0
# Config No secure boot, no swt and boot from a53
const.BOOT_CONFIG_A7            = 1


class AppInfo:
    def __init__(self):
        self.offset = 0
        self.len = 0
        self.start = 0x0
        self.entry = 0x0
    def __str__(self):
        return "app info: start=%08x, entry=%08x, len=%08x" % (self.start, self.entry, self.len)

class BindItem:
    def __init__(self):
        self.to = -1
        self.entry = -1
        self.core = -1
        self.at = -1
        self.file_name = ''
        self.size = 0
        self.length = 0 # valid length
        self.offset = 0
        self.origin_offset = 0 # offset realted to origin ivt file
        self.write = None

    def __str__(self):
        ret = '<BindItem>:'
        if self.file_name != '':
            ret += ' ' + self.file_name
        if self.to != -1:
            ret += ' TO 0x%x' % self.to
        if self.entry != -1:
            ret += ' ENTRY 0x%x' % self.entry
        if self.core != -1:
            ret += ' CORE %d' % self.core
        if self.at != -1:
            ret += ' AT 0x%x' % self.at
        if self.size != -1:
            ret += ' SIZE 0x%x' % self.size
        return ret

    def doWrite(self):
        if not self.write:
            print("write is none")
            return False
        print("write 0x%x @ [0x%x, 0x%x)" % (self.size, self.at, self.at + self.size))
        return self.write(self)

class IvtImage:
    def __init__(self):
        self.output_file = None
        self.origin_file = None
        self.loader = None
        self.app = None
        self.appBindList = []
        self.bindList = []
        self.error = 0
        self.writeOffset = 0
        self.dcd_at = -1
        self.FW_IMG_at = -1
        self.appImgList = []
        self.final_size = None

    def parse_OUTPUT(self, args):
        if self.output_file:
            print("ERROR: multiple OUTPUT")
            return False
        file_name = args[1].strip()
        print("output file name: " + file_name)
        self.output_file = open(file_name, 'wb')
        if not self.output_file:
            print('Open %s for write fail' % file_name)
            return False
        return True

    def parse_ORIGIN(self, args):
        if self.origin_file:
            print("ERROR: multiple ORIGIN")
            return False
        file_name = args[1].strip()
        print("origin file name: " + file_name)
        self.origin_file = open(file_name, 'rb')
        if not self.origin_file:
            print('Open %s for read fail' % file_name)
            return False
        return True
    
    def parse_item(self, args):
        if len(args) == 0:
            return None
        item = BindItem()
        item.file_name = args[0]
        i = 2
        while i < len(args):
            if args[i-1] == 'TO':
                item.to = int(args[i], 0) 
            if args[i-1] == 'ENTRY':
                item.entry = int(args[i], 0) 
            if args[i-1] == 'CORE':
                item.core = int(args[i], 0) 
            if args[i-1] == 'AT':
                item.at = int(args[i], 0) 
            i += 2
        #print(item)
        return item

    def parse_APP_LOADER(self, args):
        self.loader = self.parse_item(args[1:])
        #print('loader: ' + str(self.loader))
        if self.loader:
            if self.loader.entry != -1 \
                and self.loader.to != -1 \
                and (self.loader.core == 0 or self.loader.core == 4):
                return True
        self.error = 1
        return False

    def parse_APP(self, args):
        self.app = self.parse_item(args[1:])
        #print('app: ' + str(self.app))
        if self.app:
            if self.app.to != -1 and self.app.entry != -1 and self.app.core != -1:
                return True
        self.error = 2
        return False

    def parse_APP_BIND(self, args):
        item = self.parse_item(args[1:])
        #print('app.bind: ' + str(item))
        if item and item.to != -1 and item.at == -1:
            if item.entry != -1 and item.core != -1:
                # application file
                self.appBindList.append(item)
                return True
            if item.entry == -1 and item.core == -1:
                # data file
                self.appBindList.append(item)
                return True
        self.error = 3
        return False

        
    def parse_BIND(self, args):
        item = self.parse_item(args[1:])
        #print('bind: ' + str(item))
        if item and item.at != -1 \
            and item.core == -1 and item.entry == -1:
            self.bindList.append(item)
            return True
        self.error = 4
        return False
        
    def parse_APP_IMG(self, args):
        item = self.parse_item(args[1:])
        #print('parse_BIND_UBOOT_A: ' + str(item))
        if item and item.at != -1 \
            and item.core == -1:
            self.appImgList.append(item)
            return True
        self.error = 4
        return False
    
    def parse_DCD(self, args):
        item = self.parse_item(args[1:])
        #print('bind: ' + str(item))
        if item and item.at != -1 \
            and item.core == -1 and item.entry == -1:
            self.bindList.append(item)
            self.dcd_at = item.at
            return True
        self.error = 4
        return False

    def parse_FW_IMG(self, args):
        item = self.parse_item(args[1:])
        #print('bind: ' + str(item))
        if item and item.at != -1 \
            and item.core == -1 and item.entry == -1:
            self.bindList.append(item)
            self.FW_IMG_at = item.at
            return True
        self.error = 4
        return False



    def cmd_error(self, args):
        print("error cmd: " + args[0])
        self.error = 5
        return False

    def parseCfg(self, line):
        if line == '' or line[0] == '#':
            return True
        args = line.split(' ')

        switcher = {
            'OUTPUT'     : self.parse_OUTPUT,
            'ORIGIN'     : self.parse_ORIGIN,
            'APP.LOADER' : self.parse_APP_LOADER,
            'APP'        : self.parse_APP,
            'APP.BIND'   : self.parse_APP_BIND,
            'BIND'       : self.parse_BIND,
            'DCD'        : self.parse_DCD,
            'APP.IMG'    : self.parse_APP_IMG,
            'FW_IMG'     : self.parse_FW_IMG,
            'SIZE'       : self.parse_SIZE,
        }
        return switcher.get(args[0],self.cmd_error)(args)

    def parse_SIZE(self, args):
        # Expect: SIZE <value> e.g. SIZE 64M
        if len(args) < 2:
            print("ERROR: SIZE requires a value")
            self.error = 6
            return False
        if self.final_size is not None:
            print("ERROR: multiple SIZE entries")
            self.error = 6
            return False
        try:
            s = args[1].strip()
            self.final_size = parse_size_str(s)
            print("Final image size: 0x%x (%d bytes)" % (self.final_size, self.final_size))
            return True
        except Exception as e:
            print("ERROR: invalid SIZE value: %s" % e)
            self.error = 6
            return False
    
    def write_bind_file(self, item):
        print("write_bind_file 0x%x @ [0x%x, 0x%x)" % (item.size, item.at, item.at + item.size))
        print("last_offset = 0x%x, real = 0x%x" %(self.writeOffset, self.output_file.tell()))
        self.origin_file.seek(self.writeOffset)
        if self.writeOffset < item.at:
            copy_file_with_len_pad(self.origin_file, self.output_file,\
                item.at - self.writeOffset, 0xff)
    
        with open(item.file_name, 'rb') as src_file:
            copy_file_with_len_pad(src_file, self.output_file, item.size, 0xff)
        
        # update write offset
        self.writeOffset = item.at + item.size
        return True

    def write_app(self, item):
        print("write_app 0x%x @ [0x%x, 0x%x)" % (item.size, item.at, item.at + item.size))
        self.origin_file.seek(self.writeOffset)
        if self.writeOffset < item.at:
            copy_file_with_len_pad(self.origin_file, self.output_file,\
                item.at - self.writeOffset, 0xff)
        
        appHeader = bytearray(0x40)
        appHeader[0:4] = b'\xD5\x00\x00\x60' # tag
        set_le4(appHeader, 4, item.to)  # start
        set_le4(appHeader, 8, item.entry)  # entry
        set_le4(appHeader, 0xc,  item.size - 0x40)
        self.output_file.write(appHeader)
        with open(item.file_name, 'rb') as src_file:
            copy_file_with_len_pad(src_file, self.output_file, item.size - 0x40, 0xff)
        
        # update write offset
        self.writeOffset = item.at + item.size
        return True
    
    def write_loader_app(self, item):
        print("write_loader_app 0x%x @ [0x%x, 0x%x)" % (item.size, item.at, item.at + item.size))
        print("last_offset = 0x%x, real = 0x%x" %(self.writeOffset, self.output_file.tell()))
        self.origin_file.seek(self.writeOffset)
        if self.writeOffset < item.at:
            copy_file_with_len_pad(self.origin_file, self.output_file,\
                item.at - self.writeOffset, 0xff)
        #print(sys._getframe().f_lineno, "real = 0x%x" %self.output_file.tell())

        # write app header
        appHeader = bytearray(0x40)
        appHeader[0:4] = b'\xD5\x00\x00\x60' # tag
        set_le4(appHeader, 4, item.to)  # start
        set_le4(appHeader, 8, item.entry)  # entry
        set_le4(appHeader, 0xc,  item.size - 0x40)
        self.output_file.write(appHeader)

        binder_table = bytearray(len(self.appBindList) * 0x20)
        offset_in_table = 0

        # write binded file
        for app in reversed(self.appBindList):
            if app.file_name != '':
                with open(app.file_name, 'rb') as src_file:
                    copy_file_with_len_pad(src_file, self.output_file, app.size, 0xff)
            else:
                self.origin_file.seek(app.origin_offset)
                copy_file_with_len_pad(self.origin_file, self.output_file, app.size, 0xff)
            #print(sys._getframe().f_lineno, "write size = 0x%x, real = 0x%x" %(app.size, self.output_file.tell()))
            if app.entry == -1:
                # data file
                set_le4(binder_table, offset_in_table, 0x55646E62)
                set_le4(binder_table, offset_in_table + 4, app.to)
                set_le4(binder_table, offset_in_table + 0xc, app.length)
            else:
                # app file
                set_le4(binder_table, offset_in_table, 0xAA646E62)
                set_le4(binder_table, offset_in_table + 0x10, app.entry)
                set_le4(binder_table, offset_in_table + 0x14, app.core)  
            set_le4(binder_table, offset_in_table + 4, -app.offset)
            set_le4(binder_table, offset_in_table + 8, app.to)
            set_le4(binder_table, offset_in_table + 0xc, app.length)
            offset_in_table += 0x20
        #print(sys._getframe().f_lineno, "real = 0x%x" %self.output_file.tell())
        # write binder table
        show_bytes(binder_table)
        print(sys._getframe().f_lineno, "real = 0x%x" %self.output_file.tell())
        if len(binder_table) < 0x100:
            pad_file(self.output_file, 0x100 - len(binder_table), 0xff)
        self.output_file.write(binder_table)
        #print(sys._getframe().f_lineno, "real = 0x%x" %self.output_file.tell())
        # write loader
        with open(self.loader.file_name, 'rb') as src_file:
            copy_file_with_len(src_file, self.output_file, self.loader.length)
        #print(sys._getframe().f_lineno, "real = 0x%x" %self.output_file.tell())
        # update write offset
        self.writeOffset = item.at + item.size
        return True

    def write_other(self):
        self.origin_file.seek(self.writeOffset)
        copy_file(self.origin_file, self.output_file)
        return True

    def read_ivt(self):
        self.origin_file.seek(const.IVT_OFFSET)
        ivt = self.origin_file.read(const.IVT_SIZE)
        if len(ivt) < const.IVT_SIZE:
            print("Read IVT error")
            return None
        if ivt[0:4] == b'\xD1\x01\x00\x60':
            print("Get IVT at 0x%x" %const.IVT_OFFSET)
            return ivt
        else:
            print("Read: %s" % ivt[0:4])

        self.origin_file.seek(0)
        ivt = self.origin_file.read(const.IVT_SIZE)
        if ivt[0:4] == b'\xD1\x01\x00\x60':
            print("Get IVT at 0x0")
            return ivt
        print("No IVT found in origin file")
        return None

    def output(self):
        if self.error != 0:
            return self.error
        self.error = 0xf # avoid re-entry
    
        if not self.origin_file:
            print("Do not support to generate IVT, now create one")
            aes_key = b"\x10" * 16       # Example AES-128 key
            random_iv = b"\x22" * 12     # Example 12-byte IV

            ivt = IVTBuilder(
                  ivt_header=const.MAGIC_NUMBER,
                  selftest_dcd_ptr=0,
                  selftest_dcd_ptr_bkp=0,
                  dcd_ptr=0,
                  dcd_ptr_bkp=0,
                  hse_fw_ptr=0,
                  hse_fw_ptr_bkp=0,
                  app_ptr=0,
                  app_ptr_bkp=0,
                  boot_cfg_word=const.BOOT_CONFIG_M7,
                  lifecycle_word=0,
                  aes_key=aes_key,
                  random_iv=random_iv
            )

            ivt.write_to_file("ivt.bin")
            print("IVT generated successfully.")
            const.BOOT_CONFIG_M7
            self.origin_file = open("ivt.bin", 'rb')
            if not self.origin_file:
                print('Open ivt.bin for read failed')
        
        # init bindList
        for item in self.bindList:
            item.length = item.size = get_fileSize(item.file_name)
            item.write = self.write_bind_file
        
        # new application
        if self.loader:
            print("Loader")
            # init size of appBindlist
            for item in self.appBindList:
                item.length = get_fileSize(item.file_name)
                item.size = align_n(item.length, 0x100)
                print("Preproc Item: " + item.file_name)
                print("Preproc Item size: " + item.size)
            
            # read ivt for later use
            ivt = self.read_ivt()
            if ivt is None:
                return 4
            boot_config_word = get_le4(ivt[0x28:0x2c])

            # get app from origin or file
            if self.app:
                if self.app.at != -1:
                    print("Not support AT for APP with loader exist")
                    return 3
                self.app.length = get_fileSize(self.app.file_name)
                self.app.size = align_n(self.app.length, 0x100)
                self.appBindList.append(self.app)
            else:
                app_offset = get_le4(ivt[0x20:0x24])
                self.origin_file.seek(app_offset)
                app_header = self.origin_file.read(0x40)
                app = get_appInfo(app_header)
                if not app:
                    return 5
                app_bind_item = BindItem()
                app_bind_item.to = app.start
                app_bind_item.entry = app.entry
                app_bind_item.length = app.len
                app_bind_item.size = align_n(app.len, 0x100)
                app_bind_item.core = 0 if (boot_config_word & 3) == 1 else 4
                app_bind_item.origin_offset = app_offset + 0x40
                self.appBindList.append(app_bind_item)
            
            # init appBindList
            self.loader.size = self.loader.length  = get_fileSize(self.loader.file_name)
            binder_table_len = 0x20 * (len(self.appBindList) + 1)
            binder_table_len = 0x100 if binder_table_len < 0x100 else binder_table_len

            # caculate total length and offset for each bind item
            binder_len = binder_table_len
            for item in self.appBindList:
                binder_len += item.size
                item.offset = binder_len 

            app_header_len = 0x40          
            if self.loader.at == -1:
                self.loader.at = const.LOADER_AREA_START   + app_header_len + binder_len
            new_app_offset = self.loader.at - binder_len - app_header_len
            print("New app offset:" + str(new_app_offset))
            new_app_end = self.loader.at + self.loader.size
            print("New app end:" + str(new_app_end))

            if new_app_offset < const.LOADER_AREA_START   or new_app_end > const.LOADER_AREA_END  :
                print("new app start: 0x%x, end: 0x%x is not in scope [0x%x , 0x%x)"\
                    % (new_app_offset, new_app_end, const.LOADER_AREA_START, const.LOADER_AREA_END))
                return
            
            new_ivt = bytearray(ivt)
            set_le4(new_ivt, const.APP_OFFSET, new_app_offset)
            boot_config_word &= ~0x3
            if self.loader.core == 0:
                boot_config_word |= 1
            set_le4(new_ivt, const.BOOT_CONFIG_WORD_OFFSET, boot_config_word)

            app_item = BindItem()
            app_item.at = new_app_offset
            app_item.size = new_app_end - new_app_offset
            app_item.to = self.loader.to - binder_len
            app_item.core = self.loader.core
            app_item.entry = self.loader.entry
            app_item.write = self.write_loader_app
            self.bindList.append(app_item)

        elif self.app:
            print("App")
            ivt = self.read_ivt()
            if ivt is None:
                print("No IVT")
                return 4
            if self.app.core != 0 and self.app.core != 4:
                print("CORE for APP must be 0 or 4 without loader")
                return 5
            
            new_ivt = bytearray(ivt)
            if self.app.at == -1:
                self.app.at = get_le4(ivt[0x20:0x24])
            set_le4(new_ivt, const.APP_OFFSET, self.app.at)
            boot_config_word = get_le4(ivt[0x28:0x2c])
            boot_config_word &= ~0x3
            if self.app.core == 0:
                boot_config_word |= 1
            set_le4(new_ivt, const.BOOT_CONFIG_WORD_OFFSET, boot_config_word)

            self.app.length = get_fileSize(self.app.file_name)
            self.app.size = 0x40 + self.app.length
            self.app.write = self.write_app
            self.bindList.append(self.app)
        
        # application image list
        for item in self.appImgList:
            if not app_img_proc(self, item):
                return
        
        # write 
        self.bindList = sorted(self.bindList, key=lambda x:(x.at,x.size))
        for item in self.bindList:
            print(item)
        #  first check confliction 
        end = const.IVT_SIZE
        for item in self.bindList:
            print("Item: %s" % item.file_name)
            print("Item at: 0x%x" % item.at)
            if item.at == 0x200000 or item.at == 0x400000:
                item.size = 0x200000
            print("Item size: 0x%x" % item.size)
            if item.at < end:
                print('item overlapped item.at=' + str(item.at) + " end=" + str(end))
                return
            if item.at >= const.IVT_OFFSET and (item.at + item.size) < (const.IVT_OFFSET + const.IVT_SIZE):
                print("Item [0x%x, +0x%x] overlaps IVT area" % (item.at, item.size))
                return
            end = item.at + item.size
        #  then write
        # write ivt at 0x0
        if self.dcd_at != -1:
            set_le4(new_ivt, const.DCD_OFFSET, self.dcd_at)
            print('DCD at %X' % self.dcd_at)

        if self.FW_IMG_at != -1:
            set_le4(new_ivt, const.FW_IMG_OFFSET, self.FW_IMG_at)
            print('FW_IMGat %X' % self.FW_IMG_at)

        self.output_file.write(new_ivt)
        self.writeOffset = const.IVT_SIZE
        # write bindlist
        for item in self.bindList:
            item.doWrite()

        # write other
        self.write_other()

        #write IVT at IVT_OFFSET
        self.output_file.seek(const.IVT_OFFSET)
        self.output_file.write(new_ivt)
        self.writeOffset = const.IVT_OFFSET + const.IVT_SIZE
        # If a final size was requested, pad the output to that size
        if self.final_size is not None:
            # ensure we are at file end to measure current size
            self.output_file.seek(0, os.SEEK_END)
            cur = self.output_file.tell()
            if cur > self.final_size:
                print("Final image size 0x%x is smaller than output size 0x%x" % (self.final_size, cur))
                return 6
            pad_len = self.final_size - cur
            if pad_len > 0:
                print("Padding output: %d bytes to reach final size 0x%x" % (pad_len, self.final_size))
                pad_file(self.output_file, pad_len, 0xff)

    def __del__(self):
        print("del IvtImage")
        if self.output_file:
           self.output_file.close()
        if self.origin_file:
           self.origin_file.close()

def show_bytes(buf):
    line_number, more = divmod(len(buf), 16)
    for i in range(line_number):
        print(''.join([' %02X' % x for x in buf[i*16:i*16+16]]))
        #print((buf[i*16:i*16+16]).hex())
    if more > 0:
        print(''.join([' %02X' % x for x in buf[i*16:]]))

def get_fileSize(file_name):
    return int(os.path.getsize(file_name))

def align_n(x, n):
    return int((x + n -1) / n) * n

def get_le4(buf):
    return int.from_bytes(buf, byteorder = 'little')

def set_le4(buf, offset, val):
    if len(buf) < 4 + offset:
        return
    val &= 0xffffffff
    buf[offset:offset+4] = val.to_bytes(4, byteorder = 'little')

def get_appInfo(buf):
    app = AppInfo()
    if buf[0:4] != b'\xd5\x00\x00\x60':
        print(buf[0:4])
        return None
    app.start = get_le4(buf[4:8])
    app.entry = get_le4(buf[8:12])
    app.len = get_le4(buf[12:16])
    return app

def app_img_proc(self, item):
    print("Processing file:" + item.file_name)
    with open(item.file_name, 'rb') as tmp_file:
    
        tmp_file.seek(const.IVT_OFFSET)
        tmp_ivt = tmp_file.read(const.IVT_SIZE)
        if len(tmp_ivt) < const.IVT_SIZE:
            print("Read IVT error")
            tmp_file.close()
            return False
        if tmp_ivt[0:4] == b'\xD1\x01\x00\x60':
            print("Get IVT at 0x%x" %const.IVT_OFFSET)
            print('get image from IVT image...')
            tmp_app_off = get_le4(tmp_ivt[0x20:0x24])
            #print('blob app offset %X' % tmp_app_off)
            tmp_file.seek(tmp_app_off)
            tmp_header = tmp_file.read(0x40)
            tmp_app = get_appInfo(tmp_header)
            item.file_name = item.file_name + '.tmp'
            #print('copy file to ' + item.file_name)
            tmp_file.seek(tmp_app_off)
            with open(item.file_name, "wb+") as new_tmp_file:
                copy_file(tmp_file, new_tmp_file)
                new_tmp_file.close()
            
            tmp_file.close()
            
            item.to = tmp_app.start
            item.entry = tmp_app.entry
            item.length = tmp_app.len
            item.size = align_n(tmp_app.len, 0x100)
            #print('bind item: ' + str(item))
            item.write = self.write_bind_file
            self.bindList.append(item)
            return True
        else:
            if item.to != -1 \
                and item.entry != -1:
                item.length = get_fileSize(item.file_name)
                item.size = 0x40 + item.length
                item.write = self.write_app
                self.bindList.append(item)
                
                tmp_file.close()
                
                return True
            else:
                print('Error: TO or ENTRY parameters are missed!')
                return False
                

def copy_file(src, dest):
    length = 0
    while True:
        buf = src.read(512)
        if not buf:
            break
        dest.write(buf)
        length += len(buf)
    return length

def copy_file_with_len(src, dest, length):
    while True:
        buf = src.read(min(512, length))
        if not buf:
            break
        dest.write(buf)
        length -= len(buf)
    return length

def pad_file(f, length, pad):
    buf = bytearray(length)
    if (pad != 0):
        for i in range(len(buf)):
             buf[i] = pad
    f.write(buf)
    
def copy_file_with_len_pad(src, dest, length, pad):
    remain = copy_file_with_len(src, dest, length)
    if remain > 0:
        pad_file(dest, remain, pad)


def parse_size_str(s):
    """Parse human-friendly size strings like '64M', '128K', '1G' into bytes."""
    if not s:
        raise ValueError('empty size')
    v = s.strip()
    v = v.upper()
    # allow trailing B (e.g., MB)
    if v.endswith('B') and len(v) > 1:
        v = v[:-1]
    mul = 1
    if v.endswith('K'):
        mul = 1024
        v = v[:-1]
    elif v.endswith('M'):
        mul = 1024 ** 2
        v = v[:-1]
    elif v.endswith('G'):
        mul = 1024 ** 3
        v = v[:-1]
    elif v.endswith('T'):
        mul = 1024 ** 4
        v = v[:-1]
    if v == '' or v == '-':
        raise ValueError('invalid size')
    # support integer literals (decimal or hex)
    val = int(v, 0)
    return val * mul

def show_usage():
    print("args: config_file\n")

def mk_ivt_cmd(argv):
    if (sys.version_info.major < 3):
        print("Do not support" + str(sys.version_info))
        return
    if len(argv) < 1:
        show_usage()
        return
    print(sys.version_info)
    cfg_file_name = argv[0]
    with open(cfg_file_name, "r") as cfg_file:
        ivt = IvtImage()
        line_number = 0
        while True:
            line = cfg_file.readline(1000).strip()
            if not line:
                break
            line_number += 1
            if not ivt.parseCfg(line):
                print('ERROR @line%d: '%line_number + line)
                return
        ivt.output()

import struct
from Crypto.Cipher import AES

class IVTBuilder:
    """
    Builder for the S32G2 IVT header.
    Automatically computes GMAC using AES-GCM.
    """

    IVT_SIZE = 256
    GMAC_SIZE = 16
    RANDOM_IV_SIZE = 12

    def __init__(
        self,
        ivt_header,
        selftest_dcd_ptr,
        selftest_dcd_ptr_bkp,
        dcd_ptr,
        dcd_ptr_bkp,
        hse_fw_ptr,
        hse_fw_ptr_bkp,
        app_ptr,
        app_ptr_bkp,
        boot_cfg_word,
        lifecycle_word,
        aes_key,        # 16, 24 or 32 bytes
        random_iv       # 12 bytes
    ):
        if len(random_iv) != self.RANDOM_IV_SIZE:
            raise ValueError("random_iv must be 12 bytes")

        self.ivt_header = ivt_header
        self.selftest_dcd_ptr = selftest_dcd_ptr
        self.selftest_dcd_ptr_bkp = selftest_dcd_ptr_bkp
        self.dcd_ptr = dcd_ptr
        self.dcd_ptr_bkp = dcd_ptr_bkp
        self.hse_fw_ptr = hse_fw_ptr
        self.hse_fw_ptr_bkp = hse_fw_ptr_bkp
        self.app_ptr = app_ptr
        self.app_ptr_bkp = app_ptr_bkp
        self.boot_cfg_word = boot_cfg_word
        self.lifecycle_word = lifecycle_word
        self.aes_key = aes_key
        self.random_iv = random_iv

    def _pack(self):
        """Packs all IVT fields except GMAC."""
        data = b""

        # 0x00 – IVT header
        data += struct.pack("<I", self.ivt_header)

        # 0x04 – Reserved
        data += struct.pack("<I", 0)

        # 0x08 – Self-test DCD pointer
        data += struct.pack("<I", self.selftest_dcd_ptr)

        # 0x0C – Self-test DCD pointer (backup)
        data += struct.pack("<I", self.selftest_dcd_ptr_bkp)

        # 0x10 – DCD pointer
        data += struct.pack("<I", self.dcd_ptr)

        # 0x14 – DCD pointer (backup)
        data += struct.pack("<I", self.dcd_ptr_bkp)

        # 0x18 – HSE_H firmware pointer
        data += struct.pack("<I", self.hse_fw_ptr)

        # 0x1C – HSE_H firmware pointer (backup)
        data += struct.pack("<I", self.hse_fw_ptr_bkp)

        # 0x20 – Application boot code pointer
        data += struct.pack("<I", self.app_ptr)

        # 0x24 – Application boot code pointer (backup)
        data += struct.pack("<I", self.app_ptr_bkp)

        # 0x28 – Boot configuration word
        data += struct.pack("<I", self.boot_cfg_word)

        # 0x2C – Life cycle configuration word
        data += struct.pack("<I", self.lifecycle_word)

        # 0x30 – Reserved
        data += struct.pack("<I", 0)

        # 0x34 – Reserved for HSE_H firmware (36 bytes)
        data += b"\x00" * 36

        # 0x58 – Reserved (140 bytes)
        data += b"\x00" * 140

        # 0xE4 – Random IV (12 bytes)
        data += self.random_iv

        # GMAC placeholder (16 bytes)
        data += b"\x00" * self.GMAC_SIZE

        return data

    def _compute_gmac(self, ivt_without_gmac):
        """
        Computes GMAC over the first 240 bytes of the IVT.
        """
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=self.random_iv)
        cipher.update(ivt_without_gmac[:240])
        return cipher.digest()

    def build(self):
        """Builds the final IVT with GMAC included."""
        ivt = self._pack()

        if len(ivt) != self.IVT_SIZE:
            raise RuntimeError(f"IVT must be {self.IVT_SIZE} bytes, got {len(ivt)}")

        gmac = self._compute_gmac(ivt)

        # Replace GMAC at offset 0xF0
        ivt = ivt[:0xF0] + gmac + ivt[0xF0 + self.GMAC_SIZE:]

        return ivt

    def write_to_file(self, filename):
        """Writes the IVT to a binary file."""
        ivt = self.build()
        with open(filename, "wb") as f:
            f.write(ivt)
        return filename

if __name__ == "__main__":
    mk_ivt_cmd(sys.argv[1:])

